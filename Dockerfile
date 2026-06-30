FROM python:3.11-slim

# Install system dependencies and Node.js
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install python dependencies first to cache docker layers
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install node dependencies
COPY ui/package.json ./ui/
RUN npm install --prefix ./ui

# Copy application files
COPY . .

# Expose port 7860 (Hugging Face default)
EXPOSE 7860
ENV PORT=7860

# Start script
CMD ["python", "start.py"]
