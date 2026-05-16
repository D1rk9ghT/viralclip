# ── Builder Stage ───────────────────────────────────────
FROM python:3.12-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt


# ── Runtime Stage ───────────────────────────────────────
FROM python:3.12-slim

# Create non-root user
RUN groupadd -r viralclips && useradd -r -g viralclips viralclips

# Install runtime system dependencies (FFmpeg, OpenCV deps)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    libgl1 \
    libpq5 \
    curl \
    yt-dlp \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy wheels from builder and install
COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache /wheels/* && rm -rf /wheels

# Copy application code
COPY . .

# Set permissions
RUN mkdir -p /tmp/viralclips && chown -R viralclips:viralclips /app /tmp/viralclips

# Switch to non-root user
USER viralclips

ENV PORT=8080
ENV PYTHONPATH=/app
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
