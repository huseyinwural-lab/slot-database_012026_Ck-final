from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from config import settings
from app.core.database import db_wrapper

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_player(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        player_id: str = payload.get("sub")
        role: str = payload.get("role")
        
        if player_id is None or role != "player":
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
        
    db = db_wrapper.db
    player = await db.players.find_one({"id": player_id})
    if player is None:
        raise credentials_exception
        
    return player
