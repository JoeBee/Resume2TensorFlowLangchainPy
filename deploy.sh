#!/usr/bin/env bash
# Deploy to Google Cloud Run with GOOGLE_API_KEY from .env
# Usage: ./deploy.sh
# Prerequisites: gcloud CLI, Docker, and an existing Cloud Run service

set -e
cd "$(dirname "$0")"

# Load GOOGLE_API_KEY from .env
if [[ ! -f .env ]]; then
    echo "Error: .env not found. Create it from .env.example and add GOOGLE_API_KEY." >&2
    exit 1
fi

api_key=$(grep -E '^GOOGLE_API_KEY=' .env 2>/dev/null | cut -d= -f2- | tr -d '"' | xargs)
if [[ -z "$api_key" ]]; then
    api_key=$(grep -E '^GEMINI_API_KEY=' .env 2>/dev/null | cut -d= -f2- | tr -d '"' | xargs)
fi

if [[ -z "$api_key" || "$api_key" == "your-gemini-key-here" ]]; then
    echo "Error: GOOGLE_API_KEY or GEMINI_API_KEY not set in .env" >&2
    exit 1
fi

project="${GOOGLE_CLOUD_PROJECT:-$(gcloud config get-value project 2>/dev/null)}"
region="${REGION:-us-central1}"
service_name="${SERVICE_NAME:-resume-rag}"

if [[ -z "$project" ]]; then
    echo "Error: No project set. Run: gcloud config set project YOUR_PROJECT_ID" >&2
    exit 1
fi

echo "Deploying to Cloud Run: $service_name (project: $project, region: $region)"
echo "GOOGLE_API_KEY will be set from .env"

min_instances="${MIN_INSTANCES:-1}"
echo "Min instances: $min_instances (keeps instance warm; avoids cold-start 503)"

gcloud run deploy "$service_name" \
    --source . \
    --region "$region" \
    --platform managed \
    --allow-unauthenticated \
    --memory 4Gi \
    --timeout 300 \
    --min-instances "$min_instances" \
    --set-env-vars "GOOGLE_API_KEY=$api_key"

echo ""
echo "Deploy complete. Your service URL:"
gcloud run services describe "$service_name" --region "$region" --format "value(status.url)"
