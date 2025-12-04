#!/bin/bash
# Firebase + Cloud Run Deployment Script
# Usage: bash deploy.sh [PROJECT_ID] [SERVICE_NAME] [REGION]

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Firebase + Cloud Run Deployment ===${NC}"

# Configuration (override via args or edit defaults)
PROJECT_ID="${1:-}"
SERVICE_NAME="${2:-}"
REGION="${3:-us-central1}"

# Prompt for missing values
if [ -z "$PROJECT_ID" ]; then
    echo -e "${YELLOW}Available projects:${NC}"
    gcloud projects list --format="table(projectId,name)" 2>/dev/null || true
    echo ""
    read -p "Enter PROJECT_ID (or 'new' to create): " PROJECT_ID
fi

if [ "$PROJECT_ID" = "new" ]; then
    read -p "Enter new project ID: " PROJECT_ID
    read -p "Enter project display name: " PROJECT_NAME
    echo -e "${YELLOW}Creating project...${NC}"
    gcloud projects create "$PROJECT_ID" --name="$PROJECT_NAME"
fi

if [ -z "$SERVICE_NAME" ]; then
    read -p "Enter SERVICE_NAME (e.g., my-flask-app): " SERVICE_NAME
fi

echo ""
echo -e "${GREEN}Configuration:${NC}"
echo "  PROJECT_ID:   $PROJECT_ID"
echo "  SERVICE_NAME: $SERVICE_NAME"
echo "  REGION:       $REGION"
echo ""

# Set project
echo -e "${YELLOW}Setting project...${NC}"
gcloud config set project "$PROJECT_ID"

# Check billing
echo -e "${YELLOW}Checking billing...${NC}"
BILLING_ENABLED=$(gcloud billing projects describe "$PROJECT_ID" --format="value(billingEnabled)" 2>/dev/null || echo "false")
if [ "$BILLING_ENABLED" != "True" ]; then
    echo -e "${YELLOW}Billing not enabled. Available accounts:${NC}"
    gcloud billing accounts list
    read -p "Enter BILLING_ACCOUNT_ID: " BILLING_ACCOUNT
    gcloud billing projects link "$PROJECT_ID" --billing-account="$BILLING_ACCOUNT"
fi

# Enable APIs
echo -e "${YELLOW}Enabling APIs (this may take a minute)...${NC}"
gcloud services enable \
    run.googleapis.com \
    secretmanager.googleapis.com \
    artifactregistry.googleapis.com \
    cloudbuild.googleapis.com \
    firebase.googleapis.com \
    firebasehosting.googleapis.com

# Add Firebase
echo -e "${YELLOW}Adding Firebase...${NC}"
firebase projects:addfirebase "$PROJECT_ID" 2>/dev/null || echo "Firebase already added"

# Update .firebaserc
echo -e "${YELLOW}Updating .firebaserc...${NC}"
cat > .firebaserc << EOF
{
  "projects": {
    "default": "$PROJECT_ID"
  }
}
EOF

# Update firebase.json if exists
if [ -f "firebase.json" ]; then
    echo -e "${YELLOW}Updating firebase.json...${NC}"
    cat > firebase.json << EOF
{
  "hosting": {
    "public": "public",
    "rewrites": [{
      "source": "**",
      "run": { "serviceId": "$SERVICE_NAME", "region": "$REGION" }
    }]
  }
}
EOF
fi

# Create public directory if needed
mkdir -p public
if [ ! -f "public/index.html" ]; then
    echo "<!-- Firebase Hosting placeholder -->" > public/index.html
fi

# Check for secrets
read -p "Do you need to create/update a secret? (y/N): " CREATE_SECRET
if [ "$CREATE_SECRET" = "y" ] || [ "$CREATE_SECRET" = "Y" ]; then
    read -p "Secret name (e.g., api-key): " SECRET_NAME
    read -p "Secret value: " SECRET_VALUE
    echo "$SECRET_VALUE" | gcloud secrets create "$SECRET_NAME" --data-file=- 2>/dev/null || \
        echo "$SECRET_VALUE" | gcloud secrets versions add "$SECRET_NAME" --data-file=-

    # Grant access
    PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')
    gcloud secrets add-iam-policy-binding "$SECRET_NAME" \
        --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
        --role="roles/secretmanager.secretAccessor"

    read -p "Environment variable name for this secret (e.g., API_KEY): " ENV_VAR_NAME
    SECRET_FLAG="--set-secrets ${ENV_VAR_NAME}=${SECRET_NAME}:latest"
else
    SECRET_FLAG=""
fi

# Deploy to Cloud Run
echo -e "${YELLOW}Deploying to Cloud Run (this takes 2-5 minutes)...${NC}"
gcloud run deploy "$SERVICE_NAME" \
    --source . \
    --region "$REGION" \
    --allow-unauthenticated \
    --memory 512Mi \
    --timeout 120s \
    $SECRET_FLAG

# Deploy Firebase Hosting
echo -e "${YELLOW}Deploying Firebase Hosting...${NC}"
firebase deploy --only hosting

# Get URLs
CLOUD_RUN_URL=$(gcloud run services describe "$SERVICE_NAME" --region "$REGION" --format='value(status.url)')
FIREBASE_URL="https://${PROJECT_ID}.web.app"

echo ""
echo -e "${GREEN}=== Deployment Complete! ===${NC}"
echo ""
echo -e "Cloud Run URL:     ${CLOUD_RUN_URL}"
echo -e "Firebase URL:      ${FIREBASE_URL}"
echo ""
echo -e "Console Links:"
echo -e "  Firebase:  https://console.firebase.google.com/project/${PROJECT_ID}/overview"
echo -e "  Cloud Run: https://console.cloud.google.com/run/detail/${REGION}/${SERVICE_NAME}/metrics?project=${PROJECT_ID}"
