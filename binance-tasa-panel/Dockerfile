# Imagen oficial: Python + Chromium/Firefox/WebKit + deps del sistema
# https://playwright.dev/python/docs/docker
FROM mcr.microsoft.com/playwright/python:v1.49.1-jammy

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app/backend \
    FLASK_HOST=0.0.0.0 \
    FLASK_PORT=10001 \
    PLAYWRIGHT_HEADLESS=true

# Dependencias Python (navegadores ya incluidos en la imagen base)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Código de la aplicación
COPY backend/ ./backend/
COPY scraper/ ./scraper/
COPY frontend/ ./frontend/

# Datos persistentes (montar volumen en /app/data en producción)
RUN mkdir -p /app/data \
    && useradd -m -u 1000 -s /bin/bash appuser \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 10001

# Producción: Gunicorn (no usar app.run dentro del contenedor)
CMD ["gunicorn", \
     "--bind", "0.0.0.0:10001", \
     "--workers", "2", \
     "--threads", "4", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "app:app"]
