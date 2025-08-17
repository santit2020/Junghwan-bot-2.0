# ============================
# Base Image
# ============================
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# ============================
# Install system dependencies
# ============================
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ============================
# Install Python dependencies
# ============================
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ============================
# Copy application files
# ============================
COPY . .

# Create __init__.py for all directories (makes them Python packages)
RUN find . -type d -not -path "./.git*" -not -path "./.*" -exec touch {}/__init__.py \;

# ============================
# Create non-root user for security
# ============================
RUN useradd -m -u 1000 botuser && chown -R botuser:botuser /app
USER botuser

# ============================
# Environment variables
# ============================
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# ============================
# Expose port for healthcheck HTTP server
# ============================
EXPOSE 8080

# ============================
# Health Check
# ============================
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# ============================
# Start the bot
# ============================
CMD ["python", "main.py"]

