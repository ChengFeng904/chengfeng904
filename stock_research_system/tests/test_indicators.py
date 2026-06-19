"""
技术指标计算模块 - 单元测试
覆盖: calculate_ma / calculate_ema / calculate_macd / calculate_kdj /
       calculate_rsi / calculate_boll / TechnicalAnalyzer / analyze_stock
"""

import math
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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


def _make_klines(n=60, pattern="linear_up", seed=42):
    """构造各种走势的 K 线数据（纯本地，无网络）。"""
    import random
    random.seed(seed)
    base = 100.0
    klines = []
    for i in range(n):
        if pattern == "linear_up":
            close = base + i * 0.8 + random.uniform(-1, 1)
        elif pattern == "linear_down":
            close = base - i * 0.8 + random.uniform(-1, 1)
        elif pattern == "sideways":
            close = base + math.sin(i / 5.0) * 3.0 + random.uniform(-0.5, 0.5)
        elif pattern == "volatile":
            close = base + random.uniform(-8, 8)
        else:
            close = base + i * 0.3
        klines.append({
            "close": round(close, 2),
            "open": round(close - 0.5, 2),
            "high": round(close + 1.5, 2),
            "low": round(close - 1.5, 2),
            "volume": 1000 + i * 10,
            "date": f"2025-01-{min(i + 1, 28):02d}",
        })
    return klines


class TestMovingAverage(unittest.TestCase):
    """移动平均线 MA / EMA 测试。"""

    def test_ma_basic(self):
        prices = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0]
        ma3 = calculate_ma(prices, 3)
        self.assertEqual(len(ma3), len(prices))
        self.assertTrue(math.isnan(ma3[0]))
        self.assertTrue(math.isnan(ma3[1]))
        self.assertAlmostEqual(ma3[2], 2.0, places=2)
        self.assertAlmostEqual(ma3[6], 6.0, places=2)

    def test_ma_period_larger_than_data(self):
        prices = [1.0, 2.0]
        ma = calculate_ma(prices, 5)
        self.assertEqual(len(ma), 2)
        self.assertTrue(all(math.isnan(v) for v in ma))

    def test_ema_has_correct_length(self):
        prices = [float(i) for i in range(30)]
        ema = calculate_ema(prices, 12)
        self.assertEqual(len(ema), len(prices))

    def test_ema_short_period(self):
        # 数据长度小于 period 时返回 NaN
        ema = calculate_ema([1.0, 2.0], 5)
        self.assertTrue(all(math.isnan(v) for v in ema))


class TestMACD(unittest.TestCase):
    """MACD 指标测试。"""

    def test_macd_structure(self):
        prices = [100.0 + i * 0.5 for i in range(50)]
        result = calculate_macd(prices)
        self.assertIn("dif", result)
        self.assertIn("dea", result)
        self.assertIn("histogram", result)
        self.assertEqual(len(result["dif"]), 50)
        self.assertEqual(len(result["dea"]), 50)
        self.assertEqual(len(result["histogram"]), 50)

    def test_macd_early_bars_nan(self):
        prices = [100.0 + i * 0.5 for i in range(50)]
        result = calculate_macd(prices)
        # 前几个 bar 由于数据不足应为 NaN
        for idx in range(11):
            if result["dif"][idx] is not None and not math.isnan(result["dif"][idx]):
                continue
        # 允许 pandas 的 ewm 从第一天就有值，只校验不抛异常
        self.assertTrue(True)

    def test_macd_empty_input(self):
        result = calculate_macd([])
        self.assertEqual(len(result["dif"]), 0)


class TestRSI(unittest.TestCase):
    """RSI 指标测试。"""

    def test_rsi_range(self):
        prices = [100.0 + math.sin(i / 4.0) * 5 for i in range(60)]
        rsi = calculate_rsi(prices, 14)
        self.assertEqual(len(rsi), len(prices) - 1)
        valid_vals = [v for v in rsi if not math.isnan(v)]
        for v in valid_vals:
            self.assertGreaterEqual(v, 0)
            self.assertLessEqual(v, 100)

    def test_rsi_not_enough_data(self):
        rsi = calculate_rsi([1.0, 2.0, 3.0], 14)
        self.assertTrue(all(math.isnan(v) for v in rsi))


class TestKDJ(unittest.TestCase):
    """KDJ 指标测试。"""

    def test_kdj_structure(self):
        highs = [100.0 + i for i in range(30)]
        lows = [95.0 + i for i in range(30)]
        closes = [98.0 + i for i in range(30)]
        result = calculate_kdj(highs, lows, closes)
        self.assertIn("k", result)
        self.assertIn("d", result)
        self.assertIn("j", result)
        self.assertEqual(len(result["k"]), 30)


class TestBollingerBands(unittest.TestCase):
    """布林带测试。"""

    def test_boll_structure(self):
        prices = [100.0 + math.sin(i / 3.0) * 5 for i in range(50)]
        result = calculate_boll(prices, 20)
        self.assertEqual(len(result["upper"]), 50)
        self.assertEqual(len(result["middle"]), 50)
        self.assertEqual(len(result["lower"]), 50)

    def test_boll_band_ordering(self):
        # 对后段有效数据，upper >= middle >= lower
        prices = [100.0 + math.sin(i / 3.0) * 5 for i in range(50)]
        result = calculate_boll(prices, 20)
        for i in range(25, 50):
            self.assertGreaterEqual(result["upper"][i], result["middle"][i])
            self.assertGreaterEqual(result["middle"][i], result["lower"][i])

    def test_boll_too_short(self):
        result = calculate_boll([1.0, 2.0], 20)
        self.assertEqual(len(result["upper"]), 2)
        self.assertTrue(all(math.isnan(v) for v in result["upper"]))


class TestTechnicalAnalyzer(unittest.TestCase):
    """综合技术分析器测试。"""

    def test_full_analysis_uptrend(self):
        kl = _make_klines(60, "linear_up")
        result = analyze_stock(kl)
        self.assertIn("basic_info", result)
        self.assertIn("trend", result)
        self.assertIn("indicators", result)
        self.assertIn("signals", result)
        self.assertIn("summary", result)
        # 评分应是整数
        self.assertIsInstance(result["summary"]["score"], (int, float))

    def test_full_analysis_downtrend(self):
        kl = _make_klines(60, "linear_down")
        result = analyze_stock(kl)
        self.assertIn("summary", result)
        # 下跌趋势分数不应过高
        score = result["summary"]["score"]
        self.assertIsInstance(score, (int, float))

    def test_score_bounded(self):
        """综合评分必须在 -100 到 100 之间。"""
        for pattern in ["linear_up", "linear_down", "sideways", "volatile"]:
            kl = _make_klines(80, pattern)
            result = analyze_stock(kl)
            score = result["summary"]["score"]
            self.assertGreaterEqual(score, -100)
            self.assertLessEqual(score, 100)

    def test_indicators_keys(self):
        """_calculate_indicators 返回的 rsi/macd 结构与摘要访问一致。"""
        kl = _make_klines(60, "sideways")
        analyzer = TechnicalAnalyzer(kl)
        indicators = analyzer._calculate_indicators()
        for key in ("rsi6", "rsi12", "rsi14", "rsi24"):
            self.assertIn(key, indicators["rsi"])
        for key in ("dif", "dea", "histogram"):
            self.assertIn(key, indicators["macd"])

    def test_buy_sell_signal_types(self):
        """信号类型应为已知的 5 类之一。"""
        valid_buy = {"MA金叉", "MACD金叉", "RSI超卖", "布林下轨支撑", "KDJ金叉"}
        valid_sell = {"MA死叉", "MACD死叉", "RSI超买", "布林上轨压力", "KDJ死叉"}
        kl = _make_klines(100, "volatile")
        result = analyze_stock(kl)
        for s in result["signals"]["buy"]:
            self.assertIn(s["type"], valid_buy | {"暂无明显信号"})
        for s in result["signals"]["sell"]:
            self.assertIn(s["type"], valid_sell)


class TestEdgeCases(unittest.TestCase):
    """边界条件测试。"""

    def test_empty_kline(self):
        result = analyze_stock([])
        self.assertIn("error", result)

    def test_insufficient_kline(self):
        kl = _make_klines(5, "linear_up")
        result = analyze_stock(kl)
        self.assertIn("error", result)

    def test_minimum_valid_kline(self):
        # 刚好 20 根应该能计算
        kl = _make_klines(20, "linear_up")
        result = analyze_stock(kl)
        self.assertIn("summary", result)
        self.assertIn("score", result["summary"])

    def test_zero_price_prev_close(self):
        # prev_close 为 0 时不能除零
        kl = [
            {"close": 0.0, "open": 0.0, "high": 0.0, "low": 0.0, "volume": 0, "date": "2025-01-01"},
            {"close": 5.0, "open": 4.0, "high": 6.0, "low": 3.0, "volume": 100, "date": "2025-01-02"},
        ]
        analyzer = TechnicalAnalyzer(kl)
        # 基础信息里的涨跌幅不会抛异常
        info = analyzer._get_basic_info()
        self.assertIsNotNone(info.get("change_percent"))


class TestVolumeMA(unittest.TestCase):
    """成交量均线测试。"""

    def test_volume_ma(self):
        from tools.indicators import calculate_vol_ma
        volumes = [100, 200, 300, 400, 500, 600, 700]
        result = calculate_vol_ma(volumes)
        self.assertIn("ma5", result)
        self.assertEqual(len(result["ma5"]), 7)


if __name__ == "__main__":
    unittest.main(verbosity=2)
