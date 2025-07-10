# Ozlistings Chat - Schema Documentation

## Table of Contents
1. [Database Schema](#database-schema)
2. [API Schema](#api-schema)
3. [Profile Schema](#profile-schema)
4. [System Architecture](#system-architecture)
5. [Data Flow](#data-flow)
6. [Environment Variables](#environment-variables)

## Database Schema

### User Profiles Table (`user_profiles`)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | STRING | PRIMARY KEY, UNIQUE, INDEX | UUID generated primary key |
| `user_id` | STRING | UNIQUE, INDEX | User identifier (email address) |
| `accredited_investor` | BOOLEAN | NULLABLE | Whether user is an accredited investor |
| `check_size` | TEXT | NULLABLE | Investment amount range (e.g., "$100k-$500k") |
| `geographical_zone` | TEXT | NULLABLE | Preferred investment geographical area |
| `real_estate_investment_experience` | FLOAT | NULLABLE | Years of real estate investment experience |
| `investment_timeline` | TEXT | NULLABLE | Investment timeline preference |
| `investment_priorities` | TEXT[] | NULLABLE | Array of investment priorities |
| `deal_readiness` | TEXT | NULLABLE | Current deal readiness status |
| `preferred_asset_types` | TEXT[] | NULLABLE | Array of preferred asset types |
| `needs_team_contact` | BOOLEAN | NULLABLE | Flag indicating if user needs team contact |
| `created_at` | DATETIME | NOT NULL | Record creation timestamp |
| `updated_at` | DATETIME | NOT NULL | Last update timestamp |

### Database Connection
- **Production**: Supabase PostgreSQL with SSL
- **Local Development**: PostgreSQL container
- **Connection String**: `postgresql://{user}:{password}@{host}:5432/{database}?sslmode=require`

## API Schema

### Endpoints

#### POST /chat
**Purpose**: Main chat interaction endpoint

**Request Schema**:
```json
{
  "user_id": "string (email)",
  "message": "string"
}
```

**Response Schema**:
```json
{
  "response": "string (AI generated response)"
}
```

**Status Codes**:
- `200`: Success
- `500`: Internal server error

#### POST /profile
**Purpose**: Update user profile

**Request Schema**:
```json
{
  "user_id": "string (email)",
  "message": "string (message containing profile info)"
}
```

**Response Schema**:
```json
{
  "profile": {
    "accredited_investor": "boolean | null",
    "check_size": "string | null",
    "geographical_zone": "string | null",
    "real_estate_investment_experience": "number | null",
    "investment_timeline": "string | null",
    "investment_priorities": "string[] | null",
    "deal_readiness": "string | null",
    "preferred_asset_types": "string[] | null",
    "needs_team_contact": "boolean | null"
  }
}
```

#### GET /profile/{user_id}
**Purpose**: Retrieve user profile

**Response Schema**:
```json
{
  "accredited_investor": "boolean | null",
  "check_size": "string | null",
  "geographical_zone": "string | null",
  "real_estate_investment_experience": "number | null",
  "investment_timeline": "string | null",
  "investment_priorities": "string[] | null",
  "deal_readiness": "string | null",
  "preferred_asset_types": "string[] | null",
  "needs_team_contact": "boolean | null"
}
```

**Status Codes**:
- `200`: Success
- `404`: Profile not found

#### GET /
**Purpose**: Health check

**Response Schema**:
```json
{
  "message": "Welcome to Ozlistings AI Agent!"
}
```

## Profile Schema

### Profile Field Definitions

| Field | Type | Description | Example Values |
|-------|------|-------------|----------------|
| `accredited_investor` | Boolean | SEC accredited investor status | `true`, `false`, `null` |
| `check_size` | String | Investment amount range | "$100k-$500k", "$1M+", "Under $100k" |
| `geographical_zone` | String | Geographic investment preference | "Florida", "Southeast US", "National" |
| `real_estate_investment_experience` | Float | Years of experience | `0.0`, `5.5`, `15.0` |
| `investment_timeline` | String | Investment timeframe | "Immediate", "3-6 months", "Within a year" |
| `investment_priorities` | String[] | Investment goals | `["tax benefits", "cash flow", "appreciation"]` |
| `deal_readiness` | String | Current deal status | "Ready to invest", "Exploring options", "Need more info" |
| `preferred_asset_types` | String[] | Property type preferences | `["multifamily", "commercial", "opportunity zones"]` |
| `needs_team_contact` | Boolean | Contact request flag | `true`, `false`, `null` |

### Profile Extraction Logic
- **AI-Powered**: Uses Google Gemini to extract profile data from natural conversation
- **Incremental Updates**: Profile fields are updated as information becomes available
- **Type Validation**: Automatic type conversion and validation
- **Array Handling**: Comma-separated strings automatically converted to arrays

## System Architecture

### Technology Stack
- **Frontend**: React 18.2.0, React Markdown
- **Backend**: FastAPI 0.104.1, Python 3.9+
- **Database**: PostgreSQL (Supabase)
- **AI**: Google Gemini 2.0-flash
- **Deployment**: Google Cloud Run, Docker
- **Infrastructure**: Google Cloud Build, Artifact Registry

### Architecture Patterns
- **Microservices**: Separate frontend and backend services
- **RESTful API**: Standard HTTP methods and status codes
- **Event-Driven**: Profile updates triggered by chat interactions
- **Stateless Backend**: No server-side session storage
- **Cloud-Native**: Designed for containerized deployment

## Data Flow

### Chat Interaction Flow
1. **User Input**: User types message in frontend
2. **API Call**: Frontend sends POST to `/chat` endpoint
3. **AI Processing**: RAG system processes message with Gemini
4. **Profile Update**: Profile extractor analyzes message for user data
5. **Database Update**: Profile changes saved to PostgreSQL
6. **Response**: AI response returned to frontend
7. **UI Update**: Chat and profile display updated

### Profile Update Flow
1. **Message Analysis**: Gemini AI analyzes user message
2. **Data Extraction**: Structured data extracted using function calling
3. **Type Validation**: Data types validated and converted
4. **Database Merge**: New data merged with existing profile
5. **Response**: Updated profile returned to client

### Authentication Flow
- **Email-Based**: Users identified by email address
- **No Password**: Simplified access for lead generation
- **Profile Linking**: All interactions linked to email identifier

## Environment Variables

### Required Variables
```bash
# Database Configuration
DB_USER=your_supabase_user
DB_PASSWORD=your_supabase_password  
DB_HOST=your_supabase_host
DB_NAME=your_database_name

# AI Configuration
GEMINI_API_KEY=your_google_api_key

# Application Configuration
FRONTEND_URL=http://localhost:3000
PORT=8000
```

### Optional Variables
```bash
# Development
DEBUG=true
LOG_LEVEL=info

# Cloud Deployment
PROJECT_ID=your-gcp-project
REGION=us-west1
```

## Security Considerations

### Data Protection
- **SSL/TLS**: All database connections use SSL
- **Environment Variables**: Sensitive data stored in environment variables
- **Input Validation**: All user inputs validated and sanitized
- **CORS**: Cross-origin requests properly configured

### Privacy Compliance
- **Data Minimization**: Only necessary profile data collected
- **User Control**: Users can view their complete profile
- **Transparency**: Clear disclaimers about data usage
- **No PII Storage**: No sensitive personal information stored

## Performance Characteristics

### Database Performance
- **Indexed Fields**: `user_id` and `id` are indexed
- **Connection Pooling**: SQLAlchemy manages connection pool
- **Query Optimization**: Simple queries with minimal joins

### API Performance
- **Async Operations**: FastAPI with async/await patterns
- **Concurrent Processing**: Profile updates and chat responses in parallel
- **Caching**: In-memory conversation history for context

### Scalability
- **Stateless Design**: Easy horizontal scaling
- **Cloud-Native**: Auto-scaling with Cloud Run
- **Database Scaling**: Supabase handles database scaling

## Monitoring and Observability

### Logging
- **Structured Logging**: JSON format for cloud environments
- **Error Tracking**: Comprehensive error handling and logging
- **Performance Metrics**: Response times and throughput monitoring

### Health Checks
- **Database Health**: Connection testing functions
- **API Health**: Health check endpoint available
- **Service Monitoring**: Cloud Run provides built-in monitoring 