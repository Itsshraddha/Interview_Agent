"""
watsonx_client.py
=================
Central module for initialising IBM watsonx.ai clients.

All three credentials are read from environment variables (or a .env file
loaded by python-dotenv).  A clear, actionable error is raised if any are
missing so the user knows exactly what to set before running the app.

IBM watsonx.ai SDK concepts used here
--------------------------------------
- Credentials      : wraps the API key + regional URL into a typed object
                     consumed by every other SDK call.
- APIClient        : the base HTTP client; required when constructing
                     WatsonxEmbeddings through the LangChain-IBM integration.
- ModelInference   : the generation client.  Accepts a model_id, credentials,
                     and project_id.  Call .generate() or .generate_text() to
                     invoke the model.
- WatsonxEmbeddings: LangChain-compatible embeddings wrapper that uses the
                     IBM Slate retrieval model to convert text → dense vectors.
"""

import os
from dotenv import load_dotenv

# ibm-watsonx-ai — core SDK
from ibm_watsonx_ai import Credentials, APIClient
from ibm_watsonx_ai.foundation_models import ModelInference

# langchain-ibm — LangChain-compatible embeddings wrapper
from langchain_ibm import WatsonxEmbeddings

# Load variables from .env if present (no-op in production environments
# where variables are injected directly into the process environment).
load_dotenv()

# ── Default model IDs (can be overridden via .env) ────────────────────────────
DEFAULT_GRANITE_MODEL_ID = "meta-llama/llama-3-3-70b-instruct"
DEFAULT_EMBEDDING_MODEL_ID = "ibm/slate-125m-english-rtrvr-v2"


def _require_env(name: str) -> str:
    """Read an environment variable or raise a friendly error."""
    value = os.getenv(name, "").strip()
    if not value:
        raise EnvironmentError(
            f"Missing required environment variable: {name}\n"
            "Please copy .env.example to .env and fill in your IBM Cloud "
            "credentials.  See README.md → 'IBM Cloud Lite Setup' for details."
        )
    return value


def get_credentials() -> Credentials:
    """
    Build and return an IBM watsonx.ai Credentials object.

    Credentials bundles the API key and regional endpoint URL.  Every other
    SDK object (APIClient, ModelInference, WatsonxEmbeddings) requires it.
    """
    api_key = _require_env("IBM_API_Key")
    url = _require_env("Watsonx_URL")

    # Credentials automatically handles IAM token exchange under the hood —
    # no need to manually call the IAM token endpoint.
    return Credentials(api_key=api_key, url=url)


def get_project_id() -> str:
    """Return the watsonx.ai project ID from the environment."""
    return _require_env("IBM_Watsonx_Project_ID")


def get_api_client() -> APIClient:
    """
    Return an initialised APIClient.

    APIClient is the low-level HTTP client used by WatsonxEmbeddings (via
    the LangChain-IBM integration).  It is separate from ModelInference so
    that embedding and generation clients can be configured independently.
    """
    credentials = get_credentials()
    project_id = get_project_id()

    # APIClient accepts the Credentials object plus an optional project_id.
    # Passing project_id here scopes all API calls to the correct project.
    return APIClient(credentials=credentials, project_id=project_id)


def get_embedding_model() -> WatsonxEmbeddings:
    """
    Return a LangChain-compatible WatsonxEmbeddings instance.

    WatsonxEmbeddings wraps the IBM Slate model (ibm/slate-125m-english-rtrvr)
    and exposes the standard LangChain Embeddings interface (.embed_documents(),
    .embed_query()) so it can be used directly with ChromaDB's LangChain
    integration.

    model_id : the IBM Slate retrieval model — optimised for dense retrieval,
               not generation.  It produces 768-dimensional vectors.
    """
    model_id = os.getenv("EMBEDDING_MODEL_ID", DEFAULT_EMBEDDING_MODEL_ID)
    credentials = get_credentials()
    project_id = get_project_id()

    return WatsonxEmbeddings(
        model_id=model_id,
        # Pass the raw credentials dict that WatsonxEmbeddings expects:
        url=credentials.url,
        apikey=credentials.api_key,
        project_id=project_id,
    )


def get_generation_model(
    max_new_tokens: int = 4096,
    temperature: float = 0.3,
) -> ModelInference:
    """
    Return a configured ModelInference client for text generation.

    max_new_tokens raised to 4096 — the v2 schema (8 tech + 5 behavioral +
    roadmap + questions_to_ask) generates ~3000-3500 tokens of JSON.
    2048 caused truncation / malformed JSON errors.
    """
    model_id = os.getenv("GRANITE_MODEL_ID", DEFAULT_GRANITE_MODEL_ID)
    credentials = get_credentials()
    project_id = get_project_id()

    return ModelInference(
        model_id=model_id,
        credentials=credentials,
        project_id=project_id,
        params={
            "max_new_tokens": max_new_tokens,
            "temperature": temperature,
            "decoding_method": "sample",
            "repetition_penalty": 1.1,
        },
    )
