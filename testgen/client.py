"""Builds an OpenAI client pointed at an Azure AI Foundry deployment.

Auth order:
1. Keyless (default): DefaultAzureCredential -> uses your `az login` session locally,
   or a managed identity / federated credential in CI. Requires the
   "Azure AI User" (or "Cognitive Services OpenAI User") role on the resource.
2. API key fallback: only if AZURE_OPENAI_API_KEY is set.
"""

from __future__ import annotations

import os

from openai import OpenAI

SCOPE = "https://cognitiveservices.azure.com/.default"


class ConfigError(RuntimeError):
    pass


def _base_url() -> str:
    endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT", "").strip().rstrip("/")
    if not endpoint:
        raise ConfigError(
            "AZURE_OPENAI_ENDPOINT is not set, e.g. "
            "https://<your-resource>.openai.azure.com"
        )
    if not endpoint.endswith("/openai/v1"):
        endpoint += "/openai/v1"
    return endpoint + "/"


def deployment_name() -> str:
    return os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-5-mini")


def build_client() -> OpenAI:
    base_url = _base_url()

    api_key = os.environ.get("AZURE_OPENAI_API_KEY")
    if api_key:
        return OpenAI(base_url=base_url, api_key=api_key)

    from azure.identity import DefaultAzureCredential, get_bearer_token_provider

    token_provider = get_bearer_token_provider(DefaultAzureCredential(), SCOPE)
    # The OpenAI SDK accepts a callable for api_key and calls it on each request,
    # so tokens are refreshed automatically.
    return OpenAI(base_url=base_url, api_key=token_provider)
