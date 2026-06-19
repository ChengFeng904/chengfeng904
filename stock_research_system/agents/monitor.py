# -*- coding: utf-8 -*-
"""
监控Agent模块
包含大盘监控和自动盯盘Agent
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
import time
import logging
from threading import Thread, Event

logger = logging.getLogger(__name__)


class MarketMonitorAgent:
    """大盘监控Agent"""
    
    def __init__(self, data_agent):
        self.data_agent = data_agent
        self.market_status = "closed"  # closed/opening/halting
        
    def get_market_status(self) -> Dict:
        """获取市场状态"""
        now = datetime.now()
        hour = now.hour
        
        if 9 <= hour < 12 or 13 <= hour < 15:
            self.market_status = "trading"
        elif hour == 9 and now.minute < 30:
            self.market_status = "call_auction"  # 集合竞价
        elif hour == 15:
            self.market_status = "closing"
        else:
            self.market_status = "closed"
        
        return {"status": self.market_status, "time": now.strftime("%H:%M:%S")}
    
    def analyze_market_sentiment(self) -> Dict:
        """分析市场情绪"""
        # 获取四大指数
        indices = self.data_agent.get_market_overview()
        
        if not indices.get("success"):
            return {"error": "获取指数失败"}
        
        index_data = indices.get("data", {})
        
        # 计算市场强度
        total_change = 0
        index_count = 0
        sentiment = "neutral"
        details = []
        
        for code, data in index_data.items():
            change = data.get("change_percent", 0)
            total_change += change
            index_count += 1
            
            status = "上涨" if change > 0 else "下跌"
            emoji = "🔴" if change > 0 else "🟢" if change < 0 else "⚪"
            details.append(f"{emoji}{data.get('stock_name', code)}: {data.get('current_price')} ({change:+.2f}%)")
        
        if index_count > 0:
            avg_change = total_change / index_count
            
            if avg_change > 1.5:
                sentiment = "very_bullish"
            elif avg_change > 0.5:
                sentiment = "bullish"
            elif avg_change < -1.5:
                sentiment = "very_bearish"
            elif avg_change < -0.5:
                sentiment = "bearish"
        
        return {
            "sentiment": sentiment,
            "sentiment_text": {
                "very_bullish": "极强势",
                "bullish": "偏强",
                "neutral": "中性",
                "bearish": "偏弱",
                "very_bearish": "极弱势"
            }.get(sentiment, "未知"),
            "average_change": round(total_change / index_count, 2) if index_count > 0 else 0,
            "details": details,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def get_sector_performance(self) -> List[Dict]:
        """获取板块表现"""
        # 简化版：返回涨停股统计
        limit_result = self.data_agent.process({"task": "get_limit_up", "params": {}})
        
        if not limit_result.get("success"):
            return []
        
        limit_stocks = limit_result.get("data", [])
        
        return {
            "limit_up_count": len(limit_stocks),
            "limit_up_stocks": limit_stocks[:20]  # 取前20只
        }
    
    def generate_market_report(self) -> str:
        """生成大盘分析报告"""
        status = self.get_market_status()
        sentiment = self.analyze_market_sentiment()
        sector = self.get_sector_performance()
        
        report = f"""
📊 **大盘监控报告**
{'='*40}
⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
📈 市场状态: {status['status']}

**市场情绪分析**
情绪等级: {sentiment.get('sentiment_text', '未知')}
平均涨跌: {sentiment.get('average_change', 0):+.2f}%

**主要指数**
"""
        
        for detail in sentiment.get("details", []):
            report += f"- {detail}\n"
        
        report += f"""
**涨停板统计**
涨停股数量: {sector.get('limit_up_count', 0)} 只
"""
        
        limit_stocks = sector.get("limit_up_stocks", [])
        if limit_stocks:
            report += "涨停股票:\n"
            for stock in limit_stocks[:10]:
                report += f"- {stock.get('stock_name', '未知')} ({stock.get('stock_code', 'N/A')})\n"
        
        return report


class AutoWatchAgent:
    """自动盯盘Agent"""
    
    def __init__(self, data_agent, watchlist: List[Tuple[str, str]], 
                 portfolio: List[Tuple[str, str, int, float]]):
        """
        data_agent: 数据Agent
        watchlist: 自选股列表 [(代码, 名称), ...]
        portfolio: 持仓列表 [(代码, 名称, 数量, 成本), ...]
        """
        self.data_agent = data_agent
        self.watchlist = watchlist
        self.portfolio = portfolio
        self.alerts = []
        self.last_prices = {}  # 记录上次价格
        
    def update_watchlist(self, watchlist: List[Tuple[str, str]]):
        """更新自选股列表"""
        self.watchlist = watchlist
        
    def update_portfolio(self, portfolio: List[Tuple[str, str, int, float]]):
        """更新持仓列表"""
        self.portfolio = portfolio
    
    def get_all_quotes(self) -> List[Dict]:
        """获取所有关注股票的实时行情"""
        all_codes = [code for code, _ in self.watchlist]
        all_codes.extend([code for code, _, _, _ in self.portfolio])
        
        # 去重
        all_codes = list(set(all_codes))
        
        if not all_codes:
            return []
        
        result = self.data_agent.process({
            "task": "get_batch_quotes",
            "params": {"stock_codes": all_codes}
        })
        
        return result.get("data", []) if result.get("success") else []
    
    def analyze_alerts(self, quotes: List[Dict]) -> List[Dict]:
        """分析告警"""
        alerts = []
        
        for quote in quotes:
            stock_code = quote.get("stock_code")
            stock_name = quote.get("stock_name")
            current_price = quote.get("current_price", 0)
            change_percent = quote.get("change_percent", 0)
            
            if not current_price:
                continue
            
            # 检查自选股异动
            last_price = self.last_prices.get(stock_code, {}).get("price")
            
            if last_price and last_price > 0:
                price_change = (current_price - last_price) / last_price * 100
                
                # 涨幅超过阈值
                if price_change > 5:
                    alerts.append({
                        "type": "异动提醒",
                        "level": "warning",
                        "stock_name": stock_name,
                        "stock_code": stock_code,
                        "message": f"🔥 {stock_name} 快速上涨 {price_change:.2f}%！",
                        "current_price": current_price,
                        "change": price_change
                    })
                elif price_change < -5:
                    alerts.append({
                        "type": "异动提醒",
                        "level": "warning",
                        "stock_name": stock_name,
                        "stock_code": stock_code,
                        "message": f"📉 {stock_name} 快速下跌 {price_change:.2f}%！",
                        "current_price": current_price,
                        "change": price_change
                    })
            
            # 检查持仓盈亏
            for code, name, quantity, cost in self.portfolio:
                if code == stock_code:
                    profit = (current_price - cost) * quantity
                    profit_percent = (current_price - cost) / cost * 100
                    
                    # 止损提醒
                    if profit_percent <= -7:
                        alerts.append({
                            "type": "止损提醒",
                            "level": "danger",
                            "stock_name": stock_name,
                            "stock_code": stock_code,
                            "message": f"⚠️ {stock_name} 亏损达到 {profit_percent:.1f}%，建议考虑止损！",
                            "current_price": current_price,
                            "profit": profit,
                            "profit_percent": profit_percent
                        })
                    # 止盈提醒
                    elif profit_percent >= 15:
                        alerts.append({
                            "type": "止盈提醒",
                            "level": "success",
                            "stock_name": stock_name,
                            "stock_code": stock_code,
                            "message": f"🎉 {stock_name} 盈利 {profit_percent:.1f}%，是否考虑止盈？",
                            "current_price": current_price,
                            "profit": profit,
                            "profit_percent": profit_percent
                        })
                    # 新高提醒
                    elif change_percent > 9:
                        alerts.append({
                            "type": "涨停提醒",
                            "level": "info",
                            "stock_name": stock_name,
                            "stock_code": stock_code,
                            "message": f"🚀 {stock_name} 接近涨停！",
                            "current_price": current_price,
                            "change_percent": change_percent
                        })
            
            # 更新最后价格
            self.last_prices[stock_code] = {
                "price": current_price,
                "time": datetime.now()
            }
        
        self.alerts = alerts
        return alerts
    
    def generate_watch_report(self) -> str:
        """生成盯盘报告"""
        quotes = self.get_all_quotes()
        alerts = self.analyze_alerts(quotes)
        
        report = f"""
👀 **自动盯盘报告**
{'='*40}
⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**持仓盈亏**
"""
        
        # 持仓分析
        for code, name, quantity, cost in self.portfolio:
            for quote in quotes:
                if quote.get("stock_code") == code:
                    current = quote.get("current_price", 0)
                    change = quote.get("change_percent", 0)
                    profit = (current - cost) * quantity
                    profit_pct = (current - cost) / cost * 100 if cost else 0
                    
                    status = "🟢盈利" if profit >= 0 else "🔴亏损"
                    report += f"- {name}: 现价{current} (今日{change:+.2f}%)\n"
                    report += f"  {status}: {profit:.0f}元 ({profit_pct:+.1f}%)\n"
                    break
        
        report += f"""
**自选股动态**
"""
        
        # 自选股动态
        watch_codes = [code for code, _ in self.watchlist]
        for quote in quotes:
            if quote.get("stock_code") in watch_codes:
                name = quote.get("stock_name", "未知")
                price = quote.get("current_price", 0)
                change = quote.get("change_percent", 0)
                report += f"- {name}: {price} ({change:+.2f}%)\n"
        
        if alerts:
            report += f"""
**⚠️ 告警提醒** ({len(alerts)}条)
"""
            for alert in alerts:
                report += f"{alert['message']}\n"
        else:
            report += "\n**暂无告警**\n"
        
        return report
    
    def run_once(self) -> Dict:
        """执行一次盯盘检查"""
        quotes = self.get_all_quotes()
        alerts = self.analyze_alerts(quotes)
        
        return {
            "success": True,
            "quotes": quotes,
            "alerts": alerts,
            "timestamp": datetime.now().isoformat()
        }


class Watcher:
    """盯盘运行器（后台持续监控）"""
    
    def __init__(self, watch_agent: AutoWatchAgent, interval: int = 300):
        """
        watch_agent: 盯盘Agent
        interval: 检查间隔（秒），默认5分钟
        """
        self.watch_agent = watch_agent
        self.interval = interval
        self.stop_event = Event()
        self.thread = None
        
    def start(self):
        """启动后台监控"""
        if self.thread and self.thread.is_alive():
            logger.warning("盯盘已经在运行中")
            return
        
        self.stop_event.clear()
        self.thread = Thread(target=self._run_loop)
        self.thread.daemon = True
        self.thread.start()
        logger.info(f"盯盘已启动，每 {self.interval} 秒检查一次")
    
    def stop(self):
        """停止监控"""
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("盯盘已停止")
    
    def _run_loop(self):
        """运行循环"""
        while not self.stop_event.is_set():
            try:
                result = self.watch_agent.run_once()
                
                if result.get("alerts"):
                    print("\n" + "="*50)
                    print("🔔 发现告警！")
                    print("="*50)
                    for alert in result["alerts"]:
                        print(alert.get("message", ""))
                    print("="*50 + "\n")
                
            except Exception as e:
                logger.error(f"盯盘检查失败: {e}")
            
            # 等待下一次检查
            self.stop_event.wait(self.interval)


# 便捷函数
def create_market_monitor(data_agent) -> MarketMonitorAgent:
    """创建大盘监控Agent"""
    return MarketMonitorAgent(data_agent)


def create_auto_watch(data_agent, watchlist: List[Tuple[str, str]], 
                     portfolio: List[Tuple[str, str, int, float]]) -> AutoWatchAgent:
    """创建自动盯盘Agent"""
    return AutoWatchAgent(data_agent, watchlist, portfolio)


if __name__ == "__main__":
    from agents.base import create_data_agent
    
    print("=" * 50)
    print("监控Agent测试")
    print("=" * 50)
    
    # 创建数据Agent
    data_agent = create_data_agent()
    
    # 测试大盘监控
    print("\n1. 测试大盘监控:")
    monitor = create_market_monitor(data_agent)
    status = monitor.get_market_status()
    print(f"   市场状态: {status['status']}")
    
    sentiment = monitor.analyze_market_sentiment()
    print(f"   市场情绪: {sentiment.get('sentiment_text', '未知')}")
    print(f"   平均涨跌: {sentiment.get('average_change', 0):+.2f}%")
    
    # 测试盯盘
    print("\n2. 测试自动盯盘:")
    watchlist = [("000001", "平安银行"), ("600519", "贵州茅台")]
    portfolio = [("000001", "平安银行", 1000, 12.50)]
    
    watcher = create_auto_watch(data_agent, watchlist, portfolio)
    report = watcher.generate_watch_report()
    print(report)
