"""
Configuration management for the LangGraph Salesforce SAP Demo.
Uses pydantic-settings for type-safe environment variable handling.
"""

import os
from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SalesforceSettings(BaseSettings):
    """Salesforce API configuration."""
    
    model_config = SettingsConfigDict(env_prefix="SALESFORCE_")
    
    mode: Literal["mock", "real"] = Field(
        default="mock",
        description="Salesforce connection mode: 'mock' or 'real'"
    )
    client_id: str = Field(default="", description="Connected App Client ID")
    client_secret: str = Field(default="", description="Connected App Client Secret")
    username: str = Field(default="", description="Salesforce Username")
    password: str = Field(default="", description="Salesforce Password")
    security_token: str = Field(default="", description="Salesforce Security Token")
    instance_url: str = Field(
        default="https://login.salesforce.com",
        description="Salesforce Instance URL"
    )
    api_version: str = Field(default="v59.0", description="Salesforce API Version")
    
    @property
    def is_mock(self) -> bool:
        """Check if running in mock mode."""
        return self.mode == "mock"
    
    @property
    def login_url(self) -> str:
        """OAuth token endpoint."""
        return f"{self.instance_url}/services/oauth2/token"
    
    def get_api_url(self, instance_url: str) -> str:
        """Get the API URL for a given instance."""
        return f"{instance_url}/services/data/{self.api_version}"


class SAPSettings(BaseSettings):
    """SAP OData configuration."""
    
    model_config = SettingsConfigDict(env_prefix="SAP_")
    
    mode: Literal["mock", "real"] = Field(
        default="mock",
        description="SAP connection mode: 'mock' or 'real'"
    )
    base_url: str = Field(
        default="https://your-sap-instance.com/sap/opu/odata/sap",
        description="SAP OData Base URL"
    )
    username: str = Field(default="", description="SAP Username")
    password: str = Field(default="", description="SAP Password")
    client: str = Field(default="100", description="SAP Client (Mandant)")
    
    @property
    def is_mock(self) -> bool:
        """Check if running in mock mode."""
        return self.mode == "mock"


class LangSmithSettings(BaseSettings):
    """LangSmith tracing configuration."""
    
    api_key: str = Field(
        default="",
        alias="LANGSMITH_API_KEY",
        description="LangSmith API Key"
    )
    tracing_v2: bool = Field(
        default=True,
        alias="LANGCHAIN_TRACING_V2",
        description="Enable LangChain tracing"
    )
    project: str = Field(
        default="langgraph-salesforce-sap-demo",
        alias="LANGCHAIN_PROJECT",
        description="LangSmith Project Name"
    )
    endpoint: str = Field(
        default="https://api.smith.langchain.com",
        alias="LANGCHAIN_ENDPOINT",
        description="LangSmith API Endpoint"
    )


class RoutingSettings(BaseSettings):
    """Default routing configuration for lead/ticket assignment."""
    
    model_config = SettingsConfigDict(env_prefix="DEFAULT_")
    
    ae_owner_id: str = Field(
        default="005XXXXXXXXXXXXXXX",
        description="Default Account Executive Owner ID"
    )
    sdr_owner_id: str = Field(
        default="005XXXXXXXXXXXXXXX",
        description="Default Sales Dev Rep Owner ID"
    )
    nurture_owner_id: str = Field(
        default="005XXXXXXXXXXXXXXX",
        description="Default Nurture Campaign Owner ID"
    )
    escalation_owner_id: str = Field(
        default="005XXXXXXXXXXXXXXX",
        description="Default Escalation Owner ID"
    )


class AppSettings(BaseSettings):
    """Application-wide settings."""
    
    model_config = SettingsConfigDict(env_prefix="APP_")
    
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    debug: bool = Field(default=True, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    
    # Sub-configurations
    salesforce: SalesforceSettings = Field(default_factory=SalesforceSettings)
    sap: SAPSettings = Field(default_factory=SAPSettings)
    langsmith: LangSmithSettings = Field(default_factory=LangSmithSettings)
    routing: RoutingSettings = Field(default_factory=RoutingSettings)
    
    def configure_langsmith(self) -> None:
        """Set LangSmith environment variables for tracing."""
        os.environ["LANGCHAIN_TRACING_V2"] = str(self.langsmith.tracing_v2).lower()
        os.environ["LANGCHAIN_PROJECT"] = self.langsmith.project
        if self.langsmith.api_key:
            os.environ["LANGSMITH_API_KEY"] = self.langsmith.api_key
        if self.langsmith.endpoint:
            os.environ["LANGCHAIN_ENDPOINT"] = self.langsmith.endpoint


@lru_cache()
def get_settings() -> AppSettings:
    """
    Get cached application settings.
    Uses lru_cache to ensure settings are only loaded once.
    """
    return AppSettings()


# Convenience accessors
def get_salesforce_config() -> SalesforceSettings:
    """Get Salesforce configuration."""
    return get_settings().salesforce


def get_sap_config() -> SAPSettings:
    """Get SAP configuration."""
    return get_settings().sap


def get_routing_config() -> RoutingSettings:
    """Get routing configuration."""
    return get_settings().routing
