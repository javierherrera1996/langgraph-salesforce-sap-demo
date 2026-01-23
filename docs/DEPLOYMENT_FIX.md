# 🔧 Fix for "service account info is missing 'email' field" Error

## Problem

When deploying to Vertex AI Agent Engine, you get:
```
google.auth.exceptions.RefreshError: Unexpected response from metadata server: 
service account info is missing 'email' field.
```

## Root Cause

This error happens when the code tries to authenticate using Compute Engine metadata service, but:
1. The agent is running in Vertex AI Agent Engine (not Compute Engine)
2. The metadata service doesn't have the expected service account information
3. Some dependency is trying to use Vertex AI SDK with Compute Engine credentials

## Solution

### Option 1: Ensure No Vertex AI SDK Initialization in Agent Code

**Verify your `src/app.py` and related files do NOT have:**

```python
# ❌ DON'T DO THIS in agent code
import vertexai
vertexai.init(project=..., location=...)
```

**The code should only use:**
- `ChatOpenAI` (OpenAI SDK) - ✅ This is what we use
- No `ChatVertexAI` - ❌ This requires Vertex AI auth

### Option 2: Check Dependencies

Make sure `requirements.txt` doesn't include Vertex AI SDK unless needed:

```txt
# ✅ Good - we use OpenAI
langchain-openai>=0.1.0

# ❌ Only include if you need Vertex AI LLM
# google-cloud-aiplatform>=1.50.0  # Comment out if not using ChatVertexAI
```

### Option 3: Set GOOGLE_APPLICATION_CREDENTIALS (if needed)

If you're using a service account key file, set:

```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

But **for Agent Engine, this is usually NOT needed** - the agent runs with the project's default service account.

### Option 4: Use Application Default Credentials

If you need GCP authentication in your agent code, use:

```python
import google.auth
from google.auth import default

# This works in Agent Engine
credentials, project = default()
```

## Quick Fix Steps

1. **Verify no Vertex AI init in agent code:**
   ```bash
   grep -r "vertexai.init" src/
   # Should return nothing
   ```

2. **Check you're using ChatOpenAI (not ChatVertexAI):**
   ```bash
   grep -r "ChatVertexAI" src/
   # Should return nothing
   ```

3. **Verify requirements.txt:**
   - Should have `langchain-openai`
   - Should NOT have `google-cloud-aiplatform` (unless you need it)

4. **Re-deploy:**
   ```bash
   python deploy_agent.py
   ```

## Current Code Status

✅ The codebase uses `ChatOpenAI` (OpenAI SDK), which doesn't require Vertex AI authentication
✅ No `vertexai.init()` calls in `src/` directory
✅ This should work without authentication issues

## If Error Persists

The error might be coming from:
1. **A dependency** trying to use Vertex AI SDK
2. **LangChain** trying to authenticate for some reason
3. **Environment variables** causing authentication attempts

**Try this:**

1. Check what's actually being imported:
   ```python
   # In src/app.py, add at the top:
   import sys
   print("Python path:", sys.path)
   print("Imports:", sys.modules.keys())
   ```

2. Check if LangChain is trying to use Vertex AI:
   ```bash
   grep -r "vertex" requirements.txt
   ```

3. Ensure environment variables are set correctly in Agent Engine:
   - Go to Vertex AI Console → Your Agent → Environment Variables
   - Make sure `OPENAI_API_KEY` is set (not Vertex AI keys)

## Alternative: Use Local Deployment First

Test locally before deploying:

```bash
# Local test
langgraph dev

# If local works, then deploy
python deploy_agent.py
```

---

## Most Likely Fix

Since the error mentions "metadata server", it's likely that:

1. **The agent is trying to use Compute Engine credentials** when it shouldn't
2. **Solution**: Make sure you're using `ChatOpenAI` (which we are) and NOT `ChatVertexAI`

The current codebase should work. If you're still getting the error, it might be:
- A dependency issue
- An environment variable causing authentication attempts
- A cached deployment with old code

**Try:**
1. Delete and re-create the agent
2. Clear any cached dependencies
3. Verify `requirements.txt` only has what you need
