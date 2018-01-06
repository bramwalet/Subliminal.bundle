# coding=utf-8
from subliminal import ProviderError


class ServiceUnavailable(ProviderError):
    """Exception raised by providers when download limit is exceeded."""
    pass
