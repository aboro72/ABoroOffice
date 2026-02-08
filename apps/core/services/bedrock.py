import os
import json
import requests
import boto3
from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError
from django.conf import settings


class BedrockService:
    """Thin wrapper for Amazon Bedrock runtime."""

    def __init__(self):
        api_key = settings.BEDROCK_API_KEY
        region = settings.BEDROCK_REGION
        model_id = settings.BEDROCK_MODEL_ID
        max_tokens = settings.BEDROCK_MAX_TOKENS
        temperature = settings.BEDROCK_TEMPERATURE
        try:
            from apps.helpdesk.helpdesk_apps.admin_panel.models import SystemSettings
            s = SystemSettings.get_settings()
            if s.bedrock_api_key:
                api_key = s.bedrock_api_key
            if s.bedrock_region:
                region = s.bedrock_region
            if s.bedrock_model_id:
                model_id = s.bedrock_model_id
            if s.bedrock_max_tokens:
                max_tokens = s.bedrock_max_tokens
            temperature = s.bedrock_temperature if s.bedrock_temperature is not None else temperature
        except Exception:
            pass

        self.api_key = api_key
        if api_key:
            os.environ['AWS_BEARER_TOKEN_BEDROCK'] = api_key

        self.model_id = model_id
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.region = region
        self.client = boto3.client(
            service_name='bedrock-runtime',
            region_name=region,
        )

    def _converse_http(self, prompt: str, system: str | None = None) -> str:
        if not self.api_key:
            raise RuntimeError("Bedrock API key is missing.")
        url = f"https://bedrock-runtime.{self.region}.amazonaws.com/model/{self.model_id}/converse"
        payload = {
            "messages": [{"role": "user", "content": [{"text": prompt}]}],
            "inferenceConfig": {
                "maxTokens": self.max_tokens,
                "temperature": self.temperature,
            },
        }
        if system:
            payload["system"] = [{"text": system}]
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        try:
            return data["output"]["message"]["content"][0]["text"]
        except (KeyError, TypeError) as exc:
            raise RuntimeError(f"Unexpected Bedrock response: {data}") from exc

    def converse(self, prompt: str, system: str | None = None) -> str:
        messages = [{"role": "user", "content": [{"text": prompt}]}]
        request = {
            "modelId": self.model_id,
            "messages": messages,
            "inferenceConfig": {
                "maxTokens": self.max_tokens,
                "temperature": self.temperature,
            },
        }
        if system:
            request["system"] = [{"text": system}]

        try:
            response = self.client.converse(**request)
            return response["output"]["message"]["content"][0]["text"]
        except NoCredentialsError:
            if self.api_key:
                return self._converse_http(prompt, system=system)
            raise RuntimeError("Bedrock request failed: Unable to locate credentials")
        except (BotoCoreError, ClientError, KeyError) as exc:
            if self.api_key:
                return self._converse_http(prompt, system=system)
            raise RuntimeError(f"Bedrock request failed: {exc}") from exc
