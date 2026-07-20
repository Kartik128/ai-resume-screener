#!/bin/bash
# ================================================================
# One-Click GCP Cloud Run Deployment Script for AI Resume Screener
# ================================================================

PROJECT_ID=$(gcloud config get-value project 2>/dev/null)

if [ -z "$PROJECT_ID" ]; then
  echo "Error: GCP Project ID not set. Run: gcloud config set project YOUR_PROJECT_ID"
  exit 1
fi

echo "🚀 Deploying AI Resume Screener SaaS to GCP Cloud Run..."
echo "Project ID: $PROJECT_ID"

# Enable required GCP APIs
gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com

# Deploy to Cloud Run directly using source container build
gcloud run deploy ai-resume-screener \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8000 \
  --memory 1Gi \
  --cpu 1

echo "✅ Deployment Complete! Copy the public HTTPS URL printed above."
