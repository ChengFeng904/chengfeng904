# -*- coding: utf-8 -*-
"""
Agent模块初始化
"""

from agents.base import (
    BaseAgent,
    DataAgent,
    SelectorAgent,
    AnalysisAgent,
    create_data_agent,
    create_selector_agent,
    create_analysis_agent,
)

from agents.monitor import (
    MarketMonitorAgent,
    AutoWatchAgent,
    Watcher,
    create_market_monitor,
    create_auto_watch,
)

from agents.report import (
    ReportAgent,
    create_report_agent,
)

__all__ = [
    # 基类
    "BaseAgent",
    "DataAgent",
    "SelectorAgent",
    "AnalysisAgent",
    
    # 监控Agent
    "MarketMonitorAgent",
    "AutoWatchAgent",
    "Watcher",
    
    # 报告Agent
    "ReportAgent",
    
    # 工厂函数
    "create_data_agent",
    "create_selector_agent",
    "create_analysis_agent",
    "create_market_monitor",
    "create_auto_watch",
    "create_report_agent",
]
