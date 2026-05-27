#!/bin/bash
# Quick start script for AWS Serverless ML Pipeline
# Run this to get everything up and running locally or on AWS

set -e

echo "🚀 AWS Serverless ML Pipeline - Quick Start"
echo "============================================"
echo ""

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Install from https://python.org"
    exit 1
fi

if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry not found. Install with: pip install poetry"
    exit 1
fi

echo "✓ Python and Poetry installed"
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
poetry install --no-root
echo "✓ Dependencies installed"
echo ""

# Choice: Local or AWS
echo "🌍 Select deployment mode:"
echo "1. Local (FastAPI + Streamlit)"
echo "2. AWS (requires AWS CLI and SAM CLI)"
read -p "Enter choice (1 or 2): " choice

if [ "$choice" = "1" ]; then
    echo ""
    echo "🔧 Starting local development environment..."
    echo ""
    echo "Terminal 1 - Start FastAPI backend:"
    echo "  poetry run uvicorn app.app_main:app --reload"
    echo ""
    echo "Terminal 2 - Start Streamlit UI:"
    echo "  poetry run streamlit run app/streamlit_ui.py"
    echo ""
    echo "Then open: http://localhost:8501"
    echo ""

elif [ "$choice" = "2" ]; then
    echo ""
    echo "🔧 AWS deployment requires SAM CLI"
    echo ""

    if ! command -v sam &> /dev/null; then
        echo "❌ AWS SAM CLI not found"
        echo "Install with: brew install aws-sam-cli"
        echo "              (or: pip install aws-sam-cli)"
        exit 1
    fi

    echo "✓ SAM CLI found"
    echo ""
    read -p "Enter AWS region (default: us-east-1): " region
    region=${region:-us-east-1}

    echo ""
    echo "🚀 Deploying infrastructure to AWS..."
    cd infrastructure
    chmod +x deploy.sh
    ./deploy.sh ml-inference-pipeline-dev "$region" dev

else
    echo "Invalid choice"
    exit 1
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "📚 Next steps:"
echo "  - Read: README.md for full documentation"
echo "  - Check: infrastructure/template.yaml for IaC structure"
echo "  - Test: app/streamlit_ui.py for web UI"
echo ""
