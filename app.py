from __future__ import annotations

from pathlib import Path

from src.reporting.charts import format_money, format_number, hourly_table, metric_card, sparkline_svg
from src.vpp.simulate import generate_vpp_dataset, summarize_vpp_portfolio


OUTPUT = Path("outputs/虚拟电厂交易与调度决策辅助系统.html")


def _terminal_css() -> str:
    return """
    :root {
      --bg: #050505;
      --panel: #0e1116;
      --ink: #f4f7fb;
      --muted: #8f9bad;
      --line: #2a313a;
      --blue: #36a3ff;
      --green: #39ff88;
      --red: #ff4d4d;
      --amber: #ff9f1a;
    }
    * { box-sizing: border-box; }
    html { scroll-behavior: smooth; }
    body {
      margin: 0;
      font-family: "SFMono-Regular", "Menlo", "Monaco", "Consolas", "PingFang SC", "Microsoft YaHei", monospace;
      color: var(--ink);
      background:
        linear-gradient(90deg, rgba(255,159,26,0.08) 0 1px, transparent 1px 100%),
        linear-gradient(180deg, rgba(255,159,26,0.05) 0 1px, transparent 1px 100%),
        var(--bg);
      background-size: 32px 32px;
    }
    header {
      background: #070707;
      color: #fff;
      padding: 16px 22px 14px;
      border-bottom: 3px solid var(--amber);
      box-shadow: 0 0 0 1px #20242b, 0 12px 32px rgba(0,0,0,0.35);
      position: sticky;
      top: 0;
      z-index: 10;
    }
    header h1 { margin: 4px 0 6px; font-size: 24px; letter-spacing: 0; }
    header p { margin: 0; color: var(--muted); max-width: 1180px; line-height: 1.6; font-size: 13px; }
    .terminal-shell { min-height: 100vh; }
    .terminal-bar { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; color: #111; font-weight: 800; font-size: 12px; }
    .terminal-tag { background: var(--amber); padding: 3px 8px; color: #080808; }
    .terminal-meta {
      color: var(--amber);
      border: 1px solid #5a3a0b;
      padding: 2px 7px;
      text-decoration: none;
      cursor: pointer;
    }
    .terminal-meta:hover, .terminal-meta:focus {
      background: var(--amber);
      color: #080808;
      outline: none;
    }
    main { padding: 16px 20px 36px; max-width: 1480px; margin: 0 auto; }
    section { margin: 0 0 14px; scroll-margin-top: 112px; }
    h2 {
      font-size: 15px;
      margin: 0 0 9px;
      color: var(--amber);
      text-transform: uppercase;
      border-bottom: 1px solid var(--line);
      padding-bottom: 7px;
    }
    .notice {
      background: #1b1305;
      border: 1px solid #65430b;
      color: #ffc46b;
      padding: 9px 12px;
      margin-bottom: 12px;
      line-height: 1.5;
      font-size: 12px;
    }
    .grid { display: grid; gap: 10px; }
    .metrics { grid-template-columns: repeat(5, minmax(0, 1fr)); }
    .two { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .metric-card, .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 0;
      padding: 12px;
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.03), 0 16px 30px rgba(0,0,0,0.22);
    }
    .metric-card span { display: block; color: var(--muted); font-size: 11px; }
    .metric-card strong { display: block; font-size: 23px; margin: 7px 0; color: var(--green); }
    .metric-card small { color: var(--muted); line-height: 1.4; font-size: 11px; }
    .chart { width: 100%; height: 180px; background: #080b10; border: 1px solid var(--line); border-radius: 0; }
    table { width: 100%; border-collapse: collapse; background: #090c11; border: 1px solid var(--line); }
    th, td { padding: 7px 9px; border-bottom: 1px solid #202630; text-align: right; font-size: 12px; color: #e8edf5; }
    th:first-child, td:first-child { text-align: left; }
    th { background: #171d24; color: var(--amber); font-weight: 800; }
    tr:nth-child(even) td { background: rgba(255,255,255,0.018); }
    .pill { display: inline-block; padding: 3px 8px; background: var(--amber); color: #080808; font-weight: 800; }
    .story { line-height: 1.7; color: #b9c3d2; font-size: 12px; }
    @media (max-width: 900px) { .metrics, .two { grid-template-columns: 1fr; } main { padding: 12px; } header { padding: 14px 12px; } }
    """


def build_dashboard_html(seed: int = 42, capacity_mw: float = 100.0) -> str:
    data = generate_vpp_dataset(seed=seed, days=120)
    resources = data["resources"]
    hourly = data["hourly"]
    tomorrow = hourly.tail(24).copy()
    summary = summarize_vpp_portfolio(resources, hourly)

    resource_table = resources.assign(
        资源名称=resources["resource_name"],
        资源类型=resources["resource_type"],
        装机或容量=resources["capacity_mw"].map(lambda v: f"{v:.1f} MW"),
        可调节能力=resources["adjustable_mw"].map(lambda v: f"{v:.1f} MW"),
    )
    strategy_table = tomorrow.assign(
        时段=tomorrow["hour"].astype(str) + ":00",
        分布式光伏=tomorrow["distributed_pv_mwh"].round(2),
        基线净负荷=tomorrow["baseline_net_load_mwh"].round(2),
        VPP净持仓=tomorrow["vpp_net_position_mwh"].round(2),
        日前价格=tomorrow["day_ahead_price"].round(2),
        交易动作=tomorrow["vpp_net_position_mwh"].map(lambda v: "买电" if v > 0 else "卖电"),
    )
    dispatch_table = tomorrow.assign(
        时段=tomorrow["hour"].astype(str) + ":00",
        削减负荷=tomorrow["flexible_load_mwh"].round(2),
        充电桩移峰=tomorrow["ev_shift_mwh"].round(2),
        储能充电=tomorrow["storage_charge_mwh"].round(2),
        储能放电=tomorrow["storage_discharge_mwh"].round(2),
        荷电状态=tomorrow["storage_soc_mwh"].round(2),
        调度收益=tomorrow["vpp_dispatch_revenue"].round(2),
    )
    ancillary_table = resources.assign(
        资源=resources["resource_name"],
        可提供能力=resources["resource_type"].map(
            {
                "分布式光伏": "绿电出力、低价时段消纳",
                "储能": "调峰、备用、偏差修正",
                "工商业可调负荷": "需求响应、削峰",
                "充电桩": "移峰填谷、柔性负荷",
            }
        ),
        市场价值=resources["resource_type"].map(
            {
                "分布式光伏": "提升绿电交易规模",
                "储能": "捕捉峰谷价差",
                "工商业可调负荷": "获得响应补偿",
                "充电桩": "降低高价时段购电",
            }
        ),
    )

    peak_reduction = summary["peak_reduction_mwh"]
    daily_revenue = summary["expected_daily_revenue"]
    vpp_revenue = float(hourly["vpp_dispatch_revenue"].sum())

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>虚拟电厂交易与调度决策辅助系统</title>
  <style>{_terminal_css()}</style>
</head>
<body>
<div class="terminal-shell">
  <header>
    <div class="terminal-bar">
      <span class="terminal-tag">VPP MARKET TERMINAL</span>
      <a class="terminal-meta" href="#resource-pool">RESOURCE POOL</a>
      <a class="terminal-meta" href="#net-load">NET LOAD</a>
      <a class="terminal-meta" href="#day-ahead">DAY-AHEAD</a>
      <a class="terminal-meta" href="#dispatch">DISPATCH</a>
      <a class="terminal-meta" href="#risk-monitor">RISK</a>
    </div>
    <h1>虚拟电厂交易与调度决策辅助系统</h1>
    <p>把分布式光伏、储能、工商业可调负荷和充电桩聚合为可预测、可调节、可交易的组合资产。</p>
  </header>
  <main>
    <div class="notice">重要说明：本系统使用模拟数据演示虚拟电厂交易与调度流程，不代表真实交易收益，不构成交易建议；系统定位是辅助决策，不做实盘自动下单。</div>

    <section>
      <h2>一、VPP 总览</h2>
      <div class="grid metrics">
        {metric_card("聚合资源规模", f"{summary["aggregate_capacity_mw"]:.1f} MW", "光伏 + 储能 + 负荷 + 充电桩")}
        {metric_card("可调节能力", f"{summary["adjustable_capacity_mw"]:.1f} MW", "可参与需求响应/调峰")}
        {metric_card("削峰能力", f"{peak_reduction:.1f} MWh", "相对基线净负荷峰值")}
        {metric_card("日均调度收益", format_money(daily_revenue), "低价吸纳，高价响应")}
        {metric_card("累计调度收益", format_money(vpp_revenue), "模拟周期内协同调度")}
      </div>
    </section>

    <section class="grid two">
      <div class="panel" id="resource-pool">
        <h2>二、资源聚合</h2>
        {hourly_table(resource_table, ["资源名称", "资源类型", "装机或容量", "可调节能力"], limit=8)}
        <p class="story">虚拟电厂的核心不是单个电站，而是把分散资源组织成可预测、可调节、可交易的组合资产。</p>
      </div>
      <div class="panel" id="net-load">
        <h2>三、净负荷预测</h2>
        {sparkline_svg(tomorrow["baseline_net_load_mwh"].tolist(), color="#ff9f1a")}
        <p class="story">净负荷 = 工商业负荷 + 充电桩负荷 - 分布式光伏出力。净负荷越高，外购电和价格风险越高。</p>
      </div>
    </section>

    <section id="day-ahead">
      <h2>四、日前交易策略</h2>
      {hourly_table(strategy_table, ["时段", "分布式光伏", "基线净负荷", "VPP净持仓", "日前价格", "交易动作"])}
    </section>

    <section class="grid two">
      <div class="panel" id="dispatch">
        <h2>五、协同调度模拟</h2>
        {hourly_table(dispatch_table, ["时段", "削减负荷", "充电桩移峰", "储能充电", "储能放电", "荷电状态", "调度收益"])}
      </div>
      <div class="panel" id="risk-monitor">
        <h2>六、收益与风险回测</h2>
        {sparkline_svg(hourly.groupby("date")["vpp_dispatch_revenue"].sum().cumsum().tolist(), color="#39ff88")}
        <p class="story">虚拟电厂收益来自资源组合协同：低价时段吸纳光伏和充电，高价时段释放储能、削减负荷并降低净负荷峰值。</p>
        {metric_card("累计调度收益", format_money(vpp_revenue), "模拟数据，仅展示机制")}
      </div>
    </section>

    <section>
      <h2>七、辅助服务能力</h2>
      {hourly_table(ancillary_table, ["资源", "可提供能力", "市场价值"], limit=8)}
    </section>
  </main>
</div>
</body>
</html>"""


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    html = build_dashboard_html()
    OUTPUT.write_text(html, encoding="utf-8")
    print(f"已生成: {OUTPUT}")


if __name__ == "__main__":
    main()

