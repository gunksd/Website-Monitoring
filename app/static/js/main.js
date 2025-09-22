// 网站监控系统前端脚本

// DOM加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 初始化提示框
    initTooltips();

    // 自动刷新状态
    startAutoRefresh();

    // 表单验证
    initFormValidation();
});

// 初始化Bootstrap提示框
function initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// 开始自动刷新（仅在首页）
function startAutoRefresh() {
    if (window.location.pathname === '/') {
        // 每5分钟刷新一次页面状态
        setInterval(function() {
            updateWebsiteStatus();
        }, 300000); // 5分钟
    }
}

// 更新网站状态（AJAX）
function updateWebsiteStatus() {
    fetch('/api/status')
        .then(response => response.json())
        .then(data => {
            console.log('Status updated:', data);
            // 可以在这里更新页面上的状态信息
        })
        .catch(error => {
            console.error('Failed to update status:', error);
        });
}

// 初始化表单验证
function initFormValidation() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
}

// 显示通知消息
function showAlert(message, type = 'info', duration = 5000) {
    const alertContainer = document.getElementById('alert-container') || createAlertContainer();

    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    alertContainer.appendChild(alertDiv);

    // 自动移除通知
    if (duration > 0) {
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, duration);
    }

    return alertDiv;
}

// 创建通知容器
function createAlertContainer() {
    const container = document.createElement('div');
    container.id = 'alert-container';
    container.style.position = 'fixed';
    container.style.top = '20px';
    container.style.right = '20px';
    container.style.zIndex = '9999';
    container.style.maxWidth = '400px';
    document.body.appendChild(container);
    return container;
}

// 检查网站状态
async function checkWebsite(websiteId) {
    const button = event.target.closest('button');
    const originalContent = button.innerHTML;

    try {
        // 显示加载状态
        button.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>检查中...';
        button.disabled = true;

        const response = await fetch(`/api/websites/${websiteId}/check`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        const data = await response.json();

        if (response.ok && data.success) {
            showAlert('网站检查完成！', 'success');

            // 如果在详情页面，延迟刷新以显示最新结果
            if (window.location.pathname.includes('/website/')) {
                setTimeout(() => {
                    window.location.reload();
                }, 1500);
            }
        } else {
            throw new Error(data.error || '检查失败');
        }
    } catch (error) {
        showAlert(`检查失败: ${error.message}`, 'danger');
    } finally {
        // 恢复按钮状态
        button.innerHTML = originalContent;
        button.disabled = false;
    }
}

// 删除确认
function confirmDelete(message = '确定要执行此操作吗？') {
    return confirm(message);
}

// 复制到剪贴板
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        showAlert('已复制到剪贴板', 'success', 2000);
    }, function(err) {
        showAlert('复制失败', 'danger', 3000);
    });
}

// 格式化时间显示
function formatRelativeTime(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) {
        return '刚刚';
    } else if (diffMins < 60) {
        return `${diffMins}分钟前`;
    } else if (diffHours < 24) {
        return `${diffHours}小时前`;
    } else if (diffDays < 30) {
        return `${diffDays}天前`;
    } else {
        return date.toLocaleDateString('zh-CN');
    }
}

// 更新所有相对时间显示
function updateRelativeTimes() {
    const timeElements = document.querySelectorAll('[data-time]');
    timeElements.forEach(element => {
        const dateString = element.getAttribute('data-time');
        element.textContent = formatRelativeTime(dateString);
    });
}

// 搜索功能
function initSearch() {
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const query = this.value.toLowerCase();
            const items = document.querySelectorAll('.searchable-item');

            items.forEach(item => {
                const text = item.textContent.toLowerCase();
                if (text.includes(query)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        });
    }
}

// 批量操作
function initBatchOperations() {
    const selectAllCheckbox = document.getElementById('select-all');
    const itemCheckboxes = document.querySelectorAll('.item-checkbox');

    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            itemCheckboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
            updateBatchActions();
        });
    }

    itemCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', updateBatchActions);
    });
}

// 更新批量操作按钮状态
function updateBatchActions() {
    const checkedItems = document.querySelectorAll('.item-checkbox:checked');
    const batchActionButtons = document.querySelectorAll('.batch-action');

    batchActionButtons.forEach(button => {
        button.disabled = checkedItems.length === 0;
    });
}

// 页面可见性变化处理
document.addEventListener('visibilitychange', function() {
    if (!document.hidden) {
        // 页面重新可见时，更新相对时间
        updateRelativeTimes();
    }
});

// 错误处理
window.addEventListener('error', function(event) {
    console.error('JavaScript Error:', event.error);
    showAlert('页面发生错误，请刷新页面重试', 'danger');
});

// 网络状态监测
window.addEventListener('online', function() {
    showAlert('网络连接已恢复', 'success', 3000);
});

window.addEventListener('offline', function() {
    showAlert('网络连接已断开', 'warning', 0);
});

// 导出功能
function exportData(type, websiteId = null) {
    let url = `/api/export/${type}`;
    if (websiteId) {
        url += `?website_id=${websiteId}`;
    }

    fetch(url)
        .then(response => {
            if (response.ok) {
                return response.blob();
            }
            throw new Error('导出失败');
        })
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `website_monitor_${type}_${new Date().toISOString().split('T')[0]}.csv`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            showAlert('导出成功', 'success');
        })
        .catch(error => {
            showAlert(`导出失败: ${error.message}`, 'danger');
        });
}

// 设备响应式处理
function handleResponsiveChanges() {
    const isMobile = window.innerWidth <= 768;

    // 在移动设备上隐藏某些列
    const hideOnMobile = document.querySelectorAll('.hide-on-mobile');
    hideOnMobile.forEach(element => {
        element.style.display = isMobile ? 'none' : '';
    });
}

// 监听窗口大小变化
window.addEventListener('resize', handleResponsiveChanges);

// 页面加载时执行一次
handleResponsiveChanges();