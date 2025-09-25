# VAITP-Auditor Docker Image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DISPLAY=:99

# Install system dependencies
RUN apt-get update && apt-get install -y \
    xvfb \
    x11-utils \
    libgtk-3-0 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libfontconfig1 \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY setup.py .
COPY vaitp_auditor/ ./vaitp_auditor/
RUN pip install --no-cache-dir -e .[gui]

# Copy application files
COPY . .

# Create non-root user
RUN useradd -m -u 1000 vaitp && chown -R vaitp:vaitp /app
USER vaitp

# Expose port for web interface (if added in future)
EXPOSE 8080

# Start Xvfb and run the application
CMD ["sh", "-c", "Xvfb :99 -screen 0 1024x768x24 & python -m vaitp_auditor.gui"]
