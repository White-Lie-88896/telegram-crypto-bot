<p align="center">
  <h1 align="center">📊 Telegram 加密货币监控 Bot</h1>
  <p align="center">
    <em>实时价格查询 · 智能预警监控 · 定时价格汇报</em>
  </p>
  <p align="center">
    <a href="#功能特性">功能</a> •
    <a href="#快速开始">开始使用</a> •
    <a href="#使用指南">使用指南</a> •
    <a href="#部署">部署</a> •
    <a href="#技术架构">技术</a>
  </p>
</p>

---

## ✨ 功能特性

### 🔍 实时价格查询
- 查询任意加密货币的实时价格
- 数据来源：**Binance**（与 TradingView 一致）
- 支持 BTC、ETH、ADA、SOL 等主流币种
- 24小时价格变化、最高最低价等详细信息

### 🚨 智能价格预警

#### 📌 价格阈值监控
当价格突破设定的上限或下限时自动推送通知
```
示例：BTC 价格达到 $50,000 时提醒
     ETH 价格跌破 $2,800 时提醒
```

#### 📈 百分比涨跌监控
基于参考价格，当涨跌幅达到指定百分比时触发预警
```
示例：BTC 相对 $90,000 涨幅达到 5% 时提醒
     ETH 相对 $3,000 跌幅超过 10% 时提醒
```

### ⏰ 定时价格汇报
- 每 5 分钟自动推送 BTC、ETH、ADA 价格
- 精美的排版格式，带加密货币符号
- 可配置推送到个人或群组

### 🔐 安全可靠
- systemd 服务管理，开机自启
- 自动崩溃恢复机制
- 完整的日志记录
- 防骚扰冷却时间设置

---

## 📸 功能展示

### 实时价格查询
```
💰 BTC 价格信息

━━━━━━━━━━━━━━━━━━━━━━
📊 当前价格：$89,915.00
━━━━━━━━━━━━━━━━━━━━━━

24h 最高：$90,961.81
24h 最低：$88,459.96
24h 涨跌：+0.73% ↗️
24h 成交量：15,101.53 BTC

⏰ 更新时间：03:45:23
💡 数据来源：Binance
```

### 价格预警通知
```
🔴 BTC 价格预警

当前价格: $50,125.00
已达到上限: $50,000.00

📈 突破上限阈值！
```

### 定时价格汇报
```
┌─────────────────────────┐
│  📊 价格汇报 03:50:00  │
└─────────────────────────┘

₿ BTC: $89,915.00
⟠ ETH: $3,102.17
₳ ADA: $0.8524

─────────────────────────
💡 数据来源: Binance
```

---

## 🚀 快速开始

### 前置要求
- Python 3.10 或更高版本
- Telegram Bot Token（从 [@BotFather](https://t.me/BotFather) 获取）
- 稳定的网络连接

### 安装步骤

#### 1. 克隆项目
```bash
git clone https://github.com/White-Lie-88896/telegram-crypto-bot.git
cd telegram-crypto-bot
```

#### 2. 创建虚拟环境
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows
```

#### 3. 安装依赖
```bash
pip install -r requirements.txt
```

#### 4. 配置环境变量
```bash
# 复制配置模板
cp .env.example .env

# 编辑配置文件
nano .env
```

**必需配置**：
```env
# Telegram Bot Token（必需）
TELEGRAM_BOT_TOKEN=你的_BOT_TOKEN

# 接收价格汇报的用户ID（可选）
REPORT_USER_ID=你的_USER_ID
```

获取 User ID：发送任意消息给 [@userinfobot](https://t.me/userinfobot)

#### 5. 运行 Bot
```bash
python main.py
```

---

## 📖 使用指南

### 基础命令

#### 🎯 开始使用
```
/start
```
注册用户并显示欢迎信息

#### ❓ 获取帮助
```
/help
```
查看完整的命令列表和使用说明

#### 💰 查询价格
```
/price BTC      # 查询比特币价格
/price ETH      # 查询以太坊价格
/price ADA      # 查询艾达币价格
```

### 监控任务管理

#### ➕ 创建监控任务

**价格阈值监控**：
```
/add BTC price 50000              # BTC达到50000时预警（上限）
/add BTC price high 50000         # BTC达到50000时预警（明确上限）
/add BTC price low 40000          # BTC跌破40000时预警（明确下限）
/add ETH price 3500 2800          # ETH突破3500或跌破2800
```

**百分比涨跌监控**：
```
/add BTC percent 90000 5 -5       # BTC相对90000涨5%或跌5%时预警
/add ETH percent 3000 10 -10      # ETH相对3000涨10%或跌10%
```

#### 📋 查看任务列表
```
/list
```
显示所有活跃的监控任务及详细信息

#### 🗑️ 删除监控任务
```
/delete 1      # 删除任务ID为1的监控
```

### 监控特性说明

#### ⏱️ 冷却时间
- 每个任务触发后有 **5 分钟** 冷却期
- 防止同一预警频繁推送

#### 🔄 检查频率
- 监控引擎每 **5 秒** 检查一次所有活跃任务
- 快速响应价格变化

#### 💾 数据持久化
- 所有任务保存在 SQLite 数据库
- Bot 重启后自动加载任务
- 完整的预警历史记录

---

## 🖥️ 部署

### systemd 服务部署（推荐）

#### 1. 复制服务文件
```bash
sudo cp tgbot-crypto.service /etc/systemd/system/
```

#### 2. 重新加载 systemd
```bash
sudo systemctl daemon-reload
```

#### 3. 启动服务
```bash
sudo systemctl start tgbot-crypto
```

#### 4. 设置开机自启
```bash
sudo systemctl enable tgbot-crypto
```

#### 5. 查看服务状态
```bash
sudo systemctl status tgbot-crypto
```

### 服务管理命令

```bash
# 启动服务
sudo systemctl start tgbot-crypto

# 停止服务
sudo systemctl stop tgbot-crypto

# 重启服务
sudo systemctl restart tgbot-crypto

# 查看实时日志
sudo journalctl -u tgbot-crypto -f

# 查看服务状态
sudo systemctl status tgbot-crypto
```

---

## 🏗️ 技术架构

### 技术栈

| 类别 | 技术 | 版本 |
|------|------|------|
| 语言 | Python | 3.12+ |
| Bot 框架 | python-telegram-bot | 20.7 |
| 数据源 | Cryptocompare API | - |
| 数据库 | SQLite + SQLAlchemy | 2.0+ |
| 定时任务 | APScheduler | 3.10+ |
| HTTP 客户端 | aiohttp | 3.9+ |
| 服务管理 | systemd | - |

### 项目结构

```
telegram-crypto-bot/
├── config/                     # 配置模块
│   ├── settings.py             # 全局配置管理
│   └── constants.py            # 常量定义
├── src/
│   ├── bot/                    # Telegram Bot 层
│   │   ├── main.py             # Bot 主框架
│   │   └── handlers/           # 指令处理器
│   │       ├── basic.py        # 基础指令（/start, /help）
│   │       ├── query.py        # 查询指令（/price）
│   │       └── monitor.py      # 监控指令（/add, /list, /delete）
│   ├── exchange/               # 交易所数据层
│   │   ├── cryptocompare_client.py  # Cryptocompare API 客户端
│   │   ├── coingecko_client.py      # CoinGecko API 客户端（备用）
│   │   └── binance_client.py        # Binance API 客户端（废弃）
│   ├── monitor/                # 监控引擎
│   │   ├── engine.py           # 监控引擎核心
│   │   └── rules/              # 监控规则
│   │       ├── base.py         # 规则基类
│   │       ├── price_threshold.py    # 价格阈值规则
│   │       └── percentage_change.py  # 百分比涨跌规则
│   ├── database/               # 数据库层
│   │   ├── models.py           # ORM 模型定义
│   │   ├── connection.py       # 数据库连接管理
│   │   └── repositories/       # 数据访问层
│   ├── notifier/               # 消息推送模块
│   │   ├── message_formatter.py     # 消息格式化
│   │   └── price_reporter.py        # 定时价格汇报
│   └── utils/                  # 工具模块
│       ├── logger.py           # 日志管理
│       └── exceptions.py       # 自定义异常
├── scripts/                    # 运维脚本
│   ├── init_db.py              # 数据库初始化
│   ├── clear_webhook.py        # 清除 Webhook
│   └── force_clear_updates.py  # 强制清除更新
├── data/                       # 数据文件
│   └── crypto_bot.db           # SQLite 数据库
├── logs/                       # 日志文件
│   ├── bot.log                 # 应用日志
│   └── bot_error.log           # 错误日志
├── tests/                      # 测试文件
├── .env                        # 环境变量（不纳入版控）
├── .env.example                # 环境变量模板
├── .gitignore                  # Git 忽略文件
├── requirements.txt            # Python 依赖
├── tgbot-crypto.service        # systemd 服务配置
├── main.py                     # 程序入口
└── README.md                   # 项目文档
```

### 核心工作流程

#### 1. 价格查询流程
```
用户发送 /price BTC
    ↓
命令处理器解析参数
    ↓
调用 Cryptocompare API
    ↓
格式化价格信息
    ↓
发送 Markdown 消息给用户
```

#### 2. 监控预警流程
```
监控引擎每5秒执行
    ↓
加载所有活跃任务
    ↓
并发获取各币种价格
    ↓
评估规则是否触发
    ↓
检查冷却时间
    ↓
发送预警消息
    ↓
记录预警历史
    ↓
更新任务状态
```

#### 3. 定时汇报流程
```
APScheduler 定时触发（每5分钟）
    ↓
并发获取 BTC、ETH、ADA 价格
    ↓
格式化汇报消息
    ↓
发送到配置的用户/群组
```

---

## ❓ 常见问题

### Q: Bot 无法启动怎么办？

**A:** 检查以下几点：
1. 确认 `TELEGRAM_BOT_TOKEN` 配置正确
2. 检查网络是否可以访问 Telegram API
3. 查看日志文件 `logs/bot.log` 获取详细错误信息
4. 确认 Python 版本 >= 3.10

### Q: 价格查询失败？

**A:** 可能的原因：
1. 交易对名称错误（使用简写如 `BTC` 而不是 `BTCUSDT`）
2. 网络无法访问 Cryptocompare API
3. API 请求超时（网络较慢）

### Q: 监控任务不触发？

**A:** 检查：
1. 任务是否处于 ACTIVE 状态（使用 `/list` 查看）
2. 是否在冷却期内（默认5分钟）
3. 价格阈值设置是否合理
4. 查看日志确认监控引擎正常运行

### Q: 如何修改检查频率？

**A:** 编辑 `.env` 文件：
```env
CHECK_INTERVAL=5    # 修改为你想要的秒数
```
然后重启服务：`sudo systemctl restart tgbot-crypto`

### Q: 如何修改汇报频率？

**A:** 修改 `src/notifier/price_reporter.py` 中的定时任务设置：
```python
self.scheduler.add_job(
    self.send_price_report,
    'interval',
    minutes=5,  # 修改这里
    ...
)
```

### Q: 数据库损坏如何修复？

**A:** 删除并重新初始化：
```bash
rm data/crypto_bot.db
python scripts/init_db.py
```

---

## 🤝 贡献指南

欢迎贡献代码、报告 Bug 或提出新功能建议！

### 提交 Issue
- 描述问题或功能需求
- 提供复现步骤（如果是 Bug）
- 附上相关日志

### 提交 Pull Request
1. Fork 本仓库
2. 创建特性分支：`git checkout -b feature/AmazingFeature`
3. 提交更改：`git commit -m 'Add some AmazingFeature'`
4. 推送分支：`git push origin feature/AmazingFeature`
5. 提交 Pull Request

---

## 📝 开发计划

### ✅ 已完成
- [x] 项目基础架构
- [x] Telegram Bot 框架
- [x] 数据库设计与实现
- [x] Cryptocompare API 集成
- [x] 实时价格查询
- [x] 价格阈值监控
- [x] 百分比涨跌监控
- [x] 监控引擎实现
- [x] 任务管理命令
- [x] 定时价格汇报
- [x] systemd 服务部署
- [x] 完善错误处理
- [x] 创建测试套件（39个测试用例）

### 🚧 进行中
- [ ] 优化消息格式
- [ ] 性能优化

### 📅 计划中
- [ ] 技术指标预警（MA, RSI, MACD）
- [ ] WebSocket 实时数据流
- [ ] 多时间周期分析
- [ ] 更多交易所支持
- [ ] Web 管理后台
- [ ] Docker 容器化部署
- [ ] 国际化支持

---

## ⚖️ 许可证

本项目采用 [MIT License](LICENSE) 开源协议

---

## ⚠️ 免责声明

**重要提示**：

1. 本项目**仅供学习和研究使用**
2. 所有价格数据仅供参考，不构成投资建议
3. 加密货币投资存在**高风险**，可能导致本金损失
4. 使用本 Bot 进行交易决策的**风险由用户自行承担**
5. 开发者不对使用本软件造成的任何损失负责

请务必谨慎决策，理性投资！

---

## 📞 联系方式

- **GitHub**: https://github.com/White-Lie-88896/telegram-crypto-bot
- **Issues**: https://github.com/White-Lie-88896/telegram-crypto-bot/issues
- **Telegram**: @notification_60790_bot (Demo Bot)

---

<p align="center">
  Made with ❤️ by White-Lie-88896
  <br/>
  <sub>如果这个项目对你有帮助，请给个 ⭐️ Star 支持一下！</sub>
</p>
