# Ollama Setup Guide for ABoroOffice

## Overview

**Ollama** provides local, open-source LLM models (Llama 2, Mistral, Neural Chat, etc.) that run on your machine. Due to pydantic dependency conflicts on Windows, ollama is **not included in Python requirements** but can be used as a **standalone HTTP service**.

## Architecture

```
┌─────────────────────────────────────────┐
│   ABoroOffice Django Application        │
│   (Windows/Linux)                       │
└─────────────────────────────────────────┘
              ↓ HTTP API calls
         http://localhost:11434
              ↓
┌─────────────────────────────────────────┐
│   Ollama Service                        │
│   (Standalone executable/Docker)        │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│   Local LLM Models                      │
│   (Llama 2, Mistral, etc.)              │
└─────────────────────────────────────────┘
```

## Installation

### Windows 11

1. **Download Ollama**
   - Visit: https://ollama.ai/download
   - Download Windows installer
   - Run `OllamaSetup.exe`
   - Follow installation wizard

2. **Verify Installation**
   ```powershell
   ollama --version
   # Output: ollama version 0.x.x
   ```

3. **Run Ollama Service**
   ```powershell
   ollama serve
   # Output:
   # Listening on 127.0.0.1:11434
   # Listening on [::1]:11434
   ```

### Linux (Ubuntu/Debian)

1. **Install via Package Manager**
   ```bash
   curl https://ollama.ai/install.sh | sh
   ```

2. **Or Build from Source**
   ```bash
   git clone https://github.com/jmorganca/ollama.git
   cd ollama
   go run . serve
   ```

3. **Verify Installation**
   ```bash
   ollama --version
   ```

4. **Run Service**
   ```bash
   ollama serve
   # Or as systemd service:
   sudo systemctl start ollama
   ```

### Docker

1. **Pull Official Image**
   ```bash
   docker pull ollama/ollama
   ```

2. **Run Container**
   ```bash
   docker run -it --rm \
     -p 11434:11434 \
     -v ollama:/root/.ollama \
     ollama/ollama
   ```

3. **Pull Models (in another terminal)**
   ```bash
   docker exec <container-id> ollama pull llama2
   ```

## Supported Models

| Model | Size | Speed | Quality | Use Case |
|-------|------|-------|---------|----------|
| **Mistral** | 7B | ⚡⚡⚡ Fast | ⭐⭐⭐ Good | General purpose |
| **Llama 2** | 7B/13B/70B | ⚡⚡ Medium | ⭐⭐⭐⭐ Excellent | Chat/coding |
| **Neural Chat** | 7B | ⚡⚡⚡ Fast | ⭐⭐⭐ Good | Conversational |
| **Orca Mini** | 3B | ⚡⚡⚡ Very Fast | ⭐⭐ Basic | Quick responses |
| **Zephyr** | 7B | ⚡⚡⚡ Fast | ⭐⭐⭐⭐ Great | Instruction-following |

## Pulling Models

```bash
# Pull latest version
ollama pull llama2

# Pull specific version
ollama pull llama2:13b
ollama pull mistral:latest

# List installed models
ollama list

# Remove model
ollama rm llama2
```

## Django Integration

### 1. HTTP Client Service

Create a service to call Ollama via HTTP:

```python
# apps/helpdesk/services/ollama_service.py
import requests
import json
from django.conf import settings
from typing import Optional

class OllamaService:
    """
    Service for calling Ollama local models via HTTP API.
    Ollama must be running: ollama serve
    """

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.endpoint = f"{base_url}/api/generate"

    def is_available(self) -> bool:
        """Check if Ollama service is running"""
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=2
            )
            return response.status_code == 200
        except:
            return False

    def list_models(self) -> list:
        """Get list of available models"""
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            data = response.json()
            return [model['name'] for model in data.get('models', [])]
        except:
            return []

    def generate(
        self,
        prompt: str,
        model: str = "mistral",
        temperature: float = 0.7,
        top_p: float = 0.9,
        max_tokens: int = 512
    ) -> Optional[str]:
        """
        Generate text using Ollama

        Args:
            prompt: Input text
            model: Model name (llama2, mistral, neural-chat, etc.)
            temperature: Creativity (0.0-1.0)
            top_p: Diversity (0.0-1.0)
            max_tokens: Max response length

        Returns:
            Generated text or None if error
        """
        try:
            response = requests.post(
                self.endpoint,
                json={
                    "model": model,
                    "prompt": prompt,
                    "temperature": temperature,
                    "top_p": top_p,
                    "num_predict": max_tokens,
                    "stream": False
                },
                timeout=300  # 5 minute timeout for long generations
            )

            if response.status_code == 200:
                data = response.json()
                return data.get('response', '').strip()
            else:
                return None

        except requests.exceptions.ConnectionError:
            print("ERROR: Ollama service not running. Run: ollama serve")
            return None
        except Exception as e:
            print(f"ERROR: {e}")
            return None

    def stream_generate(self, prompt: str, model: str = "mistral"):
        """
        Stream generation (for real-time responses)
        Yields text chunks as they're generated
        """
        try:
            response = requests.post(
                self.endpoint,
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": True
                },
                stream=True,
                timeout=300
            )

            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        chunk = json.loads(line)
                        yield chunk.get('response', '')

                        if chunk.get('done'):
                            break
        except:
            yield "ERROR: Could not connect to Ollama service"
```

### 2. Usage in Views

```python
# apps/helpdesk/views.py
from django.shortcuts import render
from django.views import View
from .services.ollama_service import OllamaService

class GenerateResponseView(View):
    def post(self, request):
        ticket_id = request.POST.get('ticket_id')

        # Check if Ollama is available
        ollama = OllamaService()
        if not ollama.is_available():
            return render(request, 'error.html', {
                'error': 'Ollama service not running. Run: ollama serve'
            })

        # Get ticket content
        ticket = Ticket.objects.get(id=ticket_id)

        # Generate response
        prompt = f"""Based on this support ticket, provide a helpful response:

Title: {ticket.title}
Description: {ticket.description}

Response:"""

        response = ollama.generate(
            prompt=prompt,
            model="mistral",  # or "llama2", "neural-chat", etc.
            max_tokens=1024
        )

        if response:
            ticket.ai_response = response
            ticket.save()

        return redirect('ticket_detail', pk=ticket_id)
```

### 3. Usage in Celery Tasks

```python
# apps/helpdesk/tasks.py
from celery import shared_task
from .services.ollama_service import OllamaService

@shared_task
def analyze_ticket_with_ollama(ticket_id: int):
    """Async analysis using Ollama"""
    ticket = Ticket.objects.get(id=ticket_id)
    ollama = OllamaService()

    if not ollama.is_available():
        ticket.ai_error = "Ollama service unavailable"
        ticket.save()
        return

    # Categorize ticket
    categorize_prompt = f"""Categorize this ticket (bug, feature, question, other):
{ticket.description}
Category:"""

    category = ollama.generate(
        prompt=categorize_prompt,
        model="neural-chat",
        max_tokens=50
    )

    # Generate response
    response_prompt = f"""Provide a helpful response to this {category} ticket:
{ticket.description}
Response:"""

    response = ollama.generate(
        prompt=response_prompt,
        model="llama2",
        max_tokens=1024
    )

    ticket.category = category.strip()
    ticket.ai_response = response
    ticket.save()
```

## Health Check & Monitoring

### Django Management Command

```python
# apps/helpdesk/management/commands/check_ollama.py
from django.core.management.base import BaseCommand
from apps.helpdesk.services.ollama_service import OllamaService

class Command(BaseCommand):
    help = 'Check Ollama service status'

    def handle(self, *args, **options):
        ollama = OllamaService()

        if ollama.is_available():
            self.stdout.write(
                self.style.SUCCESS('✓ Ollama service is running')
            )
            models = ollama.list_models()
            self.stdout.write(f'  Available models: {", ".join(models)}')
        else:
            self.stdout.write(
                self.style.ERROR('✗ Ollama service is NOT running')
            )
            self.stdout.write('  Start with: ollama serve')
```

Usage:
```bash
python manage.py check_ollama
```

## Performance Tuning

### Model Selection by Task

```python
# Smart model selection based on task complexity
def select_model(task_type: str) -> str:
    """Select best model for task"""
    model_map = {
        'simple_response': 'orca-mini',      # Fast, 3B
        'general_chat': 'mistral',            # Balanced, 7B
        'code_analysis': 'llama2:13b',       # Capable, 13B
        'reasoning': 'llama2:70b',           # Powerful, 70B
    }
    return model_map.get(task_type, 'mistral')
```

### Response Caching

```python
from django.views.decorators.cache import cache_page

@cache_page(60 * 60)  # Cache 1 hour
def ticket_response(request, ticket_id):
    ollama = OllamaService()
    # ... generate response ...
```

## Troubleshooting

### Error: Connection refused
```
Problem: "ERROR: Ollama service not running"
Solution: Start ollama: ollama serve
```

### Error: Model not found
```
Problem: "Model 'mistral' not found"
Solution: Pull model: ollama pull mistral
```

### Slow response time
```
Problem: Responses taking >30 seconds
Solution:
1. Use smaller model: mistral or orca-mini
2. Reduce max_tokens
3. Check system RAM (7B models need ~4GB)
```

### Out of memory
```
Problem: "Out of memory" error
Solution:
1. Use smaller model (orca-mini: 3B)
2. Increase system swap
3. Run on machine with more RAM
```

## Environment Configuration

```bash
# .env or docker environment
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=mistral
OLLAMA_ENABLED=true
```

Usage in Django:
```python
# config/settings/base.py
OLLAMA_ENABLED = os.environ.get('OLLAMA_ENABLED', 'true').lower() == 'true'
OLLAMA_HOST = os.environ.get('OLLAMA_HOST', 'http://localhost:11434')
OLLAMA_DEFAULT_MODEL = os.environ.get('OLLAMA_MODEL', 'mistral')
```

## Production Considerations

1. **Run as systemd service** (Linux)
   ```bash
   sudo systemctl enable ollama
   sudo systemctl start ollama
   ```

2. **Use Docker** for containerization
   ```yaml
   # docker-compose.yml
   services:
     ollama:
       image: ollama/ollama
       ports:
         - "11434:11434"
       volumes:
         - ollama_data:/root/.ollama
   ```

3. **Load Balancing** for high traffic
   - Run multiple ollama instances on different GPUs
   - Use nginx to distribute requests

4. **Monitor Resource Usage**
   ```bash
   # Watch GPU usage
   nvidia-smi
   ```

## Integration Roadmap

- ✅ Basic HTTP client
- 🔄 HelpDesk ticket response generation
- 🔄 Async Celery task support
- 🔄 Model auto-selection by task
- 🔄 Response caching
- 🔄 Admin UI for model management

## Comparison: Ollama vs Anthropic vs AWS Bedrock

| Feature | Ollama | Anthropic | Bedrock |
|---------|--------|-----------|---------|
| **Cost** | Free (self-hosted) | $0.003-$0.024/1K tokens | $0.003-$0.024/1K tokens |
| **Setup** | Local/Docker | API key | AWS credentials |
| **Speed** | Depends on hardware | Fast API | Fast API |
| **Models** | OSS (Llama, Mistral) | Claude 3 only | Multiple (Claude, Llama, Mistral) |
| **Privacy** | 100% local | Cloud-based | Cloud-based |
| **Reliability** | Depends on you | AWS managed | AWS managed |

## References

- [Ollama Official](https://ollama.ai)
- [Ollama GitHub](https://github.com/jmorganca/ollama)
- [Available Models](https://ollama.ai/library)
- [API Documentation](https://github.com/jmorganca/ollama/blob/main/docs/api.md)

---

**Last Updated:** 2025-02-03
**Status:** Setup and integration examples complete
