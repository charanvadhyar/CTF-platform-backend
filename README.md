# CTF Platform Backend

A complete FastAPI backend for a Capture The Flag (CTF) web application with 15 interactive challenges, user authentication, admin panel, and analytics.

## Features

### 🔐 Authentication & Authorization
- JWT-based authentication with bcrypt password hashing
- Role-based access control (user/admin)
- Secure token management

### 🧩 Challenge Engine
- 15 interactive CTF challenges covering various web security topics
- Custom validation logic for each challenge
- Real-time submission tracking and scoring

### 📊 Analytics & Tracking
- Visit tracking for each challenge
- User progress monitoring
- Admin analytics dashboard
- Leaderboard system

### 🛡️ Security Features
- CORS protection
- Rate limiting
- Input sanitization
- Security headers (CSP, XSS protection, etc.)
- Environment-based configuration

### 📱 Admin Panel
- Challenge management (CRUD operations)
- User management
- Analytics and reporting
- Advertisement management

## Challenge Categories

| ID | Title | Category | Description |
|----|-------|----------|-------------|
| 1 | Bypass the Login | Authentication | Exploit insecure authentication logic |
| 2 | SQL Injection | SQLi | Extract data using SQL injection |
| 3 | Reflected XSS | XSS | Steal cookies via cross-site scripting |
| 4 | Hidden in the Cookie | Cookie Manipulation | Manipulate cookies for privilege escalation |
| 5 | Guess the Admin Panel | Obscurity | Discover hidden admin endpoints |
| 6 | Client-Side Trust | JS Logic | Extract flags from client-side code |
| 7 | Broken Access Control | IDOR | Access unauthorized user data |
| 8 | Unvalidated Redirect | Open Redirect | Exploit redirect vulnerabilities |
| 9 | Leaky Headers | Info Disclosure | Find sensitive data in HTTP headers |
| 10 | Fake JWT Auth | JWT Attack | Exploit JWT none algorithm vulnerability |
| 11 | Broken File Upload | Upload Abuse | Upload malicious files |
| 12 | Misconfigured Robots | robots.txt | Discover hidden paths |
| 13 | Weak Password Reset | Predictable Tokens | Exploit weak reset tokens |
| 14 | CSP Bypass | CSP Misconfiguration | Bypass Content Security Policy |
| 15 | Hardcoded Secrets | Source Exposure | Find secrets in source code |

## Installation

### Prerequisites
- Python 3.8+
- MongoDB 4.4+
- pip or poetry

### Setup

1. **Clone and navigate to backend directory**
   ```bash
   cd backend
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Start MongoDB**
   ```bash
   # Using Docker
   docker run -d -p 27017:27017 --name mongodb mongo:latest
   
   # Or start local MongoDB service
   mongod
   ```

5. **Run the application**
   ```bash
   python main.py
   # Or using uvicorn directly
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

## API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MONGODB_URL` | MongoDB connection string | `mongodb://localhost:27017` |
| `DATABASE_NAME` | Database name | `ctf_platform` |
| `SECRET_KEY` | JWT secret key | `your-super-secret-jwt-key` |
| `ADMIN_EMAIL` | Default admin email | `admin@ctf.com` |
| `ADMIN_PASSWORD` | Default admin password | `admin123` |
| `ALLOWED_ORIGINS` | CORS allowed origins | `http://localhost:3000` |

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - User login
- `GET /auth/me` - Get current user info
- `GET /auth/verify-token` - Verify JWT token

### Challenges
- `GET /challenges/` - List all challenges
- `GET /challenges/{id}` - Get specific challenge
- `POST /challenges/{id}/submit` - Submit challenge solution

### Admin (Protected)
- `POST /admin/challenges` - Create challenge
- `PATCH /admin/challenges/{id}` - Update challenge
- `DELETE /admin/challenges/{id}` - Delete challenge
- `GET /admin/analytics/challenge-visits` - Visit analytics
- `GET /admin/analytics/users` - User analytics

### Leaderboard
- `GET /leaderboard/` - Get leaderboard
- `GET /leaderboard/progress` - Get user progress

### Ads
- `GET /ads/` - Get advertisements
- `POST /ads/click/{id}` - Track ad click

## Database Schema

### Users Collection
```javascript
{
  _id: ObjectId,
  email: String (unique),
  username: String (unique),
  hashed_password: String,
  role: String, // "user" | "admin"
  score: Number,
  solved_challenges: [String], // Array of challenge IDs
  created_at: Date,
  last_login: Date,
  is_active: Boolean
}
```

### Challenges Collection
```javascript
{
  _id: String, // Challenge ID (1-15)
  challenge_number: Number,
  title: String,
  slug: String (unique),
  category: String,
  description: String,
  points: Number,
  difficulty: String, // "easy" | "medium" | "hard"
  solution_type: String,
  expected_flag: String,
  frontend_hint: String,
  backend_validation_script: String,
  frontend_config: Object,
  is_active: Boolean,
  solve_count: Number,
  created_at: Date,
  updated_at: Date
}
```

### Submissions Collection
```javascript
{
  _id: ObjectId,
  user_id: String,
  challenge_id: String,
  is_correct: Boolean,
  submitted_data: Object,
  result_message: String,
  points_earned: Number,
  timestamp: Date
}
```

## Security Considerations

- **JWT Tokens**: Use strong secret keys in production
- **Password Hashing**: bcrypt with salt rounds
- **Rate Limiting**: Configurable request limits
- **Input Validation**: Pydantic models for all inputs
- **CORS**: Configurable allowed origins
- **Security Headers**: CSP, XSS protection, etc.

## Development

### Running Tests
```bash
pytest tests/ -v
```

### Code Formatting
```bash
black app/
isort app/
```

### Database Migrations
The application automatically creates indexes and default data on startup.

## Production Deployment

1. **Environment Configuration**
   - Set strong `SECRET_KEY`
   - Configure production MongoDB URL
   - Set appropriate CORS origins
   - Enable HTTPS

2. **Database Setup**
   - Use MongoDB Atlas or dedicated MongoDB instance
   - Enable authentication
   - Configure backups

3. **Application Deployment**
   ```bash
   # Using Docker
   docker build -t ctf-backend .
   docker run -p 8000:8000 ctf-backend
   
   # Using systemd service
   sudo systemctl enable ctf-backend
   sudo systemctl start ctf-backend
   ```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
- Create an issue on GitHub
- Check the API documentation at `/docs`
- Review the challenge validation logic in `app/challenge_validators.py`
