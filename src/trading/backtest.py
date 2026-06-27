from __future__ import annotations

import pandas as pd

from src.trading.strategy import build_trading_plan


def run_strategy_backtest(hourly: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for strategy in ["保守", "均衡", "进取"]:
        plan = build_trading_plan(hourly, strategy)
        daily = (
            plan.assign(net_revenue=plan["expected_revenue"] - plan["estimated_deviation_loss"])
            .groupby("date", as_index=False)
            .agg(net_revenue=("net_revenue", "sum"), loss=("estimated_deviation_loss", "sum"))
        )
        rows.append(
            {
                "strategy": strategy,
                "total_revenue": round(float(daily["net_revenue"].sum()), 2),
                "average_daily_revenue": round(float(daily["net_revenue"].mean()), 2),
                "deviation_loss": round(float(daily["loss"].sum()), 2),
                "revenue_volatility": round(float(daily["net_revenue"].std(ddof=0)), 2),
                "max_daily_drawdown": round(float(daily["net_revenue"].max() - daily["net_revenue"].min()), 2),
                "win_rate": round(float((daily["net_revenue"] > daily["net_revenue"].median()).mean()), 3),
            }
        )
    return pd.DataFrame(rows)


def cumulative_revenue(hourly: pd.DataFrame) -> pd.DataFrame:
    frames = []
    for strategy in ["保守", "均衡", "进取"]:
        plan = build_trading_plan(hourly, strategy)
        daily = (
            plan.assign(net_revenue=plan["expected_revenue"] - plan["estimated_deviation_loss"])
            .groupby("date", as_index=False)
            .agg(net_revenue=("net_revenue", "sum"))
        )
        daily["strategy"] = strategy
        daily["cumulative_revenue"] = daily["net_revenue"].cumsum()
        frames.append(daily)
    return pd.concat(frames, ignore_index=True)

