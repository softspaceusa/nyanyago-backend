from datetime import datetime
from decimal import Decimal

from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from typing import Union, List


driver_not_found = JSONResponse({"status": False,
                                 "message": "Driver not found!"}, 404)
you_have_active_drive = JSONResponse({"status": False,
                                     "message": "You have active drive"}, 404)
cant_decline_in_drive_mode = JSONResponse({"status": False,
                                          "message": "You already start drive!"}, 404)
start_current_drive = JSONResponse({"status": True,
                                    "message": "Success!",
                                    "token": "string"})
schedule_not_found = JSONResponse({"status": False,
                                   "message": "Schedule by id not found!"}, 404)
tariff_by_id_not_found = JSONResponse({"status": False,
                                       "message": "Tariff by id not found!"}, 405)
get_onetime_prices = JSONResponse({"status": False,
                                   "message": "Success",
                                   "tariffs": [
                                       {
                                           "id_tariff": 0,
                                           "amount": 0
                                       }
                                   ]})
start_onetime_drive = JSONResponse({"status": False,
                                    "message": "Success",
                                    "token": "string",
                                    "time": "string",
                                    "addresses": ["dict"],
                                    "total_price": 0.0,
                                    "total_distance_meters": 0.0,
                                    "total_duration_seconds_estimated": 0.0
                                    })
get_orders = JSONResponse({"status": True,
                           "message": "Success",
                           "orders": [
                               {
                                   "id_order": 0,
                                   "username": "string",
                                   "phone": "string",
                                   "user_photo": "url-string",
                                   "amount": 0.0,
                                   "id_status": 0,
                                   "addresses": [{
                                                     "from": "string",
                                                     "isFinish": "string",
                                                     "to": "string",
                                                     "from_lat": 0.0,
                                                     "from_lon": 0.0,
                                                     "to_lat": 0.0,
                                                     "to_lon": 0.0,
                                                     "duration": 0
                                                }]
                               }
                           ]})
get_schedule_responses = JSONResponse({"status": True,
                                       "message": "Success!",
                                       "responses": [
                                           {
                                               "name": "string",
                                               "photo_path": "string",
                                               "id_driver": 0,
                                               "id_chat": 0,
                                               "id_schedule": "string",
                                               "full_time": True,
                                               "data": [
                                                            {
                                                                "id_road": 0,
                                                                "week_day": 0
                                                            }
                                               ]
                                           }
                                       ]})
get_schedule = JSONResponse({"status": True,
                             "message": "Success!",
                             "schedule": {
                                          "id": 0,
                                          "id_user": 0,
                                          "duration": 0,
                                          "children_count": 0,
                                          "week_days": [
                                                            0
                                          ],
                                          "id_tariff": 0,
                                          "other_parametrs": [{
                                              "parameter": 0,
                                              "count": 1
                                          }],
                                          "roads": [
                                                        {
                                                          "week_day": 0,
                                                          "start_time": "string",
                                                          "end_time": "string",
                                                          "addresses": [
                                                                        {
                                                                          "from_address": {
                                                                                            "address": "string",
                                                                                            "location": {
                                                                                                          "latitude": 0,
                                                                                                          "longitude": 0
                                                                                            }
                                                                          },
                                                                          "to_address": {
                                                                                            "address": "string",
                                                                                            "location": {
                                                                                                          "latitude": 0,
                                                                                                          "longitude": 0
                                                                                            }
                                                                          }
                                                                        }
                                                          ],
                                                          "title": "string",
                                                          "type_drive": [
                                                                            0
                                                          ]
                                                        }
                                          ]}
                             }, 200)
get_schedule_road = JSONResponse({"status": True,
                                  "message": "Success!",
                                  "schedule_road":
                                                  {
                                                      "week_day": 0,
                                                      "start_time": "string",
                                                      "end_time": "string",
                                                      "addresses": [
                                                          {
                                                              "from_address": {
                                                                  "address": "string",
                                                                  "location": {
                                                                      "latitude": 0,
                                                                      "longitude": 0
                                                                  }
                                                              },
                                                              "to_address": {
                                                                  "address": "string",
                                                                  "location": {
                                                                      "latitude": 0,
                                                                      "longitude": 0
                                                                  }
                                                              }
                                                          }
                                                      ],
                                                      "title": "string",
                                                      "type_drive": [
                                                          0
                                                      ]
                                                }
                                  })
get_schedules = JSONResponse({"status": True,
                             "message": "Success!",
                             "schedules": [{
                                          "id": 0,
                                          "id_user": 0,
                                          "duration": 0,
                                          "children_count": 0,
                                          "isActive": True,
                                          "datetime_create": "2024-01-01 00:00:00.00000",
                                          "week_days": [
                                                            0
                                          ],
                                          "id_tariff": 0,
                                          "other_parametrs": [{
                                              "parameter": 0,
                                              "count": 1
                                          }],
                                          "roads": [
                                                        {
                                                          "week_day": 0,
                                                          "start_time": "string",
                                                          "end_time": "string",
                                                          "addresses": [
                                                                        {
                                                                          "from_address": {
                                                                                            "address": "string",
                                                                                            "location": {
                                                                                                          "latitude": 0,
                                                                                                          "longitude": 0
                                                                                            }
                                                                          },
                                                                          "to_address": {
                                                                                            "address": "string",
                                                                                            "location": {
                                                                                                          "latitude": 0,
                                                                                                          "longitude": 0
                                                                                            }
                                                                          }
                                                                        }
                                                          ],
                                                          "title": "string",
                                                          "type_drive": [
                                                                            0
                                                          ]
                                                        }
                                          ]}]
                             }, 200)

get_schedules_responses = JSONResponse({"status": True,
                             "message": "Success!",
                             "schedules": [{
                                          "id": 0,
                                          "user": {
                                            "id_user": 0,
                                            "name": "string",
                                            "photo_path": "string"
                                          },
                                          "duration": 0,
                                          "all_salary": 0,
                                          "children_count": 0,
                                          "week_days": [
                                                            0
                                          ],
                                          "id_tariff": 0,
                                          "other_parametrs": [{
                                              "parameter": 0,
                                              "count": 1
                                          }],
                                          "roads": [
                                                        {
                                                          "salary": 0,
                                                          "week_day": 0,
                                                          "start_time": "string",
                                                          "end_time": "string",
                                                          "addresses": [
                                                                        {
                                                                          "from_address": {
                                                                                            "address": "string",
                                                                                            "location": {
                                                                                                          "latitude": 0,
                                                                                                          "longitude": 0
                                                                                            }
                                                                          },
                                                                          "to_address": {
                                                                                            "address": "string",
                                                                                            "location": {
                                                                                                          "latitude": 0,
                                                                                                          "longitude": 0
                                                                                            }
                                                                          }
                                                                        }
                                                          ],
                                                          "title": "string",
                                                          "type_drive": [
                                                                            0
                                                          ]
                                                        }
                                          ]}]
                             }, 200)
get_driver_schedules = JSONResponse({"status": True,
                                    "message": "Success!",
                                    "roads": [{
                                          "id": 0,
                                          "user": {
                                            "id_user": 0,
                                            "name": "string",
                                            "photo_path": "string"
                                          },
                                          "duration": 0,
                                          "all_salary": 0,
                                          "children_count": 0,
                                          "week_days": [
                                                            0
                                          ],
                                          "id_tariff": 0,
                                          "other_parametrs": [{
                                              "parameter": 0,
                                              "count": 1
                                          }],
                                          "roads": [
                                                        {
                                                          "salary": 0,
                                                          "week_day": 0,
                                                          "start_time": "string",
                                                          "end_time": "string",
                                                          "addresses": [
                                                                        {
                                                                          "from_address": {
                                                                                            "address": "string",
                                                                                            "location": {
                                                                                                          "latitude": 0,
                                                                                                          "longitude": 0
                                                                                            }
                                                                          },
                                                                          "to_address": {
                                                                                            "address": "string",
                                                                                            "location": {
                                                                                                          "latitude": 0,
                                                                                                          "longitude": 0
                                                                                            }
                                                                          }
                                                                        }
                                                          ],
                                                          "title": "string",
                                                          "type_drive": [
                                                                            0
                                                          ]
                                                        }
                                          ]}]
                             }, 200)
get_today_schedule = JSONResponse({"status": True,
                                   "message": "Success!",
                                   "schedule": [
                                                 {
                                                     "id": 0,
                                                     "title": "string",
                                                     "parent_name": "string",
                                                     "id_parent": 0,
                                                     "time": "12:00 - 15:50",
                                                     "date": "03.04.2024"
                                                 },
                                                 {
                                                     "id": 0,
                                                     "title": "string",
                                                     "parent_name": "string",
                                                     "id_parent": 0,
                                                     "time": "12:00 - 15:50",
                                                     "date": "02.04.2024"
                                                 },
                                                 {
                                                     "id": 0,
                                                     "title": "string",
                                                     "parent_name": "string",
                                                     "id_parent": 0,
                                                     "time": "12:00 - 15:50",
                                                     "date": "02.04.2024"
                                                 },
                                                 {
                                                     "id": 0,
                                                     "title": "string",
                                                     "parent_name": "string",
                                                     "id_parent": 0,
                                                     "time": "12:00 - 15:50",
                                                     "date": "02.04.2024"
                                                 },
                                                 {
                                                     "id": 0,
                                                     "title": "string",
                                                     "parent_name": "string",
                                                     "id_parent": 0,
                                                     "time": "12:00 - 15:50",
                                                     "date": "02.04.2024"
                                                 }
                                ]})

get_driver_token = JSONResponse({"status": True,
                                   "message": "Success!",
                                   "websocket_token": "string"})

get_total_price = JSONResponse({"status": True,
                                "message": "Success!",
                                "total_price": "string",
                                "accurately": True})

class NowLocation(BaseModel):
    latitude: float
    longitude: float


class Address(BaseModel):
    address: str
    location: NowLocation


class DriveAddresses(BaseModel):
    from_address: Address
    to_address: Address


class OneTimeOrder(BaseModel):
    """
    Одноразовый заказ (создаётся оператором для водителя).
    """

    id_driver: int = Field(..., description="ID водителя, связанного с заказом")
    from_address: str = Field(..., description="Адрес отправления")
    to_address: str = Field(..., description="Адрес назначения")
    from_time: datetime = Field(..., description="Время отправления")
    to_time: datetime = Field(..., description="Время прибытия")
    id_tariff: int = Field(..., description="ID тарифа, связанного с заказом")

    @field_validator("from_address", "to_address")
    def validate_address(cls, address: str) -> str:  # noqa
        if len(address.strip()) < 5:
            raise ValueError("Адрес слишком короткий.")
        if not any(char.isdigit() for char in address):
            raise ValueError("Адрес должен содержать номер дома.")
        if address.count(",") < 2:
            raise ValueError(
                "Адрес должен содержать минимум две запятые (например: улица, номер дома, город)"
            )
        return address

    class Config:
        json_schema_extra = {
            "example": {
                "id_driver": 5,
                "from_address": "улица Воздвиженка, 3/5с2, Москва, Россия, 119019",
                "to_address": "улица Петровка, 2, Москва, Россия, 125009",
                "from_time": "2024-11-21T09:00:00",
                "to_time": "2024-11-21T10:00:00",
                "id_tariff": 5,
            }
        }



class OtherParams(BaseModel):
    parametr: int
    count: Union[int, None] = 1


class CurrentDrive(BaseModel):
    my_location: NowLocation
    addresses: List[DriveAddresses]
    description: str
    idTariff: int
    other_parametrs: Union[List[OtherParams], None] = []


class Road(BaseModel):
    week_day: int # Номер дня от 0 до 6 (Пн, Вт, Ср, Чт, Пт, Сб, Вс) == (0, 1, 2, 3, 4, 5, 6)
    start_time: str
    end_time: str
    addresses: List[DriveAddresses]
    title: str
    type_drive: list # Тип поездки: в одну сторону, туда-обратно, с промежуточными точками (1, 2, 3)


class UpdateRoad(BaseModel):
    id: int
    week_day: Union[int, None] = None
    start_time: Union[str, None] = None
    end_time: Union[str, None] = None
    addresses: Union[List[DriveAddresses], None] = None
    title: Union[str, None] = None
    type_drive: Union[list, None] = None  # Тип поездки: в одну сторону, туда-обратно, с промежуточными точками (0, 1, 2)


class GetTotalPrice(BaseModel):
    id_tariff: int
    addresses: List[DriveAddresses]

class NewSchedule(BaseModel):
    title: str # Количество дней
    description: str # Количество дней
    duration: int # Количество дней
    children_count: int
    week_days: list # Номера дней от 0 до 6 (Пн, Вт, Ср, Чт, Пт, Сб, Вс) == (0, 1, 2, 3, 4, 5, 6)
    id_tariff: int # get_tariffs by user's franchise
    other_parametrs: List[OtherParams]
    roads: List[Road]


class UpdateSchedule(BaseModel):
    id: int
    title: Union[str, None] = None # Количество дней
    description: Union[str, None] = None # Количество дней
    duration: Union[int, None] = None # Количество дней
    children_count: Union[int, None] = None
    week_days: Union[list, None] = None # Номера дней от 0 до 6 (Пн, Вт, Ср, Чт, Пт, Сб, Вс) == (0, 1, 2, 3, 4, 5, 6)
    id_tariff: Union[int, None] = None # get_tariffs by user's franchise
    other_parametrs: Union[List[OtherParams], None] = None


class ReadSchedule(BaseModel):
    id: int
    title: str  # Количество дней
    description: str  # Количество дней
    duration: int  # Количество дней
    children_count: int
    week_days: list  # Номера дней от 0 до 6 (Пн, Вт, Ср, Чт, Пт, Сб, Вс) == (0, 1, 2, 3, 4, 5, 6)
    id_tariff: int  # get_tariffs by user's franchise
    other_parametrs: List[OtherParams]
    roads: List[Road]


class WantSchedule(BaseModel):
    id_schedule: int
    id_road: List[int]


class AnswerResponse(BaseModel):
    id_schedule: int
    id_response: int
    flag: bool


class GetPrices(BaseModel):
    duration: int
