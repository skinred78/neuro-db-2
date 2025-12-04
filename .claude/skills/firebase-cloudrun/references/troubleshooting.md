# Firebase + Cloud Run Troubleshooting

## Common Errors

### 1. Permission denied on secret

**Error:**
```
Permission denied on secret: projects/PROJECT_NUMBER/secrets/SECRET_NAME/versions/latest
for Revision service account PROJECT_NUMBER-compute@developer.gserviceaccount.com
```

**Fix:**
```bash
gcloud secrets add-iam-policy-binding SECRET_NAME \
  --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

---

### 2. Billing not enabled

**Error:**
```
FAILED_PRECONDITION: Billing account for project is not found
```

**Fix:**
```bash
# List billing accounts
gcloud billing accounts list

# Link billing
gcloud billing projects link PROJECT_ID --billing-account=BILLING_ACCOUNT_ID
```

---

### 3. Module not found (gunicorn)

**Error:**
```
ModuleNotFoundError: No module named 'app'
```

**Fix:** Check your Dockerfile CMD path matches your Python module structure:

```dockerfile
# If your app is at: myproject/webapp/app.py
# And Flask app instance is: app = Flask(__name__)
CMD exec gunicorn --bind :$PORT myproject.webapp.app:app
```

---

### 4. 404 on deployed app

**Causes:**
- Wrong module path in Dockerfile
- Missing routes in Flask app
- Files not copied in Dockerfile

**Debug:**
```bash
# Check logs
gcloud run services logs read SERVICE_NAME --region REGION --limit 50

# Check if container starts
gcloud run services describe SERVICE_NAME --region REGION
```

---

### 5. Firebase Hosting not routing to Cloud Run

**Check firebase.json:**
```json
{
  "hosting": {
    "public": "public",
    "rewrites": [{
      "source": "**",
      "run": {
        "serviceId": "SERVICE_NAME",  // Must match Cloud Run service
        "region": "us-central1"        // Must match Cloud Run region
      }
    }]
  }
}
```

**Redeploy:**
```bash
firebase deploy --only hosting
```

---

### 6. Slow cold starts

**Symptoms:** First request takes 5-10 seconds

**Mitigations:**
```bash
# Use min-instances (costs money when idle)
gcloud run services update SERVICE_NAME \
  --region REGION \
  --min-instances 1

# Or accept cold starts for free tier
```

---

### 7. Request timeout

**Error:**
```
The request has been terminated because it has reached the maximum request timeout
```

**Fix:**
```bash
# Increase timeout (max 3600s)
gcloud run services update SERVICE_NAME \
  --region REGION \
  --timeout 300s
```

---

## Useful Debug Commands

```bash
# View service details
gcloud run services describe SERVICE_NAME --region REGION

# View recent logs
gcloud run services logs read SERVICE_NAME --region REGION --limit 50

# View build logs (if build failed)
gcloud builds list --limit 5
gcloud builds log BUILD_ID

# Check secret exists
gcloud secrets list
gcloud secrets versions access latest --secret=SECRET_NAME

# Test locally with Docker
docker build -t test-app .
docker run -p 8080:8080 -e PORT=8080 test-app
```

---

## Redeployment

```bash
# Redeploy from source (rebuilds container)
gcloud run deploy SERVICE_NAME --source . --region REGION

# Redeploy with existing image (faster)
gcloud run deploy SERVICE_NAME \
  --image REGION-docker.pkg.dev/PROJECT_ID/cloud-run-source-deploy/SERVICE_NAME \
  --region REGION
```
