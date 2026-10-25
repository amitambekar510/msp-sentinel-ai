from typing import Annotated

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from msp_sentinel.collectors.wazuh import WazuhTenant


class Settings(BaseSettings):
    refresh_seconds: int = 60
    http_timeout: float = 12.0
    nvd_api_key: str | None = None
    ollama_url: str = "http://localhost:11434"
    ollama_model: str | None = None
    wazuh_tenants: dict[Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9_-]{0,63}$")], WazuhTenant] = Field(default_factory=dict, repr=False)

    @model_validator(mode="after")
    def validate_tenant_bindings(self):
        tokens = set()
        assignments = set()
        for tenant in self.wazuh_tenants.values():
            token = tenant.api_token.get_secret_value()
            if token in tokens:
                raise ValueError("each tenant must have a unique API token")
            tokens.add(token)
            for agent in tenant.agent_ids:
                binding = (tenant.indexer_url, agent)
                if binding in assignments:
                    raise ValueError("an indexer agent cannot belong to multiple tenants")
                assignments.add(binding)
        return self

    model_config = SettingsConfigDict(env_prefix="MSP_SENTINEL_", env_file=".env", extra="ignore", hide_input_in_errors=True)


settings = Settings()
