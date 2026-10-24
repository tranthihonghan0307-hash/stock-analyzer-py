# analysis/technical.py — Tính toán chỉ báo kỹ thuật

import pandas as pd
import numpy as np

def add_moving_averages(df: pd.DataFrame) -> pd.DataFrame:
    """Thêm MA20, MA50, MA200 vào DataFrame giá"""
    df = df.copy()
    for period in [20, 50, 200]:
        df[f"MA{period}"] = df["close"].rolling(window=period, min_periods=1).mean()
    return df

def add_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """Tính RSI(14)"""
    df = df.copy()
    delta = df["close"].diff()
    gain  = delta.clip(lower=0)
    loss  = (-delta).clip(lower=0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    df["RSI"] = 100 - (100 / (1 + rs))
    return df

def add_macd(df: pd.DataFrame,
             fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    """Tính MACD, Signal line, Histogram"""
    df = df.copy()
    ema_fast   = df["close"].ewm(span=fast,   adjust=False).mean()
    ema_slow   = df["close"].ewm(span=slow,   adjust=False).mean()
    df["MACD"] = ema_fast - ema_slow
    df["MACD_Signal"]    = df["MACD"].ewm(span=signal, adjust=False).mean()
    df["MACD_Histogram"] = df["MACD"] - df["MACD_Signal"]
    return df

def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Áp dụng tất cả chỉ báo"""
    df = add_moving_averages(df)
    df = add_rsi(df)
    df = add_macd(df)
    return df

def get_support_resistance(df: pd.DataFrame, window: int = 20) -> dict:
    """Tính vùng hỗ trợ và kháng cự gần nhất"""
    if df.empty:
        return {"resistance": None, "support": None, "r1": None, "r2": None, "s1": None, "s2": None}
    
    recent = df.tail(60)
    highs = recent["high"].rolling(window).max()
    lows  = recent["low"].rolling(window).min()
    
    res = round(highs.dropna().iloc[-1], 2) if not highs.dropna().empty else None
    sup = round(lows.dropna().iloc[-1],  2) if not lows.dropna().empty else None
    
    # Tính các ngưỡng hỗ trợ/kháng cự chi tiết
    last_close = df["close"].iloc[-1]
    peak = round(float(df["high"].max()), 2)
    trough = round(float(df["low"].min()), 2)
    
    r1 = res if res and res > last_close else peak
    r2 = peak
    s1 = sup if sup and sup < last_close else trough
    s2 = trough

    return {
        "resistance": r1,
        "support":    s1,
        "r1": r1, "r2": r2,
        "s1": s1, "s2": s2,
        "peak": peak, "trough": trough
    }

def get_technical_summary(df: pd.DataFrame) -> dict:
    """
    Tổng hợp trạng thái kỹ thuật và tạo bài nhận định chuyên sâu (Expert TA Review):
    - Đánh giá Biểu đồ 1 & 2: Cấu trúc giá, hệ thống MA20, MA50, MA200, Nến và Khối lượng (Volume)
    - Đánh giá Biểu đồ 3: Chỉ báo RSI(14), vùng quá mua/quá bán và phân kỳ động lượng
    - Đánh giá Biểu đồ 4: Chỉ báo MACD, Signal line và biến thiên xung lực Histogram
    - Xác định vùng hỗ trợ/kháng cự cứng & mềm
    - Đưa ra kịch bản hành động kỹ thuật & chiến lược giao dịch chuyên sâu
    """
    if df.empty:
        return {}

    last = df.iloc[-1]
    prev = df.iloc[-2] if len(df) >= 2 else last
    close = float(last["close"])
    open_p = float(last.get("open", close))
    high_p = float(last.get("high", close))
    low_p = float(last.get("low", close))

    def vs_ma(ma_col):
        ma_val = last.get(ma_col)
        if ma_val is None or pd.isna(ma_val):
            return None, None, "N/A"
        diff_pct = (close - ma_val) / ma_val * 100
        signal = "TRÊN" if close >= ma_val else "DƯỚI"
        return round(float(ma_val), 2), round(float(diff_pct), 2), signal

    ma20_val, ma20_diff, ma20_sig = vs_ma("MA20")
    ma50_val, ma50_diff, ma50_sig = vs_ma("MA50")
    ma200_val, ma200_diff, ma200_sig = vs_ma("MA200")

    # Slope/xu hướng của MA20 và MA50
    ma20_slope = "ĐI LÊN" if (len(df) >= 5 and "MA20" in df.columns and df["MA20"].iloc[-1] > df["MA20"].iloc[-5]) else "ĐI XUỐNG"
    ma50_slope = "ĐI LÊN" if (len(df) >= 5 and "MA50" in df.columns and df["MA50"].iloc[-1] > df["MA50"].iloc[-5]) else "ĐI XUỐNG"

    # Kiểm tra giao cắt MA (Golden/Death Cross)
    ma_cross = "Bình thường"
    if ma20_val and ma50_val:
        if ma20_val > ma50_val and prev.get("MA20", 0) <= prev.get("MA50", 0):
            ma_cross = "Golden Cross ngắn hạn (MA20 cắt lên MA50)"
        elif ma20_val < ma50_val and prev.get("MA20", 0) >= prev.get("MA50", 0):
            ma_cross = "Death Cross ngắn hạn (MA20 cắt xuống MA50)"
    if ma50_val and ma200_val:
        if ma50_val > ma200_val and prev.get("MA50", 0) <= prev.get("MA200", 0):
            ma_cross = "Golden Cross trung hạn (MA50 cắt lên MA200)"
        elif ma50_val < ma200_val and prev.get("MA50", 0) >= prev.get("MA200", 0):
            ma_cross = "Death Cross trung hạn (MA50 cắt xuống MA200)"

    # Khối lượng giao dịch (Volume vs MA10 Volume)
    vol = float(last.get("volume", 0))
    avg_vol_10 = float(df["volume"].tail(10).mean()) if "volume" in df.columns and len(df) >= 10 else vol
    vol_ratio = (vol / avg_vol_10) if avg_vol_10 > 0 else 1.0

    # RSI
    rsi = last.get("RSI")
    rsi_val = round(float(rsi), 2) if (rsi is not None and not pd.isna(rsi)) else None
    if rsi_val is not None:
        if rsi_val >= 70:
            rsi_signal = "Quá mua (Overbought)"
            rsi_desc = f"RSI đạt {rsi_val} điểm - nằm trong vùng Quá Mua (>70). Áp lực rung lắc chốt lời ngắn hạn có thể sớm xuất hiện; nhà đầu tư nên hạn chế mua đuổi giá cao."
        elif rsi_val <= 30:
            rsi_signal = "Quá bán (Oversold)"
            rsi_desc = f"RSI chạm {rsi_val} điểm - rơi vào vùng Quá Bán (<30). Vùng chiết khấu kỹ thuật sâu, xác suất xuất hiện nhịp phục hồi kỹ thuật (Technical Rebound) là rất cao."
        elif rsi_val >= 55:
            rsi_signal = "Tích cực (Bullish Momentum)"
            rsi_desc = f"RSI đạt {rsi_val} điểm - giữ vững trên ngưỡng cân bằng 50 và trong vùng tích cực. Phe mua đang kiểm soát hoàn toàn động lượng tăng giá."
        elif rsi_val <= 45:
            rsi_signal = "Yếu (Bearish Bias)"
            rsi_desc = f"RSI ở mức {rsi_val} điểm - dao động dưới ngưỡng 50. Động lượng suy yếu, phe bán vẫn chiếm ưu thế trong các nhịp hồi phục."
        else:
            rsi_signal = "Trung tính (Neutral)"
            rsi_desc = f"RSI đạt {rsi_val} điểm - nằm tại dải trung tính (45-55). Thị trường thể hiện trạng thái giằng co tích lũy và chờ đợi tín hiệu dòng tiền mới."
    else:
        rsi_signal = "N/A"
        rsi_desc = "Chưa có đủ dữ liệu chỉ báo RSI."

    # Phân kỳ RSI (Divergence check)
    divergence_note = "Chưa ghi nhận phân kỳ rõ rệt."
    if len(df) >= 20 and "RSI" in df.columns:
        recent_20 = df.tail(20)
        p_max_idx = recent_20["close"].idxmax()
        p_min_idx = recent_20["close"].idxmin()
        if p_max_idx != recent_20.index[-1] and recent_20["close"].iloc[-1] > recent_20.loc[p_max_idx, "close"] and recent_20["RSI"].iloc[-1] < recent_20.loc[p_max_idx, "RSI"]:
            divergence_note = "Cảnh báo Phân kỳ âm (Bearish Divergence): Giá tạo đỉnh mới nhưng RSI tạo đỉnh thấp hơn, cảnh báo rủi ro đảo chiều giảm."
        elif p_min_idx != recent_20.index[-1] and recent_20["close"].iloc[-1] < recent_20.loc[p_min_idx, "close"] and recent_20["RSI"].iloc[-1] > recent_20.loc[p_min_idx, "RSI"]:
            divergence_note = "Xuất hiện Phân kỳ dương (Bullish Divergence): Giá tạo đáy mới nhưng RSI tạo đáy cao hơn, tín hiệu sớm cho khả năng tạo đáy đi lên."

    # MACD & Histogram
    macd = last.get("MACD")
    macd_sig = last.get("MACD_Signal")
    macd_hist = last.get("MACD_Histogram")
    prev_hist = prev.get("MACD_Histogram", 0)

    if macd is not None and macd_sig is not None and not pd.isna(macd) and not pd.isna(macd_sig):
        macd_val = round(float(macd), 2)
        macd_sig_val = round(float(macd_sig), 2)
        hist_val = round(float(macd_hist), 2) if macd_hist is not None and not pd.isna(macd_hist) else 0

        macd_cross = "Mua (MACD > Signal)" if macd_val >= macd_sig_val else "Bán (MACD < Signal)"
        macd_zero = "Nằm trên trục 0 (Xu hướng tăng)" if macd_val > 0 else "Nằm dưới trục 0 (Xu hướng giảm/điều chỉnh)"
        
        if hist_val > 0:
            hist_state = "Histogram xanh mở rộng, gia tốc tăng giá đang mạnh dần" if hist_val > prev_hist else "Histogram xanh thu hẹp, đà tăng ngắn hạn có dấu hiệu chững lại"
        else:
            hist_state = "Histogram đỏ thu hẹp, lực cung xả hàng suy yếu rõ rệt" if hist_val > prev_hist else "Histogram đỏ mở rộng, áp lực bán gia tăng"

        macd_signal = f"{macd_cross}"
        macd_desc = f"Đường MACD ({macd_val}) { 'vượt lên trên' if macd_val >= macd_sig_val else 'cắt xuống dưới' } đường Signal ({macd_sig_val}), cho tín hiệu {macd_cross}. Chỉ báo {macd_zero}. {hist_state}."
    else:
        macd_val = None
        macd_sig_val = None
        macd_signal = "N/A"
        macd_desc = "Chưa có đủ dữ liệu tính toán MACD."

    # Đỉnh & Đáy chu kỳ
    peak_val = round(float(df["high"].max()), 2)
    trough_val = round(float(df["low"].min()), 2)
    peak_date = str(df.loc[df["high"].idxmax(), "date"].date())
    trough_date = str(df.loc[df["low"].idxmin(), "date"].date())

    # Hỗ trợ / Kháng cự
    sr_dict = get_support_resistance(df)
    res_val = sr_dict.get("resistance")
    sup_val = sr_dict.get("support")

    # Phân tích Nến và Khối lượng (Price Action & Volume)
    candle_body = abs(close - open_p)
    candle_range = (high_p - low_p) if (high_p - low_p) > 0 else 1.0
    upper_wick = high_p - max(close, open_p)
    lower_wick = min(close, open_p) - low_p

    if close > open_p:
        candle_type = "Nến tăng giá (Bullish)"
        if lower_wick > candle_body * 1.5:
            candle_type = "Nến rút chân tăng giá (Hammer / Pin bar)"
        elif candle_body / candle_range > 0.8:
            candle_type = "Nến Marubozu tăng mạnh (Lực cầu áp đảo)"
    else:
        candle_type = "Nến giảm giá (Bearish)"
        if upper_wick > candle_body * 1.5:
            candle_type = "Nến bắn sao (Shooting Star - Áp lực chốt lời tại đỉnh nến)"
        elif candle_body / candle_range > 0.8:
            candle_type = "Nến Marubozu giảm mạnh (Phe bán áp đảo)"

    if vol_ratio >= 1.5:
        vol_desc = f"Khối lượng phiên đạt {vol:,.0f} CP (gấp {vol_ratio:.1f}x mức TB 10 phiên: {avg_vol_10:,.0f} CP) — Bùng nổ thanh khoản, xác nhận dòng tiền lớn (Smart money) tham gia mạnh mẽ."
    elif vol_ratio >= 0.9:
        vol_desc = f"Khối lượng đạt {vol:,.0f} CP (~{vol_ratio:.1f}x TB 10 phiên) — Thanh khoản duy trì ổn định, nhịp giao dịch diễn ra nhịp nhàng."
    else:
        vol_desc = f"Khối lượng đạt {vol:,.0f} CP (chỉ bằng {vol_ratio:.1f}x TB 10 phiên) — Thanh khoản co hẹp, lực cung giá thấp suy kiệt, trạng thái tích lũy thăm dò."

    # XU HƯỚNG TỔNG HỢP & CHIẾN LƯỢC KỸ THUẬT
    trend_short = "TĂNG TRƯỞNG" if ma20_sig == "TRÊN" else "ĐIỀU CHỈNH / GIẢM"
    trend_mid = "TĂNG TRƯỞNG" if ma50_sig == "TRÊN" else "ĐIỀU CHỈNH / TÍCH LŨY"
    trend_long = "XU HƯỚNG TĂNG DÀI HẠN" if ma200_sig == "TRÊN" else "DƯỚI MA200 (THẬN TRỌNG DÀI HẠN)"

    # Nhận định chi tiết từng biểu đồ
    review_chart1_2 = (
        f"• <b>Cấu trúc Đường giá & Hệ thống MA (Biểu đồ 1 & 2):</b> "
        f"Thị giá hiện tại đóng cửa tại mức {close:,.0f}đ. Vị thế ngắn hạn đang {ma20_sig} MA20 ({ma20_val:,.0f}đ, chênh lệch {ma20_diff:+.2f}%), "
        f"vị thế trung hạn {ma50_sig} MA50 ({ma50_val:,.0f}đ, chênh lệch {ma50_diff:+.2f}%) và {ma200_sig} MA200 ({ma200_val:,.0f}đ, {ma200_diff:+.2f}%). "
        f"Đường MA20 đang có xu hướng {ma20_slope.lower()}, trong khi MA50 {ma50_slope.lower()}. "
        f"{'Hệ thống MA đang xếp lớp hướng lên (Bullish alignment), khẳng định cấu trúc tăng giá vững chắc.' if (ma20_sig == 'TRÊN' and ma50_sig == 'TRÊN') else 'Giá đang nằm dưới một số đường MA quan trọng, cần nhịp tái tích lũy để hấp thụ cung.'}"
    )

    review_volume = (
        f"• <b>Hành vi Khối lượng & Nến Nhật (Biểu đồ 2):</b> "
        f"Phiên gần nhất xuất hiện {candle_type}. {vol_desc} "
        f"{'Độ dốc giá đi kèm thanh khoản xác nhận xu hướng tiếp tục được hỗ trợ bởi dòng tiền chủ động.' if vol_ratio >= 1.0 else 'Thanh khoản thấp cho thấy lực bán tháo không xuất hiện, áp lực cung ở vùng giá này đã được kiểm soát tốt.'}"
    )

    review_chart3 = (
        f"• <b>Động lượng Chỉ báo RSI(14) (Biểu đồ 3):</b> "
        f"{rsi_desc} {divergence_note}"
    )

    review_chart4 = (
        f"• <b>Xu hướng & Xung lực MACD (Biểu đồ 4):</b> "
        f"{macd_desc}"
    )

    review_strategy = (
        f"• <b>Vùng Hỗ trợ - Kháng cự & Chiến lược hành động:</b> "
        f"Vùng kháng cự cứng gần nhất nằm tại <b>{res_val:,.0f}đ</b> (vùng đỉnh ngắn hạn và mục tiêu R1), kháng cự xa hơn tại đỉnh chu kỳ <b>{peak_val:,.0f}đ</b> ({peak_date}). "
        f"Vùng hỗ trợ tin cậy nằm tại <b>{sup_val:,.0f}đ</b> (S1) và vùng hỗ trợ MA20/MA50. "
        f"<b>Khuyến nghị kỹ thuật:</b> "
        f"{'Chiến lược Mua gia tăng tỷ trọng khi giá có nhịp kiểm định (retest) hỗ trợ thành công hoặc gia tăng vị thế khi bứt phá dứt khoát qua ngưỡng cản với khối lượng lớn.' if (ma20_sig == 'TRÊN' and 'Mua' in macd_signal) else 'Chiến lược Thận trọng quan sát; ưu tiên bảo toàn vốn, chỉ giải ngân từng phần tại các vùng hỗ trợ cứng hoặc khi có tín hiệu đảo chiều xác nhận từ khối lượng.'}"
    )

    full_nhan_dinh = (
        f"<b>TỔNG QUAN TÍN HIỆU KỸ THUẬT:</b> Xu hướng ngắn hạn: <b>{trend_short}</b> | Trung hạn: <b>{trend_mid}</b> | Dài hạn: <b>{trend_long}</b>.<br/><br/>"
        f"{review_chart1_2}<br/><br/>"
        f"{review_volume}<br/><br/>"
        f"{review_chart3}<br/><br/>"
        f"{review_chart4}<br/><br/>"
        f"{review_strategy}"
    )

    return {
        "close":      close,
        "ma20":       ma20_val,  "ma20_diff": ma20_diff,  "ma20_signal": ma20_sig,
        "ma50":       ma50_val,  "ma50_diff": ma50_diff,  "ma50_signal": ma50_sig,
        "ma200":      ma200_val, "ma200_diff": ma200_diff,"ma200_signal": ma200_sig,
        "ma_cross":   ma_cross,
        "rsi":        rsi_val,   "rsi_signal": rsi_signal, "rsi_desc": rsi_desc,
        "macd":       macd_val,  "macd_sig": macd_sig_val, "macd_signal": macd_signal, "macd_desc": macd_desc,
        "vol":        vol,       "avg_vol_10": avg_vol_10, "vol_ratio": vol_ratio, "vol_desc": vol_desc,
        "candle_type": candle_type,
        "peak":       peak_val,  "trough": trough_val,
        "peak_date":  peak_date, "trough_date": trough_date,
        "resistance": res_val,   "support": sup_val,
        "trend_short": trend_short, "trend_mid": trend_mid, "trend_long": trend_long,
        "nhan_dinh":  full_nhan_dinh,
        "review_chart1_2": review_chart1_2,
        "review_volume":   review_volume,
        "review_chart3":   review_chart3,
        "review_chart4":   review_chart4,
        "review_strategy": review_strategy,
    }

