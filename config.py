import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ENV_FILE = Path(__file__).with_name(".env")


@dataclass(frozen=True)
class Settings:
    morningstar_url: str
    morningstar_token: str
    azure_key: str
    azure_endpoint: str
    azure_deployment: str
    azure_api_version: str


def required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Missing {name} in .env")
    return value


def get_settings() -> Settings:
    # Streamlit is long-running, so reload the project file instead of
    # keeping credentials that were present when the process first started.
    load_dotenv(ENV_FILE, override=True)

    return Settings(
        morningstar_url=required("MORNINGSTAR_MCP_URL"),
        morningstar_token=required("MORNINGSTAR_ACCESS_TOKEN"),
        azure_key=required("AZURE_OPENAI_API_KEY"),
        azure_endpoint=required("AZURE_OPENAI_ENDPOINT"),
        azure_deployment=required("AZURE_OPENAI_DEPLOYMENT"),
        azure_api_version=required("AZURE_OPENAI_API_VERSION"),
    )