# test_flow.py
import sys, os
sys.path.insert(0, '.')
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass
from data.fetcher import fetch_price_history, fetch_company_info, fetch_financial_statements, fetch_current_price, fetch_industry_peers, calc_avg_volume
from data.news_fetcher import fetch_news
from analysis.technical import add_all_indicators, get_support_resistance, get_technical_summary
from analysis.fundamental import extract_income_data, extract_all_ratios, extract_cashflow, compute_scoring, compute_pe_peg
from charts.chart_generator import (
    chart1_price_line, chart2_candle_ma_volume, chart3_rsi, chart4_macd,
    chart5_news_pie, chart6_financials, chart7_roe_roa,
    chart9_peer_valuation, chart10_performance, chart11_radar
)
from reports.pdf_builder import build_pdf
import os, traceback

print('=== TEST FULL FLOW ===')
symbol = 'MWG'
all_data = {}
errors = []

try:
    price_df = fetch_price_history(symbol)
    print(f'[OK] Price rows: {len(price_df)}')
    all_data['price_df'] = price_df
except Exception as e:
    errors.append(f'fetch_price_history: {e}')

try:
    company_info = fetch_company_info(symbol)
    name = company_info.get('company_name')
    print(f'[OK] Company: {name}')
    all_data['company_info'] = company_info
except Exception as e:
    errors.append(f'fetch_company_info: {e}')
    company_info = {}

try:
    current_price = fetch_current_price(symbol)
    print(f'[OK] Price: {current_price.get("last_price")}')
    all_data['current_price'] = current_price
except Exception as e:
    errors.append(f'fetch_current_price: {e}')
    current_price = {}

try:
    price_df = add_all_indicators(price_df)
    ta_summary = get_technical_summary(price_df)
    sr = get_support_resistance(price_df)
    print(f'[OK] RSI: {ta_summary.get("rsi")}')
    all_data['ta_summary'] = ta_summary
    all_data['sr'] = sr
    all_data['price_df'] = price_df
except Exception as e:
    errors.append(f'technical: {e}')
    ta_summary = {}
    sr = {}

try:
    financials = fetch_financial_statements(symbol)
    income_rows = extract_income_data(financials.get('income'))
    ratio_data = extract_all_ratios(financials.get('info', {}))
    cashflow = extract_cashflow(financials.get('cashflow'))
    cur_p = current_price.get('last_price', 75000.0)
    pe_peg = compute_pe_peg(ratio_data, income_rows, cur_p, financials.get('info', {}))
    print(f'[OK] Income rows: {len(income_rows)}, ROE: {ratio_data.get("roe")}, P/E: {pe_peg.get("pe_ttm")}, PEG: {pe_peg.get("peg_main")}')
    all_data['income_rows'] = income_rows
    all_data['ratio_data'] = ratio_data
    all_data['cashflow'] = cashflow
    all_data['pe_peg'] = pe_peg
except Exception as e:
    errors.append(f'fundamental: {e}')
    traceback.print_exc()
    income_rows = []
    ratio_data = {}
    cashflow = {}
    pe_peg = {}

try:
    news_items = fetch_news(symbol, company_info.get('company_name', ''))
    neg = sum(1 for n in news_items if n['sentiment'] == 'TIÊU CỰC')
    print(f'[OK] News: {len(news_items)}, Negative: {neg}')
    all_data['news_items'] = news_items
except Exception as e:
    errors.append(f'news: {e}')
    news_items = []

try:
    scores = compute_scoring(ta_summary, ratio_data, income_rows, 0, news_items, pe_peg)
    print(f'[OK] Scores: {scores}')
    all_data['scores'] = scores
except Exception as e:
    errors.append(f'scoring: {e}')
    traceback.print_exc()

# Test charts
chart_paths = {}
for fn_name, fn, args, key in [
    ('chart1', chart1_price_line, (price_df, symbol), 'chart1'),
    ('chart2', chart2_candle_ma_volume, (price_df, symbol), 'chart2'),
    ('chart3', chart3_rsi, (price_df, symbol), 'chart3'),
    ('chart4', chart4_macd, (price_df, symbol), 'chart4'),
    ('chart5', chart5_news_pie, (news_items, symbol), 'chart5'),
    ('chart6', chart6_financials, (income_rows, symbol), 'chart6'),
    ('chart7', chart7_roe_roa, (ratio_data, symbol), 'chart7'),
    ('chart11', chart11_radar, (scores, symbol), 'chart11'),
]:
    try:
        path = fn(*args)
        chart_paths[key] = path
        print(f'[OK] {fn_name}: {os.path.basename(path) if path else "None"}')
    except Exception as e:
        errors.append(f'{fn_name}: {e}')
        traceback.print_exc()

from data.ctck_fetcher import get_ctck_consensus
from charts.chart_generator import chart8_target_prices

cur_p = current_price.get('last_price', 75000.0)
ctck_data = get_ctck_consensus(symbol, cur_p, company_info.get('company_name', ''))
all_data['ctck_data'] = ctck_data
try:
    c8 = chart8_target_prices(ctck_data, cur_p, symbol)
    chart_paths['chart8'] = c8
    print(f'[OK] chart8: {os.path.basename(c8) if c8 else "None"}')
except Exception as e:
    errors.append(f'chart8: {e}')
    traceback.print_exc()

# Peer data (simple)
peer_symbols = ['PNJ', 'FPT', 'DGW']
peer_data = [{
    'Mã / Sàn': f'{symbol} / HOSE',
    'Thị giá': round(current_price.get('last_price', 0), 3),
    'P/E': round(company_info.get('pe', 0) or 0, 3),
    'P/B': round(company_info.get('pb', 0) or 0, 3),
    'ROE (%)': round((company_info.get('roe', 0) or 0) * 100, 3),
    'Hệ số PEG': 0.55,
    'Hiệu suất (%)': round((price_df['close'].iloc[-1] - price_df['close'].iloc[0]) / price_df['close'].iloc[0] * 100, 3),
}]
all_data['peer_data'] = peer_data
all_data['chart_paths'] = chart_paths
all_data['perf_data'] = {}

try:
    chart9 = chart9_peer_valuation(peer_data, symbol)
    chart_paths['chart9'] = chart9
    print(f'[OK] chart9: {os.path.basename(chart9) if chart9 else "None"}')
except Exception as e:
    errors.append(f'chart9: {e}')
    traceback.print_exc()

# Test PDF, HTML, CSV
from reports.html_builder import build_html
from reports.csv_builder import build_csv

try:
    pdf_path = build_pdf(symbol, all_data)
    print(f'[OK] PDF: {pdf_path}')
except Exception as e:
    errors.append(f'PDF: {e}')
    traceback.print_exc()

try:
    html_path = build_html(symbol, all_data, "2026-10-22")
    print(f'[OK] HTML: {html_path}')
except Exception as e:
    errors.append(f'HTML: {e}')
    traceback.print_exc()

try:
    csv_path = build_csv(symbol, all_data, "2026-10-22")
    print(f'[OK] CSV: {csv_path}')
except Exception as e:
    errors.append(f'CSV: {e}')
    traceback.print_exc()

print('\n=== SUMMARY ===')
if errors:
    print(f'ERRORS ({len(errors)}):')
    for err in errors:
        print(f'  - {err}')
else:
    print('ALL PASSED!')
