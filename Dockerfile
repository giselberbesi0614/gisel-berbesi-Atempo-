# ---- Etapa 1: construcción (instala las dependencias en un prefijo aparte) ----
FROM python:3.12-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/instalado -r requirements.txt

# ---- Etapa 2: imagen final, mínima y sin privilegios ----
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ATEMPO_DB=/data/atempo.db \
    ATEMPO_PROXY=1 \
    PORT=8000
RUN useradd --system --uid 10001 --no-create-home atempo \
    && mkdir /data && chown atempo:atempo /data
WORKDIR /app
COPY --from=builder /instalado /usr/local
COPY atempo ./atempo
COPY wsgi.py .
USER atempo
VOLUME /data
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/salud', timeout=3)"
# un solo proceso: el repositorio SQLite mantiene una conexión por proceso
CMD ["gunicorn", "wsgi:app", "--workers", "1", "--threads", "8", "--bind", "0.0.0.0:8000"]
