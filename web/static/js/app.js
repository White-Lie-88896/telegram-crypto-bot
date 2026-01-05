// Apple风格Web管理后台 - JavaScript

// API基础配置
const API_BASE = '/api';
// 动态WebSocket协议
const WS_PROTOCOL = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const WS_HOST = window.location.hostname;
const WS_PORT = window.location.port || '8888';
const WS_BASE = `${WS_PROTOCOL}//${WS_HOST}:${WS_PORT}`;

// 状态管理
const state = {
    prices: {},
    tasks: [],
    alerts: [],
    systemStatus: {}
};

// DOM安全工具（防止XSS）
const DOMUtils = {
    // 转义HTML特殊字符
    escapeHtml(unsafe) {
        if (typeof unsafe !== 'string') return String(unsafe);
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    },

    // 安全创建元素
    createElement(tag, attributes = {}, textContent = '') {
        const element = document.createElement(tag);
        for (const [key, value] of Object.entries(attributes)) {
            if (key === 'className') {
                element.className = value;
            } else {
                element.setAttribute(key, value);
            }
        }
        if (textContent) {
            element.textContent = textContent;  // textContent 自动转义
        }
        return element;
    }
};

// 工具函数
const utils = {
    // 格式化数字
    formatNumber(num, decimals = 2) {
        if (num >= 1000) {
            return num.toLocaleString('en-US', {
                minimumFractionDigits: decimals,
                maximumFractionDigits: decimals
            });
        }
        return num.toFixed(decimals);
    },

    // 格式化价格
    formatPrice(price) {
        if (price >= 1000) return `$${this.formatNumber(price, 2)}`;
        if (price >= 1) return `$${this.formatNumber(price, 4)}`;
        return `$${this.formatNumber(price, 6)}`;
    },

    // 格式化时间
    formatTime(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now - date;

        if (diff < 60000) return '刚刚';
        if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`;
        if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`;
        return date.toLocaleDateString('zh-CN');
    },

    // 格式化百分比
    formatPercentage(value) {
        const sign = value >= 0 ? '+' : '';
        return `${sign}${value.toFixed(2)}%`;
    }
};

// CSRF Token管理
function getCsrfToken() {
    return document.cookie.split('; ')
        .find(row => row.startsWith('csrf_token='))
        ?.split('=')[1] || '';
}

// API请求封装
const api = {
    async get(endpoint) {
        try {
            const response = await fetch(`${API_BASE}${endpoint}`, {
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include'
            });
            if (!response.ok) {
                if (response.status === 401) {
                    window.location.href = '/login.html';
                    return null;
                }
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            showError(`API请求失败: ${error.message}`);
            return null;
        }
    },

    async post(endpoint, data) {
        try {
            const response = await fetch(`${API_BASE}${endpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': getCsrfToken()
                },
                credentials: 'include',
                body: JSON.stringify(data)
            });
            if (!response.ok) {
                if (response.status === 401) {
                    window.location.href = '/login.html';
                    return null;
                }
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            showError(`API请求失败: ${error.message}`);
            return null;
        }
    },

    async delete(endpoint) {
        try {
            const response = await fetch(`${API_BASE}${endpoint}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': getCsrfToken()
                },
                credentials: 'include'
            });
            if (!response.ok) {
                if (response.status === 401) {
                    window.location.href = '/login.html';
                    return null;
                }
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            showError(`API请求失败: ${error.message}`);
            return null;
        }
    }
};

// 错误提示
function showError(message) {
    console.error(message);
    // 可以在这里添加UI提示
}

// 数据加载函数
async function loadDashboardData() {
    // 加载统计数据
    await loadStats();

    // 加载实时价格
    await loadPrices();

    // 加载最近预警
    await loadAlerts();

    // 加载系统状态
    await loadSystemStatus();
}

// 加载统计数据
async function loadStats() {
    try {
        const stats = await api.get('/stats');
        if (!stats) return;

        document.getElementById('active-tasks').textContent = stats.activeTasks || 0;
        document.getElementById('alert-count').textContent = stats.alertCount || 0;
        document.getElementById('user-count').textContent = stats.userCount || 0;
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// 加载实时价格
async function loadPrices() {
    try {
        const priceData = await api.get('/prices');
        if (!priceData) return;

        const priceGrid = document.getElementById('price-grid');
        priceGrid.innerHTML = '';

        Object.entries(priceData).forEach(([symbol, data]) => {
            const card = createPriceCard(symbol, data);
            priceGrid.appendChild(card);
        });

        state.prices = priceData;
    } catch (error) {
        console.error('Error loading prices:', error);
    }
}

// 创建价格卡片（安全版本，防止XSS）
function createPriceCard(symbol, data) {
    const card = document.createElement('div');
    card.className = 'price-card';

    const changeClass = data.change >= 0 ? 'up' : 'down';
    const changeSymbol = data.change >= 0 ? '↗' : '↘';

    // 使用安全的DOM创建方法
    const symbolDiv = DOMUtils.createElement('div', {className: 'price-symbol'}, symbol);
    const valueDiv = DOMUtils.createElement('div', {className: 'price-value'}, utils.formatPrice(data.price));
    const changeDiv = DOMUtils.createElement('div', {className: `price-change ${changeClass}`},
        `${utils.formatPercentage(data.change)} ${changeSymbol}`);

    card.appendChild(symbolDiv);
    card.appendChild(valueDiv);
    card.appendChild(changeDiv);

    return card;
}

// 加载预警历史
async function loadAlerts() {
    try {
        const alerts = await api.get('/alerts?limit=10');
        if (!alerts) return;

        const alertsTable = document.getElementById('alerts-table');
        alertsTable.innerHTML = '';

        alerts.forEach(alert => {
            const row = createAlertRow({
                time: new Date(alert.triggered_at).getTime(),
                symbol: alert.symbol,
                type: alert.task_id ? '监控预警' : '系统预警',
                condition: parseAlertMessage(alert.message),
                price: alert.trigger_price,
                status: alert.sent_success ? 'success' : 'error'
            });
            alertsTable.appendChild(row);
        });

        state.alerts = alerts;
    } catch (error) {
        console.error('Error loading alerts:', error);
    }
}

// 解析预警消息，提取触发条件
function parseAlertMessage(message) {
    // 从消息中提取关键信息
    if (message.includes('突破') || message.includes('跌破')) {
        const match = message.match(/(\d+\.?\d*)/);
        return match ? `价格 ${message.includes('突破') ? '≥' : '≤'} $${match[1]}` : '价格预警';
    } else if (message.includes('涨') || message.includes('跌')) {
        const match = message.match(/([+-]?\d+\.?\d*)%/);
        return match ? `涨跌 ${match[1]}%` : '涨跌预警';
    }
    return '预警触发';
}

// 创建预警表格行（安全版本，防止XSS）
function createAlertRow(alert) {
    const row = document.createElement('tr');

    // 安全创建各个单元格
    const timeCell = DOMUtils.createElement('td', {}, utils.formatTime(alert.time));

    const symbolCell = document.createElement('td');
    const symbolStrong = DOMUtils.createElement('strong', {}, alert.symbol);
    symbolCell.appendChild(symbolStrong);

    const typeCell = DOMUtils.createElement('td', {}, alert.type);
    const conditionCell = DOMUtils.createElement('td', {}, alert.condition);
    const priceCell = DOMUtils.createElement('td', {}, utils.formatPrice(alert.price));

    const statusCell = document.createElement('td');
    const statusBadge = DOMUtils.createElement('span', {className: `status-badge ${alert.status}`}, '已发送');
    statusCell.appendChild(statusBadge);

    row.appendChild(timeCell);
    row.appendChild(symbolCell);
    row.appendChild(typeCell);
    row.appendChild(conditionCell);
    row.appendChild(priceCell);
    row.appendChild(statusCell);

    return row;
}

// 加载系统状态
async function loadSystemStatus() {
    try {
        const systemStatus = await api.get('/system');
        if (!systemStatus) return;

        // 更新监控引擎状态
        if (systemStatus.monitorEngine) {
            const lastCheck = new Date(systemStatus.monitorEngine.lastCheck);
            document.getElementById('last-check').textContent = lastCheck.toLocaleTimeString('zh-CN');
        }

        // 更新数据库信息
        if (systemStatus.database) {
            document.getElementById('db-records').textContent = systemStatus.database.records.toLocaleString();
            document.getElementById('db-size').textContent = systemStatus.database.size;
        }

        state.systemStatus = systemStatus;
    } catch (error) {
        console.error('Error loading system status:', error);
    }
}

// 实时更新功能
function startRealtimeUpdates() {
    // 每30秒更新一次价格
    setInterval(() => {
        loadPrices();
        loadSystemStatus();
    }, 30000);

    // 每60秒更新一次统计数据
    setInterval(() => {
        loadStats();
    }, 60000);
}

// WebSocket连接（可选，用于实时推送）
function connectWebSocket() {
    try {
        const ws = new WebSocket(WS_BASE);

        ws.onopen = () => {
            console.log('WebSocket connected');
        };

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            handleWebSocketMessage(data);
        };

        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };

        ws.onclose = () => {
            console.log('WebSocket disconnected, reconnecting...');
            setTimeout(connectWebSocket, 5000);
        };
    } catch (error) {
        console.error('WebSocket connection failed:', error);
    }
}

// 处理WebSocket消息
function handleWebSocketMessage(data) {
    switch(data.type) {
        case 'price_update':
            updatePrice(data.symbol, data.price, data.change);
            break;
        case 'new_alert':
            addNewAlert(data.alert);
            break;
        case 'task_update':
            updateTaskStatus(data.task);
            break;
        default:
            console.log('Unknown message type:', data.type);
    }
}

// 更新价格
function updatePrice(symbol, price, change) {
    if (state.prices[symbol]) {
        state.prices[symbol] = { price, change };
        loadPrices();
    }
}

// 添加新预警
function addNewAlert(alert) {
    state.alerts.unshift(alert);
    if (state.alerts.length > 10) {
        state.alerts.pop();
    }
    loadAlerts();

    // 显示通知
    showNotification('新预警', `${alert.symbol} ${alert.type} 触发`);
}

// 显示通知
function showNotification(title, message) {
    if ('Notification' in window && Notification.permission === 'granted') {
        new Notification(title, {
            body: message,
            icon: '/static/images/logo.png'
        });
    }
}

// 请求通知权限
function requestNotificationPermission() {
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    // 加载仪表板数据
    loadDashboardData();

    // 启动实时更新
    startRealtimeUpdates();

    // 请求通知权限
    requestNotificationPermission();

    // 连接WebSocket（可选）
    // connectWebSocket();

    console.log('Dashboard initialized');
});

// 导航功能
document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', (e) => {
        e.preventDefault();

        // 移除所有活动状态
        document.querySelectorAll('.nav-item').forEach(nav => {
            nav.classList.remove('active');
        });

        // 添加活动状态
        item.classList.add('active');

        // 这里可以添加页面切换逻辑
        const href = item.getAttribute('href');
        console.log('Navigate to:', href);
    });
});

// 刷新按钮
document.querySelectorAll('.btn-secondary').forEach(button => {
    button.addEventListener('click', () => {
        loadDashboardData();

        // 添加刷新动画
        button.style.opacity = '0.5';
        setTimeout(() => {
            button.style.opacity = '1';
        }, 500);
    });
});

// 导出给全局使用
window.dashboardApp = {
    loadDashboardData,
    loadPrices,
    loadAlerts,
    utils,
    state
};
