from fastapi.responses import JSONResponse
from pydantic import BaseModel
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
                                    "time": "string"
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
                                               "id": 0,
                                               "name": "string",
                                               "photo_path": "string",
                                               "id_driver": 0,
                                               "id_chat": 0,
                                               "id_schedule": 0,
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




class NowLocation(BaseModel):
    latitude: float
    longitude: float


class Address(BaseModel):
    address: str
    location: NowLocation


class DriveAddresses(BaseModel):
    from_address: Address
    to_address: Address


class OtherParams(BaseModel):
    parametr: int
    count: Union[int, None] = 1


class CurrentDrive(BaseModel):
    my_location: NowLocation
    addresses: List[DriveAddresses]
    price: int
    distance: int
    duration: int
    description: str
    typeDrive: int
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
    type_drive: Union[list, None] = None


class NewSchedule(BaseModel):
    title: str # Количество дней
    description: str # Количество дней
    duration: int # Количество дней
    children_count: int
    week_days: list # Номера дней от 0 до 6 (Пн, Вт, Ср, Чт, Пт, Сб, Вс) == (0, 1, 2, 3, 4, 5, 6)
    id_tariff: int # get_tariffs by user's franchise
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
