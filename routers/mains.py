import requests
from fastapi.responses import FileResponse, JSONResponse
from fastapi import APIRouter, Form
from starlette.requests import Request
from common.logger import logger

router = APIRouter()


@router.get("/.well-known/assetlinks.json",
            response_class=FileResponse)
async def get_well_known_assetlinks():
    return "/root/files/assetlinks.json"


#
# @router.get("/auth")
# async def get_auth():
#     return JSONResponse({}, status_code=200)


@router.post("/3ds-callback")
async def handle_3ds_callback(
        request: Request,
        MD: str = Form(None),  # Параметр MD (для 3DS v1.0 и v2.1)
        PaRes: str = Form(None),  # Параметр PaRes (для 3DS v1.0)
        CRes: str = Form(None)  # Параметр CRes (для 3DS v2.1)
):
    logger.info(f"Received MD: {MD}")
    if PaRes:
        logger.info(f"Received PaRes (3DS v1.0): {PaRes}")
        url = "https://securepay.tinkoff.ru/v2/Submit3DSAuthorization"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        form_data = {
            "MD": MD,
            "PaRes": PaRes
        }
        ds3_ver = requests.post(url, data=form_data, headers=headers).json()
        logger.info(ds3_ver)
    elif CRes:
        logger.info(f"Received CRes (3DS v2.1): {CRes}")

    return JSONResponse(
        content={"status": "success", "message": "3DS Callback Received"})
