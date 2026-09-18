"""Vendor-agnostic exceptions raised by every LLM provider.

Providers translate their SDK-specific errors into these so callers
(services, routers) never need to import a vendor SDK to handle errors.
"""


class LLMError(Exception):
    """Base class for all LLM provider errors."""


class LLMAuthenticationError(LLMError):
    """The configured API key/credentials were rejected."""


class LLMPermissionError(LLMError):
    """The account/key does not have access to the requested model."""


class LLMConnectionError(LLMError):
    """The provider's API endpoint could not be reached."""


class LLMResponseError(LLMError):
    """The provider returned an error status or an unusable response."""


class LLMConfigurationError(LLMError):
    """The provider is missing required configuration (e.g. API key)."""
