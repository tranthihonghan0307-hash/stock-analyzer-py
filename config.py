# config.py — Cấu hình toàn cục hệ thống phân tích chứng khoán

# ── Màu sắc chuẩn báo cáo ─────────────────────────────────────────
COLOR_POSITIVE = "#16A34A"      # Tăng / Dương / Lợi nhuận
COLOR_NEGATIVE = "#DC2626"      # Giảm / Âm / Lỗ
COLOR_NEUTRAL  = "#1F2937"      # Trung tính
COLOR_HEADER   = "#1E40AF"      # Banner tiêu đề mục (xanh navy)
COLOR_ROW_ALT  = "#F9FAFB"      # Dòng xen kẽ bảng biểu
COLOR_WHITE    = "#FFFFFF"

# RGB tuple cho ReportLab (0..1)
def hex_to_rgb(hex_color: str):
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4))

RGB_POSITIVE = hex_to_rgb(COLOR_POSITIVE)
RGB_NEGATIVE = hex_to_rgb(COLOR_NEGATIVE)
RGB_NEUTRAL  = hex_to_rgb(COLOR_NEUTRAL)
RGB_HEADER   = hex_to_rgb(COLOR_HEADER)
RGB_ROW_ALT  = hex_to_rgb(COLOR_ROW_ALT)

# ── Font ───────────────────────────────────────────────────────────
FONT_NAME      = "DejaVuSans"
FONT_BOLD_NAME = "DejaVuSans-Bold"

# ── Biểu đồ ───────────────────────────────────────────────────────
CHART_DPI      = 200
CHART_STYLE    = "seaborn-v0_8-whitegrid"

# ── Khung thời gian cố định ────────────────────────────────────────
START_DATE     = "2026-03-01"

# ── Đường dẫn ─────────────────────────────────────────────────────
import os
BASE_DIR       = os.path.dirname(os.path.abspath(__file__))
CHART_OUT_DIR  = os.path.join(BASE_DIR, "charts", "output")
REPORT_OUT_DIR = os.path.join(BASE_DIR, "reports", "output")
FONT_DIR       = os.path.join(BASE_DIR, "utils", "fonts")

for d in [CHART_OUT_DIR, REPORT_OUT_DIR]:
    os.makedirs(d, exist_ok=True)
