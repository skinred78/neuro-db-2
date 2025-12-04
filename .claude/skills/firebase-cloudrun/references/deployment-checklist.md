# Firebase + Cloud Run Deployment Checklist

## Phase 1: Project Files (5 min)

### 1.1 Dockerfile (at repo root)

```dockerfile
FROM python:3.11-slim
WORKDIR /app

# Copy and install requirements
COPY path/to/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY path/to/app/ ./app/

# Copy any data files needed
# COPY data/ ./data/

ENV PORT=8080
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 app.module:app
```

**Notes:**
- Adjust `path/to/` to match your project structure
- `app.module:app` = Python module path to Flask app instance
- Workers=1, Threads=8 is good for low-traffic

### 1.2 .dockerignore

```
.git
*.md
tests/
*.pyc
__pycache__
.env
.venv
venv/
node_modules/
.claude/
```

### 1.3 firebase.json

```json
{
  "hosting": {
    "public": "public",
    "rewrites": [{
      "source": "**",
      "run": { "serviceId": "SERVICE_NAME", "region": "us-central1" }
    }]
  }
}
```

**Replace:** `SERVICE_NAME` with your Cloud Run service name

### 1.4 .firebaserc

```json
{
  "projects": {
    "default": "PROJECT_ID"
  }
}
```

**Replace:** `PROJECT_ID` with your GCP project ID

### 1.5 public/index.html

```html
<!-- Firebase Hosting placeholder - all requests redirect to Cloud Run -->
```

### 1.6 Flask App Updates

Add health check endpoint:

```python
@app.route('/healthz')
def healthz():
    """Health check endpoint for Cloud Run."""
    return 'OK', 200

# Set debug=False for production
if __name__ == '__main__':
    app.run(debug=False, host='127.0.0.1', port=5000)
```

### 1.7 requirements.txt

Ensure these are included:

```
Flask>=3.0.0
gunicorn>=21.0.0
```

---

## Phase 2: GCP Setup (10 min)

### 2.1 Create Project

```bash
# Create new project
gcloud projects create PROJECT_ID --name="Project Name"

# Or list existing
gcloud projects list
```

### 2.2 Set Project & Link Billing

```bash
# Set as default
gcloud config set project PROJECT_ID

# List billing accounts
gcloud billing accounts list

# Link billing (required for Cloud Run)
gcloud billing projects link PROJECT_ID --billing-account=BILLING_ACCOUNT_ID
```

### 2.3 Enable APIs

```bash
gcloud services enable \
  run.googleapis.com \
  secretmanager.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  firebase.googleapis.com \
  firebasehosting.googleapis.com
```

### 2.4 Add Firebase

```bash
firebase projects:addfirebase PROJECT_ID
```

---

## Phase 3: Secrets (if needed)

### 3.1 Create Secret

```bash
# From value
echo "YOUR_API_KEY" | gcloud secrets create secret-name --data-file=-

# From file
gcloud secrets create secret-name --data-file=path/to/key.txt
```

### 3.2 Grant Access to Cloud Run

```bash
# Get compute service account
PROJECT_NUMBER=$(gcloud projects describe PROJECT_ID --format='value(projectNumber)')

# Grant access
gcloud secrets add-iam-policy-binding secret-name \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

---

## Phase 4: Deploy (5 min)

### 4.1 Deploy to Cloud Run

```bash
gcloud run deploy SERVICE_NAME \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 512Mi \
  --timeout 120s \
  --set-secrets ENV_VAR_NAME=secret-name:latest
```

**Options:**
- `--allow-unauthenticated` - Public access (no auth)
- `--memory 512Mi` - Adjust based on app needs
- `--timeout 120s` - Request timeout
- `--set-secrets` - Inject secrets as env vars

### 4.2 Deploy Firebase Hosting

```bash
firebase deploy --only hosting
```

---

## Phase 5: Verify

```bash
# Test Cloud Run directly
curl https://SERVICE_NAME-PROJECT_NUMBER.REGION.run.app/healthz

# Test Firebase Hosting
curl https://PROJECT_ID.web.app/

# Check logs
gcloud run services logs read SERVICE_NAME --region us-central1 --limit 20
```

---

## Common Variables Reference

| Variable | Example | Where to Find |
|----------|---------|---------------|
| PROJECT_ID | `my-app-prod` | `gcloud projects list` |
| PROJECT_NUMBER | `123456789` | `gcloud projects describe PROJECT_ID` |
| SERVICE_NAME | `my-flask-app` | Your choice |
| REGION | `us-central1` | Your choice |
| BILLING_ACCOUNT_ID | `01C9CA-61948D-B7E11D` | `gcloud billing accounts list` |
