# 🚀 Deployment Guide - Phantoms JWT Generator

## 📋 Deployment Options

### 1. 🔷 Vercel Deployment

**Steps:**
1. Push code to GitHub repository
2. Connect Vercel to your GitHub account
3. Import your repository in Vercel dashboard
4. Set environment variables:
   ```
   SESSION_SECRET=your-secret-key-here
   ```
5. Deploy automatically

**Files Required:**
- ✅ `vercel.json` (created)
- ✅ `main.py` (updated for deployment)

**Command Line Deployment:**
```bash
npm i -g vercel
vercel --prod
```

### 2. 🟦 Netlify Deployment

**Steps:**
1. Push code to GitHub repository
2. Connect Netlify to your GitHub account
3. Set build command: `echo 'Build complete'`
4. Set publish directory: `.`
5. Set environment variables:
   ```
   SESSION_SECRET=your-secret-key-here
   ```

**Files Required:**
- ✅ `netlify.toml` (created)
- ✅ `.netlify/functions/app.py` (created)

**Command Line Deployment:**
```bash
npm install -g netlify-cli
netlify deploy --prod
```

### 3. 🟣 Heroku Deployment

**Steps:**
1. Create Heroku app: `heroku create your-app-name`
2. Set environment variables:
   ```bash
   heroku config:set SESSION_SECRET=your-secret-key-here
   ```
3. Deploy:
   ```bash
   git push heroku main
   ```

**Files Required:**
- ✅ `Procfile` (created)
- ✅ `runtime.txt` (created)
- ✅ `requirements.txt` (system managed)

### 4. ☁️ Google Cloud Platform

**Steps:**
1. Enable App Engine API
2. Install Google Cloud SDK
3. Deploy:
   ```bash
   gcloud app deploy
   ```

**Files Required:**
- ✅ `app.yaml` (created)

## 🔧 Environment Variables Required

```bash
SESSION_SECRET=your-strong-secret-key-minimum-32-characters
```

**Generate Secret Key:**
```python
import secrets
print(secrets.token_hex(32))
```

## 📦 Dependencies

All dependencies are automatically managed by the deployment platforms:
- Flask 3.0.0
- Flask-Caching 2.1.0
- Flask-Limiter 3.5.0
- Requests 2.31.0
- PyCryptodome 3.19.0
- Protobuf 4.25.1
- Aiohttp 3.9.1
- And more...

## 🌟 Features Available in Deployment

✅ **JWT Token Generation** - Single & Bulk
✅ **Like System** - 113 tokens maximum likes  
✅ **Discord Webhook Integration** - Real-time notifications
✅ **File Upload Processing** - TXT/JSON support
✅ **Rate Limiting** - Anti-abuse protection
✅ **Session Management** - Secure token storage
✅ **Real UID Detection** - JWT decoder integration

## 🔗 Post-Deployment Setup

1. **Test the deployment:**
   - Visit your deployed URL
   - Try single token generation
   - Test bulk upload feature
   - Verify Discord webhook notifications

2. **Update Discord Webhook URL** (if needed):
   - Current webhook: `https://discord.com/api/webhooks/1394715737947508897/WFsiHBtLlJs2HfiphF9Y8yw35Ztv5BT_WMNPiJGDrNNaTA6TjOFRYswyzOcPpvwsvYwk`

3. **Monitor Performance:**
   - Check response times
   - Monitor rate limits
   - Verify all features work correctly

## 🚨 Important Notes

- **Session Cookie Size**: Large token lists may hit browser limits
- **Request Timeouts**: Some platforms have 30s timeout limits
- **Rate Limiting**: Built-in protection against abuse
- **File Size Limits**: Platform-specific upload limits apply

## 🎯 Recommended Platform

**For your use case, I recommend Vercel:**
- ✅ Easy GitHub integration
- ✅ Automatic deployments
- ✅ Good performance for Flask apps
- ✅ Built-in CDN
- ✅ Free tier available

Your gaming application is now ready for production deployment! 🎮