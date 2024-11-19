from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, RootModel, ConfigDict, Field
from typing import Union, List, Dict
from enum import Enum
from datetime import date

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
                                        "phone": "string",
                                        "photo_path": "string",
                                        "request_for_payment": 0.0,
                                        "status": "string",
                                        "isActive": True,
                                        "datetime_create": "string-iso"
                                    }
                                ]})

class Role(int, Enum):
    PARENT = 1
    DRIVER = 2
    OPERATOR = 3
    MANAGER = 4
    PARTNER = 5
    FRANCHISE_ADMIN = 6
    ADMIN = 7




class NewUser(BaseModel):
    phone: str = Field(
        pattern=r"^\+7 \(\d{3}\) \d{3} \d{2} \d{2}$",
        description="Phone format: '+7 (999) 999 99 99'",
    )
    password: str = Field(
        min_length=8,
        description="Password with min 8 characters, containing at least one uppercase letter, one digit, and one special character",
    )
    role: Role
    surname: str = Field(
        min_length=2,
        max_length=50,
        pattern="^[a-zA-Z]+$",
        description="Surname should contain only Latin letters.",
    )
    name: str = Field(
        min_length=2,
        max_length=50,
        pattern="^[a-zA-Z]+$",
        description="Name should contain only Latin letters.",
    )
    referal_code: Union[str, None] = Field(
        min_length=32,
        max_length=32,
        pattern="^[A-Z0-9]+$",
        description="Name should contain only Latin letters.",
    )
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


class Report(RootModel):
    root: Dict[date, int]

    model_config = ConfigDict(json_schema_extra={
        'example': {
            "2024-01-01": 0,
        },
    })


class SuccessGetSalary(BaseModel):
    status: bool = True
    message: str = "Success!"
    salary: Report


class SuccessPostSalary(BaseModel):
    status: bool = True
    message: str = "Success!"
    salary_report_file: str


class SuccessGetUserReport(BaseModel):
    status: bool = True
    message: str = "Success!"
    user_report: Report


class SuccessPostUserReport(BaseModel):
    status: bool = True
    message: str = "Success!"
    user_report_file: str


class City(BaseModel):
    id: int
    title: str


class FranchiseAdmin(BaseModel):
    id: int
    phone: str = Field(
        pattern=r"^\+7 \(\d{3}\) \d{3} \d{2} \d{2}$",
        description="Phone format: '+7 (999) 999 99 99'",
    )
    cities: List[City] | None


class FranchiseAdmins(RootModel):
    root: List[FranchiseAdmin]


class SuccessGetFranchiseAdmins(BaseModel):
    status: bool = True
    message: str = "Success!"
    franchise_admins: FranchiseAdmins