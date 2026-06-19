# -*- coding: utf-8 -*-
"""
股票投研系统主程序
适合小白使用，提供交互式菜单
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import argparse
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 导入配置
from config.settings import (
    WATCH_LIST, PORTFOLIO, MARKET_INDICES,
    SELECTION_STRATEGIES, ALERT_THRESHOLDS,
    SYSTEM_CONFIG
)

# 导入Agent
from agents import (
    create_data_agent,
    create_analysis_agent,
    create_market_monitor,
    create_auto_watch,
    create_report_agent,
)

# 导入编排器
from core import create_orchestrator


class StockResearchApp:
    """股票投研系统主应用"""
    
    def __init__(self):
        self.orchestrator = None
        self.data_agent = None
        self.analysis_agent = None
        self.monitor_agent = None
        self.watch_agent = None
        self.report_agent = None
        
    def initialize(self):
        """初始化系统"""
        print("\n" + "="*50)
        print("🚀 股票投研系统初始化中...")
        print("="*50)
        
        # 创建Agent
        self.data_agent = create_data_agent()
        self.analysis_agent = create_analysis_agent()
        self.monitor_agent = create_market_monitor(self.data_agent)
        self.watch_agent = create_auto_watch(
            self.data_agent, 
            WATCH_LIST, 
            PORTFOLIO
        )
        self.report_agent = create_report_agent(
            self.data_agent,
            self.analysis_agent,
            self.monitor_agent,
            self.watch_agent
        )
        
        # 创建编排器
        self.orchestrator = create_orchestrator()
        self.orchestrator.setup(
            self.data_agent,
            self.analysis_agent,
            self.monitor_agent,
            self.watch_agent,
            self.report_agent
        )
        self.orchestrator.set_watchlist(WATCH_LIST)
        self.orchestrator.set_portfolio(PORTFOLIO)
        
        print("✅ 初始化完成！")
        
    def show_menu(self):
        """显示菜单"""
        print("\n" + "="*50)
        print("📈 股票投研系统 - 主菜单")
        print("="*50)
        print("1. 📊 大盘监控 - 查看市场情绪和指数")
        print("2. 🔍 股票分析 - 分析单只股票")
        print("3. 📋 自选股 - 查看自选股动态")
        print("4. 💼 持仓分析 - 查看持仓盈亏")
        print("5. 🔔 盯盘检查 - 检查告警信息")
        print("6. 📝 生成报告 - 生成每日报告")
        print("7. 💡 选股推荐 - 根据策略选股")
        print("8. ⚙️  设置 - 修改自选股/持仓")
        print("0. 🚪 退出系统")
        print("="*50)
    
    def option_market(self):
        """大盘监控"""
        print("\n" + "-"*40)
        print("📊 大盘监控")
        print("-"*40)
        
        sentiment = self.monitor_agent.analyze_market_sentiment()
        
        print(f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"市场情绪: {sentiment.get('sentiment_text', '未知')}")
        print(f"平均涨跌: {sentiment.get('average_change', 0):+.2f}%\n")
        
        print("主要指数:")
        for detail in sentiment.get("details", []):
            print(f"  {detail}")
        
        print("\n板块动态:")
        sector = self.monitor_agent.get_sector_performance()
        print(f"  涨停股数量: {sector.get('limit_up_count', 0)} 只")
        
    def option_stock_analysis(self):
        """股票分析"""
        print("\n" + "-"*40)
        print("🔍 股票分析")
        print("-"*40)
        
        stock_code = input("请输入股票代码（如 000001）: ").strip()
        if not stock_code:
            print("⚠️ 股票代码不能为空")
            return
        
        print(f"\n正在分析 {stock_code}...\n")
        
        result = self.orchestrator.stock_analysis_workflow(stock_code)
        
        # 显示行情
        if result["quote"].get("success"):
            quote = result["quote"]["data"]
            print(f"📈 {quote.get('stock_name', stock_code)}({stock_code})")
            print(f"   当前价: {quote.get('current_price')} 元")
            print(f"   涨跌幅: {quote.get('change_percent'):+.2f}%\n")
        
        # 显示分析结果
        if result["analysis"].get("success"):
            analysis = result["analysis"]["analysis"]
            summary = analysis.get("summary", {})
            
            print("【技术分析】")
            print(f"   趋势: {analysis.get('trend', {}).get('trend', '未知')}")
            print(f"   MA5/MA10/MA20: {analysis.get('trend', {}).get('ma5')}/{analysis.get('trend', {}).get('ma10')}/{analysis.get('trend', {}).get('ma20')}")
            
            ind = analysis.get("indicators", {})
            print(f"   RSI(14): {ind.get('rsi', {}).get('rsi14')}")
            print(f"   MACD柱: {ind.get('macd', {}).get('histogram')}")
            
            print("\n【信号提示】")
            for sig in analysis.get("signals", {}).get("buy", [])[:3]:
                print(f"   🟢 买入: {sig.get('type')} - {sig.get('description', '')[:30]}...")
            
            for sig in analysis.get("signals", {}).get("sell", [])[:3]:
                print(f"   🔴 卖出: {sig.get('type')} - {sig.get('description', '')[:30]}...")
            
            print(f"\n【综合评分】{summary.get('score', 0)} ({summary.get('recommendation', '未知')})")
            print(f"【操作建议】{summary.get('action', '观望')}")
    
    def option_watchlist(self):
        """自选股"""
        print("\n" + "-"*40)
        print("📋 自选股动态")
        print("-"*40)
        
        if not WATCH_LIST:
            print("⚠️ 暂无自选股，请在设置中添加")
            return
        
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        results = self.watch_agent.get_all_quotes()
        
        for quote in results:
            name = quote.get("stock_name", "未知")
            code = quote.get("stock_code", "N/A")
            price = quote.get("current_price", 0)
            change = quote.get("change_percent", 0)
            
            emoji = "🔴" if change > 0 else "🟢" if change < 0 else "⚪"
            print(f"{emoji} {name}({code}): {price} ({change:+.2f}%)")
    
    def option_portfolio(self):
        """持仓分析"""
        print("\n" + "-"*40)
        print("💼 持仓分析")
        print("-"*40)
        
        if not PORTFOLIO:
            print("⚠️ 暂无持仓，请在设置中添加")
            return
        
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        results = self.watch_agent.get_all_quotes()
        
        total_cost = 0
        total_value = 0
        
        for code, name, quantity, cost in PORTFOLIO:
            for quote in results:
                if quote.get("stock_code") == code:
                    current = quote.get("current_price", 0)
                    change = quote.get("change_percent", 0)
                    
                    cost_total = cost * quantity
                    value_total = current * quantity
                    profit = value_total - cost_total
                    profit_pct = (current - cost) / cost * 100 if cost else 0
                    
                    total_cost += cost_total
                    total_value += value_total
                    
                    status = "🟢" if profit >= 0 else "🔴"
                    print(f"{status} {name}({code})")
                    print(f"   持仓: {quantity} 股, 成本: {cost:.2f}元")
                    print(f"   现价: {current:.2f}元 (今日 {change:+.2f}%)")
                    print(f"   盈亏: {profit:+.2f}元 ({profit_pct:+.1f}%)")
                    print()
                    break
        
        total_profit = total_value - total_cost
        total_profit_pct = (total_value - total_cost) / total_cost * 100 if total_cost else 0
        
        print("-"*40)
        print(f"📊 总资产: {total_value:.2f} 元")
        print(f"📉 总成本: {total_cost:.2f} 元")
        print(f"{'🟢' if total_profit >= 0 else '🔴'} 总盈亏: {total_profit:+.2f} 元 ({total_profit_pct:+.1f}%)")
    
    def option_watch_alert(self):
        """盯盘告警"""
        print("\n" + "-"*40)
        print("🔔 盯盘告警检查")
        print("-"*40)
        
        result = self.watch_agent.run_once()
        
        alerts = result.get("alerts", [])
        
        if alerts:
            print(f"\n发现 {len(alerts)} 条告警:\n")
            for alert in alerts:
                level_emoji = {
                    "danger": "🔴",
                    "warning": "🟡",
                    "success": "🟢",
                    "info": "🔵"
                }.get(alert.get("level", "info"), "⚪")
                
                print(f"{level_emoji} {alert.get('type')}")
                print(f"   {alert.get('message', '')}")
                print()
        else:
            print("\n✅ 暂无告警，一切正常")
        
        print(f"\n检查时间: {result.get('timestamp', '')}")
    
    def option_generate_report(self):
        """生成报告"""
        print("\n" + "-"*40)
        print("📝 生成每日报告")
        print("-"*40)
        
        print("\n正在生成报告，请稍候...\n")
        
        result = self.report_agent.generate_and_save(WATCH_LIST, PORTFOLIO)
        
        if result.get("success"):
            print(f"✅ 报告已生成并保存!")
            print(f"📁 保存路径: {result.get('filepath')}")
            
            # 显示报告摘要
            report = result.get("report", "")
            lines = report.split("\n")[:50]
            print("\n" + "-"*40)
            print("报告预览:")
            print("-"*40)
            print("\n".join(lines))
            print("\n... (更多内容请查看完整报告)")
        else:
            print("❌ 报告生成失败")
    
    def option_selection(self):
        """选股推荐"""
        print("\n" + "-"*40)
        print("💡 选股推荐")
        print("-"*40)
        
        print("\n请选择选股策略:")
        strategies = list(SELECTION_STRATEGIES.items())
        
        for i, (key, config) in enumerate(strategies, 1):
            print(f"{i}. {config['name']} - {config['description']}")
        
        choice = input("\n请输入选项(1-4): ").strip()
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(strategies):
                strategy_key = strategies[idx][0]
                
                print(f"\n正在执行 {strategies[idx][1]['name']}...\n")
                
                result = self.orchestrator.selection_workflow(strategy_key)
                
                if result.get("selection", {}).get("success"):
                    stocks = result["selection"].get("results", [])
                    
                    print(f"共筛选出 {len(stocks)} 只股票:\n")
                    
                    for i, stock in enumerate(stocks[:10], 1):
                        name = stock.get("stock_name", "未知")
                        code = stock.get("stock_code", "N/A")
                        score = stock.get("score", 0)
                        price = stock.get("current_price", 0)
                        change = stock.get("change_percent", 0)
                        
                        emoji = "🟢" if score > 0 else "🔴"
                        print(f"{emoji} {i}. {name}({code})")
                        print(f"   价格: {price}元, 评分: {score}")
                        print(f"   今日: {change:+.2f}%")
                        print(f"   理由: {', '.join(stock.get('reasons', [])[:2])}")
                        print()
                else:
                    print("❌ 选股失败")
            else:
                print("⚠️ 无效选项")
                
        except ValueError:
            print("⚠️ 请输入有效数字")
    
    def option_settings(self):
        """设置"""
        print("\n" + "-"*40)
        print("⚙️ 系统设置")
        print("-"*40)
        
        print("\n当前配置:")
        print(f"  自选股数量: {len(WATCH_LIST)}")
        print(f"  持仓数量: {len(PORTFOLIO)}")
        print(f"  盯盘间隔: {SYSTEM_CONFIG['check_interval']}秒")
        
        print("\n⚠️ 修改配置请编辑 config/settings.py 文件")
        print("  - 修改自选股: 编辑 WATCH_LIST")
        print("  - 修改持仓: 编辑 PORTFOLIO")
        print("  - 修改告警阈值: 编辑 ALERT_THRESHOLDS")
    
    def run(self):
        """运行应用"""
        self.initialize()
        
        while True:
            self.show_menu()
            
            choice = input("\n请输入选项(0-8): ").strip()
            
            if choice == "1":
                self.option_market()
            elif choice == "2":
                self.option_stock_analysis()
            elif choice == "3":
                self.option_watchlist()
            elif choice == "4":
                self.option_portfolio()
            elif choice == "5":
                self.option_watch_alert()
            elif choice == "6":
                self.option_generate_report()
            elif choice == "7":
                self.option_selection()
            elif choice == "8":
                self.option_settings()
            elif choice == "0":
                print("\n感谢使用，再见！👋\n")
                break
            else:
                print("\n⚠️ 无效选项，请重新输入")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="股票投研系统")
    parser.add_argument("--mode", "-m", choices=["interactive", "report", "watch"],
                       default="interactive", help="运行模式")
    parser.add_argument("--stock", "-s", help="股票代码(单次分析模式)")
    parser.add_argument("--report", "-r", action="store_true", help="生成报告")
    
    args = parser.parse_args()
    
    if args.mode == "interactive":
        app = StockResearchApp()
        app.run()
    
    elif args.mode == "report":
        # 仅生成报告
        app = StockResearchApp()
        app.initialize()
        result = app.report_agent.generate_and_save(WATCH_LIST, PORTFOLIO)
        
        if result.get("success"):
            print(f"✅ 报告已保存: {result.get('filepath')}")
        else:
            print("❌ 报告生成失败")
    
    elif args.mode == "watch":
        # 仅运行盯盘
        app = StockResearchApp()
        app.initialize()
        
        print("\n🔔 盯盘模式，按 Ctrl+C 退出\n")
        
        try:
            while True:
                app.option_watch_alert()
                import time
                time.sleep(SYSTEM_CONFIG["check_interval"])
        except KeyboardInterrupt:
            print("\n\n盯盘已停止")


if __name__ == "__main__":
    main()
