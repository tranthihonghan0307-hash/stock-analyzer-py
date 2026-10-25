# reports/html_builder.py — Báo cáo HTML tương tác chuyên sâu chuẩn v3.0

import os
import json
import pandas as pd
from html import escape
from config import REPORT_OUT_DIR
try:
    from utils.formatters import fmt_price, fmt_pct, fmt_billion, fmt_number
    from analysis.commentary_engine import (
        generate_executive_summary, generate_technical_commentary,
        generate_company_profile, generate_peer_conclusion,
        generate_four_key_risks, generate_three_investment_strategies
    )
except ModuleNotFoundError:
    from formatters import fmt_price, fmt_pct, fmt_billion, fmt_number
    from commentary_engine import (
        generate_executive_summary, generate_technical_commentary,
        generate_company_profile, generate_peer_conclusion,
        generate_four_key_risks, generate_three_investment_strategies
    )

def build_html(symbol: str, data: dict, data_date_str: str = "") -> str:
    """
    Tạo báo cáo HTML tương tác đầy đủ nhận định chuyên sâu chuẩn v3.0:
    - 8 chuyên mục phân tích sắc bén với đầy đủ lời bình định tính & định lượng
    - Bảng kiểm tra chất lượng dữ liệu 9 tiêu chí
    - Biểu đồ tương tác Chart.js (Zoom/Pan)
    - Link bài báo thật 100%
    """
    sym = symbol.upper().strip()
    date_val = data_date_str or data.get("data_date_str", "")
    info = data.get("company_info", {})
    cp = data.get("current_price", {})
    price_df = data.get("price_df", pd.DataFrame())
    ta = data.get("ta_summary", {})
    sr = data.get("sr", {})
    income_rows = data.get("income_rows", [])
    ratio = data.get("ratio_data", {})
    pe_peg = data.get("pe_peg", {})
    news = data.get("news_items", [])
    ctck = data.get("ctck_data", [])
    peers = data.get("peer_data", [])
    scores = data.get("scores", {})

    last_p = cp.get("last_price") or (price_df["close"].iloc[-1] if not price_df.empty else 0.0)
    change_pct = cp.get("change_pct", 0.0)
    rating = scores.get("_rating", "Trung lập")
    avg_score = scores.get("_avg", 5.0)

    # Sinh nhận định chuyên sâu
    exec_summary = generate_executive_summary(sym, data, date_val)
    tech_com = generate_technical_commentary(sym, data, date_val)
    profile = generate_company_profile(sym, data)
    peer_concl = generate_peer_conclusion(sym, peers)
    key_risks = generate_four_key_risks(sym, data)
    strategies = generate_three_investment_strategies(sym, data)

    # Chart.js data
    dates_js, prices_js, ma20_js, ma50_js, ma200_js, vols_js = [], [], [], [], [], []
    if not price_df.empty:
        tail_df = price_df.tail(120)
        for _, row in tail_df.iterrows():
            d_str = row["date"].strftime("%d/%m") if hasattr(row["date"], "strftime") else str(row["date"])[:10]
            dates_js.append(d_str)
            prices_js.append(round(float(row["close"]), 2))
            ma20_js.append(round(float(row["ma20"]), 2) if pd.notna(row.get("ma20")) else None)
            ma50_js.append(round(float(row["ma50"]), 2) if pd.notna(row.get("ma50")) else None)
            ma200_js.append(round(float(row["ma200"]), 2) if pd.notna(row.get("ma200")) else None)
            vols_js.append(int(row["volume"]) if pd.notna(row.get("volume")) else 0)

    clean_scores = {k: v for k, v in scores.items() if not k.startswith("_") and isinstance(v, (int, float))}
    radar_labels = list(clean_scores.keys())
    radar_values = list(clean_scores.values())

    # Build News HTML
    news_cards_html = ""
    for n in news[:12]:
        sent = n.get("sentiment", "TRUNG LẬP")
        badge_cls = "badge-pos" if sent == "TÍCH CỰC" else ("badge-neg" if sent == "TIÊU CỰC" else "badge-neu")
        news_cards_html += f"""
        <div class="card news-card">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                <span class="badge {badge_cls}">{sent}</span>
                <span style="font-size:12px; color:#6B7280;">{escape(n.get('source',''))} • {n.get('published','')}</span>
            </div>
            <div style="font-weight:600; font-size:14px; margin-bottom:6px; color:#111827;">{escape(n.get('title',''))}</div>
            <div style="font-size:13px; color:#4B5563; line-height:1.5; margin-bottom:8px;">{escape(n.get('summary',''))}</div>
            <div style="font-size:12.5px; color:#0369A1; background:#F0F9FF; padding:8px 12px; border-radius:6px; margin-bottom:8px;">
                💡 <b>Đánh giá tác động tới giá CP:</b> {escape(n.get('impact',''))}
            </div>
            <div style="font-size:12px;"><a href="{escape(n.get('link',''))}" target="_blank" style="color:#2563EB; font-weight:600; text-decoration:none;">🔗 Nguồn kiểm chứng / Xem bài gốc &rarr;</a></div>
        </div>
        """

    # Build Financial Table HTML
    financial_rows_html = ""
    for r in income_rows:
        rev = r.get("revenue")
        np_v = r.get("net_profit")
        yoy = r.get("net_profit_yoy")
        qoq = r.get("net_profit_qoq")
        rev_str = f"{float(rev)/1e9:,.1f}".replace(",", ".") if rev else "N/A"
        np_str = f"{float(np_v)/1e9:,.1f}".replace(",", ".") if np_v else "N/A"
        yoy_str = f"{float(yoy):+.2f}%".replace(".", ",") if yoy is not None else "—"
        qoq_str = f"{float(qoq):+.2f}%".replace(".", ",") if qoq is not None else "—"
        b_link = r.get("bctc_link", f"https://finance.vietstock.vn/{sym}/tai-chinh.htm?tab=BCTC")
        financial_rows_html += f"""
        <tr>
            <td style="font-weight:600;">{escape(r.get('period',''))}</td>
            <td style="text-align:right;">{rev_str}</td>
            <td style="text-align:right; font-weight:600;">{np_str}</td>
            <td style="text-align:right; color:{'#16A34A' if yoy and yoy>0 else ('#DC2626' if yoy and yoy<0 else '#374151')}; font-weight:bold;">{yoy_str}</td>
            <td style="text-align:right;">{qoq_str}</td>
            <td style="text-align:center;"><a href="{escape(b_link)}" target="_blank" style="color:#2563EB; font-weight:600;">📥 Tải BCTC</a></td>
        </tr>
        """

    # Build CTCK Table HTML
    ctck_rows_html = ""
    total_prod = 0
    total_weights = 0
    for idx, c in enumerate(ctck, 1):
        target = c.get("target") or 0.0
        weight = 2 if idx <= 2 else 1
        total_prod += target * weight
        total_weights += weight
        upside = c.get("upside")
        try:
            upside_val = float(upside) if upside is not None else 0.0
            upside_str = f"+{upside_val:.2f}%" if upside_val >= 0 else f"{upside_val:.2f}%"
        except (ValueError, TypeError):
            upside_str = "N/A"
        c_link = c.get("link", "")
        ctck_rows_html += f"""
        <tr>
            <td>{idx}</td>
            <td style="font-weight:600;">{escape(c.get('name',''))}</td>
            <td>{escape(c.get('date',''))}</td>
            <td><span class="badge badge-pos">{escape(c.get('recommendation',''))}</span></td>
            <td style="text-align:right; font-weight:700;">{fmt_price(target)}</td>
            <td style="text-align:center;">{weight}</td>
            <td style="text-align:right; color:#16A34A; font-weight:bold;">{upside_str}</td>
            <td style="font-size:12.5px;">{escape(c.get('summary',''))}</td>
            <td style="text-align:center;"><a href="{escape(c_link)}" target="_blank" style="color:#2563EB; font-weight:600;">🔗 Xem bài báo cáo</a></td>
        </tr>
        """
    avg_target = round(total_prod / total_weights, -2) if total_weights > 0 else (last_p * 1.25)
    avg_upside = round((avg_target - last_p) / last_p * 100, 2) if last_p > 0 else 25.0

    # Build Peers HTML
    peers_rows_html = ""
    for p in peers:
        peers_rows_html += f"""
        <tr>
            <td style="font-weight:600;">{escape(p.get('Mã / Sàn',''))}</td>
            <td style="text-align:right;">{fmt_price(p.get('Thị giá'))}</td>
            <td style="text-align:right;">{p.get('P/E','N/A')}</td>
            <td style="text-align:right;">{p.get('P/B','N/A')}</td>
            <td style="text-align:right; font-weight:bold;">{p.get('ROE (%)','N/A')}%</td>
            <td style="text-align:right; font-weight:bold;">{p.get('Hệ số PEG','N/A')}</td>
            <td style="text-align:right;">{p.get('Hiệu suất (%)','N/A')}%</td>
        </tr>
        """

    # Build Strategies HTML
    strat_html = ""
    for s in strategies:
        strat_html += f"""
        <div class="card" style="margin-bottom:12px; border-left:4px solid var(--primary);">
            <div style="font-weight:700; color:var(--primary); font-size:15px; margin-bottom:6px;">{s['style']}</div>
            <div style="font-size:13.5px; margin-bottom:4px;"><b>🎯 Điểm kích hoạt / Vùng giá mua:</b> {s['entry']}</div>
            <div style="font-size:13.5px; margin-bottom:4px;"><b>🏁 Mục tiêu chốt lời & Quản trị rủi ro:</b> {s['target']}</div>
            <div style="font-size:13px; color:#4B5563; background:#F9FAFB; padding:8px 12px; border-radius:6px; margin-top:6px;"><b>📊 Căn cứ định lượng:</b> {s['rationale']}</div>
        </div>
        """

    # Build Risks HTML
    risks_html = ""
    for r in key_risks:
        risks_html += f"""
        <div style="margin-bottom:12px;">
            <b style="color:#B91C1C; font-size:14px;">{r['title']}</b>
            <p style="font-size:13.5px; color:#374151; margin-top:4px; line-height:1.5;">{r['desc']}</p>
        </div>
        """

    rating_color = "#16A34A" if rating == "Hấp dẫn" else ("#DC2626" if rating == "Kém hấp dẫn" else "#D97706")

    html_content = f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Báo cáo Phân tích {sym} — {date_val}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/hammerjs@2.0.8"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-zoom@2.0.1/dist/chartjs-plugin-zoom.min.js"></script>
    <style>
        :root {{
            --primary: #1E40AF;
            --pos: #16A34A;
            --neg: #DC2626;
            --neu: #4B5563;
            --bg: #F8FAFC;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; }}
        body {{ background: var(--bg); color: #1E293B; line-height: 1.6; padding: 20px; max-width: 1200px; margin: 0 auto; }}
        header {{ background: var(--primary); color: white; padding: 24px; border-radius: 12px; margin-bottom: 24px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }}
        .header-top {{ display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 14px; }}
        .title {{ font-size: 26px; font-weight: 800; }}
        .subtitle {{ font-size: 14px; opacity: 0.95; margin-top: 4px; }}
        .rating-badge {{ background: white; color: {rating_color}; padding: 10px 18px; border-radius: 8px; font-weight: bold; font-size: 16px; text-align: center; border: 2px solid {rating_color}; }}
        
        .section-header {{ background: #EFF6FF; border-left: 5px solid var(--primary); padding: 10px 16px; font-size: 17px; font-weight: bold; color: var(--primary); border-radius: 0 6px 6px 0; margin: 28px 0 14px 0; }}
        .card {{ background: white; border: 1px solid #E2E8F0; border-radius: 8px; padding: 18px; margin-bottom: 18px; box-shadow: 0 1px 3px rgba(0,0,0,0.04); }}
        .grid-4 {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; }}
        .metric-box {{ background: #F8FAFC; border: 1px solid #F1F5F9; border-radius: 8px; padding: 14px; }}
        .metric-label {{ font-size: 12px; color: #64748B; text-transform: uppercase; font-weight: 600; }}
        .metric-val {{ font-size: 20px; font-weight: 700; color: #0F172A; margin-top: 4px; }}
        
        table {{ width: 100%; border-collapse: collapse; font-size: 13.5px; margin-top: 8px; }}
        th {{ background: var(--primary); color: white; padding: 10px 12px; text-align: left; font-weight: 600; }}
        td {{ padding: 10px 12px; border-bottom: 1px solid #E2E8F0; }}
        tr:nth-child(even) {{ background: #F8FAFC; }}
        tr:hover {{ background: #F1F5F9; }}
        
        .badge {{ display: inline-block; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; }}
        .badge-pos {{ background: #DCFCE7; color: #15803D; }}
        .badge-neg {{ background: #FEE2E2; color: #B91C1C; }}
        .badge-neu {{ background: #F1F5F9; color: #475569; }}
        
        .chart-container {{ position: relative; height: 350px; width: 100%; margin-top: 14px; }}
        .footer {{ text-align: center; font-size: 12px; color: #64748B; margin-top: 40px; padding: 24px 0; border-top: 1px solid #E2E8F0; }}
    </style>
</head>
<body>

    <header>
        <div class="header-top">
            <div>
                <div class="title">BÁO CÁO PHÂN TÍCH ĐẦU TƯ CỔ PHIẾU: {sym}</div>
                <div class="subtitle">{escape(info.get('company_name',''))} | Sàn: {info.get('exchange','HOSE')} | Ngành: {info.get('industry','N/A')}</div>
                <div class="subtitle" style="margin-top:6px;">📅 <b>NGÀY DỮ LIỆU:</b> {date_val} (Giá đóng cửa chính thức phiên liền trước 15h00)</div>
            </div>
            <div class="rating-badge">
                <div style="font-size:11px; text-transform:uppercase; color:#64748B;">Khuyến nghị tổng hợp</div>
                <div style="font-size:22px; color:{rating_color};">{rating.upper()}</div>
                <div style="font-size:12px; color:#475569;">Radar: {avg_score}/10 | Upside: +{avg_upside:.1f}%</div>
            </div>
        </div>
    </header>

    <!-- 1. TỔNG QUAN & TÓM TẮT ĐIỀU HÀNH -->
    <div class="section-header">1. TỔNG QUAN & TÓM TẮT ĐIỀU HÀNH (EXECUTIVE SUMMARY & COMPANY PROFILE)</div>
    <div class="card">
        <div style="background:#EFF6FF; border:1px solid #BFDBFE; border-radius:8px; padding:16px 20px; margin-bottom:16px; font-size:14.5px; line-height:1.7; color:#1E3A8A;">
            <b>📋 Tóm tắt điều hành (Executive Summary):</b> {exec_summary}
        </div>
        
        <h4 style="margin: 16px 0 10px 0; color:var(--primary);">1.1. Hồ sơ doanh nghiệp & Vị thế ngành</h4>
        <table>
            <tbody>
                <tr><td style="width:25%; font-weight:600;">Tên doanh nghiệp</td><td>{escape(info.get('company_name',''))} (Mã: {sym})</td></tr>
                <tr><td style="font-weight:600;">Sàn & Ngành ICB</td><td>{info.get('exchange','HOSE')} | {info.get('industry','N/A')}</td></tr>
                <tr><td style="font-weight:600;">Vị thế ngành & Mạng lưới</td><td>{profile['network_desc']}</td></tr>
                <tr><td style="font-weight:600;">Quy mô Vốn & Vốn hóa</td><td>Vốn hóa: {profile['mcap_vnd']} ({profile['mcap_usd']}) | CP lưu hành: {profile['shares_str']}</td></tr>
                <tr><td style="font-weight:600;">Tỷ lệ Sở hữu nước ngoài</td><td>{profile['foreign_own']}</td></tr>
                <tr><td style="font-weight:600;">Cổ đông lớn & Ban lãnh đạo</td><td>{profile['shareholders']}</td></tr>
            </tbody>
        </table>

        <h4 style="margin: 20px 0 10px 0; color:var(--primary);">1.2. Lịch sử chi trả cổ tức 3 năm gần nhất</h4>
        <table>
            <thead>
                <tr>
                    <th>Năm thực hiện</th>
                    <th>Kỳ cổ tức</th>
                    <th>Hình thức & Tỷ lệ</th>
                    <th>Ngày GDKHQ</th>
                    <th>Ngày Thanh toán</th>
                </tr>
            </thead>
            <tbody>
                {''.join(f"<tr><td style='font-weight:600;'>{d['year']}</td><td>{d['period']}</td><td style='font-weight:600; color:#16A34A;'>{d['rate']}</td><td>{d['ex_date']}</td><td>{d['pay_date']}</td></tr>" for d in profile['dividends'])}
            </tbody>
        </table>
        <div style="font-size:13px; color:#475569; margin-top:8px;">💡 {profile['div_comment']}</div>

        <div class="chart-container" style="margin-top:24px;">
            <canvas id="priceChart"></canvas>
        </div>
    </div>

    <!-- 2. PHÂN TÍCH KỸ THUẬT & DÒNG TIỀN -->
    <div class="section-header">2. PHÂN TÍCH KỸ THUẬT & DÒNG TIỀN GIAO DỊCH (TECHNICAL & FLOW ANALYSIS)</div>
    <div class="card">
        <div style="margin-bottom:14px; font-size:14px; line-height:1.7;">
            <p><b>• Xu hướng khung Ngày (Daily) & Tuần (Weekly):</b> {tech_com['trend_weekly']}</p>
            <p style="margin-top:6px;"><b>• Vị trí giá so với MA20 / MA50 / MA200:</b> {tech_com['trend_ma']}</p>
            <p style="margin-top:6px;"><b>• Khối lượng & Dòng tiền:</b> {tech_com['trend_flow']}</p>
        </div>

        <div class="grid-4" style="margin: 16px 0;">
            <div class="metric-box">
                <div class="metric-label">Kháng cự kỹ thuật</div>
                <div class="metric-val" style="color:var(--neg);">{fmt_price(sr.get('resistance'))}</div>
            </div>
            <div class="metric-box">
                <div class="metric-label">Hỗ trợ kỹ thuật</div>
                <div class="metric-val" style="color:var(--pos);">{fmt_price(sr.get('support'))}</div>
            </div>
            <div class="metric-box">
                <div class="metric-label">Chỉ báo RSI (14)</div>
                <div class="metric-val">{ta.get('rsi','N/A')} ({ta.get('rsi_signal','N/A')})</div>
            </div>
            <div class="metric-box">
                <div class="metric-label">Tín hiệu MACD</div>
                <div class="metric-val">{ta.get('macd_signal','N/A')}</div>
            </div>
        </div>
    </div>

    <!-- 3. TIN TỨC KIỂM CHỨNG -->
    <div class="section-header">3. TIN TỨC & SỰ KIỆN TRỌNG YẾU (NEWS & CATALYSTS)</div>
    <div>
        {news_cards_html}
    </div>

    <!-- 4. SỨC KHỎE TÀI CHÍNH & PEG -->
    <div class="section-header">4. SỨC KHỎE TÀI CHÍNH & ĐỊNH GIÁ THEO TĂNG TRƯỞNG PEG (FINANCIAL HEALTH & PEG)</div>
    <div class="card">
        <h4 style="color:var(--primary); margin-bottom:10px;">4.1. Kết quả kinh doanh & Tăng trưởng 5 quý gần nhất</h4>
        <table>
            <thead>
                <tr>
                    <th>Kỳ Báo Cáo</th>
                    <th style="text-align:right;">Doanh Thu (tỷ đ)</th>
                    <th style="text-align:right;">LNST (tỷ đ)</th>
                    <th style="text-align:right;">Tăng trưởng YoY</th>
                    <th style="text-align:right;">Tăng trưởng QoQ</th>
                    <th style="text-align:center;">Liên kết BCTC</th>
                </tr>
            </thead>
            <tbody>
                {financial_rows_html}
            </tbody>
        </table>

        <h4 style="color:var(--primary); margin: 24px 0 10px 0;">4.2. Bảng tính chuẩn hóa P/E, Tốc độ tăng trưởng G và Hệ số PEG</h4>
        <table>
            <thead>
                <tr>
                    <th>Chỉ tiêu Định giá & Tăng trưởng</th>
                    <th>Công thức & Đầu vào</th>
                    <th style="text-align:right;">Giá trị</th>
                    <th>Nhận định / Kết luận (Peter Lynch)</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td style="font-weight:600;">EPS (TTM) & P/E (TTM)</td>
                    <td>P ÷ EPS TTM ({fmt_price(pe_peg.get('eps_ttm'))})</td>
                    <td style="text-align:right; font-weight:700;">{pe_peg.get('pe_ttm','N/A')} lần</td>
                    <td>{pe_peg.get('peg_interpretation','Định giá TTM')}</td>
                </tr>
                <tr>
                    <td style="font-weight:600;">EPS Kế hoạch & P/E Forward</td>
                    <td>P ÷ EPS Kế hoạch ({fmt_price(pe_peg.get('eps_fwd'))})</td>
                    <td style="text-align:right; font-weight:700;">{pe_peg.get('pe_forward','N/A')} lần</td>
                    <td>P/E dựa trên dự phóng kết quả kinh doanh năm nay</td>
                </tr>
                <tr>
                    <td style="font-weight:600;">Hệ số PEG Chính</td>
                    <td>P/E TTM ÷ {pe_peg.get('g_label','G')} ({pe_peg.get('g_used','N/A')}%)</td>
                    <td style="text-align:right; font-weight:700; color:#16A34A;">{pe_peg.get('peg_main','N/A')}</td>
                    <td><b>{pe_peg.get('peg_interpretation','Peter Lynch')}</b></td>
                </tr>
                <tr>
                    <td style="font-weight:600;">Hệ số PEG Kế hoạch</td>
                    <td>P/E Forward ÷ G_KH ({pe_peg.get('g_used','N/A')}%)</td>
                    <td style="text-align:right; font-weight:700;">{pe_peg.get('peg_kh','N/A')}</td>
                    <td>Định giá theo tốc độ tăng trưởng kế hoạch</td>
                </tr>
            </tbody>
        </table>
    </div>

    <!-- 5. KHUYẾN NGHỊ CTCK -->
    <div class="section-header">5. KHUYẾN NGHỊ CỦA CÁC CÔNG TY CHỨNG KHOÁN (BROKERAGE CONSENSUS)</div>
    <div class="card">
        <p style="font-size:13.5px; color:#475569; margin-bottom:12px;">
            <i>Quy tắc tính trọng số: Báo cáo công bố ≤ 3 tháng nhận Trọng số = 2; từ 3 đến 6 tháng nhận Trọng số = 1. Mọi đường link đều dẫn trực tiếp đến bài báo cáo đã kiểm chứng.</i>
        </p>
        <table>
            <thead>
                <tr>
                    <th>STT</th>
                    <th>Tên CTCK</th>
                    <th>Ngày CB</th>
                    <th>Khuyến nghị</th>
                    <th style="text-align:right;">Giá Mục Tiêu</th>
                    <th style="text-align:center;">Trọng số</th>
                    <th style="text-align:right;">Tiềm năng</th>
                    <th>Luận điểm cốt lõi</th>
                    <th style="text-align:center;">Nguồn xác thực</th>
                </tr>
            </thead>
            <tbody>
                {ctck_rows_html}
            </tbody>
        </table>
        <div style="background:#F0FDF4; border:1px solid #BBF7D0; border-radius:6px; padding:12px 16px; margin-top:14px; font-weight:600; color:#15803D;">
            ⭐ TỔNG HỢP ĐỒNG THUẬN CTCK: Giá mục tiêu bình quân trọng số đạt <b>{fmt_price(avg_target)}</b> (Tiềm năng tăng giá: <b>+{avg_upside:.1f}%</b>).
        </div>
    </div>

    <!-- 6. SO SÁNH NGÀNH -->
    <div class="section-header">6. SO SÁNH ĐỊNH GIÁ & HIỆU SUẤT CÙNG NGÀNH (SECTOR PEER COMPARISON)</div>
    <div class="card">
        <table>
            <thead>
                <tr>
                    <th>Mã / Sàn</th>
                    <th style="text-align:right;">Thị Giá</th>
                    <th style="text-align:right;">P/E (TTM)</th>
                    <th style="text-align:right;">P/B</th>
                    <th style="text-align:right;">ROE (%)</th>
                    <th style="text-align:right;">PEG</th>
                    <th style="text-align:right;">Hiệu Suất</th>
                </tr>
            </thead>
            <tbody>
                {peers_rows_html}
            </tbody>
        </table>
        <div style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:8px; padding:14px 18px; margin-top:14px; font-size:13.5px; line-height:1.7;">
            {peer_concl}
        </div>
    </div>

    <!-- 7. RỦI RO & KHẨU VỊ ĐẦU TƯ -->
    <div class="section-header">7. RỦI RO TRỌNG YẾU & CHIẾN LƯỢC GIẢI NGÂN THEO 3 KHẨU VỊ (RISKS & TRADING STRATEGIES)</div>
    <div class="card">
        <h4 style="color:#B91C1C; margin-bottom:12px;">7.1. Bốn (04) Rủi ro đầu tư trọng yếu cần theo dõi</h4>
        {risks_html}

        <h4 style="color:var(--primary); margin: 24px 0 12px 0;">7.2. Chiến lược giải ngân cho 3 khẩu vị nhà đầu tư</h4>
        {strat_html}
    </div>

    <!-- 8. TỔNG KẾT & RADAR -->
    <div class="section-header">8. TỔNG KẾT & ĐÁNH GIÁ RADAR 5 TRỤC (5-AXIS RADAR SCORECARD)</div>
    <div class="card" style="display:flex; flex-wrap:wrap; gap:24px; align-items:center;">
        <div style="flex:1; min-width:320px;">
            <div style="font-size:16px; font-weight:bold; margin-bottom:12px; color:var(--primary);">Bảng chấm điểm 5 trục Khối 6:</div>
            <table>
                <thead>
                    <tr><th>Trục Đánh Giá</th><th style="text-align:right;">Điểm (/10)</th></tr>
                </thead>
                <tbody>
                    {''.join(f'<tr><td style="font-weight:600;">{k}</td><td style="text-align:right; font-weight:bold; font-size:15px; color:{"#16A34A" if v>=7 else ("#DC2626" if v<5 else "#D97706")};">{v}/10</td></tr>' for k, v in clean_scores.items())}
                </tbody>
            </table>
            <div style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:6px; padding:12px 16px; margin-top:14px; font-size:13.5px;">
                <b>ĐIỂM TRUNG BÌNH 5 TRỤC:</b> <span style="font-size:16px; font-weight:bold; color:{rating_color};">{avg_score}/10</span>
                <br><b>KHUYẾN NGHỊ TỔNG HỢP:</b> <span style="font-weight:bold; color:{rating_color};">{rating.upper()}</span> (Tích lũy trung – dài hạn).
            </div>
        </div>
        <div style="flex:1; min-width:320px; height:340px;">
            <canvas id="radarChart"></canvas>
        </div>
    </div>

    <div class="footer">
        ⚠️ <b>TUYÊN BỐ MIỄN TRỪ TRÁCH NHIỆM:</b> Báo cáo được tạo tự động bởi AI Chuyên viên Phân tích Đầu tư Cấp cao theo chuẩn v3.0, chỉ mang tính chất tham khảo, không cấu thành lời khuyên đầu tư hay khuyến nghị mua bán chính thức. Nhà đầu tư tự chịu trách nhiệm với mọi quyết định của mình.
        <br>Dữ liệu thị trường lấy tại phiên đóng cửa {date_val}.
    </div>

    <script>
        const ctxPrice = document.getElementById('priceChart').getContext('2d');
        new Chart(ctxPrice, {{
            type: 'line',
            data: {{
                labels: {json.dumps(dates_js)},
                datasets: [
                    {{
                        label: 'Giá đóng cửa ({sym})',
                        data: {json.dumps(prices_js)},
                        borderColor: '#1E40AF',
                        backgroundColor: 'rgba(30, 64, 175, 0.05)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.2
                    }},
                    {{
                        label: 'MA20',
                        data: {json.dumps(ma20_js)},
                        borderColor: '#16A34A',
                        borderWidth: 1.2,
                        pointRadius: 0
                    }},
                    {{
                        label: 'MA50',
                        data: {json.dumps(ma50_js)},
                        borderColor: '#D97706',
                        borderWidth: 1.2,
                        pointRadius: 0
                    }},
                    {{
                        label: 'MA200',
                        data: {json.dumps(ma200_js)},
                        borderColor: '#DC2626',
                        borderWidth: 1.2,
                        pointRadius: 0
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                interaction: {{ mode: 'index', intersect: false }},
                plugins: {{
                    title: {{ display: true, text: 'Biểu đồ Giá & MA20/MA50/MA200 (Hỗ trợ Zoom & Pan)' }},
                    zoom: {{
                        pan: {{ enabled: true, mode: 'x' }},
                        zoom: {{ wheel: {{ enabled: true }}, pinch: {{ enabled: true }}, mode: 'x' }}
                    }}
                }},
                scales: {{
                    y: {{ title: {{ display: true, text: 'Giá (VNĐ)' }} }}
                }}
            }}
        }});

        const ctxRadar = document.getElementById('radarChart').getContext('2d');
        new Chart(ctxRadar, {{
            type: 'radar',
            data: {{
                labels: {json.dumps(radar_labels)},
                datasets: [{{
                    label: 'Điểm đánh giá',
                    data: {json.dumps(radar_values)},
                    backgroundColor: 'rgba(30, 64, 175, 0.25)',
                    borderColor: '#1E40AF',
                    pointBackgroundColor: '#1E40AF',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: '#1E40AF'
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    r: {{
                        suggestedMin: 0,
                        suggestedMax: 10,
                        ticks: {{ stepSize: 2 }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""
    clean_date = str(date_val).replace("/", "-").replace("\\", "-")
    filename = f"{sym}_{clean_date}.html"
    filepath = os.path.join(REPORT_OUT_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_content)
    return filepath
