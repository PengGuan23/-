from __future__ import annotations

import pandas as pd


STRATEGY_FACTORS = {"保守": 0.85, "均衡": 0.92, "进取": 0.98}


def build_trading_plan(tomorrow: pd.DataFrame, strategy: str = "均衡") -> pd.DataFrame:
    if strategy not in STRATEGY_FACTORS:
        raise ValueError("strategy must be one of: 保守, 均衡, 进取")

    factor = STRATEGY_FACTORS[strategy]
    plan = tomorrow.copy()
    forecast_col = "pv_forecast_mwh" if "pv_forecast_mwh" in plan.columns else "forecast_generation_mwh"
    price_col = "price_forecast" if "price_forecast" in plan.columns else "day_ahead_price"
    plan["strategy"] = strategy
    plan["declared_mwh"] = (plan[forecast_col] * factor).clip(lower=0).round(3)
    plan["quote_low"] = (plan[price_col] * 0.92).round(2)
    plan["quote_high"] = (plan[price_col] * 1.08).round(2)
    plan["expected_revenue"] = (plan["declared_mwh"] * plan[price_col]).round(2)
    plan["deviation_mwh"] = (plan["actual_generation_mwh"] - plan["declared_mwh"]).abs().round(3)
    penalty_rate = 0.18 + (0.08 if strategy == "进取" else 0.03 if strategy == "均衡" else 0)
    plan["estimated_deviation_loss"] = (plan["deviation_mwh"] * plan[price_col] * penalty_rate).round(2)
    return plan


def recommend_strategy(tomorrow: pd.DataFrame) -> str:
    avg_cloud = float(tomorrow["cloud_index"].mean())
    avg_price = float(tomorrow["day_ahead_price"].mean())
    if avg_cloud > 0.48:
        return "保守"
    if avg_price > 330 and avg_cloud < 0.35:
        return "进取"
    return "均衡"

