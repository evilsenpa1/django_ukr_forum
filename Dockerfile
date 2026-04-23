# ============ Stage 1: Node для Tailwind ============
FROM node:18-alpine AS tailwind-builder

WORKDIR /app

# Копируем только package файлы для кэширования
COPY package*.json ./
RUN npm ci

# Копируем исходники и собираем CSS
COPY templates ./templates  
COPY static ./static   
RUN npm run build


# Используем multi-stage build для минимизации размера
FROM python:3.13.9-slim AS builder

# Устанавливаем build-зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Оптимизируем работу pip
ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Устанавливаем зависимости в отдельный слой
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# === Финальный образ ===
FROM python:3.13.9-slim

# Аргумент для определения окружения
ARG BUILD_ENV=production
ENV BUILD_ENV=${BUILD_ENV}

# Устанавливаем только runtime-зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Создаем непривилегированного пользователя
RUN useradd -m -u 1000 django

# Оптимизируем работу Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/home/django/.local/bin:$PATH

WORKDIR /app

# Копируем установленные пакеты из builder
COPY --from=builder --chown=django:django /root/.local /home/django/.local

# Копируем код приложения
COPY --chown=django:django . .

#copy tailwind css
COPY --from=tailwind-builder --chown=django:django /app/static/css /app/static/css

# Создаем необходимые директории с правильными правами
RUN mkdir -p /app/media /app/staticfiles /app/logs && \
    chown -R django:django /app

# Переключаемся на непривилегированного пользователя
USER django


EXPOSE 8000

