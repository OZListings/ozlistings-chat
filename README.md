# Ozlistings Chat

AI-powered chat application for Opportunity Zone investments. FastAPI backend with Google Gemini AI.

## Quick Start

```bash
# Local development
docker-compose -f docker-compose.local.yml up --build -d

# Production deployment
gcloud builds submit --config cloudbuild.yaml
```

**Production**: https://ozlistings-chat-876384283449.us-west1.run.app

## Environment Variables

```bash
# Database Configuration (Supabase)
DB_USER=your_supabase_user
DB_PASSWORD=your_supabase_password
DB_HOST=your_supabase_host
DB_NAME=your_database_name

# AI Configuration
GEMINI_API_KEY=your_google_api_key

# Application Configuration
PORT=8000
```

## API Endpoints

### POST /chat
```json
{
  "user_id": "user@example.com",
  "message": "I'm interested in opportunity zone investments"
}
```

### POST /profile
```json
{
  "user_id": "user@example.com",
  "message": "I have 5 years experience and want to invest $500k"
}
```

### GET /profile/{user_id}
Retrieve user profile

### GET /
Health check

## Database Schema

| Column | Type | Description |
|--------|------|-------------|
| `user_id` | STRING | Email identifier |
| `accredited_investor` | BOOLEAN | SEC accredited status |
| `check_size` | TEXT | Investment amount range |
| `geographical_zone` | TEXT | Geographic preference |
| `real_estate_investment_experience` | FLOAT | Years of experience |
| `investment_timeline` | TEXT | Investment timeframe |
| `investment_priorities` | TEXT[] | Investment goals |
| `deal_readiness` | TEXT | Current deal status |
| `preferred_asset_types` | TEXT[] | Property type preferences |
| `needs_team_contact` | BOOLEAN | Contact request flag |

## Features

- AI chat agent specialized in Opportunity Zone investments
- Automatic user profile extraction from conversations
- PostgreSQL database with Supabase
- Google Cloud Run deployment
- Email-based user identification
- Rate limiting (10/min for chat, 30/min for profile)
- Input validation and sanitization
- Security headers and CORS protection

## Security Features

- Non-root Docker container
- Rate limiting on all endpoints
- Input validation with Pydantic
- Environment variable validation
- Structured logging
- Error handling without data exposure
- SSL database connections 