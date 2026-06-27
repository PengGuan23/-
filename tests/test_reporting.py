import unittest

from src.reporting.charts import format_money, format_percent, multi_series_svg
from app import build_dashboard_html


class ReportingTest(unittest.TestCase):
    def test_format_money_uses_wan_yuan_unit(self):
        self.assertEqual(format_money(1234567.89), "123.46 万元")

    def test_format_percent_uses_percent_unit(self):
        self.assertEqual(format_percent(0.5), "50.0%")

    def test_multi_series_svg_contains_strategy_legend(self):
        svg = multi_series_svg(
            [
                ("保守", [1, 2, 3], "#2f9e44"),
                ("均衡", [1, 3, 4], "#1864ab"),
                ("进取", [1, 4, 6], "#f08c00"),
            ],
            unit_label="累计净收益",
        )

        self.assertIn("保守", svg)
        self.assertIn("均衡", svg)
        self.assertIn("进取", svg)
        self.assertIn("累计净收益", svg)

    def test_dashboard_uses_terminal_style_shell(self):
        html = build_dashboard_html(seed=3, capacity_mw=80)

        self.assertIn('class="terminal-shell"', html)
        self.assertIn("MARKET TERMINAL", html)
        self.assertIn("#ff9f1a", html)
        self.assertIn("虚拟电厂交易与调度决策辅助系统", html)

    def test_terminal_labels_are_navigation_links(self):
        html = build_dashboard_html(seed=3, capacity_mw=80)

        self.assertIn('href="#resource-pool"', html)
        self.assertIn('href="#net-load"', html)
        self.assertIn('href="#day-ahead"', html)
        self.assertIn('href="#dispatch"', html)
        self.assertIn('href="#risk-monitor"', html)
        self.assertIn('id="resource-pool"', html)
        self.assertIn('id="net-load"', html)
        self.assertIn('id="day-ahead"', html)
        self.assertIn('id="dispatch"', html)
        self.assertIn('id="risk-monitor"', html)

    def test_dashboard_contains_vpp_business_sections(self):
        html = build_dashboard_html(seed=3, capacity_mw=80)

        self.assertIn("资源聚合", html)
        self.assertIn("净负荷预测", html)
        self.assertIn("协同调度模拟", html)
        self.assertIn("辅助服务能力", html)


if __name__ == "__main__":
    unittest.main()
