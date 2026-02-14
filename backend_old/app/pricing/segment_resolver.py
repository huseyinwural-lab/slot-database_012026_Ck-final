from enum import Enum
from pydantic import BaseModel

class SegmentType(str, Enum):
    INDIVIDUAL = "INDIVIDUAL"
    DEALER = "DEALER"

class SegmentPolicy(BaseModel):
    free_quota: int
    package_access: bool
    paid_rate_modifier: float # 1.0 = standard, 0.8 = 20% off
    listing_duration_days: int

class SegmentPolicyResolver:
    """Isolates policy logic from pricing service."""
    
    _POLICIES = {
        SegmentType.INDIVIDUAL: SegmentPolicy(
            free_quota=3,
            package_access=False,
            paid_rate_modifier=1.0,
            listing_duration_days=30
        ),
        SegmentType.DEALER: SegmentPolicy(
            free_quota=50,
            package_access=True,
            paid_rate_modifier=0.8, # Dealer gets standard discount
            listing_duration_days=60
        )
    }

    @classmethod
    def resolve(cls, segment: SegmentType) -> SegmentPolicy:
        policy = cls._POLICIES.get(segment)
        if not policy:
            # Fallback to safe default (Individual) if enum drifts
            return cls._POLICIES[SegmentType.INDIVIDUAL]
        return policy
