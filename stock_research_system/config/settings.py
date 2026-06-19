# -*- coding: utf-8 -*-
"""
股票投研系统配置文件
适合小白：所有配置都可视化，方便修改
"""

import os
from pathlib import Path

# ============ 项目路径配置 ============
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"

# 确保目录存在
DATA_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)


# ============ Agent配置 ============
AGENT_CONFIG = {
    "data_agent": {
        "name": "数据采集Agent",
        "description": "负责从东方财富、同花顺等平台采集A股数据",
        "model": "gpt-4o",  # 支持中文理解
        "temperature": 0.3,  # 低温度确保数据准确性
    },
    "selector_agent": {
        "name": "选股策略Agent",
        "description": "基于财务指标、技术指标筛选优质股票",
        "model": "gpt-4o",
        "temperature": 0.5,
    },
    "analysis_agent": {
        "name": "技术分析Agent",
        "description": "分析K线形态、计算技术指标、判断买卖点",
        "model": "gpt-4o",
        "temperature": 0.4,
    },
    "monitor_agent": {
        "name": "大盘监控Agent",
        "description": "监控大盘指数、板块轮动、市场情绪",
        "model": "gpt-4o",
        "temperature": 0.3,
    },
    "watch_agent": {
        "name": "自动盯盘Agent",
        "description": "监控持仓股和自选股的实时异动",
        "model": "gpt-4o",
        "temperature": 0.4,
    },
    "report_agent": {
        "name": "报告生成Agent",
        "description": "综合分析结果，生成投资建议报告",
        "model": "gpt-4o",
        "temperature": 0.6,
    }
}


# ============ 数据源配置 ============
DATA_SOURCES = {
    "eastmoney": {
        "name": "东方财富",
        "enabled": True,
        "api": "https://push2his.eastmoney.com",
        "description": "主要数据源，实时行情、历史数据、财经新闻"
    },
    "tonghuashun": {
        "name": "同花顺",
        "enabled": True,
        "api": "https://d.10jqka.com.cn",
        "description": "补充数据源，技术分析数据"
    },
    "xueqiu": {
        "name": "雪球",
        "enabled": True,
        "api": "https://stock.xueqiu.com",
        "description": "社区数据，舆情分析"
    }
}


# ============ 选股策略配置 ============
# 小白友好：预设几个常用策略，可以直接选用
SELECTION_STRATEGIES = {
    "value_investment": {
        "name": "价值投资策略",
        "description": "筛选低估值、高分红、业绩稳定的蓝筹股",
        "filters": {
            "pe_ratio": (5, 30),           # 市盈率范围
            "pb_ratio": (0.5, 5),          # 市净率范围
            "dividend_yield": (2, None),    # 分红率（%）
            "roe": (10, None),             # 净资产收益率（%）
            "revenue_growth": (5, None),    # 营收增长率（%）
        }
    },
    "growth_investment": {
        "name": "成长投资策略",
        "description": "筛选高成长性股票，适合追求超额收益",
        "filters": {
            "pe_ratio": (20, 80),
            "revenue_growth": (20, None),
            "profit_growth": (20, None),
            "gross_margin": (30, None),
        }
    },
    "momentum": {
        "name": "趋势动量策略",
        "description": "基于技术指标，筛选强势股",
        "filters": {
            "ma_alignment": "多头排列",    # 均线多头
            "volume_ratio": (1.5, None),   # 量比
            "price_momentum": (5, 20),      # 近5日涨幅
        }
    },
    "low_volatility": {
        "name": "低波动策略",
        "description": "筛选波动较小的稳健股，适合保守型投资者",
        "filters": {
            "volatility": (None, 20),
            "beta": (0.5, 1.0),
        }
    }
}


# ============ 技术分析配置 ============
TECHNICAL_INDICATORS = {
    "MA": {"name": "均线系统", "periods": [5, 10, 20, 60, 120, 250]},
    "MACD": {"name": "MACD", "fast": 12, "slow": 26, "signal": 9},
    "KDJ": {"name": "KDJ随机指标", "period": 9, "k": 3, "d": 3},
    "RSI": {"name": "RSI相对强弱", "periods": [6, 12, 24]},
    "BOLL": {"name": "布林带", "period": 20, "std": 2},
    "VOL": {"name": "成交量", "enabled": True},
}


# ============ 买卖点判断规则 ============
# 小白友好：简单明了的买卖点规则
BUY_SIGNALS = {
    "金叉买入": {
        "description": "短期均线上穿长期均线",
        "conditions": ["MA5 > MA10", "MA10 > MA20", "KDJ_K > KDJ_D", "RSI > 50"]
    },
    "MACD底背离": {
        "description": "价格创新低但MACD未创新低",
        "conditions": ["price_new_low", "MACD_not_new_low"]
    },
    "缩量回调": {
        "description": "上涨后缩量回调到支撑位",
        "conditions": ["volume_decrease", "price_at_support"]
    },
    "放量突破": {
        "description": "放量突破重要压力位",
        "conditions": ["volume > MA20_VOL * 1.5", "price_break_resistance"]
    }
}

SELL_SIGNALS = {
    "死叉卖出": {
        "description": "短期均线下穿长期均线",
        "conditions": ["MA5 < MA10", "KDJ_K < KDJ_D", "RSI < 50"]
    },
    "高位放量": {
        "description": "高位放量大跌，可能是出货",
        "conditions": ["volume_surge", "price_drop > 3%"]
    },
    "MACD顶背离": {
        "description": "价格创新高但MACD未创新高",
        "conditions": ["price_new_high", "MACD_not_new_high"]
    },
    "止损提示": {
        "description": "亏损达到止损线",
        "conditions": ["loss > stop_loss_percent"]
    }
}


# ============ 监控配置 ============
# 自选股列表 - 小白直接在这里添加股票代码
WATCH_LIST = [
    # 格式: (股票代码, 股票名称)
    # 例如: ("000001", "平安银行"),
    #       ("600519", "贵州茅台"),
    ("000858", "五粮液"),
    ("600036", "招商银行"),
]

# 持仓股列表 - 填入你的持仓
PORTFOLIO = [
    # 格式: (股票代码, 股票名称, 持仓数量, 成本价)
    # ("000001", "平安银行", 1000, 12.50),
]

# 告警阈值
ALERT_THRESHOLDS = {
    "price_change_percent": 5,      # 价格变动超过5%告警
    "volume_ratio": 3,              # 量比超过3倍告警
    "price_drop_stop_loss": -7,      # 亏损7%止损提醒
    "price_gain_take_profit": 15,    # 盈利15%止盈提醒
    "new_high": True,                # 创新高提醒
    "new_low": True,                 # 创新低提醒
}


# ============ 大盘监控配置 ============
MARKET_INDICES = {
    "sh000001": {"name": "上证指数", "market": "SH"},
    "sz399001": {"name": "深证成指", "market": "SZ"},
    "cy399006": {"name": "创业板指", "market": "SZ"},
    "sh000300": {"name": "沪深300", "market": "SH"},
}


# ============ 报告配置 ============
REPORT_CONFIG = {
    "auto_generate": True,           # 是否自动生成报告
    "report_time": "18:00",          # 每日报告生成时间
    "include_sections": [
        "大盘回顾",
        "持仓分析",
        "自选股动态",
        "选股推荐",
        "风险提示",
        "操作建议"
    ],
    "format": "markdown",            # 报告格式
}


# ============ 系统配置 ============
SYSTEM_CONFIG = {
    "check_interval": 300,           # 检查间隔（秒），默认5分钟
    "max_stocks_per_scan": 100,      # 每次扫描最多股票数
    "log_level": "INFO",             # 日志级别
    "save_data": True,               # 是否保存历史数据
    "enable_notifications": True,    # 是否启用通知
}
