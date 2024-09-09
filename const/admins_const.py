from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Union, List

success_answer = JSONResponse({"status": True,
                               "message": "Success!"})
not_found_request = JSONResponse({"status": True,
                                  "message": "Requests from new drivers are not found!"}, 404)
not_found_payment_request = JSONResponse({"status": True,
                                  "message": "Requests from new drivers are not found!"}, 404)
unsupported_role = JSONResponse({"status": False,
                                 "message": "Role not found!"}, 404)
partner_not_found = JSONResponse({"status": False,
                                  "message": "Partner not found!"}, 404)
add_partner_not_found = JSONResponse({"status": False,
                                  "message": "Partner not found!"}, 402)
partners_referal_not_found = JSONResponse({"status": False,
                                           "message": "Partners referal not found!"}, 404)
new_user_message_dont_delivery = JSONResponse({"status": True,
                                               "message": "SMS with user authorization data don't delivery"}, 201)
user_not_found = JSONResponse({"status": True,
                               "message": "User not found!"}, 201)
get_partners = JSONResponse({"status": True,
                             "message": "Success!",
                             "partners": [
                                 {
                                     "id": 0,
                                     "surname": "string",
                                     "name": "string",
                                     "isActive": True,
                                     "datetime_create": "string",
                                     "photo_path": "string"
                                 }
                             ]})
get_partner = JSONResponse({"status": True,
                            "message": "Success!",
                            "partner": {
                             "name": "string",
                             "surname": "string",
                             "phone": "string",
                             "photo_path": "string",
                             "referal_code": "string",
                             "referal_percent": 0,
                             "referals": [
                                 {
                                     "id": 0,
                                     "name": "string",
                                     "surname": "string",
                                     "phone": "string",
                                     "isActive": True,
                                     "date_reg": "string"
                                 }
                             ]
                         }})
get_partners_referal = JSONResponse({"status": True,
                                     "message": "Success!",
                                     "data": {
                                        "name": "string",
                                        "surname": "string",
                                        "date_reg": "string",
                                        "phone": "string",
                                        "photo_path": "string",
                                        "partner_percent": 0
                                    }})
get_users = JSONResponse({"status": True,
                          "message": "Success!",
                          "users": [
                                     {
                                         "id": 0,
                                         "name": "string",
                                         "surname": "string",
                                         "phone": "string",
                                         "datetime_create": "string",
                                         "role": "string",
                                         "status": "string",
                                         "photo_path": "string"
                                     }
                          ],
                          "total": 0})
get_new_drivers = JSONResponse({"status": True,
                                "message": "Success!",
                                "drivers": [
                                    {
                                        "id": 0,
                                        "surname": "string",
                                        "name": "string",
                                        "photo_path": "string",
                                        "status": "string",
                                        "isActive": True,
                                        "datetime_create": "string-iso"
                                    }
                                ]})


class NewUser(BaseModel):
    phone: str
    password: str
    role: int
    surname: Union[str, None] = None
    name: Union[str, None] = None
    referal_code: Union[str, None] = None
    id_city: Union[List[int], None] = []


class GetPartners(BaseModel):
    search: Union[str, None] = ""
    offset: Union[int, None] = 0
    limit: Union[int, None] = 50


class GetPartner(BaseModel):
    id: int


class GetUser(BaseModel):
    id: int


class GetUsers(BaseModel):
    search: Union[str, None] = ""
    sort: Union[int, None] = 0
    offset: Union[int, None] = 0
    limit: Union[int, None] = 50
    statuses: Union[list, None] = []

