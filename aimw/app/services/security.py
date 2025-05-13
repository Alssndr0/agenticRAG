'''This file is responsible for api access token'''

from app.configs.app_config import get_app_settings
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token")  # use token authentication


def api_key_auth(api_key: str = Depends(oauth2_scheme)):
    """Checks key to grant api access

    Args:
        api_key (str, optional): API key. Defaults to Depends(oauth2_scheme).

    Raises:
        HTTPException: 401
    """
    if api_key not in get_app_settings().API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Forbidden"
        )
