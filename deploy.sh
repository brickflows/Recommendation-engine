#!/bin/bash

# Recommendation Engine Deployment Script
# Update the variables below with your credentials

# ============================================
# CONFIGURATION - UPDATE THESE VALUES
# ============================================

PROJECT_ID="your-gcp-project-id"
FUNCTION_NAME="recommend-businesses"
REGION="us-central1"

# Supabase credentials
SUPABASE_URL="https://your-project.supabase.co"
SUPABASE_KEY="your-supabase-service-role-key"

# OpenAI API key
OPENAI_API_KEY="sk-your-openai-api-key"

# ============================================
# DEPLOYMENT
# ============================================

echo "🚀 Deploying Recommendation Engine to Google Cloud Functions..."
echo "Project: $PROJECT_ID"
echo "Function: $FUNCTION_NAME"
echo "Region: $REGION"
echo ""

gcloud functions deploy $FUNCTION_NAME \
  --gen2 \
  --runtime=python311 \
  --region=$REGION \
  --source=. \
  --entry-point=recommend_businesses \
  --trigger-http \
  --allow-unauthenticated \
  --set-env-vars SUPABASE_URL=$SUPABASE_URL,SUPABASE_KEY=$SUPABASE_KEY,OPENAI_API_KEY=$OPENAI_API_KEY \
  --timeout=300s \
  --memory=512MB \
  --max-instances=10 \
  --project=$PROJECT_ID

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Deployment successful!"
    echo ""
    echo "Your function URL will be displayed above."
    echo "Copy it and use it in your frontend to call the recommendation API."
    echo ""
    echo "Example usage:"
    echo "curl -X POST https://REGION-PROJECT_ID.cloudfunctions.net/$FUNCTION_NAME \\"
    echo "  -H 'Content-Type: application/json' \\"
    echo "  -d '{\"user_id\": \"your-user-uuid\", \"limit\": 10}'"
else
    echo ""
    echo "❌ Deployment failed. Check the error messages above."
    exit 1
fi
