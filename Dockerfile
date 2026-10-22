FROM python:3.11-slim

# Thiết lập biến môi trường
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Asia/Ho_Chi_Minh

WORKDIR /app

# Cài đặt các gói hệ thống cần thiết (nếu có)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Cài đặt thư viện Python
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Tạo thư mục dữ liệu để mount volume
RUN mkdir -p /app/data

# Copy toàn bộ mã nguồn bot vào container
COPY . /app/

# Expose port REST API & Health check
EXPOSE 8080

# Cấu hình Healthcheck kiểm tra tình trạng Bot
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Khởi chạy bot
CMD ["python", "main.py"]
