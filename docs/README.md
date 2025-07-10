# Ozlistings Chat - Documentation

This folder contains comprehensive documentation for the Ozlistings Chat project.

## 📚 Documentation Index

### 🏗️ [Project Documentation](./PROJECT_DOCUMENTATION.md)
Complete overview of the project including:
- Project architecture and components
- Deployment options (Local Docker & Google Cloud)
- Getting started guide
- API endpoints
- Current status and next steps

### 📊 [Schema Documentation](./SCHEMA_DOCUMENTATION.md)
Detailed technical specifications including:
- Database schema and table structures
- API request/response schemas
- Profile field definitions
- System architecture diagrams
- Data flow documentation
- Environment variables
- Security and performance considerations

## 🎯 Quick Navigation

### For Developers
- **Getting Started**: See [Project Documentation - Getting Started](./PROJECT_DOCUMENTATION.md#getting-started)
- **API Reference**: See [Schema Documentation - API Schema](./SCHEMA_DOCUMENTATION.md#api-schema)
- **Database Schema**: See [Schema Documentation - Database Schema](./SCHEMA_DOCUMENTATION.md#database-schema)

### For DevOps/Deployment
- **Deployment Guide**: See [Project Documentation - Deployment Options](./PROJECT_DOCUMENTATION.md#deployment-options)
- **Environment Variables**: See [Schema Documentation - Environment Variables](./SCHEMA_DOCUMENTATION.md#environment-variables)
- **Cloud Build Configs**: Located in project root (`cloudbuild.yaml`, `cloudbuild-frontend.yaml`)

### For Product/Business
- **System Overview**: See [Project Documentation - Key Features](./PROJECT_DOCUMENTATION.md#key-features)
- **AI Capabilities**: See [Schema Documentation - Profile Schema](./SCHEMA_DOCUMENTATION.md#profile-schema)
- **Data Flow**: See [Schema Documentation - Data Flow](./SCHEMA_DOCUMENTATION.md#data-flow)

## 🚀 Quick Start

1. **Local Development**: `docker-compose -f docker-compose.backend.yml up --build -d`
2. **Production Backend**: Currently deployed at `https://ozlistings-chat-876384283449.us-west1.run.app`
3. **Frontend Deployment**: `gcloud builds submit --config cloudbuild-frontend.yaml`

## 📞 Support

For questions about this documentation or the project:
- Review the comprehensive guides in this docs folder
- Check the inline code comments in the source files
- Refer to the deployment configurations in the project root

---

*Last Updated: July 2025* 