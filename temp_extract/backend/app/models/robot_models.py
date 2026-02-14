from typing import Dict
from datetime import datetime
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, JSON
import uuid

class RobotDefinition(SQLModel, table=True):
    """Defines a Game Math Engine (The 'Robot')"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str = Field(index=True)
    schema_version: str = "1.0"
    
    # Config defines rules: { "lines": 20, "reel_set_ref": "basic_reels_v1", "paytable_ref": "basic_pay_v1" }
    config: Dict = Field(default={}, sa_column=Column(JSON))
    config_hash: str = Field(index=True) # SHA256 of config content for integrity
    
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class MathAsset(SQLModel, table=True):
    """Stores heavy math data (Reelsets, Paytables) referenced by Robots"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    
    # Logical Reference Key (e.g. "basic_reels_v1")
    ref_key: str = Field(index=True, unique=True)
    type: str # "reelset" | "paytable"
    version: str = "1.0"
    
    content: Dict = Field(default={}, sa_column=Column(JSON))
    content_hash: str # SHA256
    
    created_at: datetime = Field(default_factory=datetime.utcnow)

class GameRobotBinding(SQLModel, table=True):
    """Binds a Game (Catalog Item) to a Robot (Math Engine)"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    
    tenant_id: str = Field(index=True)
    game_id: str = Field(index=True) # References Game.id
    robot_id: str = Field(foreign_key="robotdefinition.id")
    
    is_enabled: bool = True
    effective_from: datetime = Field(default_factory=datetime.utcnow)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
