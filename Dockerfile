FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for OpenCV and Tesseract
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-hin \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements_enhanced.txt .
RUN pip install --no-cache-dir -r requirements_enhanced.txt gunicorn

# Copy project files
COPY . .

# Environment setup
ENV FLASK_ENV=production
ENV RAKSHA_LIVENESS_SECRET="change-this-in-production"
ENV PORT=5000

# Expose port
EXPOSE 5000

# Run the app with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "3", "app_enhanced:app"]
