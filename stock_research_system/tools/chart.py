# -*- coding: utf-8 -*-
"""
股票可视化模块
支持 K线图、技术指标叠加图的绘制（基于 matplotlib）
"""

import io
import base64
from typing import Dict, List, Optional

from tools.indicators import (
    calculate_ma,
    calculate_macd,
    calculate_kdj,
    calculate_rsi,
    calculate_boll,
)

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    import matplotlib.dates as mdates
    _MATPLOTLIB_AVAILABLE = True

    # 尝试解决中文显示问题
    for _font_name in ["Noto Sans CJK SC", "SimHei", "Microsoft YaHei", "WenQuanYi Micro Hei"]:
        try:
            font_manager.findfont(_font_name, fallback_to_default=False)
            plt.rcParams["font.sans-serif"] = [_font_name]
            break
        except Exception:
            continue
    plt.rcParams["axes.unicode_minus"] = False
except ImportError:
    _MATPLOTLIB_AVAILABLE = False


def _check_matplotlib() -> None:
    """检查 matplotlib 是否可用，不可用时抛出异常"""
    if not _MATPLOTLIB_AVAILABLE:
        raise ImportError(
            "matplotlib 未安装，请先安装：pip install matplotlib"
        )


def plot_kline_with_indicators(
    kline_data: List[Dict],
    stock_name: str = "",
    save_path: Optional[str] = None,
) -> Optional[str]:
    """
    绘制 K线图，叠加均线、MACD、成交量
    返回图片的 base64 字符串（用于网页展示），或保存到文件

    参数:
        kline_data: K线数据列表，每项包含 date/open/close/high/low/volume
        stock_name: 股票名称，显示在标题
        save_path: 若提供，则保存图片到该路径

    返回:
        base64 编码的图片字符串（PNG格式），或 None（当出错时）
    """
    _check_matplotlib()

    if not kline_data or len(kline_data) < 10:
        return None

    try:
        dates = [k["date"] for k in kline_data]
        opens = [k["open"] for k in kline_data]
        closes = [k["close"] for k in kline_data]
        highs = [k["high"] for k in kline_data]
        lows = [k["low"] for k in kline_data]
        volumes = [k["volume"] for k in kline_data]

        ma5 = calculate_ma(closes, 5)
        ma10 = calculate_ma(closes, 10)
        ma20 = calculate_ma(closes, 20)

        macd = calculate_macd(closes)
        dif = macd["dif"]
        dea = macd["dea"]
        hist = macd["histogram"]

        rsi14 = calculate_rsi(closes, 14)

        x = list(range(len(dates)))

        fig = plt.figure(figsize=(14, 10))
        gs = fig.add_gridspec(4, 1, height_ratios=[3, 1, 1, 0.3], hspace=0.15)

        # --- 子图 1: K线 + 均线 ---
        ax1 = fig.add_subplot(gs[0])
        colors = ["red" if c >= o else "green" for c, o in zip(closes, opens)]

        # 用柱状图表示 K线（简化版）
        for i in range(len(x)):
            ax1.plot([x[i], x[i]], [lows[i], highs[i]],
                     color=colors[i], linewidth=1)
            rect_h = abs(closes[i] - opens[i])
            rect_bottom = min(closes[i], opens[i])
            ax1.bar(x[i], rect_h, bottom=rect_bottom,
                    color=colors[i], width=0.7, alpha=0.8)

        ax1.plot(x, ma5, label="MA5", color="#FF9800", linewidth=1.5, alpha=0.9)
        ax1.plot(x, ma10, label="MA10", color="#2196F3", linewidth=1.5, alpha=0.9)
        ax1.plot(x, ma20, label="MA20", color="#9C27B0", linewidth=1.5, alpha=0.9)

        ax1.set_title(f"{stock_name} 技术分析", fontsize=14, fontweight="bold")
        ax1.set_ylabel("价格")
        ax1.legend(loc="upper left", fontsize=9)
        ax1.grid(True, alpha=0.3)

        # --- 子图 2: 成交量 ---
        ax2 = fig.add_subplot(gs[1], sharex=ax1)
        ax2.bar(x, volumes, color=colors, alpha=0.6)
        ax2.set_ylabel("成交量")
        ax2.grid(True, alpha=0.3)

        # --- 子图 3: MACD ---
        ax3 = fig.add_subplot(gs[2], sharex=ax1)
        ax3.plot(x, dif, label="DIF", color="#F44336", linewidth=1.2)
        ax3.plot(x, dea, label="DEA", color="#2196F3", linewidth=1.2)

        macd_colors = ["red" if v >= 0 else "green" for v in hist]
        ax3.bar(x, hist, color=macd_colors, alpha=0.6, label="MACD柱")
        ax3.axhline(y=0, color="gray", linestyle="--", linewidth=0.5)
        ax3.set_ylabel("MACD")
        ax3.legend(loc="upper left", fontsize=9)
        ax3.grid(True, alpha=0.3)

        # --- 子图 4: RSI 状态条（简化展示） ---
        latest_rsi = None
        for v in reversed(rsi14):
            if v is not None and str(v) != "nan":
                try:
                    if not (float(v) != float(v)):
                        latest_rsi = v
                        break
                except Exception:
                    continue

        status_text = "RSI 数据不足"
        status_color = "gray"
        if latest_rsi is not None:
            if latest_rsi < 30:
                status_text = f"RSI={latest_rsi:.1f} 超卖区域"
                status_color = "green"
            elif latest_rsi > 70:
                status_text = f"RSI={latest_rsi:.1f} 超买区域"
                status_color = "red"
            else:
                status_text = f"RSI={latest_rsi:.1f} 正常区域"
                status_color = "blue"

        ax4 = fig.add_subplot(gs[3])
        ax4.text(0.5, 0.5, status_text, fontsize=13, fontweight="bold",
                 color=status_color, ha="center", va="center")
        ax4.axis("off")

        # X轴标签
        step = max(1, len(dates) // 10)
        ax1.set_xticks(x[::step])
        ax1.set_xticklabels(dates[::step], rotation=30, ha="right", fontsize=8)
        plt.setp(ax2.get_xticklabels(), visible=False)
        plt.setp(ax3.get_xticklabels(), visible=False)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=100, bbox_inches="tight",
                        facecolor="white")

        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=100, bbox_inches="tight",
                    facecolor="white")
        plt.close(fig)
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode("utf-8")
        return img_base64

    except Exception as e:
        plt.close("all")
        print(f"绘制K线图失败: {e}")
        return None


def plot_market_indices(
    index_data: Dict[str, Dict],
    save_path: Optional[str] = None,
) -> Optional[str]:
    """
    绘制大盘指数涨跌柱状图

    参数:
        index_data: {指数代码: {stock_name: str, current_price: float, change_percent: float}}
        save_path: 若提供，保存到文件

    返回:
        base64 图片字符串
    """
    _check_matplotlib()

    try:
        names = []
        changes = []
        prices = []

        for code, data in index_data.items():
            names.append(data.get("stock_name", code))
            changes.append(data.get("change_percent", 0) or 0)
            prices.append(data.get("current_price", 0))

        if not names:
            return None

        fig, ax = plt.subplots(figsize=(10, 6))
        colors = ["red" if c >= 0 else "green" for c in changes]

        bars = ax.bar(names, changes, color=colors, alpha=0.8, edgecolor="black")
        ax.axhline(y=0, color="black", linewidth=0.8)
        ax.set_ylabel("涨跌幅 (%)", fontsize=11)
        ax.set_title("大盘指数涨跌", fontsize=14, fontweight="bold")
        ax.grid(True, alpha=0.3, axis="y")

        for bar, change, price in zip(bars, changes, prices):
            height = bar.get_height()
            y_pos = height + (0.1 if height >= 0 else -0.5)
            sign = "+" if change >= 0 else ""
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                y_pos,
                f"{sign}{change:.2f}%\n{price:.2f}",
                ha="center",
                va="bottom",
                fontsize=10,
                fontweight="bold",
            )

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=100, bbox_inches="tight",
                        facecolor="white")

        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=100, bbox_inches="tight",
                    facecolor="white")
        plt.close(fig)
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode("utf-8")
        return img_base64

    except Exception as e:
        plt.close("all")
        print(f"绘制大盘指数图失败: {e}")
        return None


def is_matplotlib_available() -> bool:
    """检查 matplotlib 是否可用"""
    return _MATPLOTLIB_AVAILABLE
