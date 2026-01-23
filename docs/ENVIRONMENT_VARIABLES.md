# 🔧 Environment Variables Guide

Complete list of all environment variables needed for the Belden AI Sales Agent.

---

## 📧 Email Configuration (Resend)

### Required
```bash
RESEND_API_KEY=re_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```
- Get from: https://resend.com/api-keys
- Required for sending emails

### Optional (with defaults)
```bash
RESEND_FROM_EMAIL=onboarding@resend.dev
```
- Default sender email
- Use `onboarding@resend.dev` for testing
- Use your verified domain for production

---

## 📬 Email Recipients

### Lead Qualification Emails
```bash
SALES_AGENT_EMAIL=sales@belden.com
```
- **Required for lead emails**
- Receives emails when lead score >= 60%
- If not set, falls back to `NOTIFICATION_EMAIL`

### Complaint Classification Emails

#### Product Complaints
```bash
PRODUCT_EXPERT_EMAIL=productos@belden.com
```
- **Required for product complaint emails**
- Receives emails for product-related issues (switches, cables, connectors, software)
- If not set, falls back to `NOTIFICATION_EMAIL`

#### Services/IT Support
```bash
SERVICES_AGENT_EMAIL=servicios@belden.com
```
- **Required for IT/services emails**
- Receives emails for IT support, portal access, account issues
- If not set, falls back to `NOTIFICATION_EMAIL`

### General Fallback
```bash
NOTIFICATION_EMAIL=notificaciones@belden.com
```
- **Fallback email** for all notifications
- Used if specific recipient email is not configured
- Should be set as a safety net

### IT Support Portal
```bash
IT_SUPPORT_URL=https://support.belden.com/it
```
- URL for IT support portal redirects
- Default: `https://support.belden.com/it`

---

## 📋 Complete .env Example

```bash
# ============================================================================
# Resend Email Service
# ============================================================================
RESEND_API_KEY=re_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
RESEND_FROM_EMAIL=onboarding@resend.dev

# ============================================================================
# Email Recipients
# ============================================================================
# Lead Qualification (score >= 60%)
SALES_AGENT_EMAIL=sales@belden.com

# Complaint Classification
PRODUCT_EXPERT_EMAIL=productos@belden.com
SERVICES_AGENT_EMAIL=servicios@belden.com

# General fallback
NOTIFICATION_EMAIL=notificaciones@belden.com

# IT Support Portal
IT_SUPPORT_URL=https://support.belden.com/it

# ============================================================================
# OpenAI / LLM
# ============================================================================
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ============================================================================
# LangSmith Tracing
# ============================================================================
LANGSMITH_API_KEY=lsv2_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
LANGCHAIN_PROJECT=belden-ai-agent
LANGCHAIN_TRACING_V2=true

# ============================================================================
# Salesforce (Optional - for real integration)
# ============================================================================
SALESFORCE_MODE=real
SALESFORCE_INSTANCE_URL=https://your-instance.salesforce.com
SALESFORCE_CLIENT_ID=your_client_id
SALESFORCE_CLIENT_SECRET=your_client_secret
SALESFORCE_USERNAME=your_username
SALESFORCE_PASSWORD=your_password
SALESFORCE_SECURITY_TOKEN=your_security_token

# ============================================================================
# SAP (Optional - for real integration)
# ============================================================================
SAP_MODE=real
SAP_BASE_URL=https://your-sap-instance.com
SAP_USERNAME=your_sap_username
SAP_PASSWORD=your_sap_password
```

---

## 🎯 Email Routing Summary

### Lead Qualification
- **Score >= 60%** → Email to `SALES_AGENT_EMAIL`
- **Score < 60%** → No email sent

### Complaint Classification

#### Product Complaints → `PRODUCT_EXPERT_EMAIL`
- Switch issues
- Cable problems
- Connector defects
- Software/firmware bugs
- Product installation issues
- General product inquiries (default if not IT)

#### IT/Services → `SERVICES_AGENT_EMAIL`
- Portal access problems
- Password reset requests
- Account issues
- Website/online platform problems
- IT support requests
- VPN configuration help

---

## ✅ Verification

To verify your email configuration is correct:

```bash
# Test Resend API
python scripts/test_resend_api.py

# Test email configuration loading
python scripts/test_email_config.py
```

---

## 🔍 Troubleshooting

### Email not sending for leads
- ✅ Check `RESEND_API_KEY` is set
- ✅ Check `SALES_AGENT_EMAIL` is set (or `NOTIFICATION_EMAIL` as fallback)
- ✅ Verify API key is valid: `python scripts/test_resend_api.py`

### Product emails going to wrong recipient
- ✅ Check `PRODUCT_EXPERT_EMAIL` is set
- ✅ Verify classification is correct (check logs)

### Services emails going to wrong recipient
- ✅ Check `SERVICES_AGENT_EMAIL` is set
- ✅ Verify classification is correct (check logs)

### All emails going to same recipient
- ✅ Check that `PRODUCT_EXPERT_EMAIL` and `SERVICES_AGENT_EMAIL` are different
- ✅ Verify the classification prompt is working correctly
- ✅ Check logs to see which action is being taken

---

## 📚 Related Documentation

- [Email Configuration Guide](EMAIL_CONFIGURATION.md)
- [Resend Setup Guide](RESEND_SETUP.md)
- [API Endpoints](API_ENDPOINTS.md)
