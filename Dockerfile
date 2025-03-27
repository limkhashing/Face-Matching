# Use the official Python image from the Docker Hub
FROM python:3.9-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /app

# Copy the requirements file into the image
COPY requirements.txt /app/

# Install system dependencies
RUN apt-get update && \
    apt-get install -y \
    libsm6 \
    libxrender1 \
    libfontconfig1 \
    libice6 \
    libxext6 \
    libopenblas-dev \
    liblapack-dev \
    libopenblas-dev \
    liblapack-dev \
    wget \
    tesseract-ocr \
    tesseract-ocr-eng \
    libgl1-mesa-glx \
    ffmpeg \
    build-essential \
    cmake \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . /app/

# Expose the port the app runs on
EXPOSE 5100

# Run the application
CMD ["python", "app.py"]
