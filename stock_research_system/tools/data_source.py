# -*- coding: utf-8 -*-
"""
数据源工具模块
负责从各个平台获取A股数据
"""

import requests
import pandas as pd
import json
from datetime import datetime, timedelta
import time
import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class EastMoneyDataSource:
    """东方财富数据源"""
    
    BASE_URL = "https://push2his.eastmoney.com"
    
    @staticmethod
    def get_realtime_quote(stock_code: str) -> Optional[Dict]:
        """
        获取个股实时行情
        stock_code: 股票代码，如 "000001" 或 "600519"
        """
        try:
            url = f"https://push2.eastmoney.com/api/qt/stock/get"
            params = {
                "secid": EastMoneyDataSource._get_secid(stock_code),
                "fields": "f43,f44,f45,f46,f47,f48,f57,f58,f60,f107,f169,f170",
                "ut": "fa5fd1943c7b386f172d6893dbbd3d2c",
            }
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://quote.eastmoney.com/"
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            data = response.json()
            
            if data.get("data"):
                return EastMoneyDataSource._parse_realtime(data["data"])
            return None
            
        except Exception as e:
            logger.error(f"获取实时行情失败 {stock_code}: {e}")
            return None
    
    @staticmethod
    def _get_secid(stock_code: str) -> str:
        """判断市场并生成secid（支持A股、ETF、LOF）"""
        code = stock_code.strip().lower()
        if code.startswith("sh") or code.startswith("sz"):
            market = "1" if code.startswith("sh") else "0"
            return f"{market}.{stock_code[2:]}"
        if stock_code.startswith(("6", "5", "9")):
            return f"1.{stock_code}"
        else:
            return f"0.{stock_code}"
    
    @staticmethod
    def _safe_div(value, divisor: int):
        """安全除法：值为 None 时返回 0"""
        if value is None:
            return 0
        try:
            return value / divisor
        except (TypeError, ZeroDivisionError):
            return 0

    @staticmethod
    def _parse_realtime(data: Dict) -> Dict:
        """解析实时行情数据"""
        return {
            "stock_code": data.get("f57"),
            "stock_name": data.get("f58"),
            "current_price": EastMoneyDataSource._safe_div(data.get("f43"), 100),
            "change_percent": EastMoneyDataSource._safe_div(data.get("f170"), 100),
            "change_amount": EastMoneyDataSource._safe_div(data.get("f169"), 100),
            "volume": data.get("f47", 0) or 0,
            "amount": data.get("f48", 0) or 0,
            "high": EastMoneyDataSource._safe_div(data.get("f44"), 100),
            "low": EastMoneyDataSource._safe_div(data.get("f45"), 100),
            "open": EastMoneyDataSource._safe_div(data.get("f46"), 100),
            "prev_close": EastMoneyDataSource._safe_div(data.get("f60"), 100),
            "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
    
    @staticmethod
    def get_kline_data(stock_code: str, period: str = "daily", 
                       count: int = 100) -> Optional[List[Dict]]:
        """
        获取K线数据
        period: daily/weekly/monthly 或 60分钟等
        count: 获取数据条数
        """
        try:
            url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
            params = {
                "secid": EastMoneyDataSource._get_secid(stock_code),
                "fields1": "f1,f2,f3,f4,f5,f6",
                "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
                "klt": EastMoneyDataSource._get_klt(period),
                "fqt": 1,
                "end": "20500101",
                "lmt": count
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if data.get("data") and data["data"].get("klines"):
                klines = data["data"]["klines"]
                result = []
                for kline in klines:
                    parts = kline.split(",")
                    result.append({
                        "date": parts[0],
                        "open": float(parts[1]),
                        "close": float(parts[2]),
                        "high": float(parts[3]),
                        "low": float(parts[4]),
                        "volume": int(parts[5]),
                        "amount": float(parts[6]) if len(parts) > 6 else 0,
                    })
                return result
            return None
            
        except Exception as e:
            logger.error(f"获取K线数据失败 {stock_code}: {e}")
            return None
    
    @staticmethod
    def _get_klt(period: str) -> int:
        """转换周期参数"""
        mapping = {
            "daily": 101,
            "weekly": 102,
            "monthly": 103,
            "60min": 60,
            "30min": 30,
            "15min": 15,
            "5min": 5
        }
        return mapping.get(period, 101)
    
    @staticmethod
    def get_stock_basic_info(stock_code: str) -> Optional[Dict]:
        """获取股票基本信息"""
        try:
            url = "https://push2.eastmoney.com/api/qt/stock/get"
            params = {
                "secid": EastMoneyDataSource._get_secid(stock_code),
                "fields": "f57,f58,f107,f116,f117,f162,f163,f164,f167,f168,f170,f171",
                "ut": "fa5fd1943c7b386f172d6893dbbd3d2c",
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if data.get("data"):
                d = data["data"]
                return {
                    "stock_code": d.get("f57"),
                    "stock_name": d.get("f58"),
                    "pe": d.get("f162"),           # 市盈率
                    "pb": d.get("f167"),           # 市净率
                    "total_market_cap": d.get("f116"),  # 总市值
                    "float_market_cap": d.get("f117"),   # 流通市值
                    "dividend": d.get("f171"),     # 分红
                    "roe": d.get("f168"),          # 净资产收益率
                }
            return None
            
        except Exception as e:
            logger.error(f"获取基本信息失败 {stock_code}: {e}")
            return None
    
    @staticmethod
    def get_market_index(index_code: str = "sh000001") -> Optional[Dict]:
        """获取大盘指数"""
        return EastMoneyDataSource.get_realtime_quote(index_code)
    
    @staticmethod
    def get_limit_up_stocks() -> List[Dict]:
        """获取涨停股票"""
        try:
            url = "http://push2.eastmoney.com/api/qt/clist/get"
            params = {
                "pn": 1,
                "pz": 100,
                "po": 1,
                "np": 1,
                "ut": "bd1d9ddb04089700cf9c27f6f7426281",
                "fltt": 2,
                "invt": 2,
                "fid": "f3",
                "fs": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23,m:0+t:81+s:2048",
                "fields": "f2,f3,f4,f8,f9,f12,f14",
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if data.get("data") and data["data"].get("diff"):
                return [
                    {
                        "stock_code": item.get("f12"),
                        "stock_name": item.get("f14"),
                        "current_price": item.get("f2"),
                        "change_percent": item.get("f3"),
                        "volume_ratio": item.get("f8"),
                    }
                    for item in data["data"]["diff"]
                ]
            return []
            
        except Exception as e:
            logger.error(f"获取涨停股票失败: {e}")
            return []
    
    @staticmethod
    def get_stock_news(stock_code: str = None, count: int = 10) -> List[Dict]:
        """获取股票新闻"""
        try:
            url = "https://np-anotice-stock.eastmoney.com/api/security/ann"
            params = {
                "sr": -1,
                "page_size": count,
                "page_index": 1,
                "ann_type": "ALL",
                "client_source": "web",
            }
            
            if stock_code:
                params["stock_list"] = stock_code
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if data.get("data"):
                return [
                    {
                        "title": item.get("title"),
                        "publish_time": item.get("notice_date"),
                        "summary": item.get("summary"),
                        "url": item.get("art_url"),
                    }
                    for item in data["data"]["list"]
                ]
            return []
            
        except Exception as e:
            logger.error(f"获取新闻失败: {e}")
            return []


class DataCollector:
    """数据收集器主类"""
    
    def __init__(self):
        self.eastmoney = EastMoneyDataSource()
    
    def collect_realtime(self, stock_codes: List[str]) -> List[Dict]:
        """批量收集实时行情"""
        results = []
        for code in stock_codes:
            data = self.eastmoney.get_realtime_quote(code)
            if data:
                results.append(data)
            time.sleep(0.2)  # 避免请求过快
        return results
    
    def collect_klines(self, stock_code: str, period: str = "daily", 
                       count: int = 100) -> Optional[List[Dict]]:
        """收集K线数据"""
        return self.eastmoney.get_kline_data(stock_code, period, count)
    
    def collect_market_overview(self) -> Dict:
        """收集市场概览"""
        indices = ["sh000001", "sz399001", "cy399006", "sh000300"]
        overview = {}
        for idx in indices:
            data = self.eastmoney.get_market_index(idx)
            if data:
                overview[idx] = data
        return overview


# 便捷函数
def get_quote(stock_code: str) -> Optional[Dict]:
    """获取单只股票行情"""
    return EastMoneyDataSource.get_realtime_quote(stock_code)


def get_kline(stock_code: str, period: str = "daily", count: int = 100) -> Optional[List[Dict]]:
    """获取K线数据"""
    return EastMoneyDataSource.get_kline_data(stock_code, period, count)


def get_batch_quotes(stock_codes: List[str]) -> List[Dict]:
    """批量获取股票行情"""
    collector = DataCollector()
    return collector.collect_realtime(stock_codes)


def get_market_index() -> Dict:
    """获取大盘指数"""
    collector = DataCollector()
    return collector.collect_market_overview()


def get_limit_up() -> List[Dict]:
    """获取涨停股"""
    return EastMoneyDataSource.get_limit_up_stocks()


if __name__ == "__main__":
    # 测试
    print("=" * 50)
    print("数据源测试")
    print("=" * 50)
    
    # 测试获取单只股票
    print("\n1. 测试获取贵州茅台行情:")
    quote = get_quote("600519")
    if quote:
        print(f"   {quote['stock_name']}({quote['stock_code']})")
        print(f"   当前价: {quote['current_price']} 元")
        print(f"   涨跌幅: {quote['change_percent']:.2f}%")
    
    # 测试获取K线
    print("\n2. 测试获取K线数据(最近5天):")
    klines = get_kline("000001", "daily", 5)
    if klines:
        for k in klines[-3:]:
            print(f"   {k['date']}: 收 {k['close']} 开 {k['open']} 高 {k['high']} 低 {k['low']}")
    
    # 测试大盘
    print("\n3. 测试获取大盘指数:")
    indices = get_market_index()
    for code, data in indices.items():
        print(f"   {data['stock_name']}: {data['current_price']} ({data['change_percent']:.2f}%)")
