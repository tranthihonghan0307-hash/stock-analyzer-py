# data/fetcher.py — Lấy dữ liệu bằng yfinance
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Patch curl_cffi cho yfinance trên Windows
try:
    import curl_cffi.requests
    _orig = curl_cffi.requests.Session.request
    def _patched(self, method, url, **kwargs):
        kwargs['verify'] = False
        return _orig(self, method, url, **kwargs)
    curl_cffi.requests.Session.request = _patched
except:
    pass

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import START_DATE

def _get_ticker_suffix(symbol: str) -> str:
    """Xác định đuôi cho yfinance (.VN, .HN, .UP)"""
    return f"{symbol.upper()}.VN"  # Thường HOSE dùng .VN, fallback sẽ xử lý sau nếu cần

def fetch_price_history(symbol: str, start: str = START_DATE) -> pd.DataFrame:
    tk = yf.Ticker(_get_ticker_suffix(symbol))
    df = tk.history(start=start)
    if df.empty:
        # Fallback to HNX
        tk = yf.Ticker(f"{symbol.upper()}.HN")
        df = tk.history(start=start)
    if not df.empty:
        df = df.reset_index()
        df.columns = [c.lower() for c in df.columns]
        # Xóa timezone
        if df['date'].dt.tz is not None:
            df['date'] = df['date'].dt.tz_localize(None)
        # Bắt buộc loại bỏ các dòng bị NaN (ví dụ phiên chưa có giá khớp hoặc lỗi dữ liệu yfinance)
        df = df.dropna(subset=["close"])
        return df[["date", "open", "high", "low", "close", "volume"]]
    return pd.DataFrame()

def fetch_company_info(symbol: str) -> dict:
    tk = yf.Ticker(_get_ticker_suffix(symbol))
    info = tk.info
    return {
        "symbol": symbol,
        "company_name": info.get("longName", info.get("shortName", symbol)),
        "exchange": info.get("exchange", "HOSE"),
        "industry": info.get("industry", "N/A"),
        "market_cap": info.get("marketCap"),
        "shares_outstanding": info.get("sharesOutstanding"),
        "pe": info.get("trailingPE"),
        "pb": info.get("priceToBook"),
        "eps": info.get("trailingEps"),
        "roe": info.get("returnOnEquity"),
        "peg": info.get("trailingPegRatio") or info.get("pegRatio"),
    }

def fetch_financial_statements(symbol: str) -> dict:
    tk = yf.Ticker(_get_ticker_suffix(symbol))
    return {
        "income": tk.quarterly_income_stmt,
        "balance": tk.quarterly_balance_sheet,
        "cashflow": tk.quarterly_cashflow,
        "ratio": pd.DataFrame(), # Có thể tính từ info
        "info": tk.info
    }

def fetch_current_price(symbol: str) -> dict:
    tk = yf.Ticker(_get_ticker_suffix(symbol))
    df = tk.history(period="10d")
    if not df.empty:
        # Bắt buộc loại bỏ các dòng NaN
        df = df.dropna(subset=["Close"])
    if not df.empty:
        last = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else last
        return {
            "last_price": float(last["Close"]),
            "change_pt": float(last["Close"] - prev["Close"]),
            "change_pct": float(((last["Close"] - prev["Close"]) / prev["Close"]) * 100) if prev["Close"] else 0.0,
            "open": float(last["Open"]),
            "high": float(last["High"]),
            "low": float(last["Low"]),
            "volume": float(last["Volume"])
        }
    return {}

def fetch_industry_peers(symbol: str, top_n: int = 3) -> list:
    sym = symbol.upper().strip()
    peer_sectors = {
        # Bán lẻ / Tiêu dùng
        "MWG": ["PNJ", "DGW", "FRT"],
        "PNJ": ["MWG", "DGW", "FRT"],
        "DGW": ["MWG", "FRT", "PET"],
        "FRT": ["MWG", "DGW", "PNJ"],
        "MSN": ["VNM", "SAB", "KDC"],
        "VNM": ["MSN", "SAB", "QNS"],
        "SAB": ["VNM", "MSN", "BHN"],
        # Công nghệ
        "FPT": ["CMG", "ELC", "CTR"],
        "CMG": ["FPT", "ELC", "CTR"],
        # Thép / Vật liệu
        "HPG": ["HSG", "NKG", "VGS"],
        "HSG": ["HPG", "NKG", "TLH"],
        "NKG": ["HPG", "HSG", "VGS"],
        # Ngân hàng
        "VCB": ["BID", "CTG", "TCB"],
        "BID": ["VCB", "CTG", "MBB"],
        "CTG": ["VCB", "BID", "TCB"],
        "TCB": ["MBB", "VPB", "ACB"],
        "MBB": ["TCB", "ACB", "VPB"],
        "VPB": ["TCB", "MBB", "HDB"],
        "ACB": ["MBB", "TCB", "STB"],
        "STB": ["ACB", "MBB", "SHB"],
        "HDB": ["VPB", "TPB", "MSB"],
        "TPB": ["HDB", "MSB", "OCB"],
        # Chứng khoán
        "SSI": ["VND", "VCI", "HCM"],
        "VND": ["SSI", "VCI", "HCM"],
        "VCI": ["SSI", "VND", "HCM"],
        "HCM": ["SSI", "VCI", "VND"],
        "MBS": ["SHS", "FTS", "BSI"],
        "SHS": ["MBS", "SSI", "VND"],
        # Bất động sản
        "VHM": ["VIC", "NVL", "KDH"],
        "VIC": ["VHM", "VRE", "NVL"],
        "VRE": ["VHM", "VIC", "MWG"],
        "NVL": ["PDR", "DXG", "DIG"],
        "KDH": ["NLG", "VHM", "DXG"],
        "NLG": ["KDH", "DXG", "PDR"],
        "PDR": ["NVL", "DIG", "DXG"],
        "DXG": ["PDR", "DIG", "NLG"],
        "DIG": ["DXG", "PDR", "CEO"],
        # Dầu khí / Hóa chất
        "GAS": ["PVD", "PVS", "BSR"],
        "PVD": ["PVS", "GAS", "PVC"],
        "PVS": ["PVD", "GAS", "PVB"],
        "BSR": ["OIL", "PLX", "GAS"],
        "DPM": ["DCM", "BFC", "LAS"],
        "DCM": ["DPM", "BFC", "DDV"],
        # Cảng biển / Logistics
        "GMD": ["HAH", "VSC", "PHP"],
        "HAH": ["GMD", "VSC", "PVT"],
    }
    if sym in peer_sectors:
        return peer_sectors[sym][:top_n]
    # Fallback cho mã bất kỳ: lấy top 3 mã lớn VN30
    return ["FPT", "HPG", "MBB"][:top_n]

def calc_avg_volume(df: pd.DataFrame, n: int = 10) -> float:
    if df is None or df.empty or "volume" not in df.columns: return None
    return df["volume"].tail(n).mean()
