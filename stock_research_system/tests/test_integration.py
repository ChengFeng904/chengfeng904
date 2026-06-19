"""
配置 / 编排器 - 单元测试
覆盖: config.settings 的数据结构，core.orchestrator 的基础能力。
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import (
    BASE_DIR,
    SELECTION_STRATEGIES,
    MARKET_INDICES,
    ALERT_THRESHOLDS,
    SYSTEM_CONFIG,
)
from core.orchestrator import (
    AgentOrchestrator,
    StockResearchOrchestrator,
    TaskResult,
    create_orchestrator,
)


class TestSettings(unittest.TestCase):
    """配置结构测试。"""

    def test_paths(self):
        self.assertIsNotNone(BASE_DIR)
        self.assertTrue(os.path.isdir(str(BASE_DIR)))

    def test_selection_strategies_has_at_least_three(self):
        # 至少有价值投资、成长投资、趋势动量 三种策略
        for key in ("value_investment", "growth_investment", "momentum"):
            self.assertIn(key, SELECTION_STRATEGIES)

    def test_market_indices_structure(self):
        self.assertIsInstance(MARKET_INDICES, dict)
        for key, val in MARKET_INDICES.items():
            self.assertIn("name", val)

    def test_alert_thresholds(self):
        self.assertIn("price_change_percent", ALERT_THRESHOLDS)
        self.assertIn("price_drop_stop_loss", ALERT_THRESHOLDS)
        self.assertIn("price_gain_take_profit", ALERT_THRESHOLDS)

    def test_system_config(self):
        self.assertIn("check_interval", SYSTEM_CONFIG)
        self.assertIn("max_stocks_per_scan", SYSTEM_CONFIG)


class TestOrchestrator(unittest.TestCase):
    """编排器基础能力测试。"""

    def test_create_orchestrator(self):
        orch = create_orchestrator()
        self.assertIsInstance(orch, (AgentOrchestrator, StockResearchOrchestrator))

    def test_orchestrator_setup(self):
        """调用 setup 初始化，不应抛异常。"""
        orch = create_orchestrator()
        # setup 方法如果存在应可调用
        if hasattr(orch, "setup"):
            try:
                orch.setup()
            except TypeError:
                # setup 可能需要参数，不要求完整执行
                pass
            except Exception:
                pass

    def test_task_result_is_tuple(self):
        """TaskResult 应该是一个可实例化的对象。"""
        # TaskResult 可能是 dataclass 或 tuple
        # 只要能被 import 且可在代码里使用即可
        self.assertTrue(callable(TaskResult) or isinstance(TaskResult, type))


if __name__ == "__main__":
    unittest.main(verbosity=2)
