"""
数据库 ORM 模型定义
使用 SQLAlchemy 2.0+ 语法
"""
from datetime import datetime
from typing import Optional
import json

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    """用户表"""
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True)  # Telegram User ID
    username = Column(String(255))
    first_name = Column(String(255))
    last_name = Column(String(255))
    language_code = Column(String(10), default='en')
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    tasks = relationship("MonitorTask", back_populates="user", cascade="all, delete-orphan")
    alerts = relationship("AlertHistory", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(user_id={self.user_id}, username='{self.username}')>"

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class MonitorTask(Base):
    """监控任务表"""
    __tablename__ = 'monitor_tasks'

    task_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    symbol = Column(String(20), nullable=False)  # 如 BTCUSDT
    market_type = Column(String(10), nullable=False, default='SPOT')  # SPOT / FUTURES
    rule_type = Column(String(50), nullable=False)  # PRICE_THRESHOLD, PERCENTAGE, etc.
    rule_config = Column(Text, nullable=False)  # JSON 格式
    status = Column(String(20), default='ACTIVE')  # ACTIVE, PAUSED, DELETED
    last_triggered_at = Column(DateTime)
    cooldown_seconds = Column(Integer, default=300)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    user = relationship("User", back_populates="tasks")
    alerts = relationship("AlertHistory", back_populates="task", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<MonitorTask(task_id={self.task_id}, symbol='{self.symbol}', rule_type='{self.rule_type}')>"

    def to_dict(self):
        return {
            'task_id': self.task_id,
            'user_id': self.user_id,
            'symbol': self.symbol,
            'market_type': self.market_type,
            'rule_type': self.rule_type,
            'rule_config': json.loads(self.rule_config) if isinstance(self.rule_config, str) else self.rule_config,
            'status': self.status,
            'last_triggered_at': self.last_triggered_at.isoformat() if self.last_triggered_at else None,
            'cooldown_seconds': self.cooldown_seconds,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def get_rule_config(self) -> dict:
        """解析 rule_config JSON"""
        if isinstance(self.rule_config, str):
            return json.loads(self.rule_config)
        return self.rule_config or {}

    def set_rule_config(self, config: dict):
        """设置 rule_config"""
        self.rule_config = json.dumps(config)


class AlertHistory(Base):
    """预警历史表"""
    __tablename__ = 'alert_history'

    alert_id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey('monitor_tasks.task_id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    symbol = Column(String(20), nullable=False)
    market_type = Column(String(10), nullable=False)
    trigger_price = Column(Float)
    trigger_value = Column(Text)  # JSON 格式
    message = Column(Text, nullable=False)
    triggered_at = Column(DateTime, default=datetime.utcnow)
    sent_success = Column(Boolean, default=True)

    # 关系
    task = relationship("MonitorTask", back_populates="alerts")
    user = relationship("User", back_populates="alerts")

    def __repr__(self):
        return f"<AlertHistory(alert_id={self.alert_id}, symbol='{self.symbol}', triggered_at='{self.triggered_at}')>"

    def to_dict(self):
        return {
            'alert_id': self.alert_id,
            'task_id': self.task_id,
            'user_id': self.user_id,
            'symbol': self.symbol,
            'market_type': self.market_type,
            'trigger_price': self.trigger_price,
            'trigger_value': json.loads(self.trigger_value) if isinstance(self.trigger_value, str) else self.trigger_value,
            'message': self.message,
            'triggered_at': self.triggered_at.isoformat() if self.triggered_at else None,
            'sent_success': self.sent_success
        }


class ReportConfig(Base):
    """用户价格汇报配置表"""
    __tablename__ = 'report_configs'

    user_id = Column(Integer, ForeignKey('users.user_id'), primary_key=True)
    enabled = Column(Boolean, default=False)  # 是否启用汇报
    interval_minutes = Column(Integer, default=30)  # 汇报间隔（分钟）
    symbols = Column(Text, default='BTC,ETH,ADA')  # 监控币种列表（逗号分隔）
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<ReportConfig(user_id={self.user_id}, enabled={self.enabled}, interval={self.interval_minutes})>"

    def get_symbols_list(self) -> list:
        """获取币种列表"""
        if not self.symbols:
            return ['BTC', 'ETH', 'ADA']
        return [s.strip().upper() for s in self.symbols.split(',') if s.strip()]

    def set_symbols_list(self, symbols: list):
        """设置币种列表"""
        self.symbols = ','.join([s.strip().upper() for s in symbols if s.strip()])

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'enabled': self.enabled,
            'interval_minutes': self.interval_minutes,
            'symbols': self.get_symbols_list(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class SystemConfig(Base):
    """系统配置表"""
    __tablename__ = 'system_config'

    config_key = Column(String(100), primary_key=True)
    config_value = Column(Text, nullable=False)
    description = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<SystemConfig(key='{self.config_key}', value='{self.config_value}')>"

    def to_dict(self):
        return {
            'config_key': self.config_key,
            'config_value': self.config_value,
            'description': self.description,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


__all__ = ['Base', 'User', 'MonitorTask', 'AlertHistory', 'ReportConfig', 'SystemConfig']
