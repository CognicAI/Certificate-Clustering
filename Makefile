# Certificate Segregator - Docker Makefile
.PHONY: help build run stop clean logs shell test dev

# Default target
help: ## Show this help message
	@echo "Certificate Segregator - Docker Commands"
	@echo "========================================"
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*?##/ { printf "  %-15s %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

# Environment setup
setup: ## Set up environment file from example
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "✅ Created .env file from .env.example"; \
		echo "⚠️  Please edit .env and add your Google Gemini API key"; \
	else \
		echo "✅ .env file already exists"; \
	fi

# Docker build
build: ## Build the Docker image
	@echo "🔨 Building Docker image..."
	docker build -t certificate-segregator .
	@echo "✅ Build complete!"

# Docker run (production)
run: setup ## Run the application with Docker Compose
	@echo "🚀 Starting Certificate Segregator..."
	docker-compose up -d
	@echo "✅ Application started at http://localhost:8501"

# Development mode
dev: setup ## Run in development mode with live reload
	@echo "🔧 Starting development environment..."
	docker-compose --profile dev up certificate-segregator-dev
	@echo "✅ Development server started at http://localhost:8502"

# Stop services
stop: ## Stop all running containers
	@echo "🛑 Stopping containers..."
	docker-compose down
	@echo "✅ Containers stopped"

# View logs
logs: ## View application logs
	docker-compose logs -f certificate-segregator

# View development logs
logs-dev: ## View development logs
	docker-compose logs -f certificate-segregator-dev

# Shell access
shell: ## Open shell in running container
	docker exec -it certificate-segregator /bin/bash

# Clean up
clean: ## Remove containers and images
	@echo "🧹 Cleaning up Docker resources..."
	docker-compose down --rmi all --volumes --remove-orphans
	docker image prune -f
	@echo "✅ Cleanup complete"

# Restart
restart: stop run ## Restart the application

# Update and restart
update: ## Pull latest code and restart
	@echo "📥 Pulling latest changes..."
	git pull
	@echo "🔨 Rebuilding and restarting..."
	docker-compose up --build -d
	@echo "✅ Update complete!"

# Test the application
test: ## Test if the application is running correctly
	@echo "🧪 Testing application health..."
	@if curl -f -s http://localhost:8501/_stcore/health > /dev/null; then \
		echo "✅ Application is healthy and running!"; \
	else \
		echo "❌ Application is not responding"; \
		exit 1; \
	fi

# View running containers
status: ## Show status of containers
	@echo "📊 Container Status:"
	@docker ps --filter "name=certificate-segregator" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Install dependencies locally (for development)
install: ## Install Python dependencies locally
	pip install -r requirements.txt

# Backup certificates
backup: ## Backup organized certificates
	@echo "💾 Creating backup of certificates..."
	@tar -czf certificates-backup-$(shell date +%Y%m%d-%H%M%S).tar.gz certificates/
	@echo "✅ Backup created!"

# View certificate folders
certs: ## List organized certificate folders
	@echo "📁 Organized Certificate Folders:"
	@ls -la certificates/ 2>/dev/null || echo "No certificates folder found"

# Monitor resource usage
monitor: ## Monitor Docker container resource usage
	docker stats certificate-segregator

# Environment info
info: ## Show environment information
	@echo "🔍 Environment Information:"
	@echo "================================"
	@echo "Docker version: $(shell docker --version)"
	@echo "Docker Compose version: $(shell docker-compose --version)"
	@echo "Current directory: $(shell pwd)"
	@echo "Git branch: $(shell git branch --show-current 2>/dev/null || echo 'Not a git repository')"
	@echo "API key configured: $(shell [ -f .env ] && grep -q '^key=' .env && echo 'Yes' || echo 'No')"
