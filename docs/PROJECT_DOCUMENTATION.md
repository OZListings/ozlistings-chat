# Ozlistings Chat - Project Documentation

## Project Overview
This is a full-stack AI-powered chat application for Ozlistings, a real estate investment platform specializing in Opportunity Zone investments. The system includes a React frontend, FastAPI backend, and AI-powered chat capabilities using Google's Gemini AI.

## Architecture
```
ozlistings-chat/
├── backend/          # FastAPI backend service
├── frontend/         # React chat interface
├── docker-compose.yml        # Full stack local development
├── docker-compose.backend.yml # Backend-only local development
├── cloudbuild.yaml          # Backend GCP deployment
├── cloudbuild-frontend.yaml # Frontend GCP deployment
└── pyproject.toml          # Python project configuration
```

## Backend Components

### Core Files
- **`main.py`** - FastAPI application with three main endpoints:
  - `GET /` - Health check
  - `POST /chat` - Main chat endpoint (processes message + updates profile)
  - `POST /profile` - Profile update endpoint
  - `GET /profile/{user_id}` - Get user profile

- **`rag.py`** - AI chat agent using Google Gemini:
  - Maintains conversation history in memory
  - Uses sophisticated system prompts for Ozlistings domain knowledge
  - Handles lead qualification and call recommendations
  - Manages proactive questioning for user profiling

- **`profiling.py`** - User profile extraction system:
  - Uses Gemini AI to extract user information from messages
  - Manages profile schema with 9 key fields (investment timeline, check size, etc.)
  - Automatically updates user profiles in database

- **`database.py`** - Database layer:
  - SQLAlchemy ORM with PostgreSQL/Supabase connection
  - UserProfile model with comprehensive investment profile fields
  - Connection management and utility functions

### Dependencies
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
google-generativeai==0.3.2
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
python-dotenv==1.0.0
```

### Environment Variables Required
```
DB_USER=your_supabase_user
DB_PASSWORD=your_supabase_password
DB_HOST=your_supabase_host
DB_NAME=your_database_name
GEMINI_API_KEY=your_google_api_key
FRONTEND_URL=http://localhost:3000
```

## Frontend Components

### Core Files
- **`App.js`** - Simple wrapper that renders the main chat component
- **`EnhancedChat.js`** - Main chat interface with:
  - Email collection for user identification
  - Real-time chat with markdown support
  - Profile display panel that updates automatically
  - Backend API integration

### Dependencies
```
react: ^18.2.0
react-dom: ^18.2.0
react-markdown: ^8.0.7
react-scripts: 5.0.1
```

### Features
- Email-based user identification
- Real-time chat with typing indicators
- Markdown message rendering
- Live profile updates
- Responsive design with split-panel layout

## Deployment Options

### 1. Local Development (Docker)

#### Full Stack Development
```bash
# Run both frontend and backend with local database
docker-compose up --build
```
**Endpoints:** 
- Backend: http://localhost:8000
- Frontend: http://localhost:3000
- Database: PostgreSQL on localhost:5432

#### Backend-Only Development
```bash
# Run only backend (for frontend development or testing)
docker-compose -f docker-compose.backend.yml up --build -d
```
**Endpoints:** 
- Backend: http://localhost:8001

### 2. Google Cloud Platform Deployment

#### Production URLs
- **Backend (Currently Deployed):** `https://ozlistings-chat-876384283449.us-west1.run.app`
- **Frontend:** Will be deployed to `https://ozlistings-chat-frontend-[PROJECT-ID].us-west1.run.app`

#### Backend Deployment
- **File:** `cloudbuild.yaml`
- **Region:** us-west1
- **Process:** Builds Docker image → Pushes to Artifact Registry → Deploys to Cloud Run

#### Frontend Deployment  
- **File:** `cloudbuild-frontend.yaml`
- **Region:** us-west1
- **Process:** Builds React app → Creates Nginx container → Deploys to Cloud Run
- **Auto-configured:** Backend URL is automatically set to production endpoint

#### Cloud Build Commands
```bash
# Deploy backend
gcloud builds submit --config cloudbuild.yaml

# Deploy frontend (automatically points to production backend)
gcloud builds submit --config cloudbuild-frontend.yaml
```

### 3. Database
- **Production:** Supabase PostgreSQL (configured in database.py)
- **Local:** PostgreSQL container (docker-compose.yml)
- **Schema:** Single `user_profiles` table with comprehensive investment profile fields

## Key Features

### AI Chat Agent
- **Domain Expertise:** Specialized in Opportunity Zone investments and real estate
- **Lead Qualification:** Automatically extracts and stores user investment preferences
- **Conversation Management:** Maintains context and guides users toward consultation calls
- **Smart Profiling:** Uses AI to update user profiles from natural conversation

### User Profile System
- **Fields Tracked:** Investment timeline, check size, geographical preferences, asset types, experience level, accredited investor status
- **Auto-Update:** Profiles update automatically as users chat
- **Real-time Display:** Frontend shows live profile updates

### Scalable Architecture
- **Containerized:** All components are Docker-ready
- **Cloud-Native:** Designed for Google Cloud Run deployment
- **API-First:** Clean REST API design for easy integration
- **Regional Consistency:** All services deployed in us-west1 region

## Getting Started

### Prerequisites
- Docker and Docker Compose
- Google Cloud account (for Gemini AI)
- Supabase account (for database)

### Quick Start (Local Development)
1. Clone the repository
2. Create `.env` file in root with required environment variables
3. Run: `docker-compose -f docker-compose.backend.yml up --build -d`
4. Access backend at: http://localhost:8001

### Production Deployment
1. Set up Google Cloud Project
2. Configure Artifact Registry repositories:
   - `ozlistings-backend` 
   - `ozlistings-frontend`
3. Set environment variables in Cloud Run
4. Deploy: `gcloud builds submit --config cloudbuild.yaml`

## API Endpoints

### Production Backend: https://ozlistings-chat-876384283449.us-west1.run.app

### POST /chat
**Purpose:** Main chat interaction
**Body:** `{"user_id": "email@example.com", "message": "your message"}`
**Response:** `{"response": "AI response text"}`

### POST /profile  
**Purpose:** Update user profile
**Body:** `{"user_id": "email@example.com", "message": "profile information"}`
**Response:** `{"profile": {...updated profile...}}`

### GET /profile/{user_id}
**Purpose:** Retrieve user profile
**Response:** User profile object or 404 if not found

## Security & Compliance
- **CORS:** Configured for frontend domains
- **Environment Variables:** Sensitive data in .env files
- **Database:** SSL-required connections to Supabase
- **Disclaimers:** Built-in disclaimers about financial advice
- **Regional Deployment:** Consistent us-west1 region for compliance

## Current Status
- ✅ **Backend deployed on GCP:** https://ozlistings-chat-876384283449.us-west1.run.app
- ✅ **Backend running locally on Docker:** http://localhost:8001
- ✅ **Database connection configured for Supabase**
- ✅ **AI chat functionality with Gemini integration**
- ✅ **User profiling system operational**
- ✅ **Cloud deployment configurations updated for us-west1**
- ✅ **Separate build processes for backend and frontend**
- ⚠️ **Frontend deployment ready but not yet deployed**

## Deployment Commands

### Backend (Already Deployed)
```bash
gcloud builds submit --config cloudbuild.yaml
```

### Frontend (Ready to Deploy)
```bash
gcloud builds submit --config cloudbuild-frontend.yaml
```

### Local Development
```bash
# Full stack
docker-compose up --build

# Backend only
docker-compose -f docker-compose.backend.yml up --build -d
```

## Next Steps
1. Deploy frontend to Google Cloud Run
2. Configure custom domains
3. Set up monitoring and logging
4. Implement user authentication (if required)
5. Set up CI/CD pipelines 