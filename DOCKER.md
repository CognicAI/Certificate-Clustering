# 🐳 Docker Deployment Guide

This guide will help you run the Certificate Segregator using Docker for easy deployment and consistent environments.

## 🚀 Quick Start with Docker

### Prerequisites

- Docker installed on your system
- Docker Compose (included with Docker Desktop)
- Google Gemini AI API key

### 1. Clone the Repository

```bash
git clone https://github.com/harshajustin/Certificate-Clustering.git
cd Certificate-Clustering
```

### 2. Set Up Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit the .env file and add your Google Gemini API key
echo "key=your_actual_api_key_here" > .env
```

### 3. Run with Docker Compose (Recommended)

```bash
# Start the application
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the application
docker-compose down
```

The application will be available at: http://localhost:8501

### 4. Alternative: Run with Docker Only

```bash
# Build the image
docker build -t certificate-segregator .

# Run the container
docker run -d \
  --name certificate-segregator \
  -p 8501:8501 \
  --env-file .env \
  -v $(pwd)/certificates:/app/certificates \
  certificate-segregator
```

## 🛠️ Development with Docker

For development with live code reloading:

```bash
# Start development environment
docker-compose --profile dev up certificate-segregator-dev

# Or run directly
docker run -it \
  -p 8502:8501 \
  -v $(pwd):/app \
  -v $(pwd)/certificates:/app/certificates \
  --env-file .env \
  certificate-segregator \
  streamlit run main.py --server.fileWatcherType=poll
```

## 📁 Volume Mounts

The Docker setup includes several volume mounts:

| Host Path | Container Path | Purpose |
|-----------|----------------|---------|
| `./certificates` | `/app/certificates` | Organized certificate output |
| `./input-certificates` | `/app/input-certificates` | Optional input directory |
| `.` | `/app` | Source code (dev mode only) |

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `key` | Google Gemini API key | - | ✅ Yes |
| `STREAMLIT_SERVER_PORT` | Server port | 8501 | No |
| `STREAMLIT_SERVER_ADDRESS` | Server address | 0.0.0.0 | No |
| `STREAMLIT_SERVER_HEADLESS` | Headless mode | true | No |

### Docker Compose Profiles

| Profile | Purpose | Command |
|---------|---------|---------|
| Default | Production deployment | `docker-compose up` |
| `dev` | Development with live reload | `docker-compose --profile dev up` |

## 🧪 Testing the Docker Setup

1. **Health Check**
   ```bash
   # Check if container is healthy
   docker ps --filter "name=certificate-segregator"
   
   # Check health status
   docker inspect certificate-segregator | grep -A 5 '"Health"'
   ```

2. **Test the Application**
   ```bash
   # Test the health endpoint
   curl http://localhost:8501/_stcore/health
   
   # Open in browser
   open http://localhost:8501
   ```

3. **View Logs**
   ```bash
   # Docker Compose
   docker-compose logs -f certificate-segregator
   
   # Docker only
   docker logs -f certificate-segregator
   ```

## 🐛 Troubleshooting

### Common Issues

**Container won't start:**
```bash
# Check logs
docker-compose logs certificate-segregator

# Common fixes
docker-compose down && docker-compose up --build
```

**Permission issues with volumes:**
```bash
# Fix permissions (Linux/macOS)
sudo chown -R $USER:$USER ./certificates
chmod 755 ./certificates
```

**API key not working:**
```bash
# Verify environment variables
docker exec certificate-segregator env | grep key

# Check .env file format (no spaces around =)
cat .env
```

**Port already in use:**
```bash
# Use different port
docker run -p 8502:8501 certificate-segregator

# Or kill process using port 8501
lsof -ti:8501 | xargs kill -9
```

## 🚀 Production Deployment

### Docker Swarm

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml certificate-segregator
```

### Kubernetes

```yaml
# Save as k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: certificate-segregator
spec:
  replicas: 2
  selector:
    matchLabels:
      app: certificate-segregator
  template:
    metadata:
      labels:
        app: certificate-segregator
    spec:
      containers:
      - name: certificate-segregator
        image: certificate-segregator:latest
        ports:
        - containerPort: 8501
        env:
        - name: key
          valueFrom:
            secretKeyRef:
              name: gemini-api-key
              key: api-key
---
apiVersion: v1
kind: Service
metadata:
  name: certificate-segregator-service
spec:
  selector:
    app: certificate-segregator
  ports:
  - port: 80
    targetPort: 8501
  type: LoadBalancer
```

### Cloud Deployment

**Google Cloud Run:**
```bash
# Build and push
docker build -t gcr.io/YOUR_PROJECT/certificate-segregator .
docker push gcr.io/YOUR_PROJECT/certificate-segregator

# Deploy
gcloud run deploy certificate-segregator \
  --image gcr.io/YOUR_PROJECT/certificate-segregator \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

**AWS ECS/Fargate:**
```bash
# Build and push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin ACCOUNT.dkr.ecr.us-east-1.amazonaws.com
docker build -t certificate-segregator .
docker tag certificate-segregator:latest ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/certificate-segregator:latest
docker push ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/certificate-segregator:latest
```

## 📊 Performance Optimization

### Multi-stage Build (Optional)

```dockerfile
# Build stage
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# Runtime stage
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
CMD ["streamlit", "run", "main.py"]
```

### Resource Limits

```yaml
# In docker-compose.yml
services:
  certificate-segregator:
    # ... other config
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
        reservations:
          memory: 512M
          cpus: '0.25'
```

---

## 🆘 Need Help?

- 📖 Check the main [README.md](README.md) for general usage
- 🐛 Report Docker-specific issues on [GitHub Issues](https://github.com/harshajustin/Certificate-Clustering/issues)
- 💬 Join discussions in [GitHub Discussions](https://github.com/harshajustin/Certificate-Clustering/discussions)

Happy Dockerizing! 🐳
