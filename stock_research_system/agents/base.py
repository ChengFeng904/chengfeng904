# -*- coding: utf-8 -*-
"""
Agent基类
定义Agent的基础结构和通用方法
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Agent基类"""
    
    def __init__(self, name: str, description: str, model: str = "gpt-4o", 
                 temperature: float = 0.5):
        self.name = name
        self.description = description
        self.model_name = model
        self.temperature = temperature
        self.llm = None
        self.conversation_history = []
        
    def initialize_llm(self):
        """初始化LLM（延迟加载）"""
        if self.llm is None:
            try:
                self.llm = ChatOpenAI(
                    model=self.model_name,
                    temperature=self.temperature,
                    api_key="your-api-key"  # 用户需要替换为实际API Key
                )
            except Exception as e:
                logger.error(f"初始化LLM失败: {e}")
                raise
    
    @abstractmethod
    def process(self, input_data: Any) -> Dict:
        """
        处理输入数据
        子类必须实现
        """
        pass
    
    def call_llm(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """调用LLM"""
        if self.llm is None:
            self.initialize_llm()
        
        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))
        
        try:
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            logger.error(f"LLM调用失败: {e}")
            return f"错误: {str(e)}"
    
    def save_context(self, role: str, content: str):
        """保存对话上下文"""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_context(self) -> List[Dict]:
        """获取对话上下文"""
        return self.conversation_history
    
    def clear_context(self):
        """清空对话上下文"""
        self.conversation_history = []
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "name": self.name,
            "description": self.description,
            "model": self.model_name,
            "temperature": self.temperature,
        }


class DataAgent(BaseAgent):
    """数据采集Agent"""
    
    def __init__(self):
        super().__init__(
            name="数据采集Agent",
            description="负责从各个平台采集A股市场数据",
            model="gpt-4o",
            temperature=0.3
        )
        self.data_collector = None
        
    def process(self, input_data: Dict) -> Dict:
        """
        处理数据请求
        input_data格式: {"task": "get_quote"/"get_kline"/"get_market", "params": {...}}
        """
        task = input_data.get("task")
        params = input_data.get("params", {})
        
        # 延迟导入避免循环依赖
        from tools.data_source import (
            get_quote, get_kline, get_batch_quotes, 
            get_market_index, get_limit_up, DataCollector
        )
        
        result = {"success": False, "data": None, "error": None}
        
        try:
            if task == "get_quote":
                stock_code = params.get("stock_code")
                result["data"] = get_quote(stock_code)
                result["success"] = True
                
            elif task == "get_kline":
                stock_code = params.get("stock_code")
                period = params.get("period", "daily")
                count = params.get("count", 100)
                result["data"] = get_kline(stock_code, period, count)
                result["success"] = True
                
            elif task == "get_batch_quotes":
                stock_codes = params.get("stock_codes", [])
                result["data"] = get_batch_quotes(stock_codes)
                result["success"] = True
                
            elif task == "get_market":
                result["data"] = get_market_index()
                result["success"] = True
                
            elif task == "get_limit_up":
                result["data"] = get_limit_up()
                result["success"] = True
                
            else:
                result["error"] = f"未知任务: {task}"
                
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"数据采集失败: {e}")
        
        return result
    
    def get_stock_realtime(self, stock_code: str) -> Dict:
        """获取单只股票实时行情"""
        return self.process({
            "task": "get_quote",
            "params": {"stock_code": stock_code}
        })
    
    def get_stock_kline(self, stock_code: str, period: str = "daily", 
                       count: int = 100) -> Dict:
        """获取股票K线数据"""
        return self.process({
            "task": "get_kline",
            "params": {"stock_code": stock_code, "period": period, "count": count}
        })
    
    def get_watchlist_realtime(self, watchlist: List[Tuple[str, str]]) -> List[Dict]:
        """获取自选股实时行情"""
        codes = [code for code, _ in watchlist]
        return self.process({
            "task": "get_batch_quotes",
            "params": {"stock_codes": codes}
        })
    
    def get_market_overview(self) -> Dict:
        """获取市场概览"""
        return self.process({"task": "get_market"})
    
    def analyze_with_llm(self, data: Dict, question: str) -> str:
        """使用LLM分析数据"""
        system_prompt = """你是一个专业的股票数据分析师。请根据提供的数据，回答用户的问题。
        注意：
        1. 数据分析要客观准确
        2. 可以给出趋势判断和技术分析
        3. 不构成投资建议，仅供参考
        4. 如果数据不足，明确告知用户"""
        
        prompt = f"""股票数据：{json.dumps(data, ensure_ascii=False, indent=2)}

用户问题：{question}"""
        
        return self.call_llm(prompt, system_prompt)


class SelectorAgent(BaseAgent):
    """选股策略Agent"""
    
    def __init__(self):
        super().__init__(
            name="选股策略Agent",
            description="基于财务指标和技术指标筛选优质股票",
            model="gpt-4o",
            temperature=0.5
        )
        
    def process(self, input_data: Dict) -> Dict:
        """
        处理选股请求
        input_data格式: {"strategy": "value_investment", "stocks": [...]}
        """
        from config.settings import SELECTION_STRATEGIES
        from tools.indicators import analyze_stock
        from tools.data_source import get_quote, get_kline
        
        strategy = input_data.get("strategy", "value_investment")
        stocks = input_data.get("stocks", [])
        limit = input_data.get("limit", 10)
        
        # 获取策略配置
        strategy_config = SELECTION_STRATEGIES.get(strategy)
        if not strategy_config:
            return {"success": False, "error": f"未知策略: {strategy}"}
        
        results = []
        filters = strategy_config.get("filters", {})
        
        for stock_code, stock_name in stocks[:limit]:
            try:
                # 获取实时行情
                quote = get_quote(stock_code)
                if not quote:
                    continue
                
                # 获取K线数据
                klines = get_kline(stock_code, "daily", 60)
                
                # 基础筛选
                score = 0
                reasons = []
                
                # 价值投资筛选
                if strategy == "value_investment":
                    pe = quote.get("pe", 0)
                    if filters.get("pe_ratio"):
                        min_pe, max_pe = filters["pe_ratio"]
                        if min_pe <= pe <= max_pe:
                            score += 20
                            reasons.append(f"市盈率合理: {pe}")
                        elif pe and pe > 0:
                            if pe < min_pe:
                                score += 10
                                reasons.append(f"市盈率偏低: {pe}")
                            else:
                                score -= 10
                                reasons.append(f"市盈率偏高: {pe}")
                    
                    change_percent = quote.get("change_percent", 0)
                    if change_percent < 0:
                        score += 10
                        reasons.append("今日下跌，可能存在机会")
                    elif change_percent > 5:
                        score -= 5
                        reasons.append("今日涨幅过大，追高风险")
                
                # 成长投资筛选
                elif strategy == "growth_investment":
                    change_percent = quote.get("change_percent", 0)
                    if -3 <= change_percent <= 3:
                        score += 15
                        reasons.append("涨跌幅适中，波动稳健")
                
                # 趋势动量筛选
                elif strategy == "momentum":
                    if klines:
                        ma5 = sum([k["close"] for k in klines[-5:]]) / 5
                        ma10 = sum([k["close"] for k in klines[-10:]]) / 10
                        ma20 = sum([k["close"] for k in klines[-20:]]) / 20
                        
                        if ma5 > ma10 > ma20:
                            score += 25
                            reasons.append("均线多头排列，趋势向好")
                        elif ma5 > ma10:
                            score += 10
                            reasons.append("短期均线向上")
                
                # 技术分析加分
                if klines and len(klines) >= 20:
                    analysis = analyze_stock(klines)
                    tech_score = analysis.get("summary", {}).get("score", 0)
                    score += tech_score / 5  # 归一化
                    
                    buy_signals = analysis.get("signals", {}).get("buy", [])
                    if buy_signals:
                        reasons.append(f"存在{len(buy_signals)}个买入信号")
                
                results.append({
                    "stock_code": stock_code,
                    "stock_name": stock_name,
                    "score": score,
                    "current_price": quote.get("current_price"),
                    "change_percent": quote.get("change_percent"),
                    "reasons": reasons
                })
                
            except Exception as e:
                logger.error(f"分析股票失败 {stock_code}: {e}")
                continue
        
        # 按评分排序
        results.sort(key=lambda x: x["score"], reverse=True)
        
        return {
            "success": True,
            "strategy": strategy,
            "strategy_name": strategy_config["name"],
            "results": results[:limit]
        }
    
    def recommend_with_llm(self, stocks: List[Dict], strategy: str) -> str:
        """使用LLM生成选股建议"""
        system_prompt = """你是一个专业的股票投资顾问。根据筛选结果，给出投资建议。
        注意：
        1. 客观分析每只股票的优缺点
        2. 提示潜在风险
        3. 不构成投资建议，仅供参考
        4. 建议简洁明了，适合小白理解"""
        
        prompt = f"""选股策略：{strategy}

筛选结果：{json.dumps(stocks, ensure_ascii=False, indent=2)}

请给出简要的投资建议："""
        
        return self.call_llm(prompt, system_prompt)


class AnalysisAgent(BaseAgent):
    """技术分析Agent"""
    
    def __init__(self):
        super().__init__(
            name="技术分析Agent",
            description="进行股票技术分析，判断买卖点",
            model="gpt-4o",
            temperature=0.4
        )
    
    def process(self, input_data: Dict) -> Dict:
        """
        处理分析请求
        input_data格式: {"stock_code": "000001", "period": "daily"}
        """
        from tools.data_source import get_kline, get_quote
        from tools.indicators import analyze_stock
        
        stock_code = input_data.get("stock_code")
        period = input_data.get("period", "daily")
        count = input_data.get("count", 100)
        
        # 获取K线数据
        klines = get_kline(stock_code, period, count)
        if not klines:
            return {"success": False, "error": "无法获取K线数据"}
        
        # 获取实时行情
        quote = get_quote(stock_code)
        
        # 执行技术分析
        analysis = analyze_stock(klines)
        
        # 添加实时数据
        if quote:
            analysis["realtime"] = {
                "current_price": quote.get("current_price"),
                "change_percent": quote.get("change_percent"),
                "volume": quote.get("volume"),
                "datetime": quote.get("datetime")
            }
        
        return {
            "success": True,
            "stock_code": stock_code,
            "analysis": analysis
        }
    
    def analyze_with_llm(self, analysis: Dict, stock_name: str) -> str:
        """使用LLM解读技术分析结果"""
        system_prompt = """你是一个经验丰富的股票技术分析师。请解读技术分析结果，给出通俗易懂的解释。
        注意：
        1. 用简单的语言解释专业术语
        2. 给出明确的投资建议
        3. 强调风险控制
        4. 不构成投资建议，仅供参考"""
        
        prompt = f"""请分析 {stock_name} 的技术指标：

{json.dumps(analysis, ensure_ascii=False, indent=2)}

请给出通俗易懂的解读和操作建议："""
        
        return self.call_llm(prompt, system_prompt)


# 便捷函数
def create_data_agent() -> DataAgent:
    """创建数据Agent"""
    return DataAgent()


def create_selector_agent() -> SelectorAgent:
    """创建选股Agent"""
    return SelectorAgent()


def create_analysis_agent() -> AnalysisAgent:
    """创建分析Agent"""
    return AnalysisAgent()


if __name__ == "__main__":
    print("=" * 50)
    print("Agent测试")
    print("=" * 50)
    
    # 测试数据Agent
    print("\n1. 测试数据Agent:")
    data_agent = create_data_agent()
    quote = data_agent.get_stock_realtime("000001")
    if quote.get("success"):
        data = quote["data"]
        print(f"   {data['stock_name']}: {data['current_price']} ({data['change_percent']:.2f}%)")
    
    # 测试分析Agent
    print("\n2. 测试分析Agent:")
    analysis_agent = create_analysis_agent()
    result = analysis_agent.process({
        "stock_code": "000001",
        "period": "daily",
        "count": 60
    })
    if result.get("success"):
        summary = result["analysis"]["summary"]
        print(f"   评分: {summary['score']}")
        print(f"   建议: {summary['recommendation']}")
