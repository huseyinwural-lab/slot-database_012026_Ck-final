from fastapi import HTTPException

class ProviderError(HTTPException):
    def __init__(self, code: str, message: str, status_code: int = 400):
        self.detail = {"code": code, "message": message}
        self.status_code = status_code

class SignatureError(ProviderError):
    def __init__(self):
        super().__init__("INVALID_SIGNATURE", "HMAC verification failed", 401)

class IdempotencyError(ProviderError):
    def __init__(self):
        super().__init__("DUPLICATE_REQUEST", "Request already processed", 409)
