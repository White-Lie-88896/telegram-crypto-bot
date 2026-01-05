// Apple风格Web管理后台 - JavaScript

// API基础配置
const API_BASE = '/api';
const WS_BASE = 'ws://localhost:8080';

// 状态管理
const state = {
    prices: {},
    tasks: [],
    alerts: [],
    systemStatus: {}
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

// API请求封装
const api = {
    async get(endpoint) {
        try {
            const response = await fetch(`${API_BASE}${endpoint}`);
            if (!response.ok) throw new Error('Network response was not ok');
            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            return null;
        }
    },

    async post(endpoint, data) {
        try {
            const response = await fetch(`${API_BASE}${endpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
            if (!response.ok) throw new Error('Network response was not ok');
            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            return null;
        }
    }
};

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
        // 模拟数据 - 实际应从后端API获取
        const stats = {
            activeTasks: 12,
            alertCount: 8,
            apiUptime: 98.5,
            userCount: 5
        };

        document.getElementById('active-tasks').textContent = stats.activeTasks;
        document.getElementById('alert-count').textContent = stats.alertCount;
        document.getElementById('user-count').textContent = stats.userCount;
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// 加载实时价格
async function loadPrices() {
    try {
        // 模拟数据 - 实际应从后端API获取
        const priceData = {
            'BTC': { price: 89915.00, change: 0.73 },
            'ETH': { price: 3102.17, change: -1.24 },
            'SOL': { price: 145.23, change: 2.56 },
            'ADA': { price: 0.8524, change: -0.45 },
            'BNB': { price: 612.34, change: 1.89 },
            'XRP': { price: 1.23, change: 3.45 }
        };

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

// 创建价格卡片
function createPriceCard(symbol, data) {
    const card = document.createElement('div');
    card.className = 'price-card';

    const changeClass = data.change >= 0 ? 'up' : 'down';
    const changeSymbol = data.change >= 0 ? '↗' : '↘';

    card.innerHTML = `
        <div class="price-symbol">${symbol}</div>
        <div class="price-value">${utils.formatPrice(data.price)}</div>
        <div class="price-change ${changeClass}">
            ${utils.formatPercentage(data.change)} ${changeSymbol}
        </div>
    `;

    return card;
}

// 加载预警历史
async function loadAlerts() {
    try {
        // 模拟数据 - 实际应从后端API获取
        const alerts = [
            {
                time: Date.now() - 300000,
                symbol: 'BTC',
                type: '价格阈值',
                condition: '≥ $90,000',
                price: 90125.00,
                status: 'success'
            },
            {
                time: Date.now() - 1800000,
                symbol: 'ETH',
                type: '百分比涨跌',
                condition: '涨幅 ≥ 5%',
                price: 3150.50,
                status: 'success'
            },
            {
                time: Date.now() - 3600000,
                symbol: 'SOL',
                type: '价格阈值',
                condition: '≤ $140',
                price: 139.80,
                status: 'success'
            }
        ];

        const alertsTable = document.getElementById('alerts-table');
        alertsTable.innerHTML = '';

        alerts.forEach(alert => {
            const row = createAlertRow(alert);
            alertsTable.appendChild(row);
        });

        state.alerts = alerts;
    } catch (error) {
        console.error('Error loading alerts:', error);
    }
}

// 创建预警表格行
function createAlertRow(alert) {
    const row = document.createElement('tr');
    row.innerHTML = `
        <td>${utils.formatTime(alert.time)}</td>
        <td><strong>${alert.symbol}</strong></td>
        <td>${alert.type}</td>
        <td>${alert.condition}</td>
        <td>${utils.formatPrice(alert.price)}</td>
        <td><span class="status-badge ${alert.status}">已发送</span></td>
    `;
    return row;
}

// 加载系统状态
async function loadSystemStatus() {
    try {
        // 更新最后检查时间
        const now = new Date();
        const timeStr = now.toLocaleTimeString('zh-CN', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
        document.getElementById('last-check').textContent = timeStr;

        // 模拟数据库信息
        document.getElementById('db-records').textContent = '1,234';
        document.getElementById('db-size').textContent = '2.4 MB';
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
