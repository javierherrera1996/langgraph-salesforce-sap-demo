# 🔧 Troubleshooting Vertex AI Agent Engine Deployment

## Error: "service account info is missing 'email' field"

### Problem
```
google.auth.exceptions.RefreshError: Unexpected response from metadata server: 
service account info is missing 'email' field.
```

This error occurs when the agent code tries to authenticate using Compute Engine credentials that aren't available in the Agent Engine runtime environment.

### Solution

The issue is that **when code runs inside Vertex AI Agent Engine, it should NOT call `vertexai.init()`**. The Agent Engine handles authentication automatically.

#### Check Your Code

Make sure your `src/app.py` and agent classes **DO NOT** call `vertexai.init()` in the `set_up()` method or anywhere else that runs during agent execution.

**❌ WRONG** (in `src/app.py`):
```python
def set_up(self):
    import vertexai
    vertexai.init(project=self.project, location=self.location)  # DON'T DO THIS!
```

**✅ CORRECT** (in `src/app.py`):
```python
def set_up(self):
    # NO vertexai.init() here - Agent Engine handles it
    load_dotenv()
    from src.config import get_settings
    settings = get_settings()
    settings.configure_langsmith()
    # ... rest of setup
```

#### Only Initialize Vertex AI in Deployment Script

**✅ CORRECT** (in `deploy_agent.py`):
```python
def main():
    # This is OK - we're deploying FROM local machine
    vertexai.init(
        project=PROJECT_ID,
        location=LOCATION,
        staging_bucket=STAGING_BUCKET
    )
    # ... deploy agent
```

### Verification

1. **Check `src/app.py`**: Search for `vertexai.init` - should NOT be there
2. **Check graph files**: `src/graphs/*.py` should NOT have `vertexai.init`
3. **Check tools**: `src/tools/*.py` should NOT have `vertexai.init`

### If You Need Vertex AI SDK in Agent Code

If you need to use Vertex AI SDK inside the agent (e.g., for calling other Vertex AI services), you should:

1. **Use Application Default Credentials**:
```python
import google.auth
from google.auth import default

# Get default credentials (works in Agent Engine)
credentials, project = default()
```

2. **Or use environment variables**:
```python
import os
project_id = os.getenv("PROJECT_ID")
# Don't call vertexai.init()
```

### Common Causes

1. **Copying code from deployment script**: Deployment scripts need `vertexai.init()`, but agent code should NOT
2. **Using Vertex AI LLM**: If you're using `ChatVertexAI` instead of `ChatOpenAI`, make sure it doesn't call `vertexai.init()`
3. **Testing locally**: Local tests might need `vertexai.init()`, but remove it before deployment

### Quick Fix

1. Search your codebase:
```bash
grep -r "vertexai.init" src/
```

2. Remove any `vertexai.init()` calls from:
   - `src/app.py`
   - `src/graphs/*.py`
   - `src/tools/*.py`

3. Keep `vertexai.init()` only in:
   - `deploy_agent.py` (deployment script)
   - `demo/*.py` (local demo scripts)
   - `scripts/*.py` (local utility scripts)

### Alternative: Use OpenAI Instead

If you're having authentication issues with Vertex AI, you can use OpenAI (which is what the current code uses):

```python
from langchain_openai import ChatOpenAI

# This works without any Vertex AI authentication
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)
```

The current codebase uses `ChatOpenAI`, so you shouldn't have this issue unless you've modified it.

---

## Other Common Errors

### Error: "Permission denied"
- **Cause**: Service account doesn't have required permissions
- **Fix**: Grant `Vertex AI User` role to the service account

### Error: "API not enabled"
- **Cause**: Vertex AI API not enabled
- **Fix**: `gcloud services enable aiplatform.googleapis.com`

### Error: "Bucket not found"
- **Cause**: Staging bucket doesn't exist
- **Fix**: `gsutil mb -l us-central1 gs://${PROJECT_ID}-agent-staging`

### Error: "OPENAI_API_KEY not set"
- **Cause**: Environment variable not passed to agent
- **Fix**: Add to `env_vars` in `deploy_agent.py` and ensure it's in `.env`

---

## Deployment Checklist

Before deploying, verify:

- [ ] No `vertexai.init()` in `src/app.py`
- [ ] No `vertexai.init()` in `src/graphs/*.py`
- [ ] No `vertexai.init()` in `src/tools/*.py`
- [ ] `OPENAI_API_KEY` is in `.env` and `env_vars` in `deploy_agent.py`
- [ ] `PROJECT_ID`, `LOCATION`, `STAGING_BUCKET` are set
- [ ] Vertex AI API is enabled
- [ ] Service account has proper permissions
- [ ] Staging bucket exists

---

## Getting Help

If the error persists:

1. Check logs in Cloud Console:
   - Vertex AI → Agent Engine → Your Agent → Logs

2. Test locally first:
   ```bash
   python deploy_agent.py --mode test
   ```

3. Verify credentials:
   ```bash
   gcloud auth application-default login
   ```

4. Check service account:
   ```bash
   gcloud iam service-accounts list
   ```
