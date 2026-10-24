# utils/formatters.py — Format số kiểu Việt Nam làm tròn 3 chữ số thập phân

import math
import pandas as pd
import numpy as np

def fmt_price(value, suffix="đ") -> str:
    """Format giá tiền: 75000 → '75.000đ', 73618.421 → '73.618,421đ'"""
    if value is None:
        return "N/A"
    try:
        if pd.isna(value) or np.isnan(float(value)):
            return "N/A"
        val = float(value)
        if val == int(val):
            return f"{int(val):,}".replace(",", ".") + suffix
        # Làm tròn tối đa 3 chữ số thập phân
        formatted = f"{val:,.3f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return formatted + suffix
    except:
        return "N/A"

def fmt_pct(value, sign=True) -> str:
    """Format phần trăm làm tròn 3 chữ số thập phân: 0.1245 → '+12,450%' hay 2.15 → '+2,150%'"""
    if value is None:
        return "N/A"
    try:
        if pd.isna(value) or np.isnan(float(value)):
            return "N/A"
        val = float(value)
        v = val * 100 if abs(val) < 1.0 else val
        prefix = "+" if v > 0 and sign else ""
        return f"{prefix}{v:,.3f}%".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "N/A"

def fmt_billion(value) -> str:
    """Format tỷ đồng làm tròn 3 chữ số thập phân: 1234567890000 → '1.234,568 tỷ'"""
    if value is None:
        return "N/A"
    try:
        if pd.isna(value) or np.isnan(float(value)):
            return "N/A"
        b = float(value) / 1e9
        return f"{b:,.3f} tỷ".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "N/A"

def fmt_number(value) -> str:
    """Format số nguyên có phân cách hàng nghìn: 1234567 → '1.234.567'"""
    if value is None:
        return "N/A"
    try:
        if pd.isna(value) or np.isnan(float(value)):
            return "N/A"
        return f"{int(float(value)):,}".replace(",", ".")
    except:
        return "N/A"

def color_value(value, positive_threshold=0):
    """Trả về COLOR_POSITIVE/NEGATIVE/NEUTRAL tùy giá trị"""
    from config import COLOR_POSITIVE, COLOR_NEGATIVE, COLOR_NEUTRAL
    try:
        if pd.isna(value):
            return COLOR_NEUTRAL
        v = float(value)
        if v > positive_threshold:
            return COLOR_POSITIVE
        elif v < positive_threshold:
            return COLOR_NEGATIVE
        else:
            return COLOR_NEUTRAL
    except:
        return COLOR_NEUTRAL
