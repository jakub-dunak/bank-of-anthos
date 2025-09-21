#!/bin/bash

# Open Banking Consent Choreographer - Setup Verification Script

set -e

PROJECT_ID=${PROJECT_ID:-"YOUR_PROJECT_ID"}
REGION=${REGION:-"us-central1"}

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

echo "🔍 Verifying Open Banking Consent Choreographer Setup"
echo "===================================================="
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo ""

# Check if gcloud is installed and authenticated
echo "1. Checking Google Cloud SDK..."
if ! command -v gcloud &> /dev/null; then
    log_error "❌ gcloud CLI is not installed"
    echo "   Install with: brew install --cask google-cloud-sdk"
    exit 1
else
    log_success "✅ gcloud CLI is installed"
fi

# Check authentication
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n 1 > /dev/null; then
    log_error "❌ Not authenticated with gcloud"
    echo "   Run: gcloud auth login"
    exit 1
else
    ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)")
    log_success "✅ Authenticated as: $ACCOUNT"
fi

# Check if project exists and is accessible
echo ""
echo "2. Checking GCP Project..."
if ! gcloud projects describe $PROJECT_ID &> /dev/null; then
    log_error "❌ Project $PROJECT_ID not found or not accessible"
    echo "   Verify project ID and permissions"
    exit 1
else
    BILLING=$(gcloud beta billing projects describe $PROJECT_ID --format="value(billingEnabled)")
    if [[ "$BILLING" != "True" ]]; then
        log_error "❌ Billing is not enabled for project $PROJECT_ID"
        echo "   Enable billing in GCP Console"
        exit 1
    else
        log_success "✅ Project exists and billing is enabled"
    fi
fi

# Check required APIs
echo ""
echo "3. Checking required APIs..."
REQUIRED_APIS=(
    "container.googleapis.com"
    "aiplatform.googleapis.com" 
    "artifactregistry.googleapis.com"
    "containerregistry.googleapis.com"
)

MISSING_APIS=()
for api in "${REQUIRED_APIS[@]}"; do
    if ! gcloud services list --project=$PROJECT_ID --filter="name:$api" --format="value(name)" | grep -q "$api"; then
        MISSING_APIS+=("$api")
    fi
done

if [ ${#MISSING_APIS[@]} -gt 0 ]; then
    log_warn "⚠️  Missing required APIs:"
    for api in "${MISSING_APIS[@]}"; do
        echo "   - $api"
    done
    echo ""
    echo "   Enable with:"
    for api in "${MISSING_APIS[@]}"; do
        echo "   gcloud services enable $api --project=$PROJECT_ID"
    done
else
    log_success "✅ All required APIs are enabled"
fi

# Check Docker
echo ""
echo "4. Checking Docker..."
if ! command -v docker &> /dev/null; then
    log_error "❌ Docker is not installed"
    echo "   Install with: brew install --cask docker"
    exit 1
else
    if ! docker info &> /dev/null; then
        log_warn "⚠️  Docker is installed but not running"
        echo "   Start Docker Desktop"
    else
        log_success "✅ Docker is installed and running"
    fi
fi

# Check kubectl
echo ""
echo "5. Checking kubectl..."
if ! command -v kubectl &> /dev/null; then
    log_error "❌ kubectl is not installed"
    echo "   Install with: brew install kubectl"
    exit 1
else
    log_success "✅ kubectl is installed"
fi

# Check current gcloud config
echo ""
echo "6. Checking gcloud configuration..."
CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null)
if [[ "$CURRENT_PROJECT" != "$PROJECT_ID" ]]; then
    log_warn "⚠️  Current gcloud project is '$CURRENT_PROJECT', should be '$PROJECT_ID'"
    echo "   Run: gcloud config set project $PROJECT_ID"
else
    log_success "✅ gcloud project is correctly set"
fi

# Check for existing cluster
echo ""
echo "7. Checking for existing GKE cluster..."
CLUSTER_EXISTS=$(gcloud container clusters list --project=$PROJECT_ID --region=$REGION --filter="name:boa-consent-cluster" --format="value(name)")

if [[ -n "$CLUSTER_EXISTS" ]]; then
    log_success "✅ GKE cluster 'boa-consent-cluster' already exists"
else
    log_info "ℹ️  GKE cluster 'boa-consent-cluster' does not exist (will be created during deployment)"
fi

echo ""
echo "===================================================="
echo "🎯 VERIFICATION COMPLETE"
echo ""

if [ ${#MISSING_APIS[@]} -gt 0 ]; then
    echo "❌ ACTION REQUIRED: Enable missing APIs"
    echo ""
    echo "Run these commands:"
    for api in "${MISSING_APIS[@]}"; do
        echo "gcloud services enable $api --project=$PROJECT_ID"
    done
else
    echo "✅ READY TO DEPLOY!"
    echo ""
    echo "Run: ./gke_setup.sh"
fi

echo ""
echo "📋 Quick setup commands:"
echo "brew install --cask google-cloud-sdk docker"
echo "brew install kubectl"
echo "gcloud auth login"
echo "gcloud config set project $PROJECT_ID"
