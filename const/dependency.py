from starlette.authentication import AuthenticationBackend, AuthenticationError
from models.authentication_db import UsersBearerToken, UsersUserAccount
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi import Depends, HTTPException
from datetime import datetime, timedelta
from jose.exceptions import JOSEError
from jose import jwt, JWTError


security = HTTPBearer()


secret_key = "6SmNJkORV3+HoZV3RhUrMrh0xn/+BM1LZmJzPfPwgK5j5AbQ1XHkjjDCm1VFJhiui3CERyKFG5SB4gREWRF+tQ=="
#secret_key = "263420050607200625102019310820200101202108082021"


ALGORITHM = "HS256"


async def create_access_token(data: dict):
    try:
        to_encode = data.copy()

        expire = datetime.utcnow() + timedelta(minutes=43000)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)
        return encoded_jwt
    except Exception:
        raise HTTPException(status_code=502,
                            detail="Unsuccessful authentication")


async def has_access(credentials: HTTPAuthorizationCredentials=Depends(security)):
    token = credentials.credentials
    if token == "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZF91c2VyIjotMSwiZmJpZCI6IlJlZ2lzdHJhd" \
                                    "GlvbiIsImV4cCI6NDg0MjY2NzY2NX0.lzICh4ya1hVSehS4tCFLBTwOTD6TDxaxoBpJgt6YRrw":
        raise HTTPException(403, "Forbidden")
    try:
        jwt.decode(token, key=secret_key, options={"verify_signature": False,
                                                           "verify_aud": False,
                                                           "verify_iss": False})
        return token
    except JOSEError as e:  # catches any exception
        raise HTTPException(
            status_code=401,
            detail=str(e))


async def has_access_parent(credentials: HTTPAuthorizationCredentials=Depends(security)):
    token = credentials.credentials
    if token == "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZF91c2VyIjotMSwiZmJpZCI6IlJlZ2lzdHJhd" \
                                    "GlvbiIsImV4cCI6NDg0MjY2NzY2NX0.lzICh4ya1hVSehS4tCFLBTwOTD6TDxaxoBpJgt6YRrw":
        raise HTTPException(403, "Forbidden")
    try:
        jwt.decode(token, key=secret_key, options={"verify_signature": False,
                                                           "verify_aud": False,
                                                           "verify_iss": False})
        user = await UsersBearerToken.filter(token=token).first().values()
        if await UsersUserAccount.filter(id_user=user["id_user"], id_type_account=1).count() == 0:
            raise HTTPException(403, "Forbidden")
        return token
    except JOSEError as e:  # catches any exception
        raise HTTPException(
            status_code=401,
            detail=str(e))


async def has_access_admin(credentials: HTTPAuthorizationCredentials=Depends(security)):
    token = credentials.credentials
    if token == "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZF91c2VyIjotMSwiZmJpZCI6IlJlZ2lzdHJhd" \
                                    "GlvbiIsImV4cCI6NDg0MjY2NzY2NX0.lzICh4ya1hVSehS4tCFLBTwOTD6TDxaxoBpJgt6YRrw":
        raise HTTPException(403, "Forbidden")
    try:
        jwt.decode(token, key=secret_key, options={"verify_signature": False,
                                                           "verify_aud": False,
                                                           "verify_iss": False})
        user = await UsersBearerToken.filter(token=token).first().values()
        if await UsersUserAccount.filter(id_user=user["id_user"], id_type_account=7).count() == 0:
            raise HTTPException(403, "Forbidden")
        return token
    except JOSEError as e:  # catches any exception
        raise HTTPException(
            status_code=401,
            detail=str(e))


async def has_access_driver(credentials: HTTPAuthorizationCredentials=Depends(security)):
    token = credentials.credentials
    if token == "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZF91c2VyIjotMSwiZmJpZCI6IlJlZ2lzdHJhd" \
                                    "GlvbiIsImV4cCI6NDg0MjY2NzY2NX0.lzICh4ya1hVSehS4tCFLBTwOTD6TDxaxoBpJgt6YRrw":
        raise HTTPException(403, "Forbidden")
    try:
        jwt.decode(token, key=secret_key, options={"verify_signature": False,
                                                           "verify_aud": False,
                                                           "verify_iss": False})
        user = await UsersBearerToken.filter(token=token).first().values()
        if await UsersUserAccount.filter(id_user=user["id_user"], id_type_account=2).count() == 0:
            raise HTTPException(403, "Forbidden")
        return token
    except JOSEError as e:  # catches any exception
        raise HTTPException(
            status_code=401,
            detail=str(e))


async def has_access_franchise(credentials: HTTPAuthorizationCredentials=Depends(security)):
    token = credentials.credentials
    if token == "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZF91c2VyIjotMSwiZmJpZCI6IlJlZ2lzdHJhd" \
                                    "GlvbiIsImV4cCI6NDg0MjY2NzY2NX0.lzICh4ya1hVSehS4tCFLBTwOTD6TDxaxoBpJgt6YRrw":
        raise HTTPException(403, "Forbidden")
    try:
        jwt.decode(token, key=secret_key, options={"verify_signature": False,
                                                           "verify_aud": False,
                                                           "verify_iss": False})
        user = await UsersBearerToken.filter(token=token).first().values()
        if await UsersUserAccount.filter(id_user=user["id_user"], id_type_account__in=[3, 4, 5, 6, 7]).count() == 0:
            raise HTTPException(403, "Forbidden")
        return token
    except JOSEError as e:  # catches any exception
        raise HTTPException(
            status_code=401,
            detail=str(e))


async def has_access_franchise_admin_and_main_admin(credentials: HTTPAuthorizationCredentials=Depends(security)):
    token = credentials.credentials
    if token == "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZF91c2VyIjotMSwiZmJpZCI6IlJlZ2lzdHJhd" \
                                    "GlvbiIsImV4cCI6NDg0MjY2NzY2NX0.lzICh4ya1hVSehS4tCFLBTwOTD6TDxaxoBpJgt6YRrw":
        raise HTTPException(403, "Forbidden")
    try:
        jwt.decode(token, key=secret_key, options={"verify_signature": False,
                                                           "verify_aud": False,
                                                           "verify_iss": False})
        user = await UsersBearerToken.filter(token=token).first().values()
        if await UsersUserAccount.filter(id_user=user["id_user"], id_type_account__in=[6, 7]).count() == 0:
            print(user["id_user"], user["id_type_account"])
            raise HTTPException(403, "Forbidden")
        return token
    except JOSEError as e:  # catches any exception
        raise HTTPException(
            status_code=401,
            detail=str(e))


async def has_access_franchise_admin(credentials: HTTPAuthorizationCredentials=Depends(security)):
    token = credentials.credentials
    if token == "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZF91c2VyIjotMSwiZmJpZCI6IlJlZ2lzdHJhd" \
                                    "GlvbiIsImV4cCI6NDg0MjY2NzY2NX0.lzICh4ya1hVSehS4tCFLBTwOTD6TDxaxoBpJgt6YRrw":
        raise HTTPException(403, "Forbidden")
    try:
        jwt.decode(token, key=secret_key, options={"verify_signature": False,
                                                           "verify_aud": False,
                                                           "verify_iss": False})
        user = await UsersBearerToken.filter(token=token).first().values()
        if await UsersUserAccount.filter(id_user=user["id_user"], id_type_account=6).count() == 0:
            raise HTTPException(403, "Forbidden")
        return token
    except JOSEError as e:  # catches any exception
        raise HTTPException(
            status_code=401,
            detail=str(e))


async def has_access_partner(credentials: HTTPAuthorizationCredentials=Depends(security)):
    token = credentials.credentials
    if token == "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZF91c2VyIjotMSwiZmJpZCI6IlJlZ2lzdHJhd" \
                                    "GlvbiIsImV4cCI6NDg0MjY2NzY2NX0.lzICh4ya1hVSehS4tCFLBTwOTD6TDxaxoBpJgt6YRrw":
        raise HTTPException(403, "Forbidden")
    try:
        jwt.decode(token, key=secret_key, options={"verify_signature": False,
                                                           "verify_aud": False,
                                                           "verify_iss": False})
        user = await UsersBearerToken.filter(token=token).first().values()
        if await UsersUserAccount.filter(id_user=user["id_user"], id_type_account__in=[5]).count() == 0:
            raise HTTPException(403, "Forbidden")
        return token
    except JOSEError as e:  # catches any exception
        raise HTTPException(
            status_code=401,
            detail=str(e))


async def has_back_access(token):
    if token == "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZF91c2VyIjotMSwiZmJpZCI6IlJlZ2lzdHJhd" \
                                    "GlvbiIsImV4cCI6NDg0MjY2NzY2NX0.lzICh4ya1hVSehS4tCFLBTwOTD6TDxaxoBpJgt6YRrw":
        raise HTTPException(403, "Forbidden")
    try:
        jwt.decode(token, key=secret_key, options={"verify_signature": False,
                                                           "verify_aud": False,
                                                           "verify_iss": False})
        return token
    except JOSEError as e:  # catches any exception
        raise HTTPException(
            status_code=401,
            detail=str(e))


async def has_access_files(credentials: HTTPAuthorizationCredentials=Depends(security)):
    token = credentials.credentials
    try:
        jwt.decode(token, key=secret_key, options={"verify_signature": False,
                                                           "verify_aud": False,
                                                           "verify_iss": False})
        return token
    except JOSEError as e:  # catches any exception
        raise HTTPException(
            status_code=401,
            detail=str(e))


class BearerTokenAuthBackend(AuthenticationBackend):
    async def authenticate(self, request):
        # This function is inherited from the base class and called by some other class
        if "Authorization" not in request.headers:
            return
        auth = request.headers["Authorization"]
        try:
            scheme, token = auth.split()
            if scheme.lower() != 'bearer':
                return
            payload = jwt.decode(
                token,
                secret_key,
                algorithms=[ALGORITHM],
                options={"verify_aud": False},
            )
        except (ValueError, UnicodeDecodeError, JWTError):
            raise AuthenticationError('Invalid JWT Token.')
        if await UsersBearerToken.filter(id_user=payload["id_user"], fbid=payload["fbid"], token=token).count() == 0:
            if token != "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZF91c2VyIjotMSwiZmJpZCI6IlJlZ2lzdHJhdGlvbiIsImV4cCI" \
                        "6NDg0MjY2NzY2NX0.lzICh4ya1hVSehS4tCFLBTwOTD6TDxaxoBpJgt6YRrw":
                raise AuthenticationError('Invalid JWT Token.')
        return auth, payload["id_user"]
