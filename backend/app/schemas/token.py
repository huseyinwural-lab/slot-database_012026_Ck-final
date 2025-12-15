from pydantic import BaseModel

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    admin_email: str
    admin_role: str
    # Frontend expects this key to store in localStorage for UI
    admin: dict | None = None 
