from fastapi.responses import FileResponse, JSONResponse
from fastapi import APIRouter


router = APIRouter()


@router.get("/.well-known/assetlinks.json",
            response_class=FileResponse)
async def get_well_known_assetlinks():
    return "/root/files/assetlinks.json"

#
# @router.get("/auth")
# async def get_auth():
#     return JSONResponse({}, status_code=200)
