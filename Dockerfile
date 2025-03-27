# Use the official Python image from the Docker Hub
FROM python:3.8

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
    wget \
    tesseract-ocr \
    tesseract-ocr-eng \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# Install libpng12 from the provided URL
RUN wget https://launchpad.net/~ubuntu-security/+archive/ubuntu/ppa/+build/15108504/+files/libpng12-0_1.2.54-1ubuntu1.1_amd64.deb && \
    dpkg -i libpng12-0_1.2.54-1ubuntu1.1_amd64.deb && \
    rm libpng12-0_1.2.54-1ubuntu1.1_amd64.deb

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . /app/

# Expose the port the app runs on
EXPOSE 5100

# Run the application
CMD ["python", "app.py"]
#CMD ["gunicorn", "--pythonpath", "src", "app:app", "-w", "3", "--timeout", "60", "--max-requests", "1200", "--log-level=DEBUG"]