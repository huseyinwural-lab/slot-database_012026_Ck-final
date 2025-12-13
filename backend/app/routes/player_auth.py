from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel, EmailStr
from app.models.core import Player
from app.utils.auth import get_password_hash, verify_password, create_access_token
from app.core.database import db_wrapper
from config import settings
import uuid

router = APIRouter(prefix="/api/v1/auth/player", tags=["player_auth"])

class PlayerRegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    tenant_id: str = "default_casino" # Client should send this, but can default

class PlayerLoginRequest(BaseModel):
    email: EmailStr
    password: str
    tenant_id: str = "default_casino"

class PlayerTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

@router.post("/register")
async def register_player(payload: PlayerRegisterRequest):
    db = db_wrapper.db
    
    # Check if user exists in this tenant
    existing = await db.players.find_one({
        "email": payload.email, 
        "tenant_id": payload.tenant_id
    })
    
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered in this casino")
    
    # Basic password hash
    password_hash = get_password_hash(payload.password)
    
    player_id = str(uuid.uuid4())
    
    player = Player(
        id=player_id,
        tenant_id=payload.tenant_id,
        username=payload.username,
        email=payload.email,
        balance_real=0.0,
        registered_at=datetime.now(timezone.utc)
    )
    
    player_dict = player.model_dump()
    player_dict["password_hash"] = password_hash # Store manually as Player model doesn't have it explicitly yet in shared model
    
    await db.players.insert_one(player_dict)
    
    return {"message": "Registration successful", "player_id": player_id}

@router.post("/login", response_model=PlayerTokenResponse)
async def login_player(payload: PlayerLoginRequest):
    db = db_wrapper.db
    
    player_doc = await db.players.find_one({
        "email": payload.email, 
        "tenant_id": payload.tenant_id
    })
    
    if not player_doc:
        raise HTTPException(status_code=401, detail="Invalid credentials")
        
    # Check password
    stored_hash = player_doc.get("password_hash")
    if not stored_hash or not verify_password(payload.password, stored_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Update last login
    await db.players.update_one(
        {"id": player_doc["id"]},
        {"$set": {"last_login": datetime.now(timezone.utc)}}
    )
    
    # Create Token
    token = create_access_token(
        data={"sub": player_doc["id"], "role": "player", "tenant_id": payload.tenant_id},
        expires_delta=timedelta(days=7) # Long lived for players
    )
    
    return {
        "access_token": token,
        "user": {
            "id": player_doc["id"],
            "username": player_doc["username"],
            "email": player_doc["email"],
            "balance_real": player_doc.get("balance_real", 0.0)
        }
    }
