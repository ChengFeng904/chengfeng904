# -*- coding: utf-8 -*-
"""
Agent编排器
使用LangGraph协调多个Agent的工作
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class TaskResult:
    """任务结果"""
    success: bool
    agent: str
    data: Any
    error: Optional[str] = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class AgentOrchestrator:
    """
    Agent编排器
    负责协调各个Agent的工作，实现复杂任务流程
    """
    
    def __init__(self):
        self.agents = {}
        self.task_history = []
        
    def register_agent(self, name: str, agent: Any):
        """注册Agent"""
        self.agents[name] = agent
        logger.info(f"Agent已注册: {name}")
    
    def get_agent(self, name: str) -> Any:
        """获取Agent"""
        return self.agents.get(name)
    
    def execute_task(self, task: Dict) -> TaskResult:
        """
        执行单个任务
        task格式: {"agent": "data_agent", "action": "get_quote", "params": {...}}
        """
        agent_name = task.get("agent")
        action = task.get("action")
        params = task.get("params", {})
        
        agent = self.get_agent(agent_name)
        if not agent:
            return TaskResult(
                success=False,
                agent=agent_name,
                data=None,
                error=f"Agent不存在: {agent_name}"
            )
        
        try:
            if hasattr(agent, action):
                method = getattr(agent, action)
                result = method(**params) if params else method()
                
                # 记录任务
                self.task_history.append({
                    "task": task,
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                })
                
                return TaskResult(
                    success=True,
                    agent=agent_name,
                    data=result
                )
            else:
                return TaskResult(
                    success=False,
                    agent=agent_name,
                    data=None,
                    error=f"Agent {agent_name} 没有方法: {action}"
                )
                
        except Exception as e:
            logger.error(f"执行任务失败: {e}")
            return TaskResult(
                success=False,
                agent=agent_name,
                data=None,
                error=str(e)
            )
    
    def execute_workflow(self, workflow: List[Dict]) -> List[TaskResult]:
        """
        执行工作流（顺序执行多个任务）
        """
        results = []
        
        for task in workflow:
            result = self.execute_task(task)
            results.append(result)
            
            # 如果任务失败，可以选择停止或继续
            if not result.success and task.get("critical", False):
                logger.warning(f"关键任务失败，停止工作流")
                break
        
        return results
    
    def parallel_execute(self, tasks: List[Dict]) -> List[TaskResult]:
        """
        并行执行多个独立任务
        """
        # 这里简化处理，实际可以使用线程池
        results = []
        for task in tasks:
            result = self.execute_task(task)
            results.append(result)
        return results


class StockResearchOrchestrator(AgentOrchestrator):
    """
    股票投研编排器
    封装常用的投研工作流
    """
    
    def __init__(self):
        super().__init__()
        self.watchlist = []
        self.portfolio = []
    
    def setup(self, data_agent, analysis_agent, monitor_agent, watch_agent, report_agent):
        """初始化并注册所有Agent"""
        self.register_agent("data", data_agent)
        self.register_agent("analysis", analysis_agent)
        self.register_agent("monitor", monitor_agent)
        self.register_agent("watch", watch_agent)
        self.register_agent("report", report_agent)
    
    def set_watchlist(self, watchlist: List[tuple]):
        """设置自选股"""
        self.watchlist = watchlist
    
    def set_portfolio(self, portfolio: List[tuple]):
        """设置持仓"""
        self.portfolio = portfolio
    
    def daily_research_workflow(self) -> Dict:
        """
        每日投研工作流
        1. 获取大盘数据
        2. 分析自选股
        3. 检查告警
        4. 生成报告
        """
        results = {}
        
        # 1. 大盘监控
        logger.info("执行大盘监控...")
        try:
            monitor = self.get_agent("monitor")
            sentiment = monitor.analyze_market_sentiment()
            results["market_sentiment"] = sentiment
            logger.info(f"大盘情绪: {sentiment.get('sentiment_text', '未知')}")
        except Exception as e:
            logger.error(f"大盘监控失败: {e}")
            results["market_sentiment"] = {"error": str(e)}
        
        # 2. 自选股分析
        logger.info("分析自选股...")
        analysis_results = []
        try:
            analysis_agent = self.get_agent("analysis")
            for code, name in self.watchlist[:10]:  # 限制数量
                result = analysis_agent.process({
                    "stock_code": code,
                    "period": "daily",
                    "count": 60
                })
                if result.get("success"):
                    analysis_results.append({
                        "name": name,
                        "code": code,
                        "analysis": result["analysis"]
                    })
        except Exception as e:
            logger.error(f"自选股分析失败: {e}")
        
        results["watchlist_analysis"] = analysis_results
        
        # 3. 盯盘检查
        logger.info("执行盯盘检查...")
        try:
            watch = self.get_agent("watch")
            watch_result = watch.run_once()
            results["alerts"] = watch_result.get("alerts", [])
        except Exception as e:
            logger.error(f"盯盘检查失败: {e}")
            results["alerts"] = []
        
        # 4. 生成报告
        logger.info("生成报告...")
        try:
            report_agent = self.get_agent("report")
            report_result = report_agent.generate_and_save(
                self.watchlist,
                self.portfolio
            )
            results["report"] = report_result
        except Exception as e:
            logger.error(f"报告生成失败: {e}")
            results["report"] = {"success": False, "error": str(e)}
        
        results["timestamp"] = datetime.now().isoformat()
        
        return results
    
    def stock_analysis_workflow(self, stock_code: str, 
                                period: str = "daily") -> Dict:
        """
        单只股票分析工作流
        """
        results = {}
        
        # 1. 获取实时行情
        logger.info(f"获取 {stock_code} 行情...")
        try:
            data_agent = self.get_agent("data")
            quote = data_agent.get_stock_realtime(stock_code)
            results["quote"] = quote
        except Exception as e:
            logger.error(f"获取行情失败: {e}")
            results["quote"] = {"success": False, "error": str(e)}
        
        # 2. 技术分析
        logger.info(f"分析 {stock_code} 技术指标...")
        try:
            analysis_agent = self.get_agent("analysis")
            analysis = analysis_agent.process({
                "stock_code": stock_code,
                "period": period,
                "count": 100
            })
            results["analysis"] = analysis
        except Exception as e:
            logger.error(f"技术分析失败: {e}")
            results["analysis"] = {"success": False, "error": str(e)}
        
        results["timestamp"] = datetime.now().isoformat()
        
        return results
    
    def selection_workflow(self, strategy: str = "value_investment",
                          stock_pool: List[tuple] = None) -> Dict:
        """
        选股工作流
        """
        if stock_pool is None:
            # 默认使用自选股
            stock_pool = self.watchlist
        
        results = {}
        
        # 1. 获取所有股票实时数据
        logger.info(f"获取 {len(stock_pool)} 只股票数据...")
        try:
            data_agent = self.get_agent("data")
            all_codes = [code for code, _ in stock_pool]
            quotes = data_agent.process({
                "task": "get_batch_quotes",
                "params": {"stock_codes": all_codes}
            })
            results["quotes"] = quotes
        except Exception as e:
            logger.error(f"批量获取数据失败: {e}")
            results["quotes"] = {"success": False, "error": str(e)}
        
        # 2. 执行选股策略
        logger.info(f"执行选股策略: {strategy}...")
        try:
            # 使用SelectorAgent
            from agents.base import create_selector_agent
            selector = create_selector_agent()
            selection = selector.process({
                "strategy": strategy,
                "stocks": stock_pool,
                "limit": 20
            })
            results["selection"] = selection
        except Exception as e:
            logger.error(f"选股失败: {e}")
            results["selection"] = {"success": False, "error": str(e)}
        
        results["timestamp"] = datetime.now().isoformat()
        
        return results


# 便捷函数
def create_orchestrator() -> StockResearchOrchestrator:
    """创建股票投研编排器"""
    return StockResearchOrchestrator()


if __name__ == "__main__":
    print("=" * 50)
    print("编排器测试")
    print("=" * 50)
    
    # 创建编排器
    orchestrator = create_orchestrator()
    
    # 注册Agent
    from agents import (
        create_data_agent, create_analysis_agent, 
        create_market_monitor, create_auto_watch,
        create_report_agent
    )
    
    data_agent = create_data_agent()
    analysis_agent = create_analysis_agent()
    monitor = create_market_monitor(data_agent)
    watchlist = [("000001", "平安银行"), ("600519", "贵州茅台")]
    portfolio = [("000001", "平安银行", 1000, 12.50)]
    watch = create_auto_watch(data_agent, watchlist, portfolio)
    report = create_report_agent(data_agent, analysis_agent, monitor, watch)
    
    orchestrator.setup(data_agent, analysis_agent, monitor, watch, report)
    orchestrator.set_watchlist(watchlist)
    orchestrator.set_portfolio(portfolio)
    
    # 测试大盘监控工作流
    print("\n1. 测试大盘监控:")
    sentiment = orchestrator.get_agent("monitor").analyze_market_sentiment()
    print(f"   市场情绪: {sentiment.get('sentiment_text', '未知')}")
    
    # 测试单只股票分析
    print("\n2. 测试股票分析:")
    result = orchestrator.stock_analysis_workflow("000001")
    if result["analysis"].get("success"):
        summary = result["analysis"]["analysis"]["summary"]
        print(f"   评分: {summary.get('score')}")
        print(f"   建议: {summary.get('recommendation')}")
