from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid

# --- CMS ENUMS ---
class CMSStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    SCHEDULED = "scheduled"
    ARCHIVED = "archived"

class CMSPageType(str, Enum):
    HOMEPAGE = "homepage"
    PROMO = "promo"
    STATIC = "static"
    BLOG = "blog"
    LANDING = "landing"

class CMSBannerPosition(str, Enum):
    HOME_HERO = "home_hero"
    LOBBY_TOP = "lobby_top"
    MOBILE_ONLY = "mobile_only"
    SIDEBAR = "sidebar"

# --- CMS MODELS ---

class CMSPage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    slug: str
    language: str = "en"
    template: CMSPageType = CMSPageType.STATIC
    status: CMSStatus = CMSStatus.DRAFT
    content_blocks: List[Dict[str, Any]] = [] 
    seo: Dict[str, Any] = {} 
    publish_at: Optional[datetime] = None
    updated_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    updated_by: Optional[str] = None

class CMSMenu(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    location: str 
    items: List[Dict[str, Any]] = [] 
    updated_at: datetime = Field(default_factory=lambda: datetime.utcnow())

class CMSBanner(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str 
    position: CMSBannerPosition
    language: str = "en"
    image_desktop: str
    image_mobile: Optional[str] = None
    link_url: Optional[str] = None
    status: CMSStatus = CMSStatus.DRAFT
    priority: int = 0
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    targeting: Dict[str, Any] = {} 

class CMSLayout(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str 
    sections: List[Dict[str, Any]] = [] 
    status: CMSStatus = CMSStatus.DRAFT

class CMSCollection(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    type: str 
    rules: Dict[str, Any] = {}
    game_ids: List[str] = []

class CMSPopup(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    content: str
    type: str 
    targeting: Dict[str, Any] = {}
    status: CMSStatus = CMSStatus.DRAFT

class CMSRedirect(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    from_url: str
    to_url: str
    type: int = 301

class CMSTranslation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    key: str
    default_text: str
    translations: Dict[str, str] = {} 

class CMSMedia(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    type: str
    url: str
    size: int
    tags: List[str] = []
    uploaded_at: datetime = Field(default_factory=lambda: datetime.utcnow())

class CMSLegalDoc(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str 
    version: str
    content: str
    effective_date: datetime
    status: CMSStatus = CMSStatus.DRAFT

class CMSExperiment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    target_type: str 
    variants: List[Dict[str, Any]] = []
    status: str = "running"
    results: Dict[str, Any] = {}

class CMSMaintenance(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    message: str
    type: str 
    start_time: datetime
    end_time: datetime
    active: bool = True

class CMSAuditLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    admin_id: str
    action: str
    target_type: str
    target_id: str
    diff: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.utcnow())

class CMSDashboardStats(BaseModel):
    published_pages: int
    active_banners: int
    draft_count: int
    scheduled_count: int
    recent_changes: List[CMSAuditLog] = []
