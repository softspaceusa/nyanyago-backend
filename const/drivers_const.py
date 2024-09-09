from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Union


driver_not_found = JSONResponse({"status": False,
                                 "message": "Driver not found!"}, 404)
get_driver = JSONResponse({"status": True,
                           "message": "Success!",
                           "driver": {
                                        "surname": "string",
                                        "name": "string",
                                        "inn": "string",
                                        "photo_path": "string",
                                        "video_path": "string",
                                        "date_reg": "string",
                                        "hasAuth": True,
                                        "carData":
                                                    {
                                                        "mark": "string",
                                                        "model": "string",
                                                        "color": "string",
                                                        "year": 0,
                                                        "state_number": "string",
                                                        "ctc": "string"
                                                    }
                                    }
                           })
get_my_referals = JSONResponse({"status": True,
                                "message": "Success!",
                                "total": 0,
                                "referals": [
                                                {
                                                    "id": 0,
                                                    "name": "string",
                                                    "photo_path": "string",
                                                    "status": True
                                                }
                                ]})
start_current_drive_mode = JSONResponse({"status": True,
                                         "message": "Success!",
                                         "driver-token": "string"})


class GetDriverReferals(BaseModel):
    limit: Union[int, None] = 10
    offset: Union[int, None] = 0


class GetDriver(BaseModel):
    id: int


class NowLocation(BaseModel):
    latitude: float
    longitude: float


class SendPaymentRequest(BaseModel):
    type_request: Union[int, None] = 1
    id_card: int
    amount: Union[float, None] = None



