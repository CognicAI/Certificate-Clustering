# DigitalOcean Deployment Checklist

## Pre-Deployment ✅

- [ ] All code committed and pushed to GitHub
- [ ] Google Gemini API key ready
- [ ] DigitalOcean account created
- [ ] Repository is public or DigitalOcean has access

## Files Created ✅

- [ ] `.do/app.yaml` - App Platform configuration
- [ ] `runtime.txt` - Python version specification
- [ ] `.streamlit/config.toml` - Streamlit cloud configuration
- [ ] `start.sh` - Startup script with dependencies
- [ ] `Procfile` - Process definition
- [ ] `DEPLOYMENT.md` - Deployment guide
- [ ] Updated `requirements.txt` - Pinned versions
- [ ] Updated `main.py` - Cloud-friendly API key handling

## Deployment Steps

### 1. Push to GitHub
```bash
git add .
git commit -m "Add DigitalOcean App Platform deployment configuration"
git push origin main
```

### 2. Create App on DigitalOcean
1. Go to https://cloud.digitalocean.com/apps
2. Click "Create App"
3. Select GitHub source
4. Choose repository: `CognicAI/Certificate-Clustering`
5. Select branch: `main`
6. App configuration will be auto-detected

### 3. Configure Environment Variables
Add in App Settings:
```
key = YOUR_GOOGLE_GEMINI_API_KEY (Encrypted)
```

### 4. Deploy and Test
- Deploy the application
- Test basic functionality
- Upload a sample certificate
- Verify AI processing works

## Post-Deployment Verification

- [ ] Application loads successfully
- [ ] File upload works
- [ ] PDF processing functions
- [ ] AI extraction working
- [ ] Folder creation and file saving
- [ ] Performance metrics display
- [ ] No errors in logs

## Monitoring Setup

- [ ] Check deployment logs
- [ ] Monitor resource usage
- [ ] Set up alerts (optional)
- [ ] Verify HTTPS is working

## Estimated Costs
- Basic XXS instance: ~$5/month
- Additional bandwidth/storage as needed

## Support Resources
- DigitalOcean App Platform docs
- GitHub repository issues
- Community support forums
