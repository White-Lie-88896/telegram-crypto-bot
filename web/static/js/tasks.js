// 任务管理模块
const TaskManager = {
    tasks: [],

    // 初始化
    async init() {
        await this.loadTasks();
        this.setupEventListeners();
    },

    // 加载任务列表
    async loadTasks() {
        try {
            const tasks = await api.get('/tasks');
            if (tasks) {
                this.tasks = tasks;
                this.renderTaskList();
            }
        } catch (error) {
            console.error('Error loading tasks:', error);
        }
    },

    // 渲染任务列表
    renderTaskList() {
        const container = document.getElementById('tasks-list-container');
        if (!container) return;

        container.innerHTML = '';

        if (this.tasks.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                        <path d="M2 17l10 5 10-5"/>
                        <path d="M2 12l10 5 10-5"/>
                    </svg>
                    <h3>还没有监控任务</h3>
                    <p>点击"创建任务"按钮添加您的第一个监控任务</p>
                    <button class="btn-primary" onclick="TaskManager.showCreateDialog()">创建任务</button>
                </div>
            `;
            return;
        }

        this.tasks.forEach(task => {
            const card = this.createTaskCard(task);
            container.appendChild(card);
        });
    },

    // 创建任务卡片
    createTaskCard(task) {
        const card = document.createElement('div');
        card.className = 'task-card';

        const statusClass = task.status === 'ACTIVE' ? 'success' : 'inactive';
        const ruleTypeName = {
            'PRICE_THRESHOLD': '价格阈值',
            'PERCENTAGE': '百分比涨跌'
        }[task.rule_type] || task.rule_type;

        // 解析规则配置
        let ruleDetail = '';
        try {
            const config = typeof task.rule_config === 'string'
                ? JSON.parse(task.rule_config)
                : task.rule_config;

            if (task.rule_type === 'PRICE_THRESHOLD') {
                if (config.threshold_high) {
                    ruleDetail = `目标价格: ≥ $${config.threshold_high}`;
                } else if (config.threshold_low) {
                    ruleDetail = `目标价格: ≤ $${config.threshold_low}`;
                }
            } else if (task.rule_type === 'PERCENTAGE') {
                ruleDetail = `涨跌幅: ${config.percentage_threshold}%`;
            }
        } catch (e) {
            ruleDetail = '配置错误';
        }

        const lastTriggered = task.last_triggered_at
            ? `最后触发: ${utils.formatTime(task.last_triggered_at)}`
            : '从未触发';

        card.innerHTML = `
            <div class="task-card-header">
                <div class="task-symbol">
                    <span class="symbol-badge">${DOMUtils.escapeHtml(task.symbol)}</span>
                    <span class="status-badge ${statusClass}">${task.status}</span>
                </div>
                <div class="task-actions">
                    <button class="icon-btn" onclick="TaskManager.deleteTask(${task.task_id})" title="删除任务">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="3 6 5 6 21 6"></polyline>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                        </svg>
                    </button>
                </div>
            </div>
            <div class="task-card-body">
                <div class="task-detail">
                    <span class="detail-label">规则类型:</span>
                    <span class="detail-value">${DOMUtils.escapeHtml(ruleTypeName)}</span>
                </div>
                <div class="task-detail">
                    <span class="detail-label">规则详情:</span>
                    <span class="detail-value">${DOMUtils.escapeHtml(ruleDetail)}</span>
                </div>
                <div class="task-detail">
                    <span class="detail-label">用户ID:</span>
                    <span class="detail-value">${task.user_id}</span>
                </div>
                <div class="task-detail">
                    <span class="detail-label">创建时间:</span>
                    <span class="detail-value">${new Date(task.created_at).toLocaleDateString('zh-CN')}</span>
                </div>
                <div class="task-detail">
                    <span class="detail-label">触发状态:</span>
                    <span class="detail-value">${lastTriggered}</span>
                </div>
            </div>
        `;

        return card;
    },

    // 显示创建任务对话框
    showCreateDialog() {
        const dialog = document.getElementById('create-task-modal');
        if (dialog) {
            dialog.style.display = 'flex';
            // 重置表单
            document.getElementById('create-task-form').reset();
            this.updateRuleFields();
        }
    },

    // 隐藏创建任务对话框
    hideCreateDialog() {
        const dialog = document.getElementById('create-task-modal');
        if (dialog) {
            dialog.style.display = 'none';
        }
    },

    // 根据规则类型更新表单字段
    updateRuleFields() {
        const ruleType = document.getElementById('task-rule-type').value;
        const priceFields = document.getElementById('price-threshold-fields');
        const percentFields = document.getElementById('percentage-fields');

        if (ruleType === 'PRICE_THRESHOLD') {
            priceFields.style.display = 'block';
            percentFields.style.display = 'none';
        } else if (ruleType === 'PERCENTAGE') {
            priceFields.style.display = 'none';
            percentFields.style.display = 'block';
        }
    },

    // 创建任务
    async createTask(event) {
        event.preventDefault();

        const form = event.target;
        const formData = new FormData(form);

        const userId = parseInt(formData.get('user_id'));
        const symbol = formData.get('symbol').toUpperCase();
        const ruleType = formData.get('rule_type');

        // 构建规则配置
        let ruleConfig = {};
        if (ruleType === 'PRICE_THRESHOLD') {
            const condition = formData.get('price_condition');
            const price = parseFloat(formData.get('threshold_price'));

            if (condition === 'above') {
                ruleConfig.threshold_high = price;
            } else {
                ruleConfig.threshold_low = price;
            }
        } else if (ruleType === 'PERCENTAGE') {
            ruleConfig.percentage_threshold = parseFloat(formData.get('percentage_threshold'));
            ruleConfig.reference_price = parseFloat(formData.get('reference_price'));
        }

        const taskData = {
            user_id: userId,
            symbol: symbol,
            rule_type: ruleType,
            rule_config: ruleConfig
        };

        // 显示加载状态
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        submitBtn.disabled = true;
        submitBtn.textContent = '创建中...';

        try {
            const result = await api.post('/tasks', taskData);

            if (result && result.success) {
                // 成功
                showSuccessNotification('任务创建成功');
                this.hideCreateDialog();
                await this.loadTasks();
            } else {
                showErrorNotification(result?.error || '任务创建失败');
            }
        } catch (error) {
            console.error('Create task error:', error);
            showErrorNotification('任务创建失败');
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        }
    },

    // 删除任务
    async deleteTask(taskId) {
        if (!confirm('确定要删除这个监控任务吗？')) {
            return;
        }

        try {
            const result = await api.delete(`/tasks/${taskId}`);

            if (result && result.success) {
                showSuccessNotification('任务删除成功');
                await this.loadTasks();
            } else {
                showErrorNotification(result?.error || '任务删除失败');
            }
        } catch (error) {
            console.error('Delete task error:', error);
            showErrorNotification('任务删除失败');
        }
    },

    // 设置事件监听器
    setupEventListeners() {
        // 规则类型改变时更新字段
        const ruleTypeSelect = document.getElementById('task-rule-type');
        if (ruleTypeSelect) {
            ruleTypeSelect.addEventListener('change', () => this.updateRuleFields());
        }

        // 表单提交
        const createForm = document.getElementById('create-task-form');
        if (createForm) {
            createForm.addEventListener('submit', (e) => this.createTask(e));
        }

        // 关闭对话框
        const closeBtn = document.querySelector('.modal-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.hideCreateDialog());
        }

        // 点击背景关闭
        const modal = document.getElementById('create-task-modal');
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.hideCreateDialog();
                }
            });
        }
    }
};

// 通知函数
function showSuccessNotification(message) {
    showNotification(message, 'success');
}

function showErrorNotification(message) {
    showNotification(message, 'error');
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;

    document.body.appendChild(notification);

    // 显示动画
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);

    // 3秒后移除
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

// 导出
window.TaskManager = TaskManager;
