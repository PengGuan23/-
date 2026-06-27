import unittest

from src.data.simulate import generate_demo_dataset
from src.storage.optimizer import simulate_storage_dispatch
from src.trading.backtest import run_strategy_backtest
from src.trading.strategy import build_trading_plan


class TradingLogicTest(unittest.TestCase):
    def test_strategy_levels_create_different_declared_energy(self):
        hourly = generate_demo_dataset(seed=11, days=5, capacity_mw=100)["hourly"]
        tomorrow = hourly.tail(24).copy()

        conservative = build_trading_plan(tomorrow, "保守")
        aggressive = build_trading_plan(tomorrow, "进取")

        self.assertGreater(aggressive["declared_mwh"].sum(), conservative["declared_mwh"].sum())

    def test_backtest_returns_three_strategy_rows(self):
        hourly = generate_demo_dataset(seed=11, days=20, capacity_mw=100)["hourly"]

        result = run_strategy_backtest(hourly)

        self.assertEqual(set(result["strategy"]), {"保守", "均衡", "进取"})
        self.assertGreater(result["total_revenue"].nunique(), 1)

    def test_storage_dispatch_changes_revenue_when_capacity_positive(self):
        hourly = generate_demo_dataset(seed=11, days=5, capacity_mw=100)["hourly"]
        tomorrow = hourly.tail(24).copy()

        no_storage = simulate_storage_dispatch(tomorrow, capacity_mwh=0, power_mw=0)
        with_storage = simulate_storage_dispatch(tomorrow, capacity_mwh=40, power_mw=20)

        self.assertNotEqual(with_storage["storage_revenue"].sum(), no_storage["storage_revenue"].sum())


if __name__ == "__main__":
    unittest.main()

