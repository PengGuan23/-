from __future__ import annotations

import pandas as pd


def simulate_storage_dispatch(
    tomorrow: pd.DataFrame,
    capacity_mwh: float,
    power_mw: float,
    efficiency: float = 0.9,
) -> pd.DataFrame:
    result = tomorrow.copy()
    result["charge_mwh"] = 0.0
    result["discharge_mwh"] = 0.0
    result["state_of_charge_mwh"] = 0.0
    result["storage_revenue"] = 0.0

    if capacity_mwh <= 0 or power_mw <= 0:
        return result

    price_col = "price_forecast" if "price_forecast" in result.columns else "day_ahead_price"
    low_threshold = result[price_col].quantile(0.35)
    high_threshold = result[price_col].quantile(0.75)
    soc = 0.0
    for idx, row in result.iterrows():
        price = float(row[price_col])
        if price <= low_threshold and 9 <= int(row["hour"]) <= 15:
            charge = min(power_mw, capacity_mwh - soc, max(float(row.get("forecast_generation_mwh", 0)) * 0.25, 0))
            soc += charge * efficiency
            result.at[idx, "charge_mwh"] = round(charge, 3)
            result.at[idx, "storage_revenue"] = round(-charge * price, 2)
        elif price >= high_threshold and 17 <= int(row["hour"]) <= 22:
            discharge = min(power_mw, soc)
            soc -= discharge
            result.at[idx, "discharge_mwh"] = round(discharge, 3)
            result.at[idx, "storage_revenue"] = round(discharge * price, 2)
        result.at[idx, "state_of_charge_mwh"] = round(soc, 3)
    return result

