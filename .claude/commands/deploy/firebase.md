# Deploy Flask app to Firebase + Cloud Run

Deploy a Python/Flask webapp to Google Cloud Run with Firebase Hosting.

## Context

$ARGUMENTS

## Instructions

You are deploying a Flask webapp to Firebase + Cloud Run. Follow these steps:

### Step 1: Analyze Project Structure

1. Find the Flask app entry point (look for `app = Flask(__name__)`)
2. Identify the requirements.txt location
3. Check for existing Dockerfile, firebase.json, .firebaserc

### Step 2: Create/Update Deployment Files

If files don't exist, create them:

**Dockerfile** (at repo root):
- Use python:3.11-slim base
- Copy requirements and install with pip
- Copy application code
- Set PORT=8080
- Use gunicorn with correct module path

**firebase.json**:
- Set public directory
- Add rewrite rule to Cloud Run service

**.firebaserc**:
- Set project ID

**public/index.html**:
- Create placeholder file

**requirements.txt**:
- Ensure Flask and gunicorn are included

**Flask app**:
- Add /healthz endpoint if missing
- Set debug=False

### Step 3: Deploy

Run deployment commands in sequence:

1. Create/select GCP project
2. Link billing if needed
3. Enable required APIs
4. Add Firebase to project
5. Create secrets if needed (and grant IAM access)
6. Deploy to Cloud Run with `gcloud run deploy`
7. Deploy Firebase Hosting with `firebase deploy --only hosting`
8. Test both URLs

### Step 4: Report Results

Provide:
- Firebase URL (*.web.app)
- Cloud Run URL
- Console links
- Any issues encountered

## Reference

Read the skill documentation:
- `.claude/skills/firebase-cloudrun/SKILL.md`
- `.claude/skills/firebase-cloudrun/references/deployment-checklist.md`
- `.claude/skills/firebase-cloudrun/references/troubleshooting.md`

## Automation Script

For interactive deployment, suggest running:
```bash
bash .claude/skills/firebase-cloudrun/scripts/deploy.sh
```
