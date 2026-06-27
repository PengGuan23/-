from __future__ import annotations

import pandas as pd


def forecast_pv(hourly: pd.DataFrame, capacity_mw: float) -> pd.DataFrame:
    """返回最近 24 小时的光伏预测结果，并保证符合物理边界。"""
    result = hourly.tail(24).copy()
    result["pv_forecast_mwh"] = result["forecast_generation_mwh"].clip(lower=0, upper=capacity_mw)
    result.loc[result["hour"].isin([0, 1, 2, 3, 4, 22, 23]), "pv_forecast_mwh"] = 0
    return result

