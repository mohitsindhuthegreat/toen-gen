# 🎮 Phantoms JWT Generator

A robust JWT token generation and management platform designed for high-performance gaming authentication with advanced multi-region support and intelligent token handling.

## ✨ Features

🚀 **Fast Token Generation** - Generate real, unique tokens in under 1 second  
🎯 **Bulk Processing** - Upload files with multiple credentials for batch processing  
💕 **Smart Like System** - Send up to 113 real likes using all available tokens  
🔗 **Discord Integration** - Automatic webhook notifications for file uploads  
⚡ **Rate Limiting Protection** - Smart batching to avoid 429 errors  
🔍 **Real UID Detection** - JWT decoder extracts authentic user IDs  
📊 **Session Management** - Secure token storage and retrieval  

## 🚀 Quick Start

### Local Development
```bash
git clone <repository>
cd phantoms-jwt-generator
python main.py
```

### Deploy to Production

#### Vercel (Recommended)
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel --prod

# Set environment variable
vercel env add SESSION_SECRET
```

#### Netlify
```bash
# Install Netlify CLI  
npm i -g netlify-cli

# Deploy
netlify deploy --prod
```

#### Heroku
```bash
# Create app
heroku create your-app-name

# Set environment variable
heroku config:set SESSION_SECRET=your-secret-key

# Deploy
git push heroku main
```

## 🔧 Environment Variables

```bash
SESSION_SECRET=your-strong-secret-key-minimum-32-characters
```

Generate a secure key:
```python
import secrets
print(secrets.token_hex(32))
```

## 📱 Usage

### Single Token Generation
1. Enter UID and password
2. Click "Generate Token"
3. Copy your JWT token

### Bulk Token Processing  
1. Upload TXT or JSON file with credentials
2. System processes all accounts
3. Download results in multiple formats
4. Receive Discord notifications

### Like System
1. Generate tokens first
2. Enter target UID and server
3. System sends likes using all available tokens
4. Real-time progress tracking

## 🎯 API Endpoints

- `POST /api/token` - Generate single token
- `POST /api/bulk-token` - Bulk token generation  
- `POST /api/like` - Send likes to player
- `GET /api/download/<format>` - Download results

## 🔍 Discord Webhook Integration

All bulk uploads are automatically sent to your Discord webhook:
- File upload notifications
- Processing results with statistics  
- Real-time monitoring

## 🛡️ Security Features

- Rate limiting (200 requests/day, 50/hour)
- Input validation and sanitization
- Secure file handling
- Session-based CSRF protection
- AES encryption for sensitive data

## 📊 Performance

- **Token Generation**: ~0.3 seconds per token
- **Bulk Processing**: 75+ tokens/sec with parallel processing
- **Like System**: 113 real likes maximum per request
- **Smart Batching**: 5 tokens per batch with 1.5s delays

## 🎮 Gaming Features

- Multi-region support (IND, US, General)
- Real UID extraction from JWT tokens
- Intelligent retry logic for network issues
- Background processing for large operations
- Comprehensive error handling

## 📚 File Formats Supported

**JSON Format:**
```json
[
  {
    "guest_account_info": {
      "com.garena.msdk.guest_uid": "1234567890",
      "com.garena.msdk.guest_password": "password123"
    }
  }
]
```

**TXT Format:**
```
UID: 1234567890
Password: password123

UID: 9876543210
Password: anotherpass456
```

## 🔧 Technical Stack

- **Backend**: Flask 3.0.0 with extensions
- **Authentication**: JWT with AES encryption
- **Networking**: Aiohttp for async requests
- **Data**: Protocol Buffers for serialization
- **Frontend**: Bootstrap 5 + Vanilla JavaScript
- **Deployment**: Multi-platform support

## 📈 Monitoring

- Built-in logging and debug information
- Performance metrics tracking
- Error reporting and recovery
- Real-time status updates

---

**Ready for production deployment!** 🚀

Choose your preferred platform and follow the deployment guide for setup instructions.