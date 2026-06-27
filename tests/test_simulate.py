import unittest

from src.data.simulate import generate_demo_dataset


class DemoDatasetTest(unittest.TestCase):
    def test_generate_demo_dataset_is_deterministic(self):
        first = generate_demo_dataset(seed=7, days=3, capacity_mw=50)
        second = generate_demo_dataset(seed=7, days=3, capacity_mw=50)

        self.assertTrue(first["hourly"].equals(second["hourly"]))

    def test_pv_output_respects_physical_bounds(self):
        data = generate_demo_dataset(seed=7, days=3, capacity_mw=50)
        hourly = data["hourly"]

        self.assertGreaterEqual(hourly["actual_generation_mwh"].min(), 0)
        self.assertLessEqual(hourly["actual_generation_mwh"].max(), 50)
        night = hourly[hourly["hour"].isin([0, 1, 2, 3, 4, 22, 23])]
        self.assertEqual(night["actual_generation_mwh"].max(), 0)

    def test_market_data_contains_low_noon_price_pattern(self):
        data = generate_demo_dataset(seed=7, days=30, capacity_mw=100)
        hourly = data["hourly"]

        noon = hourly[hourly["hour"].between(11, 14)]["day_ahead_price"].mean()
        evening = hourly[hourly["hour"].between(18, 21)]["day_ahead_price"].mean()
        self.assertGreater(evening, noon)


if __name__ == "__main__":
    unittest.main()
