FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Upgrade pip untuk menghindari masalah instalasi
RUN pip install --upgrade pip

# Copy dan install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy sisa file aplikasi
COPY . .

# Ekspos port 8501
EXPOSE 8501

# Gunakan python -m streamlit untuk memastikan library terpanggil dari lingkungan yang benar
CMD ["python", "-m", "streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]