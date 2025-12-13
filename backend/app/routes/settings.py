from fastapi import APIRouter, HTTPException, Body
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
import uuid
from app.models.modules import (
    Brand, DomainMarket, Currency, PaymentProvider, CountryRule,
    GameAvailabilityRule, CommunicationProvider, RegulatorySettings,
    PlatformDefaults, APIKey, Webhook, ThemeBranding, MaintenanceSchedule,
    ConfigVersion, ConfigAuditLog, BrandStatus, MaintenanceType,
    ConfigEnvironment, ConfigStatus
)
from config import settings as app_settings
from motor.motor_asyncio import AsyncIOMotorClient

from app.services.audit import audit
from app.utils.auth import get_current_admin
from app.models.domain.admin import AdminUser
from fastapi import Depends
router = APIRouter(prefix="/api/v1/settings", tags=["settings"])

from app.core.database import db_wrapper

def get_db():
    return db_wrapper.db

# --- BRANDS ---
@router.get("/brands", response_model=List[Brand])
async def get_brands():
    db = get_db()
    brands = await db.brands.find().to_list(1000)
    return [Brand(**b) for b in brands]

@router.post("/brands", response_model=Brand)
async def create_brand(brand: Brand):
    db = get_db()
    await db.brands.insert_one(brand.model_dump())
    return brand

@router.put("/brands/{brand_id}", response_model=Brand)
async def update_brand(brand_id: str, updates: Dict[str, Any] = Body(...), current_admin: AdminUser = Depends(get_current_admin)):
    db = get_db()
    await db.brands.update_one({"id": brand_id}, {"$set": updates})
    brand = await db.brands.find_one({"id": brand_id})
    
    await audit.log(
        admin=current_admin,
        action="update_brand",
        module="settings",
        target_id=brand_id,
        details=updates
    )
    
    return Brand(**brand)

@router.delete("/brands/{brand_id}")
async def delete_brand(brand_id: str):
    db = get_db()
    await db.brands.delete_one({"id": brand_id})
    return {"message": "Brand deleted"}

# --- DOMAINS & MARKETS ---
@router.get("/domains", response_model=List[DomainMarket])
async def get_domains():
    db = get_db()
    domains = await db.domain_markets.find().to_list(1000)
    return [DomainMarket(**d) for d in domains]

@router.post("/domains", response_model=DomainMarket)
async def create_domain(domain: DomainMarket):
    db = get_db()
    await db.domain_markets.insert_one(domain.model_dump())
    return domain

# --- CURRENCIES ---
@router.get("/currencies", response_model=List[Currency])
async def get_currencies():
    db = get_db()
    currencies = await db.currencies.find().to_list(100)
    return [Currency(**c) for c in currencies]

@router.post("/currencies", response_model=Currency)
async def create_currency(currency: Currency):
    db = get_db()
    await db.currencies.insert_one(currency.model_dump())
    return currency

@router.put("/currencies/{currency_id}", response_model=Currency)
async def update_currency(currency_id: str, updates: Dict[str, Any] = Body(...)):
    db = get_db()
    updates["updated_at"] = datetime.now(timezone.utc)
    await db.currencies.update_one({"id": currency_id}, {"$set": updates})
    currency = await db.currencies.find_one({"id": currency_id})
    return Currency(**currency)

@router.delete("/currencies/{currency_id}")
async def delete_currency(currency_id: str):
    db = get_db()
    await db.currencies.delete_one({"id": currency_id})
    return {"message": "Currency deleted"}

@router.post("/currencies/sync-rates")
async def sync_exchange_rates():
    """Mock: Sync from external API"""
    return {"message": "Exchange rates synced successfully"}

# --- PAYMENT PROVIDERS ---
@router.get("/payment-providers", response_model=List[PaymentProvider])
async def get_payment_providers():
    db = get_db()
    providers = await db.payment_providers.find().to_list(1000)
    return [PaymentProvider(**p) for p in providers]

@router.post("/payment-providers", response_model=PaymentProvider)
async def create_payment_provider(provider: PaymentProvider):
    db = get_db()
    await db.payment_providers.insert_one(provider.model_dump())
    return provider

@router.post("/payment-providers/{provider_id}/health-check")
async def run_health_check(provider_id: str):
    db = get_db()
    # Mock health check
    await db.payment_providers.update_one(
        {"id": provider_id},
        {"$set": {"health_status": "healthy", "last_health_check": datetime.now(timezone.utc)}}
    )
    return {"status": "healthy"}

# --- COUNTRY RULES ---
@router.get("/country-rules", response_model=List[CountryRule])
async def get_country_rules():
    db = get_db()
    rules = await db.country_rules.find().to_list(1000)
    return [CountryRule(**r) for r in rules]

@router.post("/country-rules", response_model=CountryRule)
async def create_country_rule(rule: CountryRule):
    db = get_db()
    await db.country_rules.insert_one(rule.model_dump())
    return rule

# --- GAME AVAILABILITY ---
@router.get("/game-availability", response_model=List[GameAvailabilityRule])
async def get_game_availability_rules():
    db = get_db()
    rules = await db.game_availability_rules.find().to_list(1000)
    return [GameAvailabilityRule(**r) for r in rules]

@router.post("/game-availability", response_model=GameAvailabilityRule)
async def create_game_availability_rule(rule: GameAvailabilityRule):
    db = get_db()
    await db.game_availability_rules.insert_one(rule.model_dump())
    return rule

# --- COMMUNICATION PROVIDERS ---
@router.get("/communication-providers", response_model=List[CommunicationProvider])
async def get_communication_providers():
    db = get_db()
    providers = await db.communication_providers.find().to_list(1000)
    return [CommunicationProvider(**p) for p in providers]

@router.post("/communication-providers", response_model=CommunicationProvider)
async def create_communication_provider(provider: CommunicationProvider):
    db = get_db()
    await db.communication_providers.insert_one(provider.model_dump())
    return provider

@router.post("/communication-providers/{provider_id}/test")
async def send_test_message(provider_id: str):
    return {"message": "Test message sent successfully"}

# --- REGULATORY SETTINGS ---
@router.get("/regulatory", response_model=List[RegulatorySettings])
async def get_regulatory_settings():
    db = get_db()
    settings = await db.regulatory_settings.find().to_list(100)
    return [RegulatorySettings(**s) for s in settings]

@router.post("/regulatory", response_model=RegulatorySettings)
async def create_regulatory_settings(settings: RegulatorySettings):
    db = get_db()
    await db.regulatory_settings.insert_one(settings.model_dump())
    return settings

# --- PLATFORM DEFAULTS ---
@router.get("/platform-defaults", response_model=PlatformDefaults)
async def get_platform_defaults():
    db = get_db()
    defaults = await db.platform_defaults.find_one()
    if not defaults:
        defaults = PlatformDefaults().model_dump()
        await db.platform_defaults.insert_one(defaults)
    return PlatformDefaults(**defaults)

@router.put("/platform-defaults", response_model=PlatformDefaults)
async def update_platform_defaults(updates: Dict[str, Any] = Body(...)):
    db = get_db()
    defaults = await db.platform_defaults.find_one()
    if defaults:
        await db.platform_defaults.update_one({"id": defaults["id"]}, {"$set": updates})
    else:
        new_defaults = PlatformDefaults(**updates)
        await db.platform_defaults.insert_one(new_defaults.model_dump())
    updated = await db.platform_defaults.find_one()
    return PlatformDefaults(**updated)

# --- API KEYS ---
@router.get("/api-keys", response_model=List[APIKey])
async def get_api_keys():
    db = get_db()
    keys = await db.api_keys.find().to_list(1000)
    return [APIKey(**k) for k in keys]

@router.post("/api-keys/generate")
async def generate_api_key(key_name: str = Body(..., embed=True), owner: str = Body(..., embed=True)):
    db = get_db()
    import secrets
    key = secrets.token_urlsafe(32)
    api_key = APIKey(
        key_name=key_name,
        key_hash=f"sk_{key[:8]}...{key[-8:]}",
        owner=owner,
        permissions=["read", "write"]
    )
    await db.api_keys.insert_one(api_key.model_dump())
    return {"api_key": f"sk_{key}", "key_id": api_key.id}

@router.delete("/api-keys/{key_id}")
async def revoke_api_key(key_id: str):
    db = get_db()
    await db.api_keys.update_one({"id": key_id}, {"$set": {"status": "revoked"}})
    return {"message": "API key revoked"}

# --- WEBHOOKS ---
@router.get("/webhooks", response_model=List[Webhook])
async def get_webhooks():
    db = get_db()
    webhooks = await db.webhooks.find().to_list(1000)
    return [Webhook(**w) for w in webhooks]

@router.post("/webhooks", response_model=Webhook)
async def create_webhook(webhook: Webhook):
    db = get_db()
    await db.webhooks.insert_one(webhook.model_dump())
    return webhook

# --- THEME & BRANDING ---
@router.get("/theme/{brand_id}", response_model=ThemeBranding)
async def get_theme(brand_id: str):
    db = get_db()
    theme = await db.theme_branding.find_one({"brand_id": brand_id})
    if not theme:
        raise HTTPException(404, "Theme not found")
    return ThemeBranding(**theme)

@router.post("/theme", response_model=ThemeBranding)
async def create_or_update_theme(theme: ThemeBranding):
    db = get_db()
    existing = await db.theme_branding.find_one({"brand_id": theme.brand_id})
    if existing:
        await db.theme_branding.update_one({"brand_id": theme.brand_id}, {"$set": theme.model_dump()})
    else:
        await db.theme_branding.insert_one(theme.model_dump())
    return theme

# --- MAINTENANCE ---
@router.get("/maintenance", response_model=List[MaintenanceSchedule])
async def get_maintenance_schedules():
    db = get_db()
    schedules = await db.maintenance_schedules.find().to_list(1000)
    return [MaintenanceSchedule(**s) for s in schedules]

@router.post("/maintenance", response_model=MaintenanceSchedule)
async def create_maintenance_schedule(schedule: MaintenanceSchedule):
    db = get_db()
    await db.maintenance_schedules.insert_one(schedule.model_dump())
    return schedule

@router.post("/maintenance/{schedule_id}/end")
async def end_maintenance_early(schedule_id: str):
    db = get_db()
    await db.maintenance_schedules.update_one(
        {"id": schedule_id},
        {"$set": {"status": "completed", "end_time": datetime.now(timezone.utc)}}
    )
    return {"message": "Maintenance ended"}

# --- CONFIG VERSIONS ---
@router.get("/config-versions", response_model=List[ConfigVersion])
async def get_config_versions():
    db = get_db()
    versions = await db.config_versions.find().sort("created_at", -1).to_list(100)
    return [ConfigVersion(**v) for v in versions]

@router.post("/config-versions", response_model=ConfigVersion)
async def create_config_version(version: ConfigVersion):
    db = get_db()
    await db.config_versions.insert_one(version.model_dump())
    return version

@router.post("/config-versions/{version_id}/deploy")
async def deploy_config_version(version_id: str, environment: str = Body(..., embed=True)):
    db = get_db()
    await db.config_versions.update_one(
        {"id": version_id},
        {"$set": {"status": ConfigStatus.LIVE, "environment": environment, "deployed_at": datetime.now(timezone.utc)}}
    )
    return {"message": f"Config deployed to {environment}"}

@router.post("/config-versions/{version_id}/rollback")
async def rollback_config_version(version_id: str):
    db = get_db()
    await db.config_versions.update_one(
        {"id": version_id},
        {"$set": {"status": ConfigStatus.ROLLED_BACK}}
    )
    return {"message": "Config rolled back"}

# --- CONFIG AUDIT LOG ---
@router.get("/config-audit", response_model=List[ConfigAuditLog])
async def get_config_audit_log():
    db = get_db()
    logs = await db.config_audit_logs.find().sort("timestamp", -1).limit(100).to_list(100)
    return [ConfigAuditLog(**log) for log in logs]

# --- SEED ---
@router.post("/seed")
async def seed_settings():
    db = get_db()
    
    if await db.brands.count_documents({}) == 0:
        brands = [
            Brand(
                brand_name="CasinoX",
                status=BrandStatus.ACTIVE,
                default_currency="USD",
                default_language="en",
                domains=["casinox.com", "www.casinox.com"],
                languages_supported=["en", "tr", "de"],
                country_availability=["US", "TR", "DE", "UK"]
            ),
            Brand(
                brand_name="Super777",
                status=BrandStatus.ACTIVE,
                default_currency="EUR",
                default_language="en",
                domains=["super777.com"],
                languages_supported=["en", "es", "pt"],
                country_availability=["ES", "PT", "BR"]
            )
        ]
        for brand in brands:
            await db.brands.insert_one(brand.model_dump())
    
    if await db.currencies.count_documents({}) == 0:
        currencies = [
            Currency(currency_code="USD", symbol="$", exchange_rate=1.0),
            Currency(currency_code="EUR", symbol="€", exchange_rate=0.92),
            Currency(currency_code="TRY", symbol="₺", exchange_rate=32.5),
            Currency(currency_code="GBP", symbol="£", exchange_rate=0.79)
        ]
        for curr in currencies:
            await db.currencies.insert_one(curr.model_dump())
    
    if await db.country_rules.count_documents({}) == 0:
        countries = [
            CountryRule(country_code="TR", country_name="Turkey", is_allowed=True, kyc_level=2),
            CountryRule(country_code="US", country_name="United States", is_allowed=True, kyc_level=3),
            CountryRule(country_code="UK", country_name="United Kingdom", is_allowed=True, kyc_level=2),
            CountryRule(country_code="CN", country_name="China", is_allowed=False, kyc_level=1)
        ]
        for country in countries:
            await db.country_rules.insert_one(country.model_dump())
    
    return {"message": "Settings seeded successfully"}
