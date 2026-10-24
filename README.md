# Bảng tin Chứng khoán Việt Nam

Web app Next.js tổng hợp tin tức chứng khoán hằng ngày và tra cứu thông tin cơ bản
theo mã cổ phiếu, dùng **Google Gemini API** (có Google Search grounding) để tự động
tìm kiếm và tóm tắt dữ liệu.

## Tính năng

- **Trang Tin tức hằng ngày** (`/tin-tuc`): bảng tổng hợp tin theo ngày, mã CK, tóm
  tắt, nguồn, loại tin — giống layout bảng bạn đã dùng trước đó. Có nút "Cập nhật
  tin mới nhất" để gọi Gemini tìm tin mới, và tự động chạy mỗi ngày qua Vercel Cron.
- **Trang Tra cứu mã CK** (`/tra-cuu`): nhập mã cổ phiếu → Gemini tìm thông tin công
  ty, chỉ số cơ bản (P/E, P/B, vốn hóa...), tin tức gần đây, và phân tích điểm
  mạnh/rủi ro/triển vọng (**không đưa khuyến nghị mua/bán trực tiếp** — chỉ trình
  bày dữ kiện để bạn tự quyết định).

## 1. Cài đặt

```bash
npm install
```

## 2. Lấy Gemini API Key

1. Vào https://aistudio.google.com/app/apikey
2. Tạo API key mới (miễn phí, có hạn mức request/phút)
3. Copy `.env.example` thành `.env.local`:
   ```bash
   cp .env.example .env.local
   ```
4. Dán key vào `GEMINI_API_KEY=...` trong `.env.local`
5. (Tuỳ chọn nhưng khuyến khích) Tạo `CRON_SECRET` ngẫu nhiên để khoá endpoint
   cập nhật tin, tránh người khác gọi tràn lan tốn phí:
   ```bash
   openssl rand -hex 16
   ```
   Dán vào `CRON_SECRET=...`

## 3. Chạy thử ở máy local

```bash
npm run dev
```

Mở http://localhost:3000 → vào trang **Tin tức hằng ngày**, bấm **"Cập nhật tin mới
nhất"** để gọi Gemini lần đầu (chưa có dữ liệu sẵn nên sẽ báo lỗi 404 cho tới khi bạn
bấm nút này).

## 4. Deploy lên Vercel

1. Đẩy code lên một repo GitHub (repo riêng tư nếu không muốn công khai)
2. Vào https://vercel.com → **Add New Project** → chọn repo vừa tạo
3. Ở bước cấu hình, vào **Environment Variables**, thêm:
   - `GEMINI_API_KEY` = key của bạn
   - `CRON_SECRET` = chuỗi ngẫu nhiên bạn đã tạo (nếu dùng)
4. Bấm **Deploy**

Sau khi deploy, Vercel sẽ tự đọc file `vercel.json` và **tự động gọi
`/api/news/update` mỗi ngày lúc 01:00 UTC (~8h sáng giờ Việt Nam)** để cập nhật tin
mới — không cần bạn thao tác gì thêm. Muốn đổi giờ, sửa `schedule` trong
`vercel.json` (định dạng cron chuẩn, giờ theo UTC).

### ⚠️ Lưu trữ dữ liệu trên Vercel

Project này lưu tin tức mỗi ngày thành file JSON trong thư mục `data/`. Điều này
hoạt động tốt khi chạy **local** hoặc trên **VPS riêng**. Nhưng trên **Vercel**,
filesystem ở môi trường production là **read-only** (trừ thư mục tạm `/tmp`, và
`/tmp` bị xoá sau mỗi lần "nguội" server) — nghĩa là dữ liệu ghi vào `data/` lúc
runtime sẽ **không được lưu vĩnh viễn** giữa các lần cron chạy.

Có 2 hướng xử lý, tuỳ nhu cầu:

- **Đơn giản, ít tốn công**: Deploy lên **VPS riêng** (Docker/PM2) thay vì Vercel.
  Filesystem ở đó ghi/đọc bình thường, không cần sửa code.
- **Giữ Vercel, cần lưu bền vững**: Thay `lib/store.ts` bằng một dịch vụ lưu trữ
  key-value, ví dụ [Vercel KV](https://vercel.com/docs/storage/vercel-kv) hoặc
  [Vercel Blob](https://vercel.com/docs/storage/vercel-blob). Cấu trúc code đã
  tách riêng phần đọc/ghi vào `lib/store.ts` nên bạn chỉ cần sửa 4 hàm trong file
  đó (`saveDailyNews`, `loadDailyNews`, `listAvailableDates`, `todayKey` giữ
  nguyên), không cần đụng vào phần giao diện hay API routes khác.

## 5. Cấu trúc project

```
app/
  page.tsx                     Trang chủ
  tin-tuc/page.tsx              Trang bảng tin hằng ngày
  tra-cuu/page.tsx              Trang tra cứu mã CK
  api/news/today/route.ts       API: lấy tin đã lưu của 1 ngày
  api/news/update/route.ts      API: gọi Gemini tổng hợp tin mới + lưu lại
  api/stock/[symbol]/route.ts   API: gọi Gemini tra cứu 1 mã CK
components/
  NavBar.tsx                    Thanh điều hướng
  NewsBoard.tsx                 Component bảng tin (client-side)
  StockLookup.tsx                Component tra cứu mã CK (client-side)
  CategoryBadge.tsx             Badge màu cho loại tin
lib/
  types.ts                      Định nghĩa kiểu dữ liệu
  gemini.ts                     Logic gọi Gemini API + prompt
  store.ts                      Đọc/ghi dữ liệu tin tức theo ngày
data/                           Nơi lưu file JSON tin tức mỗi ngày
vercel.json                     Cấu hình Vercel Cron (tự động cập nhật mỗi ngày)
```

## 6. Về độ chính xác dữ liệu

Toàn bộ tin tức, chỉ số tài chính, và phân tích đều do **AI (Gemini) tự tìm kiếm và
tổng hợp**, không phải dữ liệu real-time từ sàn giao dịch chính thức. AI có thể tìm
sai, thiếu, hoặc lỗi thời tuỳ chất lượng kết quả tìm kiếm tại thời điểm gọi. Nên:

- Luôn đối chiếu số liệu quan trọng (giá, P/E, vốn hóa...) với nguồn chính thức như
  HOSE, HNX, hoặc các công ty chứng khoán trước khi ra quyết định.
- Phần "phân tích" trong trang tra cứu mã CK **không phải lời khuyên đầu tư** — chỉ
  giúp bạn có góc nhìn tổng quan nhanh.

## 7. Bảo mật & chi phí cần lưu ý

- **Không commit** file `.env.local` lên GitHub (đã được `.gitignore` chặn sẵn).
- Gemini API có hạn mức miễn phí theo phút/ngày tuỳ model — nếu app có nhiều người
  dùng đồng thời bấm "Cập nhật" hoặc tra cứu liên tục, có thể vượt hạn mức miễn phí
  và phát sinh phí. Xem bảng giá: https://ai.google.dev/pricing
- Endpoint `/api/news/update` nên luôn có `CRON_SECRET` khi deploy công khai, để
  tránh người lạ spam gọi tốn phí.
- Dự án dùng Next.js 14.2.x — dòng này liên tục có các bản vá bảo mật quan trọng
  (một số ở mức nghiêm trọng, RCE). Trước khi deploy thật, chạy `npm outdated next`
  và cân nhắc `npm install next@latest` (dòng 15/16) nếu không phụ thuộc API cũ,
  hoặc ít nhất `npm update next` để lấy bản vá mới nhất trong dòng 14.x.
