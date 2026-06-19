# -*- coding: utf-8 -*-
"""
配置模块初始化
"""

from config.settings import (
    # 路径配置
    BASE_DIR,
    DATA_DIR,
    REPORTS_DIR,
    
    # Agent配置
    AGENT_CONFIG,
    
    # 数据源配置
    DATA_SOURCES,
    
    # 选股策略配置
    SELECTION_STRATEGIES,
    
    # 技术分析配置
    TECHNICAL_INDICATORS,
    
    # 买卖点配置
    BUY_SIGNALS,
    SELL_SIGNALS,
    
    # 监控配置
    WATCH_LIST,
    PORTFOLIO,
    ALERT_THRESHOLDS,
    MARKET_INDICES,
    
    # 报告配置
    REPORT_CONFIG,
    
    # 系统配置
    SYSTEM_CONFIG,
)

__all__ = [
    "BASE_DIR",
    "DATA_DIR",
    "REPORTS_DIR",
    "AGENT_CONFIG",
    "DATA_SOURCES",
    "SELECTION_STRATEGIES",
    "TECHNICAL_INDICATORS",
    "BUY_SIGNALS",
    "SELL_SIGNALS",
    "WATCH_LIST",
    "PORTFOLIO",
    "ALERT_THRESHOLDS",
    "MARKET_INDICES",
    "REPORT_CONFIG",
    "SYSTEM_CONFIG",
]
