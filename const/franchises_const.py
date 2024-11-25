from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Union, List

payment_requests = JSONResponse({"status": True,
                                 "message": "Success!",
                                 "result": [
                                     {
                                         "id": 0,
                                         "id_user": 0,
                                         "money": "string",
                                         "surname": "string",
                                         "name": "string",
                                         "photo_path": "string"
                                     }
                                 ]})
get_my_referals = JSONResponse({"status": True,
                                "message": "Success!",
                                "partner": {
                                     "name": "string",
                                     "surname": "string",
                                     "phone": "string",
                                     "photo_path": "string",
                                     "referal_code": "string",
                                     "referal_percent": 0,
                                     "all_incoming": 0,
                                     "get_percent": 0.0,
                                     "referals": [
                                                    {
                                                        "id": 0,
                                                        "name": "string",
                                                        "surname": "string",
                                                        "photo_path": "string",
                                                        "referal_code": "string",
                                                        "date_reg": "string",
                                                        "all_incoming": 0,
                                                        "get_percent": 0.0
                                                    }
                                     ]
                                 }})


get_money_stats = JSONResponse({"status": True,
                                "message": "Success!",
                                "minus": {
                                    "spending_on_bonuses": 0.0},
                                "plus": {
                                    "received_due_to_commission": 0.0}})


incorrect_period = JSONResponse({"status": False,
                                 "message": "The period must be 0 or negative",
                                 }, status_code=400)

incorrect_period_str = JSONResponse({"status": False,
                                     "message": "The period must 'day', 'week', 'month', 'year'",
                                     }, status_code=400)

incorrect_user = JSONResponse({"status": False,
                              "message": "Current users do not belong to any franchise",
                               }, status_code=400)

get_franchise_driver_orders = JSONResponse(
    {
        "status": True,
        "message": "Success!",
        "orders": [
            {
                "id": 0,
                "status": "string",
                "name": "string",
                "id_driver": 0,
                "name_driver": "string",
                "surname_driver": "string",
            }
        ],
    }
)

get_partner_payouts = JSONResponse(
    {
        "status": True,
        "message": "Success!",
        "payouts": [
            {
                "id": 0,
                "money": 0.0,
                "datetime_create": "string-iso",
                "cashback_percent": 0
            }
        ],
    }
)



class OutputPayment(BaseModel):
    id_payment: int
    id_driver: int


class NewTariff(BaseModel):
    title: str
    description: Union[str, None] = None
    percent: Union[int, None] = None
    photo_path: Union[str, None] = "https://nyanyago.ru/api/v1.0/files/econom.png"
    one_time: bool = True


class UpdateTariff(BaseModel):
    id_tariff: int
    title: Union[str, None] = None
    description: Union[str, None] = None
    photo_path: Union[str, None] = None
    one_time: Union[bool, None] = None


class BonusFineDriver(BaseModel):
    id_driver: int
    amount: int


class ResponseNewDriver(BaseModel):
    id_driver: int
    success: Union[bool, None] = False
    id_tariff: List[int]

