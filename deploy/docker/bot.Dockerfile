FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY apps ./apps
COPY src ./src

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

CMD ["python", "-m", "apps.bot.main"]