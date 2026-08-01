FROM python:3.11-slim
WORKDIR /app

# Install wkhtmltopdf and its dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    ca-certificates \
    fontconfig \
    libxrender1 \
    libxext6 \
    libx11-6 \
    xfonts-75dpi \
    xfonts-base \
    wkhtmltopdf \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
