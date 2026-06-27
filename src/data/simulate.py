from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class DemoAsset:
    name: str = "西北某 100MW 集中式光伏电站"
    province: str = "陕西"
    grid_zone: str = "西北电网"
    capacity_mw: float = 100.0


def _solar_shape(hours: np.ndarray) -> np.ndarray:
    daylight = np.where((hours >= 6) & (hours <= 20), np.sin((hours - 6) / 14 * np.pi), 0)
    return np.clip(daylight, 0, None)


def generate_demo_dataset(seed: int = 42, days: int = 120, capacity_mw: float = 100.0) -> dict[str, pd.DataFrame]:
    """生成符合新能源电力交易逻辑的小时级模拟数据。"""
    if days <= 0:
        raise ValueError("days must be positive")
    if capacity_mw <= 0:
        raise ValueError("capacity_mw must be positive")

    rng = np.random.default_rng(seed)
    timestamps = pd.date_range("2026-01-01", periods=days * 24, freq="h")
    df = pd.DataFrame({"timestamp": timestamps})
    df["date"] = df["timestamp"].dt.date.astype(str)
    df["hour"] = df["timestamp"].dt.hour
    df["weekday"] = df["timestamp"].dt.weekday
    df["is_holiday"] = df["weekday"].isin([5, 6]).astype(int)

    hours = df["hour"].to_numpy()
    solar = _solar_shape(hours)
    daily_weather = rng.beta(5, 2, size=days)
    weather_factor = np.repeat(daily_weather, 24)
    cloud_noise = rng.normal(0, 0.08, size=len(df))
    df["cloud_index"] = np.clip(1 - weather_factor + rng.normal(0, 0.06, len(df)), 0, 1)
    df["irradiance"] = np.round(1000 * solar * np.clip(weather_factor + cloud_noise, 0, 1.12), 2)
    df["temperature"] = np.round(16 + 12 * solar + 8 * np.sin(np.arange(len(df)) / 24 / 365 * 2 * np.pi) + rng.normal(0, 2, len(df)), 2)

    generation_noise = rng.normal(0, capacity_mw * 0.025, len(df))
    actual_generation = capacity_mw * solar * np.clip(weather_factor, 0.15, 1.0) + generation_noise
    actual_generation = np.where(solar == 0, 0, actual_generation)
    df["actual_generation_mwh"] = np.round(np.clip(actual_generation, 0, capacity_mw), 3)

    forecast_bias = rng.normal(0, capacity_mw * (0.035 + df["cloud_index"].to_numpy() * 0.035), len(df))
    forecast_generation = df["actual_generation_mwh"].to_numpy() + forecast_bias
    forecast_generation = np.where(solar == 0, 0, forecast_generation)
    df["forecast_generation_mwh"] = np.round(np.clip(forecast_generation, 0, capacity_mw), 3)

    load_shape = 0.86 + 0.1 * np.sin((hours - 8) / 24 * 2 * np.pi) + 0.16 * np.where((hours >= 18) & (hours <= 21), 1, 0)
    weekday_factor = np.where(df["is_holiday"].to_numpy() == 1, 0.94, 1.0)
    df["load_mw"] = np.round(9000 * load_shape * weekday_factor + rng.normal(0, 180, len(df)), 2)
    df["renewable_ratio"] = np.round(np.clip(0.18 + 0.34 * solar * weather_factor + rng.normal(0, 0.025, len(df)), 0.08, 0.7), 3)

    base_price = 315 + 55 * np.where((hours >= 18) & (hours <= 21), 1, 0)
    noon_solar_discount = 95 * np.where((hours >= 11) & (hours <= 14), solar * weather_factor, 0)
    load_premium = (df["load_mw"].to_numpy() - df["load_mw"].mean()) / 55
    price_noise = rng.normal(0, 18, len(df))
    day_ahead = base_price + load_premium - noon_solar_discount - 45 * df["is_holiday"].to_numpy() + price_noise
    df["day_ahead_price"] = np.round(np.clip(day_ahead, 40, 720), 2)
    df["real_time_price"] = np.round(np.clip(df["day_ahead_price"].to_numpy() + rng.normal(0, 26, len(df)), 20, 820), 2)

    assets = pd.DataFrame(
        [
            {
                "asset_name": DemoAsset(capacity_mw=capacity_mw).name,
                "province": DemoAsset().province,
                "grid_zone": DemoAsset().grid_zone,
                "capacity_mw": capacity_mw,
                "data_note": "模拟数据，仅用于演示交易决策流程",
            }
        ]
    )
    return {"assets": assets, "hourly": df}

