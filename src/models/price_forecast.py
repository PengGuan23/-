from __future__ import annotations

import pandas as pd


def forecast_price(hourly: pd.DataFrame) -> pd.DataFrame:
    """返回最近 24 小时的电价预测和风险标签。"""
    result = hourly.tail(24).copy()
    result["price_forecast"] = result["day_ahead_price"]
    result["price_band_low"] = (result["price_forecast"] * 0.9).round(2)
    result["price_band_high"] = (result["price_forecast"] * 1.1).round(2)
    result["price_period"] = "平段"
    result.loc[result["hour"].between(11, 14), "price_period"] = "谷段"
    result.loc[result["hour"].between(18, 21), "price_period"] = "峰段"
    result["risk_level"] = "中"
    result.loc[(result["price_forecast"] < 180) | (result["cloud_index"] > 0.55), "risk_level"] = "高"
    result.loc[(result["price_forecast"] > 360) & (result["cloud_index"] < 0.35), "risk_level"] = "低"
    return result

