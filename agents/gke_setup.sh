#!/bin/bash

# Open Banking Consent Choreographer - GKE Setup Script
# This script sets up a GKE Autopilot cluster and deploys the multi-agent system

set -e

# Configuration
PROJECT_ID=${PROJECT_ID:-"your-gcp-project-id"}
CLUSTER_NAME=${CLUSTER_NAME:-"boa-consent-cluster"}
REGION=${REGION:-"us-central1"}
IMAGE_REPO="gcr.io/${PROJECT_ID}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    if ! command -v gcloud &> /dev/null; then
        log_error "gcloud CLI is not installed. Please install it first."
        exit 1
    fi

    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install it first."
        exit 1
    fi

    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed. Please install it first."
        exit 1
    fi

    # Check if authenticated
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n 1 > /dev/null; then
        log_error "Not authenticated with gcloud. Please run 'gcloud auth login' first."
        exit 1
    fi

    log_info "Prerequisites check passed."
}

# Set up GCP project
setup_gcp_project() {
    log_info "Setting up GCP project: ${PROJECT_ID}"

    gcloud config set project ${PROJECT_ID}

    # Enable required APIs
    log_info "Enabling required GCP APIs..."
    gcloud services enable container.googleapis.com
    gcloud services enable aiplatform.googleapis.com
    gcloud services enable artifactregistry.googleapis.com

    # Create Artifact Registry repository
    log_info "Creating Artifact Registry repository..."
    gcloud artifacts repositories create consent-agents-repo \
        --repository-format=docker \
        --location=${REGION} \
        --description="Docker repository for consent choreographer agents" || \
    log_warn "Artifact Registry repository may already exist."
}

# Create GKE Autopilot cluster
create_gke_cluster() {
    log_info "Creating GKE Autopilot cluster: ${CLUSTER_NAME}"

    gcloud container clusters create-auto ${CLUSTER_NAME} \
        --region=${REGION} \
        --project=${PROJECT_ID} \
        --release-channel=regular \
        --enable-private-nodes

    log_info "Getting cluster credentials..."
    gcloud container clusters get-credentials ${CLUSTER_NAME} --region=${REGION}

    log_info "Cluster created successfully!"}
create_gke_cluster() {
    log_info "Creating GKE Autopilot cluster: ${CLUSTER_NAME}"

    gcloud container clusters create-auto ${CLUSTER_NAME} \
        --region=${REGION} \
        --project=${PROJECT_ID} \
        --release-channel=regular \
        --enable-private-nodes

    log_info "Getting cluster credentials..."
    gcloud container clusters get-credentials ${CLUSTER_NAME} --region=${REGION}

    log_info "Cluster created successfully!"}
create_gke_cluster() {
    log_info "Creating GKE Autopilot cluster: ${CLUSTER_NAME}"

    gcloud container clusters create-auto ${CLUSTER_NAME} \
        --region=${REGION} \
        --project=${PROJECT_ID} \
        --release-channel=regular \
        --enable-private-nodes

    log_info "Getting cluster credentials..."
    gcloud container clusters get-credentials ${CLUSTER_NAME} --region=${REGION}

    log_info "Cluster created successfully!"}
create_gke_cluster() {
    log_info "Creating GKE Autopilot cluster: ${CLUSTER_NAME}"

    gcloud container clusters create-auto ${CLUSTER_NAME} \
        --region=${REGION} \
        --project=${PROJECT_ID} \
        --release-channel=regular \
        --enable-private-nodes

    log_info "Getting cluster credentials..."
    gcloud container clusters get-credentials ${CLUSTER_NAME} --region=${REGION}

    log_info "Cluster created successfully!"}
create_gke_cluster() {
    log_info "Creating GKE Autopilot cluster: ${CLUSTER_NAME}"

    gcloud container clusters create-auto ${CLUSTER_NAME} \
        --region=${REGION} \
        --project=${PROJECT_ID} \
        --release-channel=regular \
        --enable-private-nodes

    log_info "Getting cluster credentials..."
    gcloud container clusters get-credentials ${CLUSTER_NAME} --region=${REGION}

    log_info "Cluster created successfully!"}
create_gke_cluster() {
    log_info "Creating GKE Autopilot cluster: ${CLUSTER_NAME}"

    gcloud container clusters create-auto ${CLUSTER_NAME} \
        --region=${REGION} \
        --project=${PROJECT_ID} \
        --release-channel=regular \
        --enable-private-nodes

    log_info "Getting cluster credentials..."
    gcloud container clusters get-credentials ${CLUSTER_NAME} --region=${REGION}

    log_info "Cluster created successfully!"}
create_gke_cluster() {
    log_info "Creating GKE Autopilot cluster: ${CLUSTER_NAME}"

    gcloud container clusters create-auto ${CLUSTER_NAME} \
        --region=${REGION} \
        --project=${PROJECT_ID} \
        --release-channel=regular \
        --enable-private-nodes

    log_info "Getting cluster credentials..."
    gcloud container clusters get-credentials ${CLUSTER_NAME} --region=${REGION}

    log_info "Cluster created successfully!"}
create_gke_cluster() {
    log_info "Creating GKE Autopilot cluster: ${CLUSTER_NAME}"

    gcloud container clusters create-auto ${CLUSTER_NAME} \
        --region=${REGION} \
        --project=${PROJECT_ID} \
        --release-channel=regular \
        --enable-private-nodes

    log_info "Getting cluster credentials..."
    gcloud container clusters get-credentials ${CLUSTER_NAME} --region=${REGION}

    log_info "Cluster created successfully!"}
create_gke_cluster() {
    log_info "Creating GKE Autopilot cluster: ${CLUSTER_NAME}"

    gcloud container clusters create-auto ${CLUSTER_NAME} \
        --region=${REGION} \
        --project=${PROJECT_ID} \
        --release-channel=regular \
        --enable-private-nodes

    log_info "Getting cluster credentials..."
    gcloud container clusters get-credentials ${CLUSTER_NAME} --region=${REGION}

    log_info "Cluster created successfully!"}
create_gke_cluster() {
    log_info "Creating GKE Autopilot cluster: ${CLUSTER_NAME}"

    gcloud container clusters create-auto ${CLUSTER_NAME} \
        --region=${REGION} \
        --project=${PROJECT_ID} \
        --release-channel=regular \
        --enable-private-nodes

    log_info "Getting cluster credentials..."
    gcloud container clusters get-credentials ${CLUSTER_NAME} --region=${REGION}

    log_info "Cluster created successfully!"}
create_gke_cluster() {
    log_info "Creating GKE Autopilot cluster: ${CLUSTER_NAME}"

    gcloud container clusters create-auto ${CLUSTER_NAME} \
        --region=${REGION} \
        --project=${PROJECT_ID} \
        --release-channel=regular \
        --enable-private-nodes

    log_info "Getting cluster credentials..."
    gcloud container clusters get-credentials ${CLUSTER_NAME} --region=${REGION}

    log_info "Cluster created successfully!"}
create_gke_cluster() {
    log_info "Creating GKE Autopilot cluster: ${CLUSTER_NAME}"

    gcloud container clusters create-auto ${CLUSTER_NAME} \
        --region=${REGION} \
        --project=${PROJECT_ID} \
        --release-channel=regular \
        --enable-private-nodes

    log_info "Getting cluster credentials..."
    gcloud container clusters get-credentials ${CLUSTER_NAME} --region=${REGION}

    log_info "Cluster created successfully!"}
create_gke_cluster() {
    log_info "Creating GKE Autopilot cluster: ${CLUSTER_NAME}"

    gcloud container clusters create-auto ${CLUSTER_NAME} \
        --region=${REGION} \
        --project=${PROJECT_ID} \
        --release-channel=regular \
        --enable-private-nodes

    log_info "Getting cluster credentials..."
    gcloud container clusters get-credentials ${CLUSTER_NAME} --region=${REGION}

    log_info "Cluster created successfully!"}
create_gke_cluster() {
    log_info "Creating GKE Autopilot cluster: ${CLUSTER_NAME}"

    gcloud container clusters create-auto ${CLUSTER_NAME} \
        --region=${REGION} \
        --project=${PROJECT_ID} \
        --release-channel=regular \
        --enable-private-nodes

    log_info "Getting cluster credentials..."
    gcloud container clusters get-credentials ${CLUSTER_NAME} --region=${REGION}

    log_info "Cluster created successfully!"}
create_gke_cluster() {
    log_info "Creating GKE Autopilot cluster: ${CLUSTER_NAME}"

    gcloud container clusters create-auto ${CLUSTER_NAME} \
        --region=${REGION} \
        --project=${PROJECT_ID} \
        --release-channel=regular \
        --enable-private-nodes

    log_info "Getting cluster credentials..."
    gcloud container clusters get-credentials ${CLUSTER_NAME} --region=${REGION}

    log_info "Cluster created successfully!"}
}

# Build and push Docker images
build_and_push_images() {
    log_info "Building and pushing Docker images..."

    # Authenticate Docker with gcloud
    gcloud auth configure-docker ${REGION}-docker.pkg.dev --quiet

    # Build monitoring agent
    log_info "Building monitoring agent image..."
    docker build -f Dockerfile-monitoring -t ${IMAGE_REPO}/monitoring-agent:latest .
    docker push ${IMAGE_REPO}/monitoring-agent:latest

    # Build validation agent
    log_info "Building validation agent image..."
    docker build -f Dockerfile-validation -t ${IMAGE_REPO}/validation-agent:latest .
    docker push ${IMAGE_REPO}/validation-agent:latest

    # Build audit agent
    log_info "Building audit agent image..."
    docker build -f Dockerfile-audit -t ${IMAGE_REPO}/audit-agent:latest .
    docker push ${IMAGE_REPO}/audit-agent:latest

    # Build streamlit dashboard
    log_info "Building Streamlit dashboard image..."
    docker build -f Dockerfile-streamlit -t ${IMAGE_REPO}/streamlit-dashboard:latest .
    docker push ${IMAGE_REPO}/streamlit-dashboard:latest

    log_info "All images built and pushed successfully!"
}

# Deploy Bank of Anthos (original app)
deploy_bank_of_anthos() {
    log_info "Deploying Bank of Anthos application..."

    # Navigate to the root directory
    cd ..

    # Apply the original manifests
    kubectl apply -f kubernetes-manifests/

    # Wait for deployments to be ready
    log_info "Waiting for Bank of Anthos deployments to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/frontend -n default
    kubectl wait --for=condition=available --timeout=300s deployment/ledger-writer -n default
    kubectl wait --for=condition=available --timeout=300s deployment/user-service -n default

    log_info "Bank of Anthos deployed successfully!"
}

# Deploy agents
deploy_agents() {
    log_info "Deploying consent choreographer agents..."

    # Update the deployment YAML with actual image paths
    sed -i "s|gcr.io/YOUR_PROJECT|${IMAGE_REPO}|g" agents-deployment.yaml

    # Apply the agents deployment
    kubectl apply -f agents-deployment.yaml

    # Wait for agents to be ready
    log_info "Waiting for agents to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/monitoring-agent -n agents-ns
    kubectl wait --for=condition=available --timeout=300s deployment/validation-agent -n agents-ns
    kubectl wait --for=condition=available --timeout=300s deployment/audit-agent -n agents-ns
    kubectl wait --for=condition=available --timeout=300s deployment/streamlit-dashboard -n agents-ns

    log_info "All agents deployed successfully!"
}

# Setup ingress and external access
setup_ingress() {
    log_info "Setting up ingress for dashboard access..."

    # Reserve a static IP (optional - comment out if not needed)
    # gcloud compute addresses create agents-static-ip --global

    # The ingress is already defined in the deployment YAML
    log_info "Dashboard will be accessible via the ingress once DNS is configured."
}

# Main deployment function
main() {
    log_info "Starting Open Banking Consent Choreographer deployment..."
    log_info "Project ID: ${PROJECT_ID}"
    log_info "Region: ${REGION}"
    log_info "Cluster: ${CLUSTER_NAME}"

    check_prerequisites
    setup_gcp_project
    create_gke_cluster
    build_and_push_images
    deploy_bank_of_anthos
    deploy_agents
    setup_ingress

    log_info "🎉 Deployment completed successfully!"
    log_info ""
    log_info "Next steps:"
    log_info "1. Get the dashboard URL: kubectl get ingress agents-ingress -n agents-ns"
    log_info "2. Monitor agent logs: kubectl logs -f deployment/monitoring-agent -n agents-ns"
    log_info "3. Check agent status: kubectl get pods -n agents-ns"
    log_info ""
    log_info "For demo purposes, you can:"
    log_info "- Access the Streamlit dashboard to see agent activity"
    log_info "- Check audit logs for compliance reports"
    log_info "- Monitor agent coordination via A2A messaging"
}

# Handle command line arguments
case "${1:-}" in
    "check")
        check_prerequisites
        ;;
    "cluster")
        check_prerequisites
        setup_gcp_project
        create_gke_cluster
        ;;
    "images")
        check_prerequisites
        setup_gcp_project
        build_and_push_images
        ;;
    "deploy-boa")
        check_prerequisites
        deploy_bank_of_anthos
        ;;
    "deploy-agents")
        check_prerequisites
        deploy_agents
        ;;
    "all"|*)
        main
        ;;
esac
