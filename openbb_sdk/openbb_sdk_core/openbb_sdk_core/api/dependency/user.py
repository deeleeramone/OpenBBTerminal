from datetime import datetime, timedelta
from typing import Annotated, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from openbb_sdk_core.api.dependency.system import get_system_settings
from openbb_sdk_core.api.model.access_token import AccessToken
from openbb_sdk_core.app.model.system_settings import SystemSettings
from openbb_sdk_core.app.model.user_settings import UserSettings
from openbb_sdk_core.app.service.user_service import UserService
from passlib.context import CryptContext
from pymongo import MongoClient

SECRET_KEY = "a0657288545d1d2e991195841782ae2a22574a22954081db0c2888c5f5ddbecc"  # nosec # pragma: allowlist secret
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440

__user_service: Optional[UserService] = None
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/account/token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def authenticate_user(
    password: str,
    username: str,
    user_service: UserService,
) -> Optional[UserSettings]:
    user = user_service.user_settings_repository.read_by_profile(
        filter_list=[("username", username)],
    )
    if (
        user
        and user.profile
        and user.profile.password_hash
        and verify_password(password, user.profile.password_hash)
    ):
        return user

    return None


def create_access_token(
    sub: str,
    expiration_delta: Optional[timedelta] = None,
) -> AccessToken:
    if expiration_delta is None:
        expiration_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    expiration_datetime = datetime.utcnow() + expiration_delta
    return AccessToken(
        sub=sub,
        exp=expiration_datetime,
    )


def create_jwt_token(
    access_token: AccessToken,
    key=SECRET_KEY,
    algorithm=ALGORITHM,
) -> str:
    claims = access_token.dict()
    encoded_jwt = jwt.encode(claims=claims, key=key, algorithm=algorithm)
    return encoded_jwt


async def get_user_service(
    system_settings: Annotated[SystemSettings, Depends(get_system_settings)]
) -> UserService:
    global __user_service  # pylint: disable=global-statement

    if __user_service is None:
        dbms_uri = system_settings.dbms_uri
        if dbms_uri and dbms_uri.startswith("mongodb://"):
            mongodb_client: MongoClient = MongoClient(dbms_uri)
            __user_service = UserService(mongodb_client=mongodb_client)
        else:
            __user_service = UserService()

    return __user_service


async def get_user(
    jwt_token: Annotated[str, Depends(oauth2_scheme)],
    user_service: Annotated[UserService, Depends(get_user_service)],
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        jwt_payload = jwt.decode(jwt_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_settings_id: Optional[str] = jwt_payload.get("sub")
        if user_settings_id is None:
            raise credentials_exception
    except JWTError as e:
        raise credentials_exception from e

    user_settings = user_service.user_settings_repository.read(
        filter_list=[("id", user_settings_id)]
    )
    if (
        user_settings is None
        or user_settings.profile is None
        or user_settings.profile.active is None
    ):
        raise credentials_exception
    if user_settings and user_settings.profile and not user_settings.profile.active:
        raise HTTPException(status_code=400, detail="Inactive user")

    return user_settings
