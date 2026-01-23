#!/bin/bash
# Quick script to update Agent Engine environment variables
# This script loads from .env and updates the agent

set -e

echo "🔄 Updating Vertex AI Agent Engine Environment Variables"
echo "=========================================================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "   Please create a .env file with your environment variables."
    exit 1
fi

# Check if Python script exists
SCRIPT_PATH="scripts/update_agent_env_vars.py"
if [ ! -f "$SCRIPT_PATH" ]; then
    echo "❌ Error: $SCRIPT_PATH not found!"
    exit 1
fi

# Run the update script
echo "📋 Loading variables from .env..."
python3 "$SCRIPT_PATH"

echo ""
echo "✅ Done! Check the output above for any errors."
