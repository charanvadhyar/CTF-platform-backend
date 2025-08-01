# CTF Platform Backend - Quick Start Guide

## 🚀 Quick Setup (5 minutes)

### Option 1: Docker (Recommended)
```bash
cd backend
docker-compose up -d
```
This will start both MongoDB and the backend API at `http://localhost:8000`

### Option 2: Local Development
```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Start MongoDB (if not running)
# Docker: docker run -d -p 27017:27017 mongo
# Or start your local MongoDB service

# Run the application
python main.py
```

## 🔑 Default Admin Credentials
- **Email**: `admin@ctf.com`
- **Password**: `admin123`

## 📚 API Documentation
Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **API Health**: http://localhost:8000/health

## 🧪 Test the API

### 1. Register a new user
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "testuser",
    "password": "password123"
  }'
```

### 2. Login and get token
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }'
```

### 3. Get challenges
```bash
curl -X GET "http://localhost:8000/challenges/" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### 4. Submit a challenge solution (Challenge 1 - Bypass Login)
```bash
curl -X POST "http://localhost:8000/challenges/1/submit" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "challenge_id": "1",
    "submission_data": {
      "username": "admin",
      "password": "anything"
    }
  }'
```

## 🏆 Challenge Solutions (Spoilers!)

<details>
<summary>Click to reveal challenge solutions</summary>

### Challenge 1: Bypass the Login
```json
{
  "username": "admin",
  "password": "anything"
}
```
OR
```json
{
  "username": "anything", 
  "password": "admin"
}
```

### Challenge 2: SQL Injection
```json
{
  "input": "' UNION SELECT flag FROM secrets--"
}
```

### Challenge 4: Cookie Manipulation
```json
{
  "cookie": "admin"
}
```

### Challenge 5: Admin Panel Discovery
```json
{
  "path": "/super/secret/flag"
}
```

</details>

## 🛠️ Development

### Run tests
```bash
pytest tests/ -v
```

### View logs
```bash
# Docker
docker-compose logs -f backend

# Local
# Logs are printed to console
```

### Database access
```bash
# Connect to MongoDB
mongo mongodb://localhost:27017/ctf_platform

# Or with Docker
docker exec -it ctf_mongodb mongo ctf_platform
```

## 🔧 Configuration

Edit `.env` file to customize:
- Database URL
- JWT secret key
- Admin credentials
- CORS origins
- Rate limiting

## 📊 Admin Features

Login as admin to access:
- Challenge management at `/admin/challenges`
- User analytics at `/admin/analytics/users`
- Visit tracking at `/admin/analytics/challenge-visits`
- Advertisement management at `/ads/admin/`

## 🚨 Troubleshooting

### MongoDB Connection Issues
```bash
# Check if MongoDB is running
docker ps | grep mongo

# Restart MongoDB
docker-compose restart mongodb
```

### Port Already in Use
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Or change port in docker-compose.yml
```

### Permission Issues
```bash
# Fix upload directory permissions
mkdir -p uploads
chmod 755 uploads
```

## 🌟 Next Steps

1. **Frontend Integration**: Connect your React/Next.js frontend to this API
2. **Custom Challenges**: Add more challenges by modifying `challenge_validators.py`
3. **Deployment**: Use the provided Docker setup for production
4. **Monitoring**: Add logging and monitoring tools
5. **Security**: Update default credentials and JWT secret in production

Happy hacking! 🎯
