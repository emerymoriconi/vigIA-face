from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader
from src.config import VIGIA_API_KEY

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(header_key: str = Security(api_key_header)):
    if header_key == VIGIA_API_KEY:
        return header_key
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Acesso negado: API Key inválida ou ausente."
    )
