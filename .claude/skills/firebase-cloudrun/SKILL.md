# Firebase + Cloud Run Deployment Skill

Deploy Flask/Python webapps to Google Cloud Run with Firebase Hosting for friendly URLs. Zero-cost for low-traffic internal tools.

## When to Use

- Deploying Python/Flask webapps to cloud
- Need friendly URLs (*.web.app) instead of Cloud Run URLs
- Internal tools with 1-10 users
- Projects needing secret management (API keys)

## Architecture

```
User → Firebase Hosting (CDN) → Cloud Run (Flask) → External APIs
              ↓                       ↓
         Nice URL              Secret Manager
    (project.web.app)       (env var injection)
```

## Prerequisites

```bash
# Check installations
gcloud --version    # Google Cloud SDK
firebase --version  # Firebase CLI

# Install if needed
brew install google-cloud-sdk
npm install -g firebase-tools

# Authenticate
gcloud auth login
firebase login
```

## Quick Start

1. **Create project files** (see references/deployment-checklist.md)
2. **Run deployment script**: `bash .claude/skills/firebase-cloudrun/scripts/deploy.sh`
3. **Or use slash command**: `/deploy:firebase`

## Required Files

| File | Purpose |
|------|---------|
| `Dockerfile` | Container definition |
| `.dockerignore` | Exclude files from build |
| `firebase.json` | Hosting rewrites to Cloud Run |
| `.firebaserc` | Project ID |
| `public/index.html` | Firebase Hosting placeholder |
| `requirements.txt` | Python dependencies (include gunicorn) |

## Cost (Free Tier)

| Service | Free Tier |
|---------|-----------|
| Cloud Run | 2M requests/month |
| Secret Manager | 6 secrets |
| Firebase Hosting | 1GB storage |
| Artifact Registry | ~$0.10/month storage |

## References

- [deployment-checklist.md](references/deployment-checklist.md) - Step-by-step guide
- [architecture.md](references/architecture.md) - Architecture patterns
- [troubleshooting.md](references/troubleshooting.md) - Common issues

## Scripts

- [deploy.sh](scripts/deploy.sh) - Automated deployment script
