# reports/csv_builder.py — Xuất file số liệu CSV theo chuẩn Khối 9 prompt v3.0
import os
import csv
import pandas as pd
from config import REPORT_OUT_DIR

def build_csv(symbol: str, data: dict, data_date_str: str = "") -> str:
    """
    Tạo file CSV số liệu chuẩn Khối 9:
    Tên: [MÃ]_[YYYY-MM-DD]_data.csv
    Một dòng gồm: ngay, ma, gia, pe_ttm, pe_forward, peg, diem_radar, danh_gia_tong_hop, gia_muc_tieu_binh_quan, upside_pct
    """
    sym = symbol.upper().strip()
    date_val = data_date_str or data.get("data_date_str", "")
    
    cp = data.get("current_price", {})
    price_df = data.get("price_df", None)
    last_price = cp.get("last_price") or (price_df["close"].iloc[-1] if price_df is not None and not price_df.empty else 0.0)
    
    pe_peg = data.get("pe_peg", {})
    pe_ttm = pe_peg.get("pe_ttm", "") or ""
    pe_fwd = pe_peg.get("pe_forward", "") or ""
    peg_val = pe_peg.get("peg_main", "") or ""
    
    scores = data.get("scores", {})
    radar_avg = scores.get("_avg", "")
    rating = scores.get("_rating", "Trung lập")
    
    ctck_data = data.get("ctck_data", [])
    valid_targets = [c.get("target") for c in ctck_data if c.get("target") and c.get("target") > 0]
    avg_target = round(sum(valid_targets) / len(valid_targets), 2) if valid_targets else ""
    
    upside_pct = ""
    if avg_target and last_price and last_price > 0:
        upside_pct = round((avg_target - last_price) / last_price * 100, 2)
        
    clean_date = str(date_val).replace("/", "-").replace("\\", "-")
    filename = f"{sym}_{clean_date}_data.csv"
    filepath = os.path.join(REPORT_OUT_DIR, filename)
    
    headers = [
        "ngay", "ma", "gia", "pe_ttm", "pe_forward", "peg",
        "diem_radar", "danh_gia_tong_hop", "gia_muc_tieu_binh_quan", "upside_pct"
    ]
    row = [
        date_val, sym, last_price, pe_ttm, pe_fwd, peg_val,
        radar_avg, rating, avg_target, upside_pct
    ]
    
    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerow(row)
        
    return filepath
