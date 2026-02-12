class ProviderAdapter:
    """Base class for Provider Adapters"""
    
    def validate_signature(self, request) -> bool:
        raise NotImplementedError

    def map_error(self, error) -> dict:
        raise NotImplementedError

class PragmaticAdapter(ProviderAdapter):
    """Stub for Pragmatic Play"""
    def validate_signature(self, request):
        # TODO: Implement HMAC check
        return True

class EvolutionAdapter(ProviderAdapter):
    """Stub for Evolution Gaming"""
    def validate_signature(self, request):
        # TODO: Implement OAuth check
        return True
