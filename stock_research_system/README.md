# 股票投研系统

基于 Claude Code 多Agent 架构的 A股智能投研系统

## 功能特性

- **数据采集Agent**: 从东方财富、同花顺等平台实时获取A股数据
- **选股策略Agent**: 支持价值投资、成长投资、趋势动量等多种策略
- **技术分析Agent**: K线形态、技术指标、买卖点提示
- **大盘监控Agent**: 市场情绪、板块轮动、涨停板统计
- **自动盯盘Agent**: 持仓股、自选股实时监控，异常告警
- **报告生成Agent**: 自动生成每日投资研究报告

## 快速开始

### 1. 安装依赖

```bash
cd stock_research_system
pip install -r requirements.txt
```

### 2. 配置API Key

```bash
cp .env.example .env
# 编辑 .env，填入您的 OpenAI API Key
```

### 3. 运行系统

```bash
# 交互模式（推荐新手）
python main.py

# 仅生成报告
python main.py --mode report

# 盯盘模式
python main.py --mode watch
```

## 使用说明

### 菜单功能

| 选项 | 功能 | 说明 |
|------|------|------|
| 1 | 大盘监控 | 查看市场情绪和主要指数 |
| 2 | 股票分析 | 分析单只股票的技术指标 |
| 3 | 自选股 | 查看自选股实时行情 |
| 4 | 持仓分析 | 查看持仓盈亏情况 |
| 5 | 盯盘检查 | 检查是否有异常告警 |
| 6 | 生成报告 | 生成每日投资报告 |
| 7 | 选股推荐 | 根据策略筛选股票 |
| 8 | 系统设置 | 查看/修改配置 |

### 自定义配置

编辑 `config/settings.py`:

```python
# 自选股列表
WATCH_LIST = [
    ("000858", "五粮液"),
    ("600036", "招商银行"),
]

# 持仓列表
PORTFOLIO = [
    ("000001", "平安银行", 1000, 12.50),  # 代码, 名称, 数量, 成本价
]

# 告警阈值
ALERT_THRESHOLDS = {
    "price_change_percent": 5,   # 价格变动超过5%告警
    "price_drop_stop_loss": -7,  # 亏损7%止损提醒
    ...
}
```

## 技术架构

```
stock_research_system/
├── config/          # 配置文件
│   └── settings.py
├── agents/          # Agent模块
│   ├── base.py      # Agent基类
│   ├── monitor.py   # 监控Agent
│   └── report.py    # 报告Agent
├── tools/           # 工具函数
│   ├── data_source.py   # 数据源
│   └── indicators.py    # 技术指标
├── core/            # 核心模块
│   └── orchestrator.py  # Agent编排器
├── data/            # 数据目录
├── reports/         # 报告目录
└── main.py          # 主程序入口
```

## 免责声明

本系统仅供学习研究使用，不构成投资建议。股市有风险，投资需谨慎。
