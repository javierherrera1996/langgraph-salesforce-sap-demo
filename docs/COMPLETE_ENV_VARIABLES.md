# 🔧 Complete Environment Variables Reference

Complete list of all environment variables for the Belden AI Sales Agent, including Vertex AI deployment.

---

## 📋 Quick Setup

1. Copy `.env.example` to `.env`
2. Fill in your actual values
3. For Vertex AI: Set these in Cloud Run or Agent Engine environment variables

---

## 🔑 Required Variables (Minimum Setup)

### For Local Development
```bash
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
RESEND_API_KEY=re_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
SALES_AGENT_EMAIL=sales@belden.com
PRODUCT_EXPERT_EMAIL=productos@belden.com
SERVICES_AGENT_EMAIL=servicios@belden.com
NOTIFICATION_EMAIL=notificaciones@belden.com
```

### For Vertex AI Deployment
```bash
PROJECT_ID=your-gcp-project-id
LOCATION=us-central1
STAGING_BUCKET=gs://your-project-id-agent-staging
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

## 📦 Complete Variable List

### Google Cloud Platform (Vertex AI)
```bash
PROJECT_ID=logical-hallway-485016-r7
LOCATION=us-central1
STAGING_BUCKET=gs://logical-hallway-485016-r7-agent-staging
```

**How to get:**
- `PROJECT_ID`: Your GCP project ID from Cloud Console
- `LOCATION`: Usually `us-central1` or your preferred region
- `STAGING_BUCKET`: Create with `gsutil mb -l us-central1 gs://${PROJECT_ID}-agent-staging`

---

### OpenAI / LLM
```bash
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**How to get:**
- Go to https://platform.openai.com/api-keys
- Create a new API key
- Copy the key (starts with `sk-`)

---

### LangSmith Tracing (Recommended)
```bash
LANGSMITH_API_KEY=lsv2_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=belden-ai-agent
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
```

**How to get:**
- Go to https://smith.langchain.com
- Sign up / Log in
- Go to Settings → API Keys
- Create a new API key (starts with `lsv2_`)

---

### Resend Email Service
```bash
RESEND_API_KEY=re_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
RESEND_FROM_EMAIL=onboarding@resend.dev
```

**How to get:**
- Go to https://resend.com/api-keys
- Create a new API key
- Copy the key (starts with `re_`)
- For testing, use `onboarding@resend.dev` as sender
- For production, verify your domain

---

### Email Recipients
```bash
# Lead Qualification (score >= 60%)
SALES_AGENT_EMAIL=sales@belden.com

# Complaint Classification - Product
PRODUCT_EXPERT_EMAIL=productos@belden.com

# Complaint Classification - IT/Services
SERVICES_AGENT_EMAIL=servicios@belden.com

# General fallback
NOTIFICATION_EMAIL=notificaciones@belden.com

# IT Support Portal
IT_SUPPORT_URL=https://support.belden.com/it
```

**Email Routing:**
- Lead score >= 60% → `SALES_AGENT_EMAIL`
- Product complaint → `PRODUCT_EXPERT_EMAIL`
- IT/Services → `SERVICES_AGENT_EMAIL`
- Fallback → `NOTIFICATION_EMAIL`

---

### Salesforce (Optional - for real integration)
```bash
SALESFORCE_MODE=mock
# OR
SALESFORCE_MODE=real
SALESFORCE_INSTANCE_URL=https://your-instance.salesforce.com
SALESFORCE_CLIENT_ID=your_connected_app_client_id
SALESFORCE_CLIENT_SECRET=your_connected_app_client_secret
SALESFORCE_USERNAME=your_salesforce_username
SALESFORCE_PASSWORD=your_salesforce_password
SALESFORCE_SECURITY_TOKEN=your_security_token
SALESFORCE_LOGIN_URL=https://login.salesforce.com
SALESFORCE_API_VERSION=v59.0
```

**For mock mode (demo):**
- Set `SALESFORCE_MODE=mock`
- No other Salesforce variables needed

**For real integration:**
- Create a Connected App in Salesforce
- Get Client ID and Client Secret
- Get Security Token from your user profile

---

### SAP (Optional - for real integration)
```bash
SAP_MODE=mock
# OR
SAP_MODE=real
SAP_BASE_URL=https://your-sap-instance.com/sap/opu/odata/sap
SAP_API_KEY=your_sap_api_key
SAP_USERNAME=your_sap_username
SAP_PASSWORD=your_sap_password
SAP_CLIENT=100
```

**For mock mode (demo):**
- Set `SAP_MODE=mock`
- No other SAP variables needed

---

### Routing Configuration (Salesforce Owner IDs)
```bash
ROUTING_AE_OWNER_ID=005000000000001AAA
ROUTING_SDR_OWNER_ID=005000000000002AAA
ROUTING_NURTURE_OWNER_ID=005000000000003AAA
ROUTING_ESCALATION_OWNER_ID=005000000000004AAA
```

**How to get:**
- Go to Salesforce → Setup → Users
- Find the user you want to assign leads to
- Copy their User ID (18 characters, starts with `005`)

---

### Application Settings
```bash
APP_HOST=0.0.0.0
APP_PORT=8000
APP_DEBUG=true
APP_LOG_LEVEL=INFO
```

**Defaults:**
- `APP_HOST`: `0.0.0.0` (all interfaces)
- `APP_PORT`: `8000`
- `APP_DEBUG`: `true` (set to `false` in production)
- `APP_LOG_LEVEL`: `INFO` (options: DEBUG, INFO, WARNING, ERROR)

---

### Product Owner Emails (Optional)
```bash
PRODUCT_OWNER_SWITCHES=switches-owner@belden.com
PRODUCT_OWNER_CABLES=cables-owner@belden.com
PRODUCT_OWNER_CONNECTORS=connectors-owner@belden.com
PRODUCT_OWNER_SOFTWARE=software-owner@belden.com
PRODUCT_OWNER_INFRASTRUCTURE=infrastructure-owner@belden.com
PRODUCT_OWNER_GENERAL=productos@belden.com
```

**Usage:**
- If set, product complaints are routed to specific owners by category
- If not set, uses `PRODUCT_EXPERT_EMAIL` for all product complaints

---

## 🚀 Setup for Different Environments

### Local Development (.env file)
```bash
# Copy example
cp .env.example .env

# Edit with your values
nano .env

# Load variables
export $(grep -v '^#' .env | xargs)
```

### Vertex AI Agent Engine
Set environment variables in Cloud Console:
1. Go to Vertex AI → Agent Engine
2. Select your agent
3. Edit → Environment Variables
4. Add all required variables

Or use `update_env_vars.py`:
```bash
python update_env_vars.py
```

### Cloud Run (if deploying separately)
```bash
gcloud run services update belden-ai-agent \
  --set-env-vars="OPENAI_API_KEY=sk-xxx,RESEND_API_KEY=re-xxx" \
  --region=us-central1
```

---

## ✅ Verification

### Test Resend Configuration
```bash
python scripts/test_resend_api.py
```

### Test Email Configuration Loading
```bash
python scripts/test_email_config.py
```

### Test API Endpoints
```bash
# Health check
curl http://localhost:8000/health

# Config status
curl http://localhost:8000/status/config
```

---

## 🔍 Troubleshooting

### Variables not loading
```bash
# Check if .env exists
ls -la .env

# Check if variables are loaded
echo $OPENAI_API_KEY

# Load manually
export $(grep -v '^#' .env | xargs)
```

### Vertex AI deployment fails
```bash
# Verify GCP project
gcloud config get project

# Verify APIs enabled
gcloud services list --enabled | grep aiplatform

# Check permissions
gcloud projects get-iam-policy $PROJECT_ID
```

### Emails not sending
```bash
# Check Resend API key
echo $RESEND_API_KEY

# Check recipient emails
echo $SALES_AGENT_EMAIL
echo $PRODUCT_EXPERT_EMAIL
echo $SERVICES_AGENT_EMAIL

# Test Resend API
python scripts/test_resend_api.py
```

---

## 📚 Related Documentation

- [Environment Variables Guide](ENVIRONMENT_VARIABLES.md)
- [Resend Setup](RESEND_SETUP.md)
- [Vertex AI Deployment](DEPLOY_CLOUDSHELL.md)
- [API Endpoints](API_ENDPOINTS.md)
