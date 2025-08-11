#!/bin/bash

# Install system dependencies
apt-get update && apt-get install -y \
    poppler-utils \
    libpoppler-cpp-dev \
    && rm -rf /var/lib/apt/lists/*

# Create certificates directory
mkdir -p certificates

# Start the application
streamlit run main.py --server.port=${PORT:-8080} --server.address=0.0.0.0 --server.enableCORS=false --server.enableXsrfProtection=false --server.headless=true
