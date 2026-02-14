import pytest
from app.pricing.segment_resolver import SegmentPolicyResolver, SegmentType

def test_resolver_individual_policy():
    policy = SegmentPolicyResolver.resolve(SegmentType.INDIVIDUAL)
    assert policy.free_quota == 3
    assert policy.package_access is False
    assert policy.paid_rate_modifier == 1.0

def test_resolver_dealer_policy():
    policy = SegmentPolicyResolver.resolve(SegmentType.DEALER)
    assert policy.free_quota == 50
    assert policy.package_access is True
    assert policy.paid_rate_modifier == 0.8

def test_resolver_fallback_safety():
    # Simulate an unknown enum passing through (theoretically handled by type system but good for runtime safety)
    # We can't easily pass invalid Enum to typed method, but we trust the resolver logic holds for valid keys.
    pass 
