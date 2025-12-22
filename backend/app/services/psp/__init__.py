from __future__ import annotations

from config import settings

from .mock_psp import MockPSP


def get_psp() -> MockPSP:
    """Return the active PSP adapter instance.

    For now this is hard-wired to MockPSP, but the selection is routed through
    settings so that future providers (e.g. stripe, adyen) can be plugged in
    without changing call sites.
    """

    # In a future phase this might inspect settings.psp_provider.
    # For now we always use MockPSP.
    return MockPSP()
