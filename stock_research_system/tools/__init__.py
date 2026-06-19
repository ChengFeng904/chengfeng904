# -*- coding: utf-8 -*-
"""
工具模块初始化
"""

from tools.data_source import (
    EastMoneyDataSource,
    DataCollector,
    get_quote,
    get_kline,
    get_batch_quotes,
    get_market_index,
    get_limit_up,
)

from tools.indicators import (
    calculate_ma,
    calculate_ema,
    calculate_macd,
    calculate_kdj,
    calculate_rsi,
    calculate_boll,
    TechnicalAnalyzer,
    analyze_stock,
)

# 可视化模块（可选依赖：matplotlib）
try:
    from tools.chart import (
        plot_kline_with_indicators,
        plot_market_indices,
        is_matplotlib_available,
    )

    _CHART_AVAILABLE = True
except ImportError:
    plot_kline_with_indicators = None
    plot_market_indices = None
    is_matplotlib_available = lambda: False
    _CHART_AVAILABLE = False

__all__ = [
    # 数据源
    "EastMoneyDataSource",
    "DataCollector",
    "get_quote",
    "get_kline",
    "get_batch_quotes",
    "get_market_index",
    "get_limit_up",
    # 技术指标
    "calculate_ma",
    "calculate_ema",
    "calculate_macd",
    "calculate_kdj",
    "calculate_rsi",
    "calculate_boll",
    "TechnicalAnalyzer",
    "analyze_stock",
    # 可视化
    "plot_kline_with_indicators",
    "plot_market_indices",
    "is_matplotlib_available",
]
