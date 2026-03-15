FROM python:3.12.6-slim-bullseye

WORKDIR /app

COPY requirements.txt .

# Install essential system dependencies
RUN apt-get update && \
    apt-get install -y build-essential cmake pkg-config && \
    apt-get upgrade -y && \
    pip install --upgrade pip && \
    pip install --no-cache-dir --timeout 900 -r requirements.txt && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY . . 

# Tạo thư mục instance với quyền đúng
RUN mkdir -p /app/instance && \
    chmod 755 /app/instance && \
    chown -R root:root /app/instance

# Tạo database và chạy migrations
RUN python -c "from app import create_app; from app.db import db; app = create_app(); \
with app.app_context(): db.create_all(); print('Database initialized successfully!')" \
|| echo "Database initialization failed, will create at runtime"

# Chạy seed_data.py để tạo admin user
RUN python seed_data.py || echo "Seed data execution failed, admin may already exist or will be created at runtime"

EXPOSE 5000

CMD ["python", "main.py"]