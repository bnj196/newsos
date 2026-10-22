# S0szalo - Zalo SOS Dead Man's Switch Bot Backend 🚨

Hệ thống Bot Backend Zalo triển khai cơ chế **"Dead Man's Switch" (Công tắc cứu hộ tự động)**, hỗ trợ triển khai chuẩn hóa qua **Docker & Docker Compose**.

Hệ thống được thiết kế dành cho người dùng khi đi vào các tình huống có rủi ro hoặc nguy hiểm (đi công tác xa, đi rừng, làm việc mạo hiểm, khám phá, hoặc phòng ngừa bất trắc). Người dùng có thể cấu hình trước các thông điệp cứu hộ, thời hạn phản hồi và danh sách bạn bè/người thân. Nếu quá thời hạn đếm ngược mà người dùng **không tắt lệnh**, Bot sẽ **tự động gửi tin nhắn cứu hộ khẩn cấp** kèm theo thông tin chi tiết đến danh sách bạn bè đã chuẩn bị trước!

---

## 📖 1. Câu Chuyện Người Dùng (User Story) & Quy Tắc Hoạt Động

### Câu chuyện:
- **Người dùng chuẩn bị trước rủi ro:** Trước khi bắt đầu một hoạt động rủi ro (hoặc dự định có thể gặp nạn), người dùng vào **nhóm Zalo nội bộ** (Internal Group - nhóm quản trị điều khiển) để cấu hình danh sách người nhận tin khẩn cấp và nội dung cứu hộ.
- **Bật chế độ khẩn cấp (ARM / START):** Người dùng kích hoạt lệnh hẹn giờ với một khoảng thời gian đếm ngược (ví dụ: `30m`, `1h`, `2h`, `45m`).
- **Quy tắc đếm ngược:**
  1. **Trường hợp an toàn (SAFE):** Nếu người dùng hoàn thành công việc hoặc trở về an toàn trước hạn chót, chỉ cần gõ `/sos safe` (hoặc `/sos cancel`). Hệ thống ngay lập tức **hủy đếm ngược**, không gửi bất kỳ tin nhắn nào đến bạn bè.
  2. **Trường hợp gặp nạn / Quá hạn không phản hồi (DEADLINE EXPIRED):** 
     - Trước khi hết hạn 5 phút và 1 phút, bot sẽ gửi cảnh báo khẩn cấp vào nhóm nội bộ nhắc nhở người dùng báo an toàn.
     - **Nếu quá thời hạn mà người dùng KHÔNG tắt lệnh**, hệ thống xác định người dùng đang gặp nguy hiểm và **TỰ ĐỘNG GỬI TIN NHẮN SOS** đến toàn bộ danh sách bạn bè/người thân đã cấu hình!
     - Đồng thời, bot gửi báo cáo tổng kết chi tiết vào nhóm nội bộ để thông báo kết quả gửi cứu hộ.
  3. **Trường hợp cần thêm thời gian (EXTEND):** Nếu chưa hoàn thành công việc kịp thời hạn, người dùng có thể gõ `/sos extend 30m` để gia hạn thêm.

---

## 🛠️ 2. Nơi Nhận & Cấu Hình Lệnh (Nhóm Nội Bộ)

Các lệnh quản trị và điều khiển SOS được bảo vệ an toàn:
- Được lắng nghe và xử lý trong **nhóm Zalo nội bộ** (Internal Control Group).
- Bot xác định nhóm nội bộ thông qua biến môi trường `INTERNAL_GROUP_ID` hoặc tự động tìm theo `INTERNAL_GROUP_NAME` (mặc định: `test group`).
- Ngoài ra, có thể kích hoạt nhóm hiện tại làm nhóm nội bộ bằng cách gõ lệnh:
  ```text
  /sos setgroup
  ```
- Tin nhắn trong các nhóm khác hoặc người lạ nhắn sẽ bị bỏ qua, chống việc người ngoài can thiệp tắt/bật cảnh báo.

---

## 📋 3. Bảng Lệnh Điều Khiển Zalo

| Lệnh | Cú pháp | Mô tả |
| :--- | :--- | :--- |
| **Trợ giúp** | `/sos help` hoặc `/help` | Xem danh sách hướng dẫn chi tiết các lệnh |
| **Trạng thái** | `/sos status` | Xem trạng thái đếm ngược, danh bạ SOS & tin nhắn mẫu |
| **Mẫu SOS** | `/sos setmsg <nội dung>` | Cấu hình nội dung tin nhắn SOS (hỗ trợ `{time}`) |
| **Thêm bạn bè** | `/sos add <uid> [tên]` | Thêm Zalo UID bạn bè nhận tin (hoặc tag `@NgườiDùng`) |
| **Xóa bạn bè** | `/sos remove <uid>` | Xóa bạn bè khỏi danh bạ nhận tin SOS |
| **Danh bạ** | `/sos list` | Xem danh sách bạn bè đã cấu hình nhận tin |
| **Bật đếm ngược** | `/sos start <thời gian>` | Bắt đầu đếm ngược (VD: `/sos start 30m`, `/sos start 1h`) |
| **Báo an toàn** | `/sos safe` hoặc `/sos cancel` | **HỦY ĐẾM NGƯỢC**, xác nhận an toàn, không gửi SOS |
| **Gia hạn** | `/sos extend <thời gian>` | Cộng thêm thời gian đếm ngược (VD: `/sos extend 45m`) |
| **Gửi khẩn cấp** | `/sos now` hoặc `/sos trigger` | Gửi tin nhắn SOS đến bạn bè **NGAY LẬP TỨC** |
| **Thời gian mặc định** | `/sos timeout <số_phút>` | Cài đặt thời gian đếm ngược mặc định (VD: 30) |
| **Cài đặt nhóm** | `/sos setgroup` | Đặt nhóm hiện tại làm nhóm điều khiển nội bộ |
| **Test định dạng** | `/sos test` | Gửi thử tin SOS mẫu vào nhóm nội bộ để kiểm tra |
| **Nhật ký** | `/sos logs` | Xem lịch sử các sự kiện và trạng thái gửi tin |

---

## 🏗️ 4. Cấu Trúc Thư Mục `S0szalo`

```text
S0szalo/
├── zlpp/                    # Thư viện Zalo SDK lõi của bot (hỗ trợ Zalo Web WebSocket)
├── config.py                # Quản lý cấu hình, nạp .env, tải/lưu session cookies
├── database.py              # SQLite persistence (Lưu contacts, sessions, configs, logs)
├── sos_engine.py            # Động cơ Dead Man's Switch, tính giờ, cảnh báo, broadcast SOS
├── bot_handler.py           # Bộ định tuyến & xử lý các câu lệnh Zalo
├── api.py                   # Flask REST API phục vụ Docker Healthcheck & Webhook điều khiển
├── main.py                  # Entrypoint chính khởi chạy Bot & Background Worker
├── Dockerfile               # File build Docker container siêu nhẹ (Python 3.11-slim)
├── docker-compose.yml       # Cấu hình Docker Compose có mount volume dữ liệu bền vững
├── .dockerignore            # Danh sách bỏ qua khi build image
├── .env.example             # File mẫu biến môi trường
├── requirements.txt         # Thư viện phụ thuộc
└── README.md                # Tài liệu hướng dẫn sử dụng
```

---

## 🚀 5. Hướng Dẫn Triển Khai Docker

### Bước 1: Chuẩn bị file `.env`
Sao chép `.env.example` thành `.env` và điền cấu hình tài khoản:
```bash
cp .env.example .env
```
Các thông số quan trọng:
- `ZALO_PHONE`: Số điện thoại Zalo của bot.
- `ZALO_PASSWORD`: Mật khẩu Zalo.
- `ZALO_IMEI`: IMEI thiết bị.
- `INTERNAL_GROUP_NAME`: Tên nhóm Zalo nội bộ để nhận lệnh (hoặc điền `INTERNAL_GROUP_ID`).

### Bước 2: Khởi chạy bằng Docker Compose
```bash
docker compose up -d --build
```

### Bước 3: Kiểm tra Logs & Tình trạng Container
```bash
# Xem log trực tiếp của bot
docker compose logs -f

# Kiểm tra container healthcheck
docker compose ps
```

Container đã được cấu hình:
- Tự khởi động lại nếu có sự cố (`restart: unless-stopped`).
- Mount volume `./data:/app/data` để **dữ liệu SQLite và session cookies không bị mất** khi nâng cấp hoặc restart container.
- Tích hợp `HEALTHCHECK` tự động giám sát bot qua endpoint `http://localhost:8080/health`.

---

## 💻 6. Hướng Dẫn Chạy Cục Bộ (Không Dùng Docker)

### Cài đặt môi trường:
```bash
python -m venv .venv
# Trên Windows:
.venv\Scripts\activate
# Trên Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

### Khởi chạy:
```bash
python main.py
```

---

## 🌐 7. REST API & Webhook Endpoints

Hệ thống cung cấp sẵn các API trên port `8080`:
- `GET /health`: Kiểm tra sức khỏe của bot (trả về trạng thái kết nối Zalo và uptime).
- `GET /api/status`: Lấy trạng thái phiên đếm ngược hiện tại, danh sách contacts.
- `POST /api/arm`: Kích hoạt đếm ngược từ xa qua HTTP POST:
  ```json
  {
    "user_id": "84793634088",
    "duration": "45m",
    "message": "Nội dung SOS tùy chọn"
  }
  ```
- `POST /api/safe`: Báo an toàn từ xa qua HTTP POST:
  ```json
  {
    "user_id": "84793634088"
  }
  ```
