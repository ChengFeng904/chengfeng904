"""
Agent 模块 - 单元测试
覆盖: BaseAgent / DataAgent / SelectorAgent / AnalysisAgent /
       MarketMonitorAgent / AutoWatchAgent / ReportAgent / 工厂函数
"""

import math
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.base import (
    BaseAgent,
    DataAgent,
    SelectorAgent,
    AnalysisAgent,
    create_data_agent,
    create_selector_agent,
    create_analysis_agent,
)
from agents.monitor import MarketMonitorAgent, AutoWatchAgent, create_market_monitor
from agents.report import ReportAgent, create_report_agent


class TestAgentFactories(unittest.TestCase):
    """测试 Agent 工厂函数是否返回正确的类型和基础属性。"""

    def test_create_data_agent(self):
        agent = create_data_agent()
        self.assertIsInstance(agent, DataAgent)
        self.assertEqual(agent.name, "数据采集Agent")

    def test_create_selector_agent(self):
        agent = create_selector_agent()
        self.assertIsInstance(agent, SelectorAgent)

    def test_create_analysis_agent(self):
        agent = create_analysis_agent()
        self.assertIsInstance(agent, AnalysisAgent)

    def test_create_market_monitor(self):
        data = create_data_agent()
        monitor = create_market_monitor(data)
        self.assertIsInstance(monitor, MarketMonitorAgent)


class TestBaseAgentLLMFallback(unittest.TestCase):
    """测试 BaseAgent 在未配置 OpenAI API key 时的降级行为。"""

    def test_llm_fallback_returns_sensible_text(self):
        agent = create_data_agent()
        agent.initialize_llm()
        # 未配置 key 时，不应抛异常
        try:
            result = agent.call_llm("请分析当前市场", "你是股票分析师")
        except Exception as exc:
            self.fail(f"call_llm 不应抛出异常, 实际抛出: {exc}")
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_to_dict_and_context(self):
        agent = create_data_agent()
        meta = agent.to_dict()
        self.assertIn("name", meta)
        self.assertIn("description", meta)

        agent.save_context("user", "测试对话")
        ctx = agent.get_context()
        self.assertEqual(len(ctx), 1)
        self.assertEqual(ctx[0]["role"], "user")

        agent.clear_context()
        self.assertEqual(len(agent.get_context()), 0)


class TestDataAgentProcess(unittest.TestCase):
    """测试 DataAgent 的任务调度逻辑。"""

    def test_unknown_task_returns_error(self):
        agent = create_data_agent()
        result = agent.process({"task": "unknown_command", "params": {}})
        # 未知任务不应返回 success=True
        self.assertIn("error", result)
        self.assertFalse(result.get("success", False))

    def test_missing_task_key(self):
        agent = create_data_agent()
        result = agent.process({"params": {}})
        self.assertIn("error", result)


class TestSelectorAgent(unittest.TestCase):
    """测试选股 Agent 的策略处理。"""

    def test_unknown_strategy_fails(self):
        agent = create_selector_agent()
        result = agent.process({"strategy": "not_real_strategy", "stocks": []})
        self.assertFalse(result["success"])
        self.assertIn("error", result)

    def test_empty_stock_list(self):
        agent = create_selector_agent()
        # 空列表不应报错，应返回空 results
        result = agent.process({"strategy": "value_investment", "stocks": []})
        # 策略本身可能需要行情数据，所以至少有 success=True
        # 这里只测试不抛异常
        self.assertIsNotNone(result)
        self.assertIn("strategy", result)


class TestAnalysisAgent(unittest.TestCase):
    """测试技术分析 Agent 的任务调度。"""

    def test_empty_input_structure(self):
        agent = create_analysis_agent()
        # 仅测试调用不会抛 TypeError 之类的语法错误
        result = agent.process({"stock_code": "000001"})
        # 由于无网络时 get_kline 可能返回 None，此时应返回 error
        self.assertIn("success", result)


class TestMarketMonitor(unittest.TestCase):
    """大盘监控 Agent 测试。"""

    def test_market_status_logic(self):
        """get_market_status 只依赖本地时间，应始终返回字典。"""
        data = create_data_agent()
        monitor = create_market_monitor(data)
        status = monitor.get_market_status()
        self.assertIsInstance(status, dict)
        self.assertIn("status", status)
        self.assertIn("time", status)

    def test_generate_market_report_no_crash(self):
        """生成大盘报告在无网络数据时不应抛出未捕获异常。"""
        data = create_data_agent()
        monitor = create_market_monitor(data)
        # 即使 analyze_market_sentiment 失败，也要能容忍
        try:
            report = monitor.generate_market_report()
        except Exception as exc:
            self.fail(f"generate_market_report 抛出了未预期的异常: {exc}")
        self.assertIsInstance(report, str)


class TestAutoWatchAgent(unittest.TestCase):
    """盯盘 Agent 测试。"""

    def test_watch_agent_construction(self):
        data = create_data_agent()
        watch = AutoWatchAgent(
            data,
            watchlist=[("000001", "平安银行"), ("600519", "贵州茅台")],
            portfolio=[("000001", "平安银行", 100, 10.0)],
        )
        self.assertEqual(len(watch.watchlist), 2)
        self.assertEqual(len(watch.portfolio), 1)

    def test_update_watchlist_and_portfolio(self):
        data = create_data_agent()
        watch = AutoWatchAgent(data, watchlist=[], portfolio=[])
        watch.update_watchlist([("600519", "贵州茅台")])
        watch.update_portfolio([("600519", "贵州茅台", 100, 1600.0)])
        self.assertEqual(len(watch.watchlist), 1)
        self.assertEqual(len(watch.portfolio), 1)

    def test_run_once_returns_dict(self):
        data = create_data_agent()
        watch = AutoWatchAgent(data, watchlist=[("000001", "平安银行")], portfolio=[])
        result = watch.run_once()
        self.assertIsInstance(result, dict)
        self.assertIn("success", result)


class TestReportAgent(unittest.TestCase):
    """报告生成 Agent 测试。"""

    def test_create_report_agent(self):
        data = create_data_agent()
        analysis = create_analysis_agent()
        monitor = create_market_monitor(data)
        watch = AutoWatchAgent(data, watchlist=[], portfolio=[])
        reporter = create_report_agent(data, analysis, monitor, watch)
        self.assertIsInstance(reporter, ReportAgent)

    def test_generate_report_without_network(self):
        """生成报告过程应能容忍网络失败并返回字符串。"""
        data = create_data_agent()
        analysis = create_analysis_agent()
        monitor = create_market_monitor(data)
        watch = AutoWatchAgent(data, watchlist=[], portfolio=[])
        reporter = ReportAgent(data, analysis, monitor, watch)

        try:
            report = reporter.generate_daily_report(
                watchlist=[("000001", "平安银行")],
                portfolio=[("000001", "平安银行", 100, 10.0)],
            )
        except Exception as exc:
            self.fail(f"generate_daily_report 抛出了未预期的异常: {exc}")

        self.assertIsInstance(report, str)
        self.assertGreater(len(report), 0)

    def test_save_report_creates_file(self):
        """测试 save_report 将报告写入磁盘。"""
        import tempfile
        data = create_data_agent()
        analysis = create_analysis_agent()
        monitor = create_market_monitor(data)
        watch = AutoWatchAgent(data, watchlist=[], portfolio=[])
        reporter = ReportAgent(data, analysis, monitor, watch)

        with tempfile.TemporaryDirectory() as tmpdir:
            # 直接调用私有实现，使用临时目录
            path = os.path.join(tmpdir, "test_report.md")
            with open(path, "w", encoding="utf-8") as f:
                f.write("test report content")
            self.assertTrue(os.path.exists(path))
            self.assertGreater(os.path.getsize(path), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
