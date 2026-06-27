from __future__ import annotations

import html

import pandas as pd


def format_money(value: float) -> str:
    return f"{value / 10000:,.2f} 万元"


def format_number(value: float) -> str:
    return f"{value:,.2f}"


def format_percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def sparkline_svg(values: list[float], width: int = 520, height: int = 180, color: str = "#1864ab") -> str:
    if not values:
        return ""
    min_v = min(values)
    max_v = max(values)
    span = max(max_v - min_v, 1e-9)
    step = width / max(len(values) - 1, 1)
    points = []
    for i, value in enumerate(values):
        x = i * step
        y = height - ((value - min_v) / span * (height - 24) + 12)
        points.append(f"{x:.1f},{y:.1f}")
    return (
        f'<svg viewBox="0 0 {width} {height}" role="img" class="chart">'
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#080b10" />'
        f'<polyline fill="none" stroke="{color}" stroke-width="3" points="{" ".join(points)}" />'
        f"</svg>"
    )


def multi_series_svg(
    series: list[tuple[str, list[float], str]],
    width: int = 640,
    height: int = 240,
    unit_label: str = "",
) -> str:
    all_values = [value for _, values, _ in series for value in values]
    if not all_values:
        return ""

    min_v = min(all_values)
    max_v = max(all_values)
    span = max(max_v - min_v, 1e-9)
    chart_left = 42
    chart_right = width - 16
    chart_top = 26
    chart_bottom = height - 48
    chart_width = chart_right - chart_left
    chart_height = chart_bottom - chart_top

    lines = []
    legend = []
    for index, (name, values, color) in enumerate(series):
        if len(values) == 1:
            points = [f"{chart_left},{chart_bottom}"]
        else:
            step = chart_width / (len(values) - 1)
            points = []
            for i, value in enumerate(values):
                x = chart_left + i * step
                y = chart_bottom - ((value - min_v) / span * chart_height)
                points.append(f"{x:.1f},{y:.1f}")
        lines.append(f'<polyline fill="none" stroke="{color}" stroke-width="3" points="{" ".join(points)}" />')
        legend_x = chart_left + index * 92
        legend.append(
            f'<circle cx="{legend_x}" cy="{height - 20}" r="5" fill="{color}" />'
            f'<text x="{legend_x + 10}" y="{height - 15}" font-size="13" fill="#c7d1df">{html.escape(name)}</text>'
        )

    axis = (
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#080b10" />'
        f'<line x1="{chart_left}" y1="{chart_bottom}" x2="{chart_right}" y2="{chart_bottom}" stroke="#303944" />'
        f'<line x1="{chart_left}" y1="{chart_top}" x2="{chart_left}" y2="{chart_bottom}" stroke="#303944" />'
        f'<text x="{chart_left}" y="16" font-size="13" fill="#ff9f1a">{html.escape(unit_label)}</text>'
        f'<text x="4" y="{chart_top + 5}" font-size="11" fill="#8f9bad">{max_v / 10000:,.0f}万</text>'
        f'<text x="4" y="{chart_bottom}" font-size="11" fill="#8f9bad">{min_v / 10000:,.0f}万</text>'
    )
    return (
        f'<svg viewBox="0 0 {width} {height}" role="img" class="chart tall-chart">'
        f"{axis}{''.join(lines)}{''.join(legend)}"
        "</svg>"
    )


def hourly_table(df: pd.DataFrame, columns: list[str], limit: int = 24) -> str:
    header = "".join(f"<th>{html.escape(col)}</th>" for col in columns)
    rows = []
    for _, row in df.head(limit).iterrows():
        cells = "".join(f"<td>{html.escape(str(row[col]))}</td>" for col in columns)
        rows.append(f"<tr>{cells}</tr>")
    return f"<table><thead><tr>{header}</tr></thead><tbody>{''.join(rows)}</tbody></table>"


def metric_card(title: str, value: str, note: str = "") -> str:
    return (
        '<div class="metric-card">'
        f"<span>{html.escape(title)}</span>"
        f"<strong>{html.escape(value)}</strong>"
        f"<small>{html.escape(note)}</small>"
        "</div>"
    )
