# -*- coding: utf-8 -*-
"""
技术指标计算模块
包含常用的股票技术指标计算
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple


def calculate_ma(prices: List[float], period: int) -> List[float]:
    """
    计算移动平均线 (MA)
    prices: 价格列表
    period: 周期
    """
    if len(prices) < period:
        return [np.nan] * len(prices)
    
    result = []
    for i in range(len(prices)):
        if i < period - 1:
            result.append(np.nan)
        else:
            result.append(np.mean(prices[i - period + 1:i + 1]))
    return result


def calculate_ema(prices: List[float], period: int) -> List[float]:
    """
    计算指数移动平均线 (EMA)
    """
    if len(prices) < period:
        return [np.nan] * len(prices)
    
    df = pd.Series(prices)
    ema = df.ewm(span=period, adjust=False).mean()
    return ema.tolist()


def calculate_macd(prices: List[float], fast: int = 12, 
                   slow: int = 26, signal: int = 9) -> Dict[str, List[float]]:
    """
    计算MACD指标
    返回: DIF, DEA, MACD柱
    """
    if len(prices) < slow:
        return {"dif": [np.nan] * len(prices), 
                "dea": [np.nan] * len(prices), 
                "histogram": [np.nan] * len(prices)}
    
    df = pd.Series(prices)
    ema_fast = df.ewm(span=fast, adjust=False).mean()
    ema_slow = df.ewm(span=slow, adjust=False).mean()
    
    dif = (ema_fast - ema_slow).tolist()
    dea = pd.Series(dif).ewm(span=signal, adjust=False).mean().tolist()
    macd_hist = [(dif[i] - dea[i]) * 2 for i in range(len(dif))]
    
    return {"dif": dif, "dea": dea, "histogram": macd_hist}


def calculate_kdj(highs: List[float], lows: List[float], 
                 closes: List[float], period: int = 9,
                 k_period: int = 3, d_period: int = 3) -> Dict[str, List[float]]:
    """
    计算KDJ随机指标
    """
    if len(closes) < period:
        return {"k": [np.nan] * len(closes), 
                "d": [np.nan] * len(closes), 
                "j": [np.nan] * len(closes)}
    
    k_values = []
    d_values = []
    j_values = []
    
    for i in range(len(closes)):
        if i < period - 1:
            k_values.append(50)
            d_values.append(50)
            j_values.append(50)
        else:
            low_min = min(lows[i - period + 1:i + 1])
            high_max = max(highs[i - period + 1:i + 1])
            
            if high_max == low_min:
                rsv = 50
            else:
                rsv = (closes[i] - low_min) / (high_max - low_min) * 100
            
            # K值
            if len(k_values) == 0:
                k = rsv
            else:
                k = (k_values[-1] * (k_period - 1) + rsv) / k_period
            
            # D值
            if len(d_values) == 0:
                d = k
            else:
                d = (d_values[-1] * (d_period - 1) + k) / d_period
            
            # J值
            j = 3 * k - 2 * d
            
            k_values.append(k)
            d_values.append(d)
            j_values.append(j)
    
    return {"k": k_values, "d": d_values, "j": j_values}


def calculate_rsi(prices: List[float], period: int = 14) -> List[float]:
    """
    计算RSI相对强弱指标
    """
    if len(prices) < period + 1:
        return [np.nan] * len(prices)
    
    deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    
    result = []
    for i in range(len(deltas)):
        if i < period - 1:
            result.append(np.nan)
        else:
            gains = [max(0, d) for d in deltas[i - period + 1:i + 1]]
            losses = [abs(min(0, d)) for d in deltas[i - period + 1:i + 1]]
            
            avg_gain = sum(gains) / period
            avg_loss = sum(losses) / period
            
            if avg_loss == 0:
                result.append(100)
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
                result.append(rsi)
    
    return result


def calculate_boll(closes: List[float], period: int = 20, 
                   std_dev: int = 2) -> Dict[str, List[float]]:
    """
    计算布林带指标
    返回: 上轨, 中轨, 下轨
    """
    if len(closes) < period:
        n = len(closes)
        return {"upper": [float("nan")] * n,
                "middle": [float("nan")] * n,
                "lower": [float("nan")] * n}

    df = pd.Series(closes)
    middle_series = df.rolling(window=period).mean()
    std_series = df.rolling(window=period).std()

    upper = (middle_series + std_dev * std_series).tolist()
    middle = middle_series.tolist()
    lower = (middle_series - std_dev * std_series).tolist()

    return {"upper": upper, "middle": middle, "lower": lower}


def calculate_vol_ma(volumes: List[int], periods: List[int] = [5, 10, 20]) -> Dict[str, List[float]]:
    """
    计算成交量均线
    """
    result = {}
    for period in periods:
        if len(volumes) >= period:
            ma = calculate_ma([float(v) for v in volumes], period)
            result[f"ma{period}"] = ma
        else:
            result[f"ma{period}"] = [np.nan] * len(volumes)
    return result


class TechnicalAnalyzer:
    """技术分析主类"""
    
    def __init__(self, kline_data: List[Dict]):
        """
        kline_data: K线数据列表，格式为 [{date, open, close, high, low, volume}, ...]
        """
        self.data = kline_data
        self.closes = [k["close"] for k in kline_data]
        self.opens = [k["open"] for k in kline_data]
        self.highs = [k["high"] for k in kline_data]
        self.lows = [k["low"] for k in kline_data]
        self.volumes = [k["volume"] for k in kline_data]
        
    def analyze(self) -> Dict:
        """执行完整技术分析"""
        result = {
            "basic_info": self._get_basic_info(),
            "trend": self._analyze_trend(),
            "indicators": self._calculate_indicators(),
            "signals": self._generate_signals(),
            "summary": {}
        }
        
        result["summary"] = self._generate_summary(result)
        return result
    
    def _get_basic_info(self) -> Dict:
        """获取基本信息"""
        if not self.data:
            return {}

        latest = self.data[-1]
        prev_close = self.data[-2]["close"] if len(self.data) > 1 else latest["close"]

        change_percent = 0.0
        if prev_close and prev_close != 0:
            change_percent = (latest["close"] - prev_close) / prev_close * 100

        return {
            "latest_price": latest["close"],
            "change": latest["close"] - prev_close,
            "change_percent": change_percent,
            "latest_date": latest.get("date"),
            "period_high": max(self.highs[-60:]) if len(self.highs) >= 60 else max(self.highs) if self.highs else 0,
            "period_low": min(self.lows[-60:]) if len(self.lows) >= 60 else min(self.lows) if self.lows else 0,
            "avg_volume_20": float(np.mean(self.volumes[-20:])) if len(self.volumes) >= 20 else (float(np.mean(self.volumes)) if self.volumes else 0),
        }
    
    def _analyze_trend(self) -> Dict:
        """分析趋势"""
        ma5 = calculate_ma(self.closes, 5)
        ma10 = calculate_ma(self.closes, 10)
        ma20 = calculate_ma(self.closes, 20)
        ma60 = calculate_ma(self.closes, 60)
        
        latest_ma5 = ma5[-1] if ma5 and not np.isnan(ma5[-1]) else 0
        latest_ma10 = ma10[-1] if ma10 and not np.isnan(ma10[-1]) else 0
        latest_ma20 = ma20[-1] if ma20 and not np.isnan(ma20[-1]) else 0
        latest_ma60 = ma60[-1] if ma60 and not np.isnan(ma60[-1]) else 0
        
        # 判断均线多头/空头
        current_price = self.closes[-1]
        
        if current_price > latest_ma5 > latest_ma10 > latest_ma20:
            trend = "多头排列（强势上涨）"
        elif current_price < latest_ma5 < latest_ma10 < latest_ma20:
            trend = "空头排列（弱势下跌）"
        elif latest_ma5 > latest_ma10 > latest_ma20:
            trend = "上升趋势"
        elif latest_ma5 < latest_ma10 < latest_ma20:
            trend = "下降趋势"
        else:
            trend = "震荡整理"
        
        return {
            "trend": trend,
            "ma5": round(latest_ma5, 2),
            "ma10": round(latest_ma10, 2),
            "ma20": round(latest_ma20, 2),
            "ma60": round(latest_ma60, 2) if latest_ma60 else None,
        }
    
    def _calculate_indicators(self) -> Dict:
        """计算各项技术指标"""
        macd = calculate_macd(self.closes)
        kdj = calculate_kdj(self.highs, self.lows, self.closes)
        rsi6 = calculate_rsi(self.closes, 6)
        rsi12 = calculate_rsi(self.closes, 12)
        rsi14 = calculate_rsi(self.closes, 14)
        rsi24 = calculate_rsi(self.closes, 24)
        boll = calculate_boll(self.closes)

        # 最新值
        def get_latest(values):
            if values and len(values) > 0:
                val = values[-1]
                if val is None:
                    return None
                try:
                    if np.isnan(val):
                        return None
                except TypeError:
                    return None
                return round(float(val), 4)
            return None

        return {
            "macd": {
                "dif": get_latest(macd["dif"]),
                "dea": get_latest(macd["dea"]),
                "histogram": get_latest(macd["histogram"]),
            },
            "kdj": {
                "k": get_latest(kdj["k"]),
                "d": get_latest(kdj["d"]),
                "j": get_latest(kdj["j"]),
            },
            "rsi": {
                "rsi6": get_latest(rsi6),
                "rsi12": get_latest(rsi12),
                "rsi14": get_latest(rsi14),
                "rsi24": get_latest(rsi24),
            },
            "boll": {
                "upper": get_latest(boll["upper"]),
                "middle": get_latest(boll["middle"]),
                "lower": get_latest(boll["lower"]),
            },
        }
    
    def _generate_signals(self) -> Dict:
        """生成买卖点信号"""
        signals = {"buy": [], "sell": [], "neutral": []}

        def _is_num(v):
            if v is None:
                return False
            try:
                return not np.isnan(v)
            except (TypeError, ValueError):
                return False

        # 均线信号
        ma5 = calculate_ma(self.closes, 5)
        ma10 = calculate_ma(self.closes, 10)
        ma20 = calculate_ma(self.closes, 20)

        if len(ma5) >= 2 and len(ma10) >= 2:
            v5_1, v5_0 = ma5[-2], ma5[-1]
            v10_1, v10_0 = ma10[-2], ma10[-1]
            if all(_is_num(v) for v in (v5_1, v5_0, v10_1, v10_0)):
                # 金叉（MA5上穿MA10）
                if v5_1 < v10_1 and v5_0 > v10_0:
                    signals["buy"].append({
                        "type": "MA金叉",
                        "description": f"MA5({v5_0:.2f})上穿MA10({v10_0:.2f})，短期看涨信号",
                        "confidence": "中"
                    })
                # 死叉（MA5下穿MA10）
                if v5_1 > v10_1 and v5_0 < v10_0:
                    signals["sell"].append({
                        "type": "MA死叉",
                        "description": f"MA5({v5_0:.2f})下穿MA10({v10_0:.2f})，短期看跌信号",
                        "confidence": "中"
                    })

        # MACD信号
        macd = calculate_macd(self.closes)
        hist = macd.get("histogram", [])
        if len(hist) >= 2 and _is_num(hist[-2]) and _is_num(hist[-1]):
            # MACD金叉
            if hist[-2] < 0 and hist[-1] > 0:
                signals["buy"].append({
                    "type": "MACD金叉",
                    "description": "MACD柱由负转正，快线金叉慢线，看涨信号",
                    "confidence": "高"
                })
            # MACD死叉
            elif hist[-2] > 0 and hist[-1] < 0:
                signals["sell"].append({
                    "type": "MACD死叉",
                    "description": "MACD柱由正转负，快线死叉慢线，看跌信号",
                    "confidence": "高"
                })

        # RSI信号
        rsi14 = calculate_rsi(self.closes, 14)
        if rsi14 and len(rsi14) > 0 and _is_num(rsi14[-1]):
            rsi_val = rsi14[-1]
            if rsi_val < 30:
                signals["buy"].append({
                    "type": "RSI超卖",
                    "description": f"RSI14={rsi_val:.1f}，处于超卖区域，可能反弹",
                    "confidence": "中"
                })
            elif rsi_val > 70:
                signals["sell"].append({
                    "type": "RSI超买",
                    "description": f"RSI14={rsi_val:.1f}，处于超买区域，注意风险",
                    "confidence": "中"
                })

        # 布林带信号
        boll = calculate_boll(self.closes)
        current_price = self.closes[-1]
        if len(boll.get("lower", [])) > 0 and _is_num(boll["lower"][-1]):
            if current_price < boll["lower"][-1]:
                signals["buy"].append({
                    "type": "布林下轨支撑",
                    "description": "价格触及布林下轨，可能获得支撑",
                    "confidence": "中"
                })
        if len(boll.get("upper", [])) > 0 and _is_num(boll["upper"][-1]):
            if current_price > boll["upper"][-1]:
                signals["sell"].append({
                    "type": "布林上轨压力",
                    "description": "价格触及布林上轨，面临压力",
                    "confidence": "中"
                })

        # KDJ信号
        kdj = calculate_kdj(self.highs, self.lows, self.closes)
        k = kdj.get("k", [])
        d = kdj.get("d", [])
        if len(k) >= 2 and len(d) >= 2:
            v = [k[-2], k[-1], d[-2], d[-1]]
            if all(_is_num(x) for x in v):
                if v[0] < v[2] and v[1] > v[3]:
                    signals["buy"].append({
                        "type": "KDJ金叉",
                        "description": f"K({v[1]:.1f})上穿D({v[3]:.1f})",
                        "confidence": "中"
                    })
                elif v[0] > v[2] and v[1] < v[3]:
                    signals["sell"].append({
                        "type": "KDJ死叉",
                        "description": f"K({v[1]:.1f})下穿D({v[3]:.1f})",
                        "confidence": "中"
                    })

        # 如果没有信号
        if not signals["buy"] and not signals["sell"]:
            signals["neutral"].append({
                "type": "暂无明显信号",
                "description": "当前技术指标暂无明确买卖信号，建议观望",
                "confidence": "-"
            })

        return signals
    
    def _generate_summary(self, analysis: Dict) -> Dict:
        """生成分析总结"""
        buy_count = len(analysis["signals"]["buy"])
        sell_count = len(analysis["signals"]["sell"])
        
        # 综合评分（-100到100）
        score = 0
        
        # 趋势权重
        trend = analysis["trend"]["trend"]
        if "多头" in trend:
            score += 30
        elif "空头" in trend:
            score -= 30
        elif "上升" in trend:
            score += 15
        elif "下降" in trend:
            score -= 15
        
        # RSI权重
        rsi = analysis["indicators"]["rsi"]["rsi14"]
        if rsi:
            if rsi < 30:
                score += 20  # 超卖，可能反弹
            elif rsi > 70:
                score -= 20  # 超买，注意风险
        
        # MACD权重
        macd_hist = analysis["indicators"]["macd"]["histogram"]
        if macd_hist:
            if macd_hist > 0:
                score += 15
            else:
                score -= 15
        
        # 买卖信号权重
        score += buy_count * 10 - sell_count * 10
        
        # 限制在-100到100
        score = max(-100, min(100, score))
        
        # 评分说明
        if score >= 60:
            recommendation = "强势买入"
            action = "建议关注，可在回调时考虑买入"
        elif score >= 30:
            recommendation = "温和买入"
            action = "建议轻仓关注，等待更好买点"
        elif score >= -30:
            recommendation = "观望"
            action = "建议观望，等待趋势明朗"
        elif score >= -60:
            recommendation = "谨慎"
            action = "建议减仓或观望，不宜追高"
        else:
            recommendation = "卖出"
            action = "建议减仓或止损，注意风险"
        
        return {
            "score": score,
            "recommendation": recommendation,
            "action": action,
            "buy_signals_count": buy_count,
            "sell_signals_count": sell_count,
        }


# 便捷函数
def analyze_stock(kline_data: List[Dict]) -> Dict:
    """分析单只股票"""
    if not kline_data or len(kline_data) < 20:
        return {"error": "数据不足，无法进行分析"}
    
    analyzer = TechnicalAnalyzer(kline_data)
    return analyzer.analyze()


def get_buy_signals(signals: Dict) -> List[Dict]:
    """获取买入信号"""
    return signals.get("buy", [])


def get_sell_signals(signals: Dict) -> List[Dict]:
    """获取卖出信号"""
    return signals.get("sell", [])


if __name__ == "__main__":
    # 简单测试
    from tools.data_source import get_kline
    
    print("=" * 50)
    print("技术分析测试")
    print("=" * 50)
    
    # 获取K线数据
    klines = get_kline("000001", "daily", 100)
    if klines:
        result = analyze_stock(klines)
        
        print("\n【基本信息】")
        info = result["basic_info"]
        print(f"   最新价: {info['latest_price']}")
        print(f"   涨跌幅: {info['change_percent']:.2f}%")
        
        print("\n【趋势分析】")
        trend = result["trend"]
        print(f"   趋势: {trend['trend']}")
        print(f"   MA5/MA10/MA20: {trend['ma5']}/{trend['ma10']}/{trend['ma20']}")
        
        print("\n【技术指标】")
        ind = result["indicators"]
        print(f"   MACD: DIF={ind['macd']['dif']}, DEA={ind['macd']['dea']}, 柱={ind['macd']['histogram']}")
        print(f"   RSI(14): {ind['rsi']['rsi14']}")
        print(f"   KDJ: K={ind['kdj']['k']:.1f}, D={ind['kdj']['d']:.1f}, J={ind['kdj']['j']:.1f}")
        
        print("\n【买卖信号】")
        for sig in result["signals"]["buy"]:
            print(f"   买入: {sig['type']} - {sig['description']}")
        for sig in result["signals"]["sell"]:
            print(f"   卖出: {sig['type']} - {sig['description']}")
        
        print("\n【综合建议】")
        summary = result["summary"]
        print(f"   评分: {summary['score']} ({summary['recommendation']})")
        print(f"   操作建议: {summary['action']}")
