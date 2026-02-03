# AWS Bedrock Integration Setup

## Overview

ABoroOffice now supports **AWS Bedrock** as a long-term AI provider alongside Anthropic Claude and Ollama self-hosted models.

## Supported LLM Providers

| Provider | Package | Model Examples | Status |
|----------|---------|-----------------|--------|
| **Anthropic Claude** | anthropic==0.30.1 | Claude 3 (Opus/Sonnet/Haiku) | ✅ Active |
| **Ollama** | ollama==0.4.3 (Win) / 0.6.1 (Linux) | Llama 2, Mistral, Neural Chat | ✅ Local/Self-hosted |
| **AWS Bedrock** | boto3==1.34.18 | Claude 3, Llama 2, Mistral | ✅ Enabled |

## AWS Bedrock Setup

### 1. Install Requirements

Bedrock support is included in `requirements-windows.txt` and `requirements-linux.txt`:

```bash
# Windows
pip install -r requirements-windows.txt

# Linux
pip install -r requirements-linux.txt
```

### 2. AWS Credentials Configuration

Bedrock requires AWS credentials. Configure one of the following:

#### Option A: AWS Credentials File (Recommended)

```bash
# Windows
mkdir %USERPROFILE%\.aws
# Create: %USERPROFILE%\.aws\credentials

# Linux/Mac
mkdir -p ~/.aws
# Create: ~/.aws/credentials
```

**File format:**
```ini
[default]
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_KEY
aws_region = us-east-1

[bedrock-profile]
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_KEY
aws_region = us-west-2
```

#### Option B: Environment Variables

```bash
# Windows (PowerShell)
$env:AWS_ACCESS_KEY_ID = "YOUR_ACCESS_KEY"
$env:AWS_SECRET_ACCESS_KEY = "YOUR_SECRET_KEY"
$env:AWS_REGION = "us-east-1"

# Linux/Mac (Bash)
export AWS_ACCESS_KEY_ID="YOUR_ACCESS_KEY"
export AWS_SECRET_ACCESS_KEY="YOUR_SECRET_KEY"
export AWS_REGION="us-east-1"
```

#### Option C: Django Settings

```python
# config/settings/production.py
import os

AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
AWS_BEDROCK_ENABLED = True
```

### 3. Available Models

Bedrock provides access to several providers' models:

#### Anthropic Claude
- **claude-3-opus-20240229** - Most capable, longest context
- **claude-3-sonnet-20240229** - Balanced performance/cost
- **claude-3-haiku-20240307** - Fast, cost-effective

#### Meta Llama
- **meta.llama2-13b-chat-v1** - Open-source alternative
- **meta.llama2-70b-chat-v1** - Large model

#### Mistral
- **mistral.mistral-7b-instruct-v0:2** - Fast instruction-following
- **mistral.mistral-large-2402-v1** - High-capacity model

### 4. Django Integration Example

```python
# apps/helpdesk/services/ai_service.py
import boto3
from django.conf import settings

class BedrockAIService:
    def __init__(self):
        self.client = boto3.client(
            'bedrock-runtime',
            region_name=settings.AWS_REGION
        )

    def invoke_claude(self, prompt: str, model: str = "claude-3-sonnet-20240229"):
        """Invoke Claude via AWS Bedrock"""
        response = self.client.invoke_model(
            modelId=model,
            body=json.dumps({
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1024
            })
        )
        return json.loads(response['body'].read())['content'][0]['text']

# Usage in views/tasks
service = BedrockAIService()
response = service.invoke_claude("Summarize this support ticket...")
```

### 5. Async Support (Celery Tasks)

```python
# apps/helpdesk/tasks.py
from celery import shared_task
import aioboto3

@shared_task
def generate_response_bedrock(ticket_id: int):
    """Async Bedrock invocation via Celery"""
    ticket = Ticket.objects.get(id=ticket_id)

    session = aioboto3.Session()
    async with session.client('bedrock-runtime', region_name='us-east-1') as client:
        response = await client.invoke_model(
            modelId='claude-3-sonnet-20240229',
            body=json.dumps({
                "messages": [{"role": "user", "content": ticket.description}],
                "max_tokens": 2048
            })
        )

    ticket.ai_response = json.loads(response['body'].read())['content'][0]['text']
    ticket.save()
```

### 6. Cost Management

**Bedrock Pricing (approximate):**

| Model | Input | Output |
|-------|-------|--------|
| Claude 3 Haiku | $0.25 / 1M tokens | $1.25 / 1M tokens |
| Claude 3 Sonnet | $3 / 1M tokens | $15 / 1M tokens |
| Claude 3 Opus | $15 / 1M tokens | $75 / 1M tokens |
| Llama 2 70B | $0.99 / 1M tokens | $1.32 / 1M tokens |

**Best Practices:**

1. Use Haiku/Sonnet for high-volume operations
2. Implement token counting before requests
3. Cache responses when possible
4. Monitor CloudWatch metrics
5. Set up budget alerts

### 7. Testing Bedrock Integration

```bash
# Test AWS credentials
aws sts get-caller-identity

# Test Bedrock access
aws bedrock list-foundation-models --region us-east-1

# Verify boto3 installation
python -c "import boto3; print(boto3.__version__)"
```

### 8. Troubleshooting

#### Error: "NoCredentialsError"
```
Solution: Ensure AWS credentials are configured in:
- ~/.aws/credentials (recommended)
- Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
- IAM role (if running on EC2)
```

#### Error: "User: ... is not authorized to perform bedrock:InvokeModel"
```
Solution: Ensure IAM user/role has policy:
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": ["bedrock:InvokeModel"],
    "Resource": "arn:aws:bedrock:*::foundation-model/*"
  }]
}
```

#### Error: "Model access not enabled for account"
```
Solution: Request model access in AWS Bedrock console:
1. Go to AWS Bedrock > Model access
2. Enable desired models
3. Wait for activation (usually instant)
```

### 9. Environment Variables Reference

```bash
# AWS Configuration
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1  # Default: us-east-1

# Optional: Bedrock-specific settings
BEDROCK_MODEL_ID=claude-3-sonnet-20240229
BEDROCK_MAX_TOKENS=2048
BEDROCK_TEMPERATURE=0.7
```

### 10. Security Best Practices

1. **Never commit credentials** to git
   - Use `.env` files (ignored by .gitignore)
   - Use AWS IAM roles on production servers

2. **Use least-privilege IAM policies**
   - Only bedrock:InvokeModel permission needed
   - Restrict to specific foundation models

3. **Enable AWS CloudTrail** for audit logging

4. **Encrypt data in transit** (HTTPS only)

5. **Monitor usage** via CloudWatch

### 11. Feature Toggle

Enable/disable Bedrock in settings:

```python
# config/settings/base.py
BEDROCK_ENABLED = os.environ.get('BEDROCK_ENABLED', 'true').lower() == 'true'
BEDROCK_PREFERRED_MODEL = os.environ.get('BEDROCK_PREFERRED_MODEL', 'claude-3-sonnet-20240229')

# Usage in code
if settings.BEDROCK_ENABLED:
    service = BedrockAIService()
    response = service.invoke_claude(prompt)
else:
    # Fallback to Anthropic or Ollama
    response = None
```

## Integration Roadmap

- ✅ **Phase 1**: Basic Bedrock support (boto3, credentials)
- 🔄 **Phase 2**: HelpDesk AI integration (ticket summaries, responses)
- 🔄 **Phase 3**: Classroom AI (deployment recommendations)
- 🔄 **Phase 4**: Approvals AI (decision support)
- 🔄 **Phase 5**: Cloude AI (file analysis, metadata generation)

## Related Documentation

- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [boto3 Bedrock Client](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-runtime.html)
- [Claude API Reference](https://docs.anthropic.com/claude/reference)

## Support

For issues with AWS Bedrock setup:
1. Check AWS Bedrock console for model access
2. Verify IAM permissions
3. Test with `aws bedrock list-foundation-models`
4. Check CloudWatch Logs for request errors

---

**Last Updated:** 2025-02-03
**Status:** Setup documentation complete, integration pending
