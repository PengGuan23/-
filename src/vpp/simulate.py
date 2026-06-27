from __future__ import annotations

import numpy as np
import pandas as pd


def _solar_shape(hours: np.ndarray) -> np.ndarray:
    daylight = np.where((hours >= 6) & (hours <= 20), np.sin((hours - 6) / 14 * np.pi), 0)
    return np.clip(daylight, 0, None)


def generate_vpp_dataset(seed: int = 42, days: int = 120) -> dict[str, pd.DataFrame]:
    """生成虚拟电厂聚合资源与小时级调度模拟数据。"""
    if days <= 0:
        raise ValueError("days must be positive")

    rng = np.random.default_rng(seed)
    timestamps = pd.date_range("2026-01-01", periods=days * 24, freq="h")
    df = pd.DataFrame({"timestamp": timestamps})
    df["date"] = df["timestamp"].dt.date.astype(str)
    df["hour"] = df["timestamp"].dt.hour
    df["weekday"] = df["timestamp"].dt.weekday
    df["is_holiday"] = df["weekday"].isin([5, 6]).astype(int)

    resources = pd.DataFrame(
        [
            {"resource_name": "园区屋顶分布式光伏", "resource_type": "分布式光伏", "capacity_mw": 68.0, "adjustable_mw": 0.0},
            {"resource_name": "用户侧储能集群", "resource_type": "储能", "capacity_mw": 32.0, "adjustable_mw": 32.0},
            {"resource_name": "工商业可调负荷", "resource_type": "工商业可调负荷", "capacity_mw": 46.0, "adjustable_mw": 18.0},
            {"resource_name": "充电桩聚合负荷", "resource_type": "充电桩", "capacity_mw": 24.0, "adjustable_mw": 10.0},
        ]
    )

    hours = df["hour"].to_numpy()
    solar = _solar_shape(hours)
    daily_weather = rng.beta(5, 2, size=days)
    weather_factor = np.repeat(daily_weather, 24)
    df["distributed_pv_mwh"] = np.round(np.clip(68 * solar * weather_factor + rng.normal(0, 1.5, len(df)), 0, 68), 3)

    industrial_shape = 38 + 8 * np.where((hours >= 8) & (hours <= 18), 1, 0) + 5 * np.where((hours >= 19) & (hours <= 21), 1, 0)
    holiday_factor = np.where(df["is_holiday"].to_numpy() == 1, 0.82, 1.0)
    df["industrial_load_mwh"] = np.round(np.clip(industrial_shape * holiday_factor + rng.normal(0, 2.2, len(df)), 18, 58), 3)

    ev_shape = 3 + 9 * np.where((hours >= 18) & (hours <= 23), 1, 0) + 4 * np.where((hours >= 11) & (hours <= 14), 1, 0)
    df["ev_load_mwh"] = np.round(np.clip(ev_shape + rng.normal(0, 1.2, len(df)), 0, 24), 3)
    df["baseline_net_load_mwh"] = np.round(df["industrial_load_mwh"] + df["ev_load_mwh"] - df["distributed_pv_mwh"], 3)

    base_price = 310 + 72 * np.where((hours >= 18) & (hours <= 21), 1, 0) - 92 * np.where((hours >= 11) & (hours <= 14), solar * weather_factor, 0)
    df["day_ahead_price"] = np.round(np.clip(base_price + rng.normal(0, 18, len(df)), 45, 760), 2)
    low_price = df["day_ahead_price"].quantile(0.35)
    high_price = df["day_ahead_price"].quantile(0.75)

    storage_capacity = 96.0
    storage_power = 32.0
    soc = 36.0
    charge_values = []
    discharge_values = []
    soc_values = []
    flexible_load = []
    ev_shift = []
    revenue = []
    vpp_position = []

    for _, row in df.iterrows():
        hour = int(row["hour"])
        price = float(row["day_ahead_price"])
        baseline = float(row["baseline_net_load_mwh"])

        load_cut = 0.0
        ev_adjust = 0.0
        charge = 0.0
        discharge = 0.0
        cashflow = 0.0

        if price >= high_price and 18 <= hour <= 21:
            load_cut = min(18.0, max(baseline * 0.18, 0))
            ev_adjust = min(10.0, max(float(row["ev_load_mwh"]) * 0.45, 0))
            discharge = min(storage_power, soc, max(baseline - load_cut - ev_adjust, 0))
            soc -= discharge
            cashflow += (load_cut + ev_adjust + discharge) * price
        elif price <= low_price and 10 <= hour <= 15:
            charge = min(storage_power, storage_capacity - soc, max(float(row["distributed_pv_mwh"]) * 0.28, 0))
            soc += charge * 0.9
            cashflow -= charge * price
            ev_adjust = -min(8.0, max(float(row["ev_load_mwh"]) * 0.3, 0))

        net_position = baseline - load_cut - ev_adjust - discharge + charge
        charge_values.append(round(charge, 3))
        discharge_values.append(round(discharge, 3))
        soc_values.append(round(soc, 3))
        flexible_load.append(round(load_cut, 3))
        ev_shift.append(round(ev_adjust, 3))
        revenue.append(round(cashflow, 2))
        vpp_position.append(round(net_position, 3))

    df["flexible_load_mwh"] = flexible_load
    df["ev_shift_mwh"] = ev_shift
    df["storage_charge_mwh"] = charge_values
    df["storage_discharge_mwh"] = discharge_values
    df["storage_soc_mwh"] = soc_values
    df["vpp_net_position_mwh"] = vpp_position
    df["vpp_dispatch_revenue"] = revenue
    df["adjustable_capacity_mw"] = 60.0

    return {"resources": resources, "hourly": df}


def summarize_vpp_portfolio(resources: pd.DataFrame, hourly: pd.DataFrame) -> dict[str, float]:
    return {
        "aggregate_capacity_mw": float(resources["capacity_mw"].sum()),
        "adjustable_capacity_mw": float(resources["adjustable_mw"].sum()),
        "distributed_pv_mw": float(resources.loc[resources["resource_type"] == "分布式光伏", "capacity_mw"].sum()),
        "storage_power_mw": float(resources.loc[resources["resource_type"] == "储能", "capacity_mw"].sum()),
        "expected_daily_revenue": float(hourly.groupby("date")["vpp_dispatch_revenue"].sum().mean()),
        "peak_reduction_mwh": float(hourly["baseline_net_load_mwh"].max() - hourly["vpp_net_position_mwh"].max()),
    }

