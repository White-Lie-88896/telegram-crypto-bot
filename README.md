# Telegram 加密货币价格监控机器人

一个基于 Telegram Bot 的加密货币价格监控与预警系统，数据来源于 Binance 交易所。

## 功能特性

### MVP 版本（当前）

- ✅ **实时价格查询** - 查询 Binance 现货市场价格
- ✅ **用户管理** - 自动注册和管理用户信息
- ✅ **帮助系统** - 完整的指令说明和使用指南

### 开发中功能

- ⏳ **价格阈值预警** - 当价格达到指定值时发送通知
- ⏳ **百分比涨跌监控** - 监控涨跌幅并触发预警
- ⏳ **定时价格汇报** - 定期推送监控标的的价格摘要
- ⏳ **任务管理** - 创建、查看、删除监控任务

## 技术栈

- **语言**: Python 3.10+
- **Bot 框架**: python-telegram-bot 20.7
- **数据源**: Binance API (python-binance)
- **数据库**: SQLite (异步 SQLAlchemy)
- **异步框架**: asyncio

## 快速开始

### 1. 安装依赖

```bash
# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，设置你的 Telegram Bot Token
nano .env  # 或使用其他编辑器
```

**必需配置**:
- `TELEGRAM_BOT_TOKEN`: 从 [@BotFather](https://t.me/BotFather) 获取

**可选配置**:
- `BINANCE_API_KEY` / `BINANCE_API_SECRET`: 仅在需要私有 API 时配置
- 其他配置项见 `.env.example`

### 3. 初始化数据库

```bash
python scripts/init_db.py
```

### 4. 运行 Bot

```bash
python main.py
```

## 可用指令

### 基础指令

- `/start` - 开始使用 Bot，注册用户
- `/help` - 查看帮助信息

### 查询指令

- `/price <symbol>` - 查询实时价格
  - 示例: `/price BTC` 或 `/price BTCUSDT`

### 监控任务管理（开发中）

- `/add` - 创建监控任务
- `/list` - 查看所有任务
- `/delete <task_id>` - 删除指定任务

## 项目结构

```
/opt/tgbotbinance/
├── config/                  # 配置模块
│   ├── settings.py          # 全局配置
│   └── constants.py         # 常量定义
├── src/                     # 源代码
│   ├── bot/                 # Telegram Bot 层
│   │   ├── main.py          # Bot 主框架
│   │   └── handlers/        # 指令处理器
│   ├── exchange/            # 交易所数据层
│   │   └── binance_client.py
│   ├── monitor/             # 监控引擎（开发中）
│   ├── database/            # 数据库层
│   │   ├── models.py        # ORM 模型
│   │   └── connection.py    # 连接管理
│   ├── notifier/            # 消息推送
│   │   └── message_formatter.py
│   └── utils/               # 工具模块
│       ├── logger.py
│       └── exceptions.py
├── scripts/                 # 运维脚本
│   └── init_db.py
├── data/                    # 数据文件
│   └── crypto_bot.db        # SQLite 数据库
├── logs/                    # 日志文件
├── requirements.txt         # Python 依赖
├── .env.example             # 环境变量模板
└── main.py                  # 程序入口
```

## 数据库管理

### 初始化数据库

```bash
python scripts/init_db.py
```

### 重置数据库（删除所有数据）

```bash
python scripts/init_db.py --reset
```

## 开发计划

### MVP 阶段（已完成）

- [x] 项目基础架构
- [x] 数据库设计与实现
- [x] Binance API 集成
- [x] Telegram Bot 基础框架
- [x] 实时价格查询功能

### 下一步开发

- [ ] 价格阈值监控规则
- [ ] 百分比涨跌监控规则
- [ ] 监控引擎核心
- [ ] 任务管理指令（/add, /list, /delete）
- [ ] 预警消息推送
- [ ] 定时汇报功能

### 未来功能

- [ ] 技术指标预警（MA, RSI, MACD）
- [ ] Binance 永续合约支持
- [ ] 时间窗口波动监控
- [ ] Docker 部署支持
- [ ] WebSocket 实时数据流
- [ ] 多用户管理后台

## 故障排除

### Bot 无法启动

1. 检查 `TELEGRAM_BOT_TOKEN` 是否正确设置
2. 确认网络连接正常，可以访问 Telegram API
3. 查看日志文件: `logs/bot.log`

### 价格查询失败

1. 检查交易对名称是否正确（如 BTCUSDT）
2. 确认网络可以访问 Binance API
3. 检查 Binance API 是否限流

### 数据库错误

1. 删除 `data/crypto_bot.db` 并重新初始化: `python scripts/init_db.py`
2. 检查文件权限

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License

## 免责声明

本项目仅供学习和研究使用。使用本 Bot 进行交易决策的风险由用户自行承担。
加密货币投资存在高风险，请谨慎决策。

## 联系方式

- 项目地址: https://github.com/yourusername/tgbotbinance
- Issue 反馈: https://github.com/yourusername/tgbotbinance/issues
