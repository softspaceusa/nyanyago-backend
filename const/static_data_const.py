from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Union, Any


not_user_photo = "https://nyanyago.ru/api/v1.0/files/not_user_photo.png"


access_forbidden = JSONResponse({"detail": "Forbidden"}, 403)
not_found_other_parametr = JSONResponse({"status": False,
                                         "message": "Other parametr of drive by id not found!"})
country = JSONResponse({"status": True,
                        "message": "Success!",
                        "countries": [
                                        {
                                            "id": 0,
                                            "title": "string"
                                        }
                                    ]
                        })

get_tariffs = JSONResponse(
    {
        "status": True,
        "message": "Success!",
        "tariffs": [
            {
                "id": 0,
                "name": "string",
                "amount": 0.0,
                "photo_path": "string",
                "type": "string",
                "one_time": True,
            }
        ],
    }
)

franchise_not_found = JSONResponse(
    {"status": False, "message": "Franchise for current user not found!"},
    status_code=404,
)

color = JSONResponse({"status": True,
                      "message": "Success!",
                      "colors": [
                        {
                          "id": 0,
                          "title": "string"
                        }
                      ]
                    })
city = JSONResponse({"status": True,
                     "message": "Success!",
                     "cities": [
                        {
                            "id": 0,
                            "title": "string"
                        }
                      ]
                    })
car_mark = JSONResponse({"status": True,
                     "message": "Success!",
                     "cities": [
                        {
                            "id": 0,
                            "title": "string"
                        }
                      ]
                    })
car_model = JSONResponse({"status": True,
                          "message": "Success!",
                          "models": [
                            {
                              "id": 0,
                              "title": "string",
                              "id_car_mark": 0,
                              "releaseYear": 0
                            }
                          ]
                        })
biometric_setting = JSONResponse({"status": True,
                                  "message": "Success!",
                                  "value": True})
drive_params = JSONResponse({"status": True,
                             "message": "Success!",
                             "data": [
                                 {
                                     "id": 0,
                                     "title": "string",
                                     "amount": 0.0
                                 }
                             ]})
drive_statuses = JSONResponse({"status": True,
                               "message": "Success!",
                               "drive_statuses": [
                                   {
                                       "id": 0,
                                       "title": "string",
                                   }
                               ]})



class DictToModel:
    def __init__(self, d: dict):
        self.d = d

    def get_value(self):
        return self.d

    def __getattr__(self, item: str):
        value = self.d.get(item)
        if isinstance(value, dict):
            return self.__class__(value)

        return value
    def __repr__(self):
        return repr(self.d)


class GetCountry(BaseModel):
    id: Union[int, None] = None
    title: Union[str, None] = None


class SearchAddress(BaseModel):
    query: str
    offset: int
    limit: int
    lat: Union[float, None] = None
    lon: Union[float, None] = None


class UpdateOtherDriveParametr(BaseModel):
    id: int
    title: Union[str, None] = None
    amount: Union[float, None] = None


class OtherDriveParametr(BaseModel):
    title: Union[str, None] = None
    amount: Union[float, None] = None

