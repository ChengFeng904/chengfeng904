# -*- coding: utf-8 -*-
"""
股票投研系统 - Streamlit Web 界面
运行方式: streamlit run app.py
"""

import sys
import os

# 确保项目目录在路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from typing import Dict, List, Optional

import streamlit as st

# 设置页面配置（必须是第一个 Streamlit 调用）
st.set_page_config(
    page_title="A股智能投研系统",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ========== 延迟导入工具模块，避免未安装依赖时崩溃 ==========
from tools import (
    get_quote,
    get_kline,
    get_batch_quotes,
    get_market_index,
    get_limit_up,
    analyze_stock,
    is_matplotlib_available,
    plot_kline_with_indicators,
    plot_market_indices,
)

from agents import (
    create_data_agent,
    create_selector_agent,
    create_report_agent,
    create_market_monitor,
    create_auto_watch,
)

from core import create_orchestrator

from config.settings import (
    WATCH_LIST,
    PORTFOLIO,
    MARKET_INDICES,
    SELECTION_STRATEGIES,
    SYSTEM_CONFIG,
)


# ========== 页面辅助函数 ==========
def _display_metric_row(label: str, value: str, delta: Optional[str] = None,
                         delta_color: str = "normal") -> None:
    """显示指标行（优雅降级：支持旧版 Streamlit）"""
    try:
        st.metric(label=label, value=value, delta=delta, delta_color=delta_color)
    except TypeError:
        # 旧版本不支持 delta_color
        st.metric(label=label, value=value, delta=delta)


def _color_for_change(change: float) -> str:
    """根据涨跌幅返回颜色"""
    if change > 0:
        return "red"
    if change < 0:
        return "green"
    return "gray"


def _format_change(change: float) -> str:
    """格式化涨跌幅（带正负号）"""
    if change > 0:
        return f"+{change:.2f}%"
    return f"{change:.2f}%"


def _safe_get_stock_name(code: str) -> str:
    """从自选股列表中获取股票名称"""
    for c, n in WATCH_LIST:
        if c == code:
            return n
    return code


# ========== 页面定义 ==========
def page_market() -> None:
    """大盘监控页面"""
    st.markdown("## 📊 大盘监控")
    st.info(
        "数据来源：东方财富公开接口。点击「刷新数据」获取最新行情。",
        icon="ℹ️",
    )

    if st.button("🔄 刷新大盘数据", type="primary"):
        st.rerun()

    # 获取大盘指数
    index_map = get_market_index()

    col1, col2, col3, col4 = st.columns(4)
    cols = [col1, col2, col3, col4]

    if index_map:
        for idx, (code, data) in enumerate(list(index_map.items())[:4]):
            name = data.get("stock_name", code)
            price = data.get("current_price", 0)
            change = data.get("change_percent", 0) or 0
            sign = "+" if change >= 0 else ""

            with cols[idx]:
                _display_metric_row(
                    label=name,
                    value=f"{price:.2f}",
                    delta=f"{sign}{change:.2f}%",
                    delta_color="inverse",
                )
    else:
        for col in cols:
            with col:
                st.metric(label="暂无数据", value="-", delta="-")

    st.divider()

    # 绘制指数涨跌图（如果 matplotlib 可用）
    if is_matplotlib_available() and index_map:
        st.markdown("### 📈 指数涨跌图")
        img = plot_market_indices(index_map)
        if img:
            st.image(f"data:image/png;base64,{img}", use_column_width=True)
    elif not is_matplotlib_available():
        st.info("💡 如需查看图表，请安装 matplotlib: `pip install matplotlib`")

    # 涨停股列表
    st.markdown("### 🔥 涨停股 / 热门股")
    with st.spinner("获取热门股数据..."):
        limit_stocks = get_limit_up() or []

    if limit_stocks:
        display = []
        for stock in limit_stocks[:20]:
            code = stock.get("stock_code", "")
            name = stock.get("stock_name", code)
            price = stock.get("current_price", 0)
            change = stock.get("change_percent", 0) or 0
            display.append({
                "代码": code,
                "名称": name,
                "现价": price,
                "涨跌幅": f"{change:+.2f}%",
            })

        st.dataframe(display, hide_index=True, use_container_width=True)
    else:
        st.warning("⚠️ 暂时无法获取热门股数据（可能是网络问题或非交易时间）")

    st.caption(f"数据时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def page_stock_analysis() -> None:
    """股票分析页面"""
    st.markdown("## 🔍 股票技术分析")

    col_a, col_b = st.columns([2, 1])
    with col_a:
        stock_code = st.text_input(
            "输入股票代码",
            value="000001",
            placeholder="例如 000001, 600519, 000858",
            help="支持沪市/深市股票代码",
        )
    with col_b:
        kline_count = st.slider("K线数量", min_value=30, max_value=200, value=100, step=10)

    if st.button("📊 开始分析", type="primary", key="analyze_btn"):
        if not stock_code or not stock_code.strip().isdigit():
            st.error("❌ 请输入有效的股票代码")
            return

        stock_code = stock_code.strip()

        with st.spinner(f"正在分析 {stock_code} ..."):
            quote = get_quote(stock_code)
            klines = get_kline(stock_code, "daily", kline_count)

            if not quote and not klines:
                st.error(
                    "❌ 无法获取股票数据。请检查：\n\n"
                    "1. 股票代码是否正确\n"
                    "2. 网络是否正常\n"
                    "3. 是否在交易时间（9:30-15:00）"
                )
                return

            # ===== 基础行情 =====
            st.markdown("### 📌 基础行情")
            if quote:
                c1, c2, c3, c4 = st.columns(4)
                name = quote.get("stock_name", stock_code)
                price = quote.get("current_price", 0)
                change = quote.get("change_percent", 0) or 0
                high = quote.get("high", 0)
                low = quote.get("low", 0)

                with c1:
                    _display_metric_row(
                        label=f"{name}",
                        value=f"{price:.2f}",
                        delta=f"{change:+.2f}%",
                        delta_color="inverse",
                    )
                with c2:
                    _display_metric_row(label="最高", value=f"{high:.2f}")
                with c3:
                    _display_metric_row(label="最低", value=f"{low:.2f}")
                with c4:
                    vol = quote.get("volume", 0) or 0
                    _display_metric_row(
                        label="成交量",
                        value=f"{vol / 10000:.1f}万" if vol > 10000 else f"{vol}",
                    )

            # ===== K线图 =====
            if klines and len(klines) >= 20:
                st.markdown("### 📈 K线图 + 技术指标")
                if is_matplotlib_available():
                    stock_name = quote.get("stock_name", stock_code) if quote else stock_code
                    img = plot_kline_with_indicators(klines, stock_name=stock_name)
                    if img:
                        st.image(f"data:image/png;base64,{img}",
                                 use_column_width=True)
                else:
                    st.info(
                        "💡 如需查看K线图表，请安装:\n\n"
                        "`pip install matplotlib`"
                    )

                # ===== 技术指标分析 =====
                analysis = analyze_stock(klines)

                if "error" not in analysis:
                    st.markdown("### 📊 技术指标详解")

                    trend = analysis.get("trend", {})
                    indicators = analysis.get("indicators", {})
                    signals = analysis.get("signals", {})
                    summary = analysis.get("summary", {})

                    # 趋势
                    with st.expander("📈 趋势分析", expanded=True):
                        trend_text = trend.get("trend", "未知")
                        st.markdown(f"**趋势判断:** `{trend_text}`")
                        st.markdown(
                            f"- **MA5:** {trend.get('ma5', '-')}  \n"
                            f"- **MA10:** {trend.get('ma10', '-')}  \n"
                            f"- **MA20:** {trend.get('ma20', '-')}  \n"
                            f"- **MA60:** {trend.get('ma60', '-')}"
                        )

                    # 指标
                    with st.expander("🔬 技术指标详解", expanded=True):
                        macd = indicators.get("macd", {})
                        kdj = indicators.get("kdj", {})
                        rsi = indicators.get("rsi", {})
                        boll = indicators.get("boll", {})

                        col_m, col_k, col_r = st.columns(3)
                        with col_m:
                            st.markdown("**MACD**")
                            st.write(f"- DIF: `{macd.get('dif', '-')}`")
                            st.write(f"- DEA: `{macd.get('dea', '-')}`")
                            st.write(f"- MACD柱: `{macd.get('histogram', '-')}`")
                        with col_k:
                            st.markdown("**KDJ**")
                            st.write(f"- K: `{kdj.get('k', '-')}`")
                            st.write(f"- D: `{kdj.get('d', '-')}`")
                            st.write(f"- J: `{kdj.get('j', '-')}`")
                        with col_r:
                            st.markdown("**RSI**")
                            st.write(f"- RSI6: `{rsi.get('rsi6', '-')}`")
                            st.write(f"- RSI12: `{rsi.get('rsi12', '-')}`")
                            st.write(f"- RSI14: `{rsi.get('rsi14', '-')}`")

                        st.markdown("**布林带**")
                        st.write(
                            f"- 上轨: `{boll.get('upper', '-')}` | "
                            f"中轨: `{boll.get('middle', '-')}` | "
                            f"下轨: `{boll.get('lower', '-')}`"
                        )

                    # 买卖信号
                    with st.expander("🎯 买卖信号提示", expanded=True):
                        buy_signals = signals.get("buy", [])
                        sell_signals = signals.get("sell", [])

                        if buy_signals:
                            st.markdown("**🟢 买入信号**")
                            for sig in buy_signals:
                                st.write(
                                    f"- **{sig.get('type', '')}**: "
                                    f"{sig.get('description', '')}"
                                )
                        else:
                            st.write("🟢 暂无明确买入信号")

                        if sell_signals:
                            st.markdown("**🔴 卖出信号**")
                            for sig in sell_signals:
                                st.write(
                                    f"- **{sig.get('type', '')}**: "
                                    f"{sig.get('description', '')}"
                                )
                        else:
                            st.write("🔴 暂无明确卖出信号")

                    # 综合评分
                    with st.expander("⭐ 综合评分与操作建议", expanded=True):
                        score = summary.get("score", 0)
                        rec = summary.get("recommendation", "观望")
                        action = summary.get("action", "建议观望")

                        score_cols = st.columns(3)
                        with score_cols[0]:
                            _display_metric_row(
                                label="综合评分",
                                value=str(score),
                                delta="偏多" if score > 0 else "偏空" if score < 0 else "中性",
                                delta_color="inverse",
                            )
                        with score_cols[1]:
                            _display_metric_row(label="建议", value=rec)
                        with score_cols[2]:
                            _display_metric_row(label="操作", value=action)

                        # 可视化评分条
                        if score >= 0:
                            st.progress(min(score / 100, 1.0),
                                        text=f"偏多倾向 {score}/100")
                        else:
                            st.progress(min(-score / 100, 1.0),
                                        text=f"偏空倾向 {abs(score)}/100")

            # K线数据表格预览
            if klines:
                with st.expander("📋 查看历史K线数据（表格）", expanded=False):
                    table_data = []
                    for k in klines[-30:]:
                        table_data.append({
                            "日期": k.get("date", ""),
                            "开盘": k.get("open", 0),
                            "最高": k.get("high", 0),
                            "最低": k.get("low", 0),
                            "收盘": k.get("close", 0),
                            "成交量": k.get("volume", 0),
                        })
                    st.dataframe(table_data, hide_index=True,
                                 use_container_width=True)

    else:
        st.info("👆 请输入股票代码后点击「开始分析」")


def page_watchlist() -> None:
    """自选股页面"""
    st.markdown("## 📋 自选股动态")

    if not WATCH_LIST:
        st.warning("⚠️ 当前未配置自选股，请编辑 `config/settings.py` 修改 `WATCH_LIST`")
        return

    st.info(f"当前共 {len(WATCH_LIST)} 只自选股，点击刷新获取最新行情", icon="📝")

    if st.button("🔄 刷新自选股", type="primary"):
        st.rerun()

    codes = [code for code, _ in WATCH_LIST]

    with st.spinner("获取自选股行情..."):
        quotes = get_batch_quotes(codes) or []

    if not quotes:
        st.warning("⚠️ 暂无行情数据（可能是非交易时间或网络问题）")
        return

    # 展示自选股
    cols = st.columns(3)
    for idx, (code, name) in enumerate(WATCH_LIST):
        quote = next((q for q in quotes if q.get("stock_code") == code), None)

        if not quote:
            continue

        price = quote.get("current_price", 0)
        change = quote.get("change_percent", 0) or 0
        volume = quote.get("volume", 0) or 0

        with cols[idx % 3]:
            st.markdown(f"### {name}")
            st.markdown(f"**代码:** `{code}`")

            _display_metric_row(
                label="现价",
                value=f"{price:.2f}",
                delta=f"{change:+.2f}%",
                delta_color="inverse",
            )
            st.write(f"成交量: {volume:,}")

            # K线图链接
            if st.button(f"📊 技术分析 {name}", key=f"watch_{code}"):
                st.session_state["nav"] = "股票分析"
                st.session_state["auto_code"] = code
                st.rerun()

            st.divider()


def page_portfolio() -> None:
    """持仓分析页面"""
    st.markdown("## 💼 持仓盈亏分析")

    if not PORTFOLIO:
        st.warning("⚠️ 当前未配置持仓，请编辑 `config/settings.py` 修改 `PORTFOLIO`")
        return

    codes = [code for code, _, _, _ in PORTFOLIO]

    with st.spinner("获取持仓股实时行情..."):
        quotes = get_batch_quotes(codes) or []

    if not quotes:
        st.warning("⚠️ 暂无行情数据")
        return

    # 计算盈亏
    portfolio_data = []
    total_cost = 0.0
    total_value = 0.0

    for code, name, qty, cost in PORTFOLIO:
        quote = next((q for q in quotes if q.get("stock_code") == code), None)
        if not quote:
            continue

        price = quote.get("current_price", 0)
        change = quote.get("change_percent", 0) or 0
        value = price * qty
        cost_total = cost * qty
        profit = value - cost_total
        profit_pct = (price - cost) / cost * 100 if cost else 0

        total_cost += cost_total
        total_value += value

        portfolio_data.append({
            "代码": code,
            "名称": name,
            "持仓": qty,
            "成本价": f"{cost:.2f}",
            "现价": f"{price:.2f}",
            "今日涨跌": f"{change:+.2f}%",
            "市值": f"{value:.2f}",
            "盈亏": f"{profit:+.2f}",
            "盈亏率": f"{profit_pct:+.2f}%",
        })

    # 展示表格
    st.dataframe(portfolio_data, hide_index=True, use_container_width=True)

    st.divider()

    # 汇总
    total_profit = total_value - total_cost
    total_profit_pct = (total_value - total_cost) / total_cost * 100 if total_cost else 0

    col1, col2, col3 = st.columns(3)
    with col1:
        _display_metric_row(label="总市值", value=f"¥ {total_value:.2f}")
    with col2:
        _display_metric_row(label="总成本", value=f"¥ {total_cost:.2f}")
    with col3:
        _display_metric_row(
            label="总盈亏",
            value=f"¥ {total_profit:.2f}",
            delta=f"{total_profit_pct:+.2f}%",
            delta_color="inverse",
        )

    # 简单盈亏条
    st.markdown("### 📊 盈亏可视化")
    if total_profit >= 0:
        st.success(f"🟢 当前总盈利 ¥{total_profit:.2f}（{total_profit_pct:+.2f}%）")
    else:
        st.error(f"🔴 当前总亏损 ¥{abs(total_profit):.2f}（{total_profit_pct:+.2f}%）")


def page_report() -> None:
    """生成报告页面"""
    st.markdown("## 📝 每日投资报告")

    st.info("综合大盘、自选股、持仓数据生成投资报告", icon="📋")

    if st.button("🚀 生成报告", type="primary"):
        with st.spinner("正在汇总数据并生成报告..."):
            # 创建 Agent
            data_agent = create_data_agent()
            analysis_agent = create_selector_agent()
            monitor = create_market_monitor(data_agent)
            watch_agent = create_auto_watch(data_agent, WATCH_LIST, PORTFOLIO)

            report_agent = create_report_agent(
                data_agent, analysis_agent, monitor, watch_agent
            )

            result = report_agent.generate_and_save(WATCH_LIST, PORTFOLIO)

            if result and result.get("report"):
                report_content = result["report"]

                # 展示报告
                st.markdown("### 📋 报告预览")
                st.markdown(report_content)

                if result.get("filepath"):
                    st.success(f"✅ 报告已保存到: `{result['filepath']}`")
                    with open(result["filepath"], "rb") as f:
                        st.download_button(
                            label="📥 下载报告 (Markdown)",
                            data=f,
                            file_name=os.path.basename(result["filepath"]),
                            mime="text/markdown",
                        )
            else:
                st.error("❌ 报告生成失败，请检查日志")


def page_selection() -> None:
    """选股推荐页面"""
    st.markdown("## 💡 选股策略推荐")

    strategy_names = list(SELECTION_STRATEGIES.keys())
    display_names = [SELECTION_STRATEGIES[k]["name"] for k in strategy_names]

    col_a, col_b = st.columns([1, 1])
    with col_a:
        chosen = st.selectbox("选择选股策略", display_names)
    with col_b:
        top_n = st.slider("筛选股票数量", min_value=5, max_value=30, value=10)

    strategy_key = strategy_names[display_names.index(chosen)]
    strategy_info = SELECTION_STRATEGIES[strategy_key]

    st.markdown(f"**策略说明:** {strategy_info.get('description', '')}")

    if st.button("🔍 开始选股", type="primary"):
        with st.spinner("根据策略筛选股票..."):
            # 简化：用自选股 + 默认股票池做筛选
            stock_pool = list(WATCH_LIST) + [
                ("600519", "贵州茅台"),
                ("601318", "中国平安"),
                ("000002", "万科A"),
                ("000858", "五粮液"),
                ("600036", "招商银行"),
                ("000333", "美的集团"),
                ("600276", "恒瑞医药"),
                ("300750", "宁德时代"),
                ("600887", "伊利股份"),
                ("002415", "海康威视"),
                ("601888", "中国中免"),
                ("600030", "中信证券"),
                ("601012", "隆基绿能"),
                ("002594", "比亚迪"),
                ("600900", "长江电力"),
                ("601166", "兴业银行"),
            ]

            # 去重
            seen = set()
            unique_pool = []
            for code, name in stock_pool:
                if code not in seen:
                    seen.add(code)
                    unique_pool.append((code, name))

            selector = create_selector_agent()
            result = selector.process({
                "strategy": strategy_key,
                "stocks": unique_pool,
                "limit": top_n,
            })

            if not result or not result.get("success"):
                st.warning(f"⚠️ 选股失败: {result.get('error', '未知错误')}")
                return

            results = result.get("results", [])
            if not results:
                st.info("ℹ️ 没有符合条件的股票")
                return

            st.success(f"✅ 共筛选出 {len(results)} 只股票")

            # 展示表格
            display_list = []
            for rank, item in enumerate(results, 1):
                display_list.append({
                    "排名": f"#{rank}",
                    "代码": item.get("stock_code", ""),
                    "名称": item.get("stock_name", ""),
                    "评分": item.get("score", 0),
                    "现价": item.get("current_price", 0),
                    "涨跌": f"{item.get('change_percent', 0):+.2f}%",
                    "理由": "; ".join(item.get("reasons", [])[:3]),
                })

            st.dataframe(display_list, hide_index=True, use_container_width=True)

            # 评分柱状图（如果 matplotlib 可用）
            if is_matplotlib_available() and results:
                try:
                    import matplotlib
                    matplotlib.use("Agg")
                    import matplotlib.pyplot as plt

                    names = [f"{r.get('stock_name', r.get('stock_code', ''))}" for r in results]
                    scores = [r.get("score", 0) for r in results]

                    fig, ax = plt.subplots(figsize=(10, 5))
                    colors = ["red" if s >= 0 else "green" for s in scores]

                    ax.barh(names, scores, color=colors, alpha=0.8, edgecolor="black")
                    ax.axvline(x=0, color="black", linewidth=0.8)
                    ax.set_xlabel("评分")
                    ax.set_title(f"{strategy_info.get('name', '')} - 评分排名")
                    ax.invert_yaxis()
                    ax.grid(True, alpha=0.3, axis="x")

                    for i, v in enumerate(scores):
                        ax.text(v + (1 if v >= 0 else -1), i, str(v),
                                va="center", fontsize=9, fontweight="bold")

                    st.pyplot(fig)
                    plt.close(fig)
                except Exception as e:
                    st.info(f"图表绘制失败: {e}")


def page_settings() -> None:
    """设置页面"""
    st.markdown("## ⚙️ 系统设置")

    st.markdown("### 📋 当前配置")

    with st.expander("📌 自选股列表", expanded=True):
        if WATCH_LIST:
            watch_table = []
            for code, name in WATCH_LIST:
                watch_table.append({"代码": code, "名称": name})
            st.dataframe(watch_table, hide_index=True, use_container_width=True)
        else:
            st.warning("暂无自选股")

    with st.expander("💼 持仓列表", expanded=True):
        if PORTFOLIO:
            portfolio_table = []
            for code, name, qty, cost in PORTFOLIO:
                portfolio_table.append({
                    "代码": code,
                    "名称": name,
                    "持仓数量": qty,
                    "成本价": f"¥{cost:.2f}",
                })
            st.dataframe(portfolio_table, hide_index=True, use_container_width=True)
        else:
            st.info("暂无持仓")

    with st.expander("🎯 选股策略", expanded=False):
        strategy_table = []
        for key, cfg in SELECTION_STRATEGIES.items():
            strategy_table.append({
                "策略键": key,
                "名称": cfg.get("name", ""),
                "说明": cfg.get("description", ""),
            })
        st.dataframe(strategy_table, hide_index=True, use_container_width=True)

    with st.expander("🔧 系统配置", expanded=False):
        st.json(SYSTEM_CONFIG)

    st.divider()
    st.markdown("### ✏️ 如何修改配置")
    st.info(
        "编辑 `config/settings.py` 文件：\n\n"
        "- 修改 `WATCH_LIST` → 调整自选股\n"
        "- 修改 `PORTFOLIO` → 调整持仓\n"
        "- 修改 `SELECTION_STRATEGIES` → 调整选股策略\n"
        "- 修改 `ALERT_THRESHOLDS` → 调整告警阈值\n"
        "- 修改 `SYSTEM_CONFIG` → 调整系统参数（如盯盘间隔）",
        icon="📝",
    )

    st.markdown("### 🔑 LLM 配置")
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if api_key and not api_key.startswith("your-"):
        st.success("✅ OPENAI_API_KEY 已配置")
    else:
        st.warning(
            "⚠️ OPENAI_API_KEY 未配置（将使用本地解释模式，AI 功能受限）\n\n"
            "请在 `.env` 文件中设置：`OPENAI_API_KEY=your-key-here`"
        )


# ========== 主应用 ==========
def main() -> None:
    """主应用入口"""
    # 侧边栏导航
    with st.sidebar:
        st.title("📈 A股投研系统")
        st.markdown(f"**数据时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        st.divider()

        pages = [
            "大盘监控",
            "股票分析",
            "自选股",
            "持仓分析",
            "选股推荐",
            "生成报告",
            "系统设置",
        ]
        icons = ["📊", "🔍", "📋", "💼", "💡", "📝", "⚙️"]

        current_nav = st.session_state.get("nav", pages[0])
        if current_nav not in pages:
            current_nav = pages[0]

        st.markdown("### 🧭 导航")
        selected = st.radio(
            "选择功能",
            pages,
            index=pages.index(current_nav) if current_nav in pages else 0,
            format_func=lambda x: f"{icons[pages.index(x)]} {x}",
            label_visibility="collapsed",
        )
        st.session_state["nav"] = selected

        st.divider()

        # 快捷操作
        st.markdown("### ⚡ 快捷操作")
        if st.button("🔄 刷新页面"):
            st.rerun()

        st.divider()
        st.markdown(
            f"""
            <small>
            **当前状态:**<br>
            - matplotlib: {'✅' if is_matplotlib_available() else '❌'}<br>
            - 自选股: {len(WATCH_LIST)} 只<br>
            - 持仓: {len(PORTFOLIO)} 只<br>
            </small>
            """,
            unsafe_allow_html=True,
        )

        st.divider()
        st.caption("版本: 0.1.0 | 仅供学习研究")

    # 自动填充股票代码（从自选股页面跳转）
    page = st.session_state.get("nav", pages[0])

    # 路由分发
    page_map = {
        "大盘监控": page_market,
        "股票分析": page_stock_analysis,
        "自选股": page_watchlist,
        "持仓分析": page_portfolio,
        "选股推荐": page_selection,
        "生成报告": page_report,
        "系统设置": page_settings,
    }

    handler = page_map.get(page)
    if handler:
        handler()
    else:
        page_market()


if __name__ == "__main__":
    main()
