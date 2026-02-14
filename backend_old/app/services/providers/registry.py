from typing import Dict, Type
from app.services.providers.base import ProviderAdapter
from app.services.providers.adapters import PragmaticAdapter, EvolutionAdapter

class ProviderRegistry:
    _adapters: Dict[str, Type[ProviderAdapter]] = {
        "pragmatic": PragmaticAdapter,
        "evolution": EvolutionAdapter,
        # "simulator" handled natively in callback logic or can be added here
    }

    @classmethod
    def get_adapter(cls, provider_name: str) -> ProviderAdapter:
        adapter_cls = cls._adapters.get(provider_name)
        if not adapter_cls:
            raise ValueError(f"Provider '{provider_name}' not supported")
        return adapter_cls()

    @classmethod
    def register(cls, name: str, adapter: Type[ProviderAdapter]):
        cls._adapters[name] = adapter
