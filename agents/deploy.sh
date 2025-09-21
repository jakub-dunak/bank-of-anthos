#!/bin/bash
# Open Banking Consent Choreographer - Deployment Script

set -e

echo "🤖 Open Banking Consent Choreographer - Deployment"
echo ""

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found!"
    echo "Please copy .env.template to .env and fill in your values:"
    echo "  cp .env.template .env"
    echo "  # Then edit .env with your actual values"
    exit 1
fi

# Source environment variables
echo "📄 Loading environment from .env..."
source .env

# Validate required variables
if [ -z "$PROJECT_ID" ] || [ "$PROJECT_ID" = "your-gcp-project-id" ]; then
    echo "❌ Error: PROJECT_ID not set in .env file!"
    exit 1
fi

if [ -z "$GOOGLE_API_KEY" ] || [ "$GOOGLE_API_KEY" = "your-google-ai-api-key" ]; then
    echo "❌ Error: GOOGLE_API_KEY not set in .env file!"
    exit 1
fi

echo "✅ Environment variables loaded:"
echo "   PROJECT_ID: $PROJECT_ID"
echo "   GOOGLE_API_KEY: ${GOOGLE_API_KEY:0:20}..."
echo "   GCP_LOCATION: ${GCP_LOCATION:-us-central1}"
echo ""

# Deploy using sed for variable substitution
echo "🚀 Deploying agents..."
sed -e "s|\${PROJECT_ID}|$PROJECT_ID|g" \
    -e "s|\${GOOGLE_API_KEY}|$GOOGLE_API_KEY|g" \
    -e "s|\${GCP_LOCATION}|${GCP_LOCATION:-us-central1}|g" \
    agents-deployment.yaml | kubectl apply -f -

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🌐 Dashboard will be available at:"
echo "   kubectl get ingress streamlit-dashboard-ingress -n agents-ns"
echo ""
echo "📊 To monitor logs:"
echo "   kubectl logs -l app=validation-agent -n agents-ns --follow"
