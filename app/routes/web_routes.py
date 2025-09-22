from flask import render_template, request, redirect, url_for, flash, send_from_directory, jsonify
from app.routes import main_bp
from app import db
from app.models import Website, ChangeRecord, Keyword
from datetime import datetime
import os

@main_bp.route('/')
def index():
    """主页 - 显示所有网站监控状态"""
    websites = Website.query.all()
    return render_template('index.html', websites=websites)

@main_bp.route('/website/<int:website_id>')
def website_detail(website_id):
    """网站详情页 - 显示变化记录和关键词"""
    website = Website.query.get_or_404(website_id)
    change_records = ChangeRecord.query.filter_by(website_id=website_id)\
                                      .order_by(ChangeRecord.created_at.desc())\
                                      .limit(50).all()
    return render_template('website_detail.html',
                         website=website,
                         change_records=change_records)

@main_bp.route('/add_website', methods=['GET', 'POST'])
def add_website():
    """添加网站页面"""
    if request.method == 'POST':
        name = request.form.get('name')
        url = request.form.get('url')
        check_interval = int(request.form.get('check_interval', 300))
        keywords = request.form.get('keywords', '').split(',')

        if not name or not url:
            flash('网站名称和URL不能为空', 'error')
            return render_template('add_website.html')

        # 创建网站
        website = Website(name=name, url=url, check_interval=check_interval)
        db.session.add(website)
        db.session.flush()  # 获取website.id

        # 添加关键词
        for keyword_text in keywords:
            keyword_text = keyword_text.strip()
            if keyword_text:
                keyword = Keyword(website_id=website.id, keyword=keyword_text)
                db.session.add(keyword)

        db.session.commit()
        flash('网站添加成功', 'success')
        return redirect(url_for('main.index'))

    return render_template('add_website.html')

@main_bp.route('/edit_website/<int:website_id>', methods=['GET', 'POST'])
def edit_website(website_id):
    """编辑网站页面"""
    website = Website.query.get_or_404(website_id)

    if request.method == 'POST':
        website.name = request.form.get('name')
        website.url = request.form.get('url')
        website.check_interval = int(request.form.get('check_interval', 300))
        website.is_active = 'is_active' in request.form

        # 删除现有关键词
        Keyword.query.filter_by(website_id=website_id).delete()

        # 添加新关键词
        keywords = request.form.get('keywords', '').split(',')
        for keyword_text in keywords:
            keyword_text = keyword_text.strip()
            if keyword_text:
                keyword = Keyword(website_id=website.id, keyword=keyword_text)
                db.session.add(keyword)

        db.session.commit()
        flash('网站信息更新成功', 'success')
        return redirect(url_for('main.website_detail', website_id=website_id))

    return render_template('edit_website.html', website=website)

@main_bp.route('/delete_website/<int:website_id>', methods=['POST'])
def delete_website(website_id):
    """删除网站"""
    website = Website.query.get_or_404(website_id)
    db.session.delete(website)
    db.session.commit()
    flash('网站删除成功', 'success')
    return redirect(url_for('main.index'))

@main_bp.route('/changes')
def changes_list():
    """变化记录列表页"""
    page = request.args.get('page', 1, type=int)
    changes = ChangeRecord.query.order_by(ChangeRecord.created_at.desc())\
                                .paginate(
                                    page=page,
                                    per_page=20,
                                    error_out=False
                                )
    return render_template('changes_list.html', changes=changes)

@main_bp.route('/logs')
def logs():
    """日志页面"""
    return render_template('logs.html')

@main_bp.route('/api/logs')
def api_logs():
    """获取最新日志"""
    limit = request.args.get('limit', 50, type=int)

    # 获取最新的变化记录作为日志
    records = ChangeRecord.query.join(Website)\
                                .order_by(ChangeRecord.created_at.desc())\
                                .limit(limit).all()

    logs = []
    for record in records:
        logs.append({
            'id': record.id,
            'timestamp': record.created_at.strftime('%Y-%m-%d %H:%M:%S') if record.created_at else '',
            'website_name': record.website.name,
            'website_url': record.website.url,
            'change_type': record.change_type,
            'notification_sent': record.notification_sent,
            'matched_keywords': record.matched_keywords,
            'created_at_iso': record.created_at.isoformat() if record.created_at else ''
        })

    return jsonify({
        'success': True,
        'logs': logs,
        'total': len(logs)
    })

@main_bp.route('/api/system/status')
def system_status():
    """获取系统状态"""
    active_websites = Website.query.filter_by(is_active=True).count()
    total_websites = Website.query.count()

    # 获取最后一次检查时间
    last_record = ChangeRecord.query.order_by(ChangeRecord.created_at.desc()).first()
    last_check = last_record.created_at if last_record else None

    return jsonify({
        'success': True,
        'data': {
            'active_websites': active_websites,
            'total_websites': total_websites,
            'last_check': last_check.strftime('%H:%M:%S') if last_check else None,
            'status': 'online',
            'timestamp': datetime.utcnow().isoformat()
        }
    })

@main_bp.route('/favicon.ico')
def favicon():
    """返回favicon"""
    return send_from_directory(os.path.join(main_bp.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')