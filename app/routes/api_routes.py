from flask import jsonify, request
from app.routes import main_bp
from app import db
from app.models import Website, ChangeRecord, Keyword
from app.services.monitor import WebsiteMonitor

@main_bp.route('/api/websites', methods=['GET'])
def api_get_websites():
    """获取所有网站列表"""
    websites = Website.query.all()
    return jsonify([website.to_dict() for website in websites])

@main_bp.route('/api/websites', methods=['POST'])
def api_create_website():
    """创建新网站"""
    data = request.get_json()

    if not data or not data.get('name') or not data.get('url'):
        return jsonify({'error': '网站名称和URL不能为空'}), 400

    website = Website(
        name=data['name'],
        url=data['url'],
        check_interval=data.get('check_interval', 300),
        is_active=data.get('is_active', True)
    )

    db.session.add(website)
    db.session.flush()

    # 添加关键词
    keywords = data.get('keywords', [])
    for keyword_text in keywords:
        if keyword_text.strip():
            keyword = Keyword(website_id=website.id, keyword=keyword_text.strip())
            db.session.add(keyword)

    db.session.commit()

    return jsonify(website.to_dict()), 201

@main_bp.route('/api/websites/<int:website_id>', methods=['GET'])
def api_get_website(website_id):
    """获取单个网站信息"""
    website = Website.query.get_or_404(website_id)
    return jsonify(website.to_dict())

@main_bp.route('/api/websites/<int:website_id>', methods=['PUT'])
def api_update_website(website_id):
    """更新网站信息"""
    website = Website.query.get_or_404(website_id)
    data = request.get_json()

    if data.get('name'):
        website.name = data['name']
    if data.get('url'):
        website.url = data['url']
    if 'check_interval' in data:
        website.check_interval = data['check_interval']
    if 'is_active' in data:
        website.is_active = data['is_active']

    # 更新关键词
    if 'keywords' in data:
        Keyword.query.filter_by(website_id=website_id).delete()
        for keyword_text in data['keywords']:
            if keyword_text.strip():
                keyword = Keyword(website_id=website.id, keyword=keyword_text.strip())
                db.session.add(keyword)

    db.session.commit()
    return jsonify(website.to_dict())

@main_bp.route('/api/websites/<int:website_id>', methods=['DELETE'])
def api_delete_website(website_id):
    """删除网站"""
    website = Website.query.get_or_404(website_id)
    db.session.delete(website)
    db.session.commit()
    return jsonify({'message': '网站删除成功'})

@main_bp.route('/api/websites/<int:website_id>/check', methods=['POST'])
def api_check_website(website_id):
    """手动检查网站"""
    website = Website.query.get_or_404(website_id)
    monitor = WebsiteMonitor()

    try:
        result = monitor.monitor_website(website)
        return jsonify({'success': result, 'message': '检查完成'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@main_bp.route('/api/changes', methods=['GET'])
def api_get_changes():
    """获取变化记录"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    website_id = request.args.get('website_id', type=int)

    query = ChangeRecord.query
    if website_id:
        query = query.filter_by(website_id=website_id)

    changes = query.order_by(ChangeRecord.created_at.desc())\
                   .paginate(
                       page=page,
                       per_page=per_page,
                       error_out=False
                   )

    return jsonify({
        'changes': [change.to_dict() for change in changes.items],
        'total': changes.total,
        'pages': changes.pages,
        'current_page': changes.page
    })

@main_bp.route('/api/status', methods=['GET'])
def api_status():
    """获取系统状态"""
    website_count = Website.query.count()
    active_website_count = Website.query.filter_by(is_active=True).count()
    recent_changes_count = ChangeRecord.query.filter(
        ChangeRecord.created_at >= db.func.date('now', '-1 day')
    ).count()

    return jsonify({
        'total_websites': website_count,
        'active_websites': active_website_count,
        'recent_changes': recent_changes_count,
        'status': 'running'
    })