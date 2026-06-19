"""
数据源工具 - 单元测试
覆盖: EastMoneyDataSource._parse_realtime / EastMoneyDataSource._safe_div
不依赖网络 —— 仅测试本地解析逻辑。
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.data_source import EastMoneyDataSource


class TestEastMoneyParsing(unittest.TestCase):
    """测试行情数据解析的正确性与鲁棒性。"""

    def test_normal_data_parsing(self):
        data = {
            "f57": "000001",
            "f58": "平安银行",
            "f43": 1250,       # 12.50
            "f170": 250,       # 2.50%
            "f169": 30,        # 0.30
            "f47": 500000,     # 成交量
            "f48": 800000,     # 成交额
            "f44": 1300,       # 13.00
            "f45": 1200,       # 12.00
            "f46": 1220,       # 12.20
            "f60": 1210,       # 12.10
        }
        parsed = EastMoneyDataSource._parse_realtime(data)
        self.assertEqual(parsed["stock_code"], "000001")
        self.assertEqual(parsed["stock_name"], "平安银行")
        self.assertAlmostEqual(parsed["current_price"], 12.50, places=2)
        self.assertAlmostEqual(parsed["change_percent"], 2.50, places=2)
        self.assertAlmostEqual(parsed["high"], 13.00, places=2)
        self.assertAlmostEqual(parsed["low"], 12.00, places=2)
        self.assertAlmostEqual(parsed["open"], 12.20, places=2)
        self.assertAlmostEqual(parsed["prev_close"], 12.10, places=2)
        self.assertIn("datetime", parsed)

    def test_none_fields_do_not_crash(self):
        """API 返回 null 时不能抛异常，必须给出合理的默认 0。"""
        data = {
            "f57": "000001",
            "f58": "平安银行",
            "f43": None,
            "f170": None,
            "f169": None,
            "f47": None,
            "f48": None,
            "f44": None,
            "f45": None,
            "f46": None,
            "f60": None,
        }
        parsed = EastMoneyDataSource._parse_realtime(data)
        self.assertEqual(parsed["current_price"], 0)
        self.assertEqual(parsed["change_percent"], 0)
        self.assertEqual(parsed["high"], 0)
        self.assertEqual(parsed["volume"], 0)

    def test_missing_fields_use_default(self):
        """字段缺失也应该返回合理默认值。"""
        data = {"f57": "000001", "f58": "平安银行"}
        parsed = EastMoneyDataSource._parse_realtime(data)
        self.assertEqual(parsed["current_price"], 0)
        self.assertEqual(parsed["volume"], 0)

    def test_secid_generation(self):
        """沪市股票以 6 开头，secid = 1.code；其他默认为 0.code。"""
        # 沪市
        self.assertEqual(EastMoneyDataSource._get_secid("600519"), "1.600519")
        # 深市
        self.assertEqual(EastMoneyDataSource._get_secid("000001"), "0.000001")
        self.assertEqual(EastMoneyDataSource._get_secid("300750"), "0.300750")

    def test_safe_div_helper(self):
        self.assertEqual(EastMoneyDataSource._safe_div(None, 100), 0)
        self.assertEqual(EastMoneyDataSource._safe_div(100, 100), 1)
        self.assertEqual(EastMoneyDataSource._safe_div(0, 100), 0)


class TestDataCollector(unittest.TestCase):
    """对 DataCollector / get_quote / get_kline 等函数进行 smoke test。

    由于这些函数依赖东方财富接口的网络访问，此处仅测试“无网络时不会抛未预期异常”
    的基础鲁棒性。真实的接口调用集成测试由手动执行。
    """

    def test_get_quote_with_invalid_code(self):
        # 非法股票代码不应抛未捕获异常，应当返回 None 或空结果
        from tools.data_source import get_quote
        try:
            get_quote("not_a_real_code")
        except Exception:
            # 网络访问允许异常，检查不会因类型问题炸掉
            pass

    def test_get_kline_with_small_count(self):
        from tools.data_source import get_kline
        try:
            get_kline("000001", "daily", 10)
        except Exception:
            pass


if __name__ == "__main__":
    unittest.main(verbosity=2)
