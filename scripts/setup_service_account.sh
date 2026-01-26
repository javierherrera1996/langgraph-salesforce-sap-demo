#!/bin/bash
# Setup Google Cloud Service Account for Vertex AI authentication
# This eliminates the need to regenerate tokens every hour

set -e

# Configuration
PROJECT_ID="logical-hallway-485016-r7"
SERVICE_ACCOUNT_NAME="belden-ai-agent"
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
KEY_FILE="$HOME/belden-ai-service-account.json"

echo "======================================================================="
echo "🔐 GOOGLE CLOUD SERVICE ACCOUNT SETUP"
echo "======================================================================="
echo ""
echo "This script will:"
echo "  1. Create a Service Account for Vertex AI"
echo "  2. Grant necessary permissions"
echo "  3. Generate a JSON key file (never expires)"
echo "  4. Update your .env file"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found. Please install it first:"
    echo "   macOS: brew install --cask google-cloud-sdk"
    echo "   Or: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    echo "❌ Not authenticated with gcloud. Run:"
    echo "   gcloud auth login"
    exit 1
fi

echo "✅ gcloud CLI found and authenticated"
echo ""

# Check if service account already exists
if gcloud iam service-accounts describe "$SERVICE_ACCOUNT_EMAIL" --project="$PROJECT_ID" &> /dev/null; then
    echo "⚠️  Service Account already exists: $SERVICE_ACCOUNT_EMAIL"
    read -p "Do you want to use it? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Aborted"
        exit 1
    fi
else
    # Create service account
    echo "📝 Creating Service Account..."
    gcloud iam service-accounts create "$SERVICE_ACCOUNT_NAME" \
        --display-name="Belden AI Agent" \
        --project="$PROJECT_ID"
    echo "✅ Service Account created"
fi

# Grant permissions
echo ""
echo "🔐 Granting permissions..."

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/aiplatform.user" \
    --quiet

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/storage.objectViewer" \
    --quiet

echo "✅ Permissions granted"

# Create key file
echo ""
if [ -f "$KEY_FILE" ]; then
    echo "⚠️  Key file already exists: $KEY_FILE"
    read -p "Do you want to overwrite it? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Aborted"
        exit 1
    fi
    rm "$KEY_FILE"
fi

echo "🔑 Creating JSON key file..."
gcloud iam service-accounts keys create "$KEY_FILE" \
    --iam-account="$SERVICE_ACCOUNT_EMAIL" \
    --project="$PROJECT_ID"

echo "✅ Key file created: $KEY_FILE"

# Update .env
echo ""
echo "📝 Updating .env file..."
ENV_FILE="$(dirname "$0")/../.env"

# Check if GOOGLE_APPLICATION_CREDENTIALS already exists in .env
if grep -q "GOOGLE_APPLICATION_CREDENTIALS" "$ENV_FILE" 2>/dev/null; then
    # Update existing line
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s|^GOOGLE_APPLICATION_CREDENTIALS=.*|GOOGLE_APPLICATION_CREDENTIALS=$KEY_FILE|" "$ENV_FILE"
    else
        # Linux
        sed -i "s|^GOOGLE_APPLICATION_CREDENTIALS=.*|GOOGLE_APPLICATION_CREDENTIALS=$KEY_FILE|" "$ENV_FILE"
    fi
else
    # Add new line
    echo "" >> "$ENV_FILE"
    echo "# Google Cloud Service Account (for Vertex AI authentication)" >> "$ENV_FILE"
    echo "GOOGLE_APPLICATION_CREDENTIALS=$KEY_FILE" >> "$ENV_FILE"
fi

echo "✅ .env file updated"

# Summary
echo ""
echo "======================================================================="
echo "✅ SETUP COMPLETE!"
echo "======================================================================="
echo ""
echo "📋 What was done:"
echo "   1. ✅ Service Account created: $SERVICE_ACCOUNT_EMAIL"
echo "   2. ✅ Permissions granted (aiplatform.user, storage.objectViewer)"
echo "   3. ✅ JSON key saved to: $KEY_FILE"
echo "   4. ✅ .env updated with GOOGLE_APPLICATION_CREDENTIALS"
echo ""
echo "🎯 Next Steps:"
echo "   1. Test the connection:"
echo "      python scripts/test_vertex_auth.py"
echo ""
echo "   2. Deploy your agent:"
echo "      python deploy_agent.py"
echo ""
echo "   3. Your Postman requests will now work without updating tokens!"
echo ""
echo "⚠️  IMPORTANT:"
echo "   - Keep $KEY_FILE secure (never commit to git)"
echo "   - The key never expires (unlike gcloud tokens)"
echo "   - Rotate the key periodically for security"
echo ""
