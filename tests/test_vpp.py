import unittest

from src.vpp.simulate import generate_vpp_dataset, summarize_vpp_portfolio


class VppSimulationTest(unittest.TestCase):
    def test_vpp_dataset_is_deterministic(self):
        first = generate_vpp_dataset(seed=9, days=3)
        second = generate_vpp_dataset(seed=9, days=3)

        self.assertTrue(first["hourly"].equals(second["hourly"]))
        self.assertTrue(first["resources"].equals(second["resources"]))

    def test_vpp_resource_pool_contains_four_resource_types(self):
        data = generate_vpp_dataset(seed=9, days=3)
        resource_types = set(data["resources"]["resource_type"])

        self.assertEqual(resource_types, {"分布式光伏", "储能", "工商业可调负荷", "充电桩"})

    def test_vpp_dispatch_reduces_peak_net_load(self):
        hourly = generate_vpp_dataset(seed=9, days=14)["hourly"]

        baseline_peak = hourly["baseline_net_load_mwh"].max()
        dispatch_peak = hourly["vpp_net_position_mwh"].max()

        self.assertLess(dispatch_peak, baseline_peak)

    def test_vpp_dispatch_creates_revenue_impact(self):
        hourly = generate_vpp_dataset(seed=9, days=14)["hourly"]

        self.assertNotEqual(round(hourly["vpp_dispatch_revenue"].sum(), 2), 0)

    def test_vpp_summary_reports_adjustable_capacity(self):
        data = generate_vpp_dataset(seed=9, days=14)
        summary = summarize_vpp_portfolio(data["resources"], data["hourly"])

        self.assertGreater(summary["aggregate_capacity_mw"], 0)
        self.assertGreater(summary["adjustable_capacity_mw"], 0)
        self.assertIn("expected_daily_revenue", summary)


if __name__ == "__main__":
    unittest.main()

