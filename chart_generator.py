# charts/chart_generator.py — Tạo 11 biểu đồ PNG (DPI 200, font tiếng Việt)

import os, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker
from matplotlib.gridspec import GridSpec
import numpy as np
import pandas as pd
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (CHART_DPI, CHART_OUT_DIR,
                    COLOR_POSITIVE, COLOR_NEGATIVE, COLOR_NEUTRAL, COLOR_HEADER)

# ── Font setup (DejaVu Sans — hỗ trợ tiếng Việt) ─────────────────
plt.rcParams.update({
    "font.family":       "DejaVu Sans",
    "font.size":         9,
    "axes.titlesize":    11,
    "axes.labelsize":    9,
    "xtick.labelsize":   8,
    "ytick.labelsize":   8,
    "figure.facecolor":  "white",
    "axes.facecolor":    "#F9FAFB",
    "axes.grid":         True,
    "grid.alpha":        0.4,
    "axes.spines.top":   False,
    "axes.spines.right": False,
})

def _save(fig, filename: str) -> str:
    path = os.path.join(CHART_OUT_DIR, filename)
    fig.savefig(path, dpi=CHART_DPI, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    plt.close(fig)
    return path

def _fmt_price(val):
    return f"{val:,.0f}".replace(",", ".")

# ── Biểu đồ 1: Đường giá đóng cửa + Đỉnh/Đáy/Hiện tại ──────────
def chart1_price_line(df: pd.DataFrame, symbol: str) -> str:
    fig, ax = plt.subplots(figsize=(12, 4.5))
    dates  = df["date"]
    closes = df["close"]

    ax.plot(dates, closes, color=COLOR_HEADER, linewidth=1.8, label="Giá đóng cửa")
    ax.fill_between(dates, closes, closes.min() * 0.98,
                    alpha=0.08, color=COLOR_HEADER)

    # Đỉnh
    idx_peak = closes.idxmax()
    ax.annotate(f"Đỉnh\n{_fmt_price(closes[idx_peak])}",
                xy=(dates[idx_peak], closes[idx_peak]),
                xytext=(0, 20), textcoords="offset points",
                ha="center", fontsize=8, color=COLOR_POSITIVE,
                fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=COLOR_POSITIVE, lw=1.2))

    # Đáy
    idx_trough = closes.idxmin()
    ax.annotate(f"Đáy\n{_fmt_price(closes[idx_trough])}",
                xy=(dates[idx_trough], closes[idx_trough]),
                xytext=(0, -30), textcoords="offset points",
                ha="center", fontsize=8, color=COLOR_NEGATIVE,
                fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=COLOR_NEGATIVE, lw=1.2))

    # Hiện tại
    ax.axhline(closes.iloc[-1], color="#6B7280", linewidth=0.9,
               linestyle="--", alpha=0.7)
    ax.text(dates.iloc[-1], closes.iloc[-1],
            f"  {_fmt_price(closes.iloc[-1])}đ", va="center",
            fontsize=8.5, color=COLOR_NEUTRAL, fontweight="bold")

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(
        lambda x, _: f"{x:,.0f}".replace(",", ".")))
    ax.set_title(f"Biểu đồ 1 — Giá đóng cửa {symbol} (01/03/2026 → nay)",
                 fontweight="bold", pad=12)
    ax.set_ylabel("Giá (đồng)")
    ax.legend(loc="upper left", fontsize=8)
    fig.tight_layout()
    return _save(fig, f"{symbol}_chart1_price.png")

# ── Biểu đồ 2: Nến + MA + Volume ────────────────────────────────
def chart2_candle_ma_volume(df: pd.DataFrame, symbol: str) -> str:
    fig = plt.figure(figsize=(13, 7))
    gs  = GridSpec(3, 1, figure=fig, height_ratios=[3, 1, 0.05], hspace=0.05)
    ax_price  = fig.add_subplot(gs[0])
    ax_volume = fig.add_subplot(gs[1], sharex=ax_price)

    dates  = np.arange(len(df))
    closes = df["close"].values
    opens  = df["open"].values
    highs  = df["high"].values
    lows   = df["low"].values

    for i in range(len(df)):
        color = COLOR_POSITIVE if closes[i] >= opens[i] else COLOR_NEGATIVE
        ax_price.plot([dates[i], dates[i]], [lows[i], highs[i]],
                      color=color, linewidth=0.6)
        ax_price.bar(dates[i], abs(closes[i] - opens[i]),
                     bottom=min(closes[i], opens[i]),
                     color=color, width=0.6, alpha=0.85)

    # MA lines
    for col, label, lw, style in [
        ("MA20",  "MA20",  1.4, "-"),
        ("MA50",  "MA50",  1.6, "--"),
        ("MA200", "MA200", 1.8, "-."),
    ]:
        if col in df.columns:
            ax_price.plot(dates, df[col].values, linewidth=lw,
                          linestyle=style, label=label, alpha=0.9)

    ax_price.yaxis.set_major_formatter(mticker.FuncFormatter(
        lambda x, _: f"{x:,.0f}".replace(",", ".")))
    ax_price.set_title(f"Biểu đồ 2 — Nến Nhật + MA20/50/200 + Khối lượng — {symbol}",
                       fontweight="bold", pad=10)
    ax_price.legend(loc="upper left", fontsize=8)
    plt.setp(ax_price.get_xticklabels(), visible=False)

    # Volume bars
    vol_colors = [COLOR_POSITIVE if closes[i] >= opens[i] else COLOR_NEGATIVE
                  for i in range(len(df))]
    ax_volume.bar(dates, df["volume"].values, color=vol_colors, alpha=0.7)
    ax_volume.set_ylabel("Khối lượng")
    ax_volume.yaxis.set_major_formatter(mticker.FuncFormatter(
        lambda x, _: f"{x/1e6:.1f}M"))

    # X-axis labels (mốc thời gian)
    step = max(1, len(df) // 8)
    tick_locs = dates[::step]
    tick_labels = [df["date"].iloc[i].strftime("%m/%Y")
                   for i in range(0, len(df), step)]
    ax_volume.set_xticks(tick_locs)
    ax_volume.set_xticklabels(tick_labels, rotation=30, ha="right")

    fig.tight_layout()
    return _save(fig, f"{symbol}_chart2_candle.png")

# ── Biểu đồ 3: RSI ───────────────────────────────────────────────
def chart3_rsi(df: pd.DataFrame, symbol: str) -> str:
    fig, ax = plt.subplots(figsize=(12, 3))
    dates = df["date"]
    rsi   = df["RSI"]

    ax.plot(dates, rsi, color="#7C3AED", linewidth=1.5, label="RSI(14)")
    ax.axhline(70, color=COLOR_NEGATIVE, linestyle="--", linewidth=1, alpha=0.8, label="Quá mua (70)")
    ax.axhline(30, color=COLOR_POSITIVE, linestyle="--", linewidth=1, alpha=0.8, label="Quá bán (30)")
    ax.axhline(50, color="#9CA3AF", linestyle=":", linewidth=0.8, alpha=0.6)

    ax.fill_between(dates, rsi, 70, where=(rsi >= 70),
                    alpha=0.15, color=COLOR_NEGATIVE, label="Vùng quá mua")
    ax.fill_between(dates, rsi, 30, where=(rsi <= 30),
                    alpha=0.15, color=COLOR_POSITIVE, label="Vùng quá bán")

    # Giá trị RSI hiện tại
    last_rsi = rsi.iloc[-1]
    rsi_color = (COLOR_NEGATIVE if last_rsi >= 70
                 else COLOR_POSITIVE if last_rsi <= 30
                 else COLOR_NEUTRAL)
    ax.text(dates.iloc[-1], last_rsi, f"  RSI: {last_rsi:.1f}",
            va="center", fontsize=9, color=rsi_color, fontweight="bold")

    ax.set_ylim(0, 100)
    ax.set_ylabel("RSI")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))
    ax.set_title(f"Biểu đồ 3 — RSI(14) — {symbol}", fontweight="bold")
    ax.legend(loc="upper left", fontsize=7.5, ncol=3)
    fig.tight_layout()
    return _save(fig, f"{symbol}_chart3_rsi.png")

# ── Biểu đồ 4: MACD ──────────────────────────────────────────────
def chart4_macd(df: pd.DataFrame, symbol: str) -> str:
    fig, ax = plt.subplots(figsize=(12, 3))
    dates = df["date"]

    ax.plot(dates, df["MACD"],        color="#2563EB", linewidth=1.4, label="MACD")
    ax.plot(dates, df["MACD_Signal"], color="#F59E0B", linewidth=1.2,
            linestyle="--", label="Signal")

    hist = df["MACD_Histogram"]
    colors = [COLOR_POSITIVE if v >= 0 else COLOR_NEGATIVE for v in hist]
    ax.bar(dates, hist, color=colors, alpha=0.7, width=pd.Timedelta(days=1), label="Histogram")
    ax.axhline(0, color="#6B7280", linewidth=0.8)

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))
    ax.set_title(f"Biểu đồ 4 — MACD(12,26,9) — {symbol}", fontweight="bold")
    ax.legend(loc="upper left", fontsize=8)
    fig.tight_layout()
    return _save(fig, f"{symbol}_chart4_macd.png")

# ── Biểu đồ 5: Phân bổ tin tức ───────────────────────────────────
def chart5_news_pie(news_items: list, symbol: str) -> str:
    counts = {"TÍCH CỰC": 0, "TIÊU CỰC": 0, "TRUNG LẬP": 0}
    for n in news_items:
        counts[n.get("sentiment", "TRUNG LẬP")] += 1

    labels  = [k for k, v in counts.items() if v > 0]
    values  = [v for v in counts.values() if v > 0]
    colors  = {
        "TÍCH CỰC": COLOR_POSITIVE,
        "TIÊU CỰC": COLOR_NEGATIVE,
        "TRUNG LẬP": "#6B7280",
    }
    pie_colors = [colors[l] for l in labels]

    fig, ax = plt.subplots(figsize=(5, 4))
    wedges, texts, autotexts = ax.pie(
        values, labels=labels, colors=pie_colors,
        autopct="%1.0f%%", startangle=140,
        textprops={"fontsize": 9},
        wedgeprops={"linewidth": 1, "edgecolor": "white"},
    )
    for at in autotexts:
        at.set_fontweight("bold")
        at.set_fontsize(9)

    ax.set_title(f"Biểu đồ 5 — Phân bổ tin tức {symbol}", fontweight="bold", pad=10)
    fig.tight_layout()
    return _save(fig, f"{symbol}_chart5_news.png")

# ── Biểu đồ 6: Doanh thu & Lợi nhuận theo quý ───────────────────
def chart6_financials(income_rows: list, symbol: str) -> str:
    if not income_rows:
        return None
    # Lọc bỏ dòng 'Cả năm' để các thanh quý hiển thị đồng nhất trên cùng thang đo
    chart_rows = [r for r in income_rows if "cả năm" not in str(r.get("period", "")).lower() and "fy" not in str(r.get("period", "")).lower()]
    if not chart_rows:
        chart_rows = income_rows
    periods = [r.get("period", f"Q{i+1}") for i, r in enumerate(chart_rows)]
    revenues    = [r.get("revenue") or 0 for r in chart_rows]
    net_profits = [r.get("net_profit") or 0 for r in chart_rows]

    x = np.arange(len(periods))
    w = 0.35

    fig, ax = plt.subplots(figsize=(10, 4.5))
    bars1 = ax.bar(x - w/2, [v/1e9 for v in revenues],
                   w, label="Doanh thu (tỷ)", color=COLOR_HEADER, alpha=0.85)
    bars2 = ax.bar(x + w/2, [v/1e9 for v in net_profits],
                   w, label="LNST (tỷ)",
                   color=[COLOR_POSITIVE if v >= 0 else COLOR_NEGATIVE
                          for v in net_profits], alpha=0.85)

    for bar in [*bars1, *bars2]:
        h = bar.get_height()
        if h != 0:
            ax.text(bar.get_x() + bar.get_width()/2,
                    h + abs(h)*0.02, f"{h:,.0f}".replace(",", "."),
                    ha="center", va="bottom", fontsize=7)

    ax.set_xticks(x)
    ax.set_xticklabels(periods, rotation=30, ha="right")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(
        lambda x, _: f"{x:,.0f}".replace(",", ".")))
    ax.set_ylabel("Tỷ đồng")
    ax.set_title(f"Biểu đồ 6 — Doanh thu & LNST theo quý — {symbol}", fontweight="bold")
    ax.legend(fontsize=8)
    fig.tight_layout()
    return _save(fig, f"{symbol}_chart6_financials.png")

# ── Biểu đồ 7: Xu hướng ROE & ROA ───────────────────────────────
def chart7_roe_roa(ratio_data: dict, symbol: str) -> str:
    roe_hist = ratio_data.get("roe_history", [])
    roa_hist = ratio_data.get("roa_history", [])
    
    # Nếu không có history, dùng giá trị đơn lẻ hiện tại để vẽ bar chart
    if not roe_hist and not roa_hist:
        roe = ratio_data.get("roe")
        roa = ratio_data.get("roa")
        if not roe and not roa:
            return None
        
        fig, ax = plt.subplots(figsize=(8, 4))
        labels, vals, colors = [], [], []
        if roe is not None:
            labels.append("ROE (%)")
            vals.append(round(float(roe), 3))
            colors.append(COLOR_POSITIVE)
        if roa is not None:
            labels.append("ROA (%)")
            vals.append(round(float(roa), 3))
            colors.append(COLOR_HEADER)
        
        bars = ax.bar(labels, vals, color=colors, width=0.4, edgecolor="white", linewidth=1)
        for bar, val in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                    f"{val:.1f}%", ha="center", va="bottom", fontweight="bold", fontsize=10)
        ax.set_ylabel("% (%)")
        ax.set_title(f"Biểu đồ 7 — ROE & ROA hiện tại — {symbol}", fontweight="bold")
        ax.set_ylim(0, max(vals) * 1.3 if vals else 30)
        fig.tight_layout()
        return _save(fig, f"{symbol}_chart7_roe_roa.png")
    
    periods = [r["period"] for r in (roe_hist or roa_hist)]
    roe_vals = [r["value"] for r in roe_hist]
    roa_vals = [r["value"] for r in roa_hist]

    fig, ax = plt.subplots(figsize=(10, 4))
    if roe_vals:
        ax.plot(periods, roe_vals, marker="o", color=COLOR_POSITIVE,
                linewidth=1.8, label="ROE (%)", markersize=5)
    if roa_vals:
        ax.plot(periods, roa_vals, marker="s", color=COLOR_HEADER,
                linewidth=1.8, label="ROA (%)", linestyle="--", markersize=5)

    ax.set_xticks(range(len(periods)))
    ax.set_xticklabels(periods, rotation=30, ha="right")
    ax.set_ylabel("% (%)")
    ax.set_title(f"Biểu đồ 7 — Xu hướng ROE & ROA — {symbol}", fontweight="bold")
    ax.legend(fontsize=8)
    fig.tight_layout()
    return _save(fig, f"{symbol}_chart7_roe_roa.png")

# ── Biểu đồ 8: Giá mục tiêu CTCK ──────────────────────────────────
def chart8_target_prices(ctck_data: list, current_price: float, symbol: str) -> str:
    if not ctck_data:
        return None

    # Lọc các mức giá mục tiêu hợp lệ
    valid_data = [d for d in ctck_data if d.get("target") and float(d.get("target", 0)) > 0]
    if not valid_data:
        return None

    n = len(valid_data)
    targets = [float(d["target"]) for d in valid_data]
    
    # Tạo nhãn phân biệt rõ ràng cho từng cột, tránh trường hợp tên CTCK trùng nhau bị dồn vào 1 cột
    labels = []
    seen = {}
    for idx, d in enumerate(valid_data, 1):
        b_name = d.get("name", f"CTCK {idx}").replace(" Research", "").replace(" Securities", "")
        date_str = d.get("date", "")
        # Nếu trùng tên CTCK thì thêm ngày hoặc số thứ tự
        if b_name in seen:
            seen[b_name] += 1
            labels.append(f"{b_name} ({date_str})" if date_str else f"{b_name} #{seen[b_name]}")
        else:
            seen[b_name] = 1
            labels.append(f"{b_name}\n({date_str})" if date_str else b_name)

    fig, ax = plt.subplots(figsize=(max(8, n * 1.8), 4.5))
    x = np.arange(n)
    colors = [COLOR_POSITIVE if t >= current_price else COLOR_NEGATIVE for t in targets]
    
    # Vẽ từng cột độc lập theo vị trí số thực x
    bars = ax.bar(x, targets, color=colors, alpha=0.85, width=0.45, edgecolor="none", zorder=3)

    # Đường tham chiếu thị giá hiện tại
    ax.axhline(current_price, color=COLOR_NEUTRAL, linewidth=1.5,
               linestyle="--", label=f"Thị giá: {_fmt_price(current_price)}đ", zorder=4)

    # Đặt khoảng giới hạn trục Y thoáng, tránh chữ trên đầu cột bị tràn mép biểu đồ
    max_val = max(max(targets), current_price)
    ax.set_ylim(0, max_val * 1.22)

    for bar, val, d in zip(bars, targets, valid_data):
        h = bar.get_height()
        reco = d.get("recommendation", "")
        txt = f"{_fmt_price(val)}đ\n({reco})" if reco else f"{_fmt_price(val)}đ"
        ax.text(bar.get_x() + bar.get_width() / 2, h + max_val * 0.02,
                txt, ha="center", va="bottom", fontsize=8.5, fontweight="bold",
                color="#065F46" if val >= current_price else "#991B1B")

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=9, fontweight="bold")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(
        lambda y, _: f"{y:,.0f}".replace(",", ".")))
    ax.set_ylabel("Giá (VNĐ)", fontsize=9)
    ax.set_title(f"Biểu đồ 8 — Giá mục tiêu CTCK vs Thị giá — {symbol}", fontsize=11, fontweight="bold", pad=12)
    ax.grid(axis="y", linestyle=":", alpha=0.6, zorder=0)
    ax.legend(loc="upper right", fontsize=8.5, framealpha=0.9)
    fig.tight_layout()
    return _save(fig, f"{symbol}_chart8_targets.png")

# ── Biểu đồ 9: So sánh định giá chéo (P/E, P/B, ROE) ────────────
def chart9_peer_valuation(peer_data: list, symbol: str) -> str:
    if not peer_data:
        return None
    metrics = ["P/E", "P/B", "ROE (%)", "Hệ số PEG"]
    n = len(peer_data)
    x = np.arange(len(metrics))
    w = 0.7 / n

    fig, ax = plt.subplots(figsize=(9, 4.5))
    cmap = plt.cm.Set2.colors

    for i, company in enumerate(peer_data):
        vals = [company.get("P/E"), company.get("P/B"), company.get("ROE (%)"), company.get("Hệ số PEG")]
        vals = [v if v is not None else 0 for v in vals]
        color = cmap[i % len(cmap)]
        # Highlight mã chính
        sym_name = company.get("Mã / Sàn", "").split(" / ")[0] if company.get("Mã / Sàn") else ""
        alpha = 1.0 if sym_name == symbol else 0.7
        edge  = "black" if sym_name == symbol else "none"
        ax.bar(x + i*w, vals, w, label=sym_name,
               color=color, alpha=alpha, edgecolor=edge, linewidth=1.2)

    ax.set_xticks(x + w*(n-1)/2)
    ax.set_xticklabels(metrics)
    ax.set_title(f"Biểu đồ 9 — So sánh định giá chéo — {symbol} vs đối thủ", fontweight="bold")
    ax.legend(fontsize=8)
    fig.tight_layout()
    return _save(fig, f"{symbol}_chart9_peers.png")

# ── Biểu đồ 10: Hiệu suất giá tích lũy ─────────────────────────
def chart10_performance(perf_data: dict, symbol: str) -> str:
    """
    perf_data = {symbol: pd.Series(indexed by date, values = cumulative return %)}
    """
    if not perf_data:
        return None
    fig, ax = plt.subplots(figsize=(11, 4.5))
    colors_list = [COLOR_HEADER, COLOR_POSITIVE, COLOR_NEGATIVE, "#F59E0B", "#7C3AED"]

    for i, (sym, series) in enumerate(perf_data.items()):
        if series is None or series.empty:
            continue
        lw = 2.2 if sym == symbol else 1.3
        ax.plot(series.index, series.values,
                label=sym, linewidth=lw,
                color=colors_list[i % len(colors_list)])

    ax.axhline(0, color="#9CA3AF", linewidth=0.8, linestyle=":")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:+.1f}%"))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))
    ax.set_title(f"Biểu đồ 10 — Hiệu suất sinh lời tích lũy từ 01/03/2026", fontweight="bold")
    ax.set_ylabel("% thay đổi")
    ax.legend(fontsize=8)
    fig.tight_layout()
    return _save(fig, f"{symbol}_chart10_perf.png")

# ── Biểu đồ 11: Radar Chart (Spider) 5 trục ─────────────────────
def chart11_radar(scores: dict, symbol: str) -> str:
    clean_scores = {k: float(v) for k, v in scores.items() if not k.startswith("_") and isinstance(v, (int, float))}
    categories = list(clean_scores.keys())
    N = len(categories)
    if N == 0:
        return None
    values = list(clean_scores.values())
    values += values[:1]  # close the polygon

    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(6, 5.5),
                           subplot_kw=dict(polar=True))

    ax.plot(angles, values, color=COLOR_HEADER, linewidth=2, linestyle="solid")
    ax.fill(angles, values, color=COLOR_HEADER, alpha=0.18)

    # Điểm tham chiếu (5/10)
    ref = [5] * N + [5]
    ax.plot(angles, ref, color="#9CA3AF", linewidth=1,
            linestyle="--", alpha=0.7, label="Điểm trung bình (5)")
    ax.fill(angles, ref, color="#9CA3AF", alpha=0.05)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=9, fontweight="bold")
    ax.set_ylim(0, 10)
    ax.set_yticks([2, 4, 6, 8, 10])
    ax.set_yticklabels(["2", "4", "6", "8", "10"], fontsize=7)
    ax.yaxis.set_tick_params(labelsize=7)

    # Ghi điểm lên từng đỉnh
    for angle, val, cat in zip(angles[:-1], values[:-1], categories):
        ax.text(angle, val + 0.5, f"{val}", ha="center", va="center",
                fontsize=9, color=COLOR_HEADER, fontweight="bold")

    ax.set_title(f"Biểu đồ 11 — Đánh giá đa chiều\n{symbol}",
                 fontweight="bold", pad=20, fontsize=10)
    ax.legend(loc="lower right", fontsize=7.5)
    fig.tight_layout()
    return _save(fig, f"{symbol}_chart11_radar.png")
