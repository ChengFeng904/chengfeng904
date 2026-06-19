# -*- coding: utf-8 -*-
"""
报告生成Agent
生成每日投资研究报告
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class ReportAgent:
    """报告生成Agent"""
    
    def __init__(self, data_agent, analysis_agent, monitor_agent, watch_agent):
        """
        初始化报告Agent
        需要注入其他Agent
        """
        self.data_agent = data_agent
        self.analysis_agent = analysis_agent
        self.monitor_agent = monitor_agent
        self.watch_agent = watch_agent
    
    def generate_daily_report(self, watchlist: List[tuple], 
                              portfolio: List[tuple] = None) -> str:
        """
        生成每日投资报告
        """
        report_date = datetime.now().strftime("%Y年%m月%d日 %H:%M")
        
        report = f"""
# 📊 股票投研日报
{'='*50}
📅 日期: {report_date}

---

## 一、大盘概览

"""
        
        # 大盘分析
        try:
            sentiment = self.monitor_agent.analyze_market_sentiment()
            report += f"**市场情绪**: {sentiment.get('sentiment_text', '未知')}\n"
            report += f"**平均涨跌**: {sentiment.get('average_change', 0):+.2f}%\n\n"
            
            for detail in sentiment.get("details", []):
                report += f"- {detail}\n"
            
        except Exception as e:
            logger.error(f"获取大盘数据失败: {e}")
            report += "⚠️ 暂无大盘数据\n"
        
        report += "\n## 二、涨停板分析\n\n"
        
        try:
            sector = self.monitor_agent.get_sector_performance()
            report += f"**涨停股数量**: {sector.get('limit_up_count', 0)} 只\n\n"
            
            limit_stocks = sector.get("limit_up_stocks", [])
            if limit_stocks:
                report += "### 涨停股票\n"
                for stock in limit_stocks[:15]:
                    name = stock.get("stock_name", "未知")
                    code = stock.get("stock_code", "N/A")
                    change = stock.get("change_percent", 0)
                    report += f"- {name}({code}): {change:.2f}%\n"
            else:
                report += "暂无涨停股票\n"
                
        except Exception as e:
            logger.error(f"获取涨停数据失败: {e}")
            report += "⚠️ 暂无涨停数据\n"
        
        report += "\n## 三、持仓分析\n\n"
        
        # 持仓分析
        if portfolio:
            for code, name, quantity, cost in portfolio:
                try:
                    quote_result = self.data_agent.get_stock_realtime(code)
                    if quote_result.get("success"):
                        quote = quote_result["data"]
                        current = quote.get("current_price", 0)
                        change = quote.get("change_percent", 0)
                        
                        if cost > 0:
                            profit = (current - cost) * quantity
                            profit_pct = (current - cost) / cost * 100
                            
                            status = "🟢盈利" if profit >= 0 else "🔴亏损"
                            status_text = "建议持有" if profit >= 0 else "关注止损"
                            
                            report += f"### {name}({code})\n"
                            report += f"- 当前价格: {current:.2f} 元\n"
                            report += f"- 持仓成本: {cost:.2f} 元\n"
                            report += f"- 持仓数量: {quantity} 股\n"
                            report += f"- 今日涨跌: {change:+.2f}%\n"
                            report += f"- 持仓盈亏: {profit:+.2f} 元 ({profit_pct:+.1f}%) {status}\n"
                            report += f"- 操作建议: {status_text}\n\n"
                    
                except Exception as e:
                    logger.error(f"分析持仓失败 {code}: {e}")
                    report += f"### {name}({code})\n⚠️ 数据获取失败\n\n"
        else:
            report += "暂无持仓记录\n\n"
        
        report += "## 四、自选股动态\n\n"
        
        # 自选股分析
        if watchlist:
            watch_analysis = []
            for code, name in watchlist:
                try:
                    # 获取K线数据进行技术分析
                    analysis_result = self.analysis_agent.process({
                        "stock_code": code,
                        "period": "daily",
                        "count": 60
                    })
                    
                    if analysis_result.get("success"):
                        analysis = analysis_result["analysis"]
                        summary = analysis.get("summary", {})
                        quote = analysis.get("realtime", {})
                        
                        watch_analysis.append({
                            "code": code,
                            "name": name,
                            "price": quote.get("current_price"),
                            "change": quote.get("change_percent"),
                            "score": summary.get("score"),
                            "recommendation": summary.get("recommendation"),
                            "action": summary.get("action"),
                            "buy_signals": len(analysis.get("signals", {}).get("buy", [])),
                            "sell_signals": len(analysis.get("signals", {}).get("sell", []))
                        })
                        
                except Exception as e:
                    logger.error(f"分析自选股失败 {code}: {e}")
            
            # 按评分排序
            watch_analysis.sort(key=lambda x: x.get("score", 0), reverse=True)
            
            for item in watch_analysis:
                score = item.get("score", 0)
                score_emoji = "🟢" if score >= 30 else "🟡" if score >= -30 else "🔴"
                
                report += f"### {item['name']}({item['code']}) {score_emoji}\n"
                report += f"- 当前价格: {item.get('price', 'N/A')} 元\n"
                report += f"- 今日涨跌: {item.get('change', 0):+.2f}%\n"
                report += f"- 综合评分: {score} ({item.get('recommendation', '未知')})\n"
                report += f"- 买入信号: {item.get('buy_signals', 0)} 个\n"
                report += f"- 卖出信号: {item.get('sell_signals', 0)} 个\n"
                report += f"- 操作建议: {item.get('action', '观望')}\n\n"
        else:
            report += "暂无自选股\n\n"
        
        report += "## 五、选股推荐\n\n"
        
        # 选股推荐（涨停股中筛选）
        try:
            sector = self.monitor_agent.get_sector_performance()
            limit_stocks = sector.get("limit_up_stocks", [])[:5]
            
            if limit_stocks:
                report += "基于市场热点，推荐关注以下涨停股：\n\n"
                
                for i, stock in enumerate(limit_stocks, 1):
                    code = stock.get("stock_code")
                    name = stock.get("stock_name")
                    
                    report += f"### {i}. {name}({code})\n"
                    report += "- 理由: 今日涨停，市场热点\n"
                    report += "- 风险提示: 追高风险大，建议观望\n"
                    report += "- 建议: 可加入自选观察\n\n"
            else:
                report += "今日暂无明显热点板块\n"
                
        except Exception as e:
            logger.error(f"生成推荐失败: {e}")
            report += "暂无推荐\n\n"
        
        report += "## 六、风险提示\n\n"
        
        # 风险提示
        report += "⚠️ **重要提醒**\n\n"
        report += "1. 本报告仅供参考，不构成投资建议\n"
        report += "2. 股市有风险，投资需谨慎\n"
        report += "3. 请根据自身风险承受能力决策\n"
        report += "4. 建议止损设置在7%以内\n"
        report += "5. 避免追涨杀跌，保持理性\n\n"
        
        report += f"""
---

**免责声明**: 本报告由AI自动生成，数据来源于公开行情，仅供参考。投资者据此操作，风险自担。

生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
        
        return report
    
    def save_report(self, report: str, filename: str = None) -> str:
        """保存报告到文件"""
        from config.settings import REPORTS_DIR
        
        if filename is None:
            filename = f"daily_report_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
        
        filepath = REPORTS_DIR / filename
        
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(report)
            
            logger.info(f"报告已保存: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"保存报告失败: {e}")
            return None
    
    def generate_and_save(self, watchlist: List[tuple], 
                         portfolio: List[tuple] = None) -> Dict:
        """生成并保存报告"""
        report = self.generate_daily_report(watchlist, portfolio)
        filepath = self.save_report(report)
        
        return {
            "success": filepath is not None,
            "report": report,
            "filepath": filepath
        }


def create_report_agent(data_agent, analysis_agent, 
                       monitor_agent, watch_agent) -> ReportAgent:
    """创建报告Agent"""
    return ReportAgent(data_agent, analysis_agent, monitor_agent, watch_agent)


if __name__ == "__main__":
    from agents.base import create_data_agent, create_analysis_agent
    from agents.monitor import create_market_monitor, create_auto_watch
    
    print("=" * 50)
    print("报告生成测试")
    print("=" * 50)
    
    # 创建各Agent
    data_agent = create_data_agent()
    analysis_agent = create_analysis_agent()
    monitor = create_market_monitor(data_agent)
    
    watchlist = [("000001", "平安银行"), ("600519", "贵州茅台")]
    portfolio = [("000001", "平安银行", 1000, 12.50)]
    
    watch_agent = create_auto_watch(data_agent, watchlist, portfolio)
    
    # 生成报告
    report_agent = create_report_agent(data_agent, analysis_agent, monitor, watch_agent)
    result = report_agent.generate_and_save(watchlist, portfolio)
    
    if result["success"]:
        print(f"\n✅ 报告已保存: {result['filepath']}")
        print("\n" + "="*50)
        print("报告预览（前100行）:")
        print("="*50)
        lines = result["report"].split("\n")[:100]
        print("\n".join(lines))
