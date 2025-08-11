# DigitalOcean App Platform Deployment Guide

## Overview
This guide will help you deploy the Certificate Clustering application to DigitalOcean App Platform.

## Prerequisites
- DigitalOcean account
- GitHub repository with the code
- Google Gemini API key

## Files Created for Deployment

### 1. `.do/app.yaml` - App Platform Configuration
- Defines the application structure
- Sets environment variables
- Configures routing and scaling

### 2. `runtime.txt` - Python Version
- Specifies Python 3.11.6 for consistent deployment

### 3. `.streamlit/config.toml` - Streamlit Configuration
- Optimized settings for cloud deployment
- Disabled development features
- Configured for headless operation

### 4. `start.sh` - Startup Script
- Installs system dependencies (poppler-utils)
- Creates necessary directories
- Starts the Streamlit application

### 5. `Procfile` - Process Definition
- Alternative deployment configuration
- Defines the web process command

## Deployment Steps

### Step 1: Push Code to GitHub
```bash
git add .
git commit -m "Add DigitalOcean App Platform deployment configuration"
git push origin main
```

### Step 2: Create App on DigitalOcean
1. Log into your DigitalOcean account
2. Go to the Apps section
3. Click "Create App"
4. Choose "GitHub" as the source
5. Select your repository: `CognicAI/Certificate-Clustering`
6. Choose the `main` branch
7. DigitalOcean will auto-detect the app configuration from `.do/app.yaml`

### Step 3: Configure Environment Variables
In the DigitalOcean App Platform dashboard:
1. Go to Settings → Environment Variables
2. Add the following variable:
   - **Key**: `key`
   - **Value**: Your Google Gemini API key
   - **Type**: Encrypted (Secret)

### Step 4: Deploy
1. Review the app configuration
2. Click "Create Resources"
3. Wait for deployment to complete (5-10 minutes)

### Step 5: Access Your Application
Once deployed, you'll receive a URL like:
`https://certificate-clustering-xxxxx.ondigitalocean.app`

## Configuration Details

### Resource Allocation
- **Instance Size**: Basic XXS (512 MB RAM, 0.5 vCPU)
- **Instance Count**: 1
- **Scaling**: Can be increased in settings

### System Dependencies
The application requires:
- `poppler-utils` - For PDF processing
- `libpoppler-cpp-dev` - PDF library development files

These are automatically installed via the startup script.

### Port Configuration
- **Application Port**: 8080
- **Streamlit Configuration**: Configured for cloud deployment
- **CORS**: Disabled for security

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `key` | Google Gemini API Key | ✅ Yes |
| `PORT` | Application port (auto-set) | ✅ Auto |
| `STREAMLIT_SERVER_PORT` | Streamlit port | ✅ Auto |
| `STREAMLIT_SERVER_ADDRESS` | Server address | ✅ Auto |
| `STREAMLIT_SERVER_HEADLESS` | Headless mode | ✅ Auto |

## Troubleshooting

### Common Issues

1. **API Key Not Found**
   - Ensure the `key` environment variable is set
   - Check that it's marked as "Encrypted"
   - Verify the API key is valid

2. **PDF Processing Errors**
   - System dependencies are installed via startup script
   - Check deployment logs for poppler installation errors

3. **Application Won't Start**
   - Check the deployment logs
   - Verify all dependencies in requirements.txt
   - Ensure Python version compatibility

### Checking Logs
1. Go to your app in DigitalOcean dashboard
2. Click on the "Runtime Logs" tab
3. Check for any error messages

### Redeployment
To redeploy after changes:
1. Push changes to GitHub
2. DigitalOcean will auto-deploy (if enabled)
3. Or manually trigger deployment in the dashboard

## Cost Estimation
- **Basic XXS Instance**: ~$5/month
- **Bandwidth**: Usually covered in the base plan
- **Storage**: Ephemeral (files don't persist between deployments)

## Security Considerations
- API key is encrypted and secure
- CORS is disabled for security
- Application runs in isolated container
- HTTPS is automatically provided

## Scaling Options
If you need more resources:
1. Increase instance size (Basic XS, S, M)
2. Increase instance count for load balancing
3. Add database component for persistent storage

## Monitoring
DigitalOcean provides:
- CPU and memory usage metrics
- Request logs and error tracking
- Uptime monitoring
- Performance insights

## Support
- DigitalOcean documentation: https://docs.digitalocean.com/products/app-platform/
- Community forums for troubleshooting
- Direct support for paid plans
