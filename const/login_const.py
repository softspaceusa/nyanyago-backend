from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Union


login_answer = JSONResponse({"status": True,
                             "token": "string",
                             "message": "Success!"}, 200)
password_uncorrect = JSONResponse({"status": False,
                                   "message": "Password uncorrect!"}, 403)
user_not_verify = JSONResponse({"status": False,
                                "message": "User not verify!"}, 405)
forbidden = JSONResponse({"detail": "Forbidden"}, 403)
user_not_found = JSONResponse({"status": False,
                               "message": "User not found!"}, 406)
success_answer = JSONResponse({"status": True,
                               "message": "Success!"}, 200)
uncorrect_phone = JSONResponse({"status": False,
                                     "message": "Phone number uncorrect!"}, 404)
uncorrect_code = JSONResponse({"status": False,
                                     "message": "Code of verify uncorrect!"}, 404)
error_create_user = JSONResponse({"status": False,
                                     "message": "Can't create user!"}, 500)
user_already_creates = JSONResponse({"status": False,
                                     "message": "User with this phone already created!"}, 404)
mobile_authentication_unsuccessful = JSONResponse({"detail": "Mobile Authentication unsuccessful!"}, 404)


class VerifyMobilePhone(BaseModel):
    phone: str


class VerifyCodeMobilePhone(BaseModel):
    phone: str
    code: str


class NewMobileAuthentication(BaseModel):
    code: str


class VerifyResetPassword(BaseModel):
    phone: str
    password: str


class RegistrationParent(BaseModel):
    surname: str
    name: str
    phone: str
    password: str


class LoginApp(BaseModel):
    login: str
    password: str
    fbid: str


class ResetPassword(BaseModel):
    phone: str


class DriverLicense(BaseModel):
    license: str
    receiveCountry: int
    receiveDate: str


class CarData(BaseModel):
    autoMark: int
    autoModel: int
    autoColor: int
    releaseYear: int
    state_number: str
    ctc: str


class DriverAnswers(BaseModel):
    first: str
    second: str
    third: str
    fourth: str
    fifth: str
    sixth: str
    seventh: str


class RegistrationDriver(BaseModel):
    photoUrl: str
    videoUrl: Union[str, None] = None
    surname: str
    name: str
    phone: str
    inn_data: str
    password: str
    city: int
    description: str
    age: int
    refCode: Union[str, None] = None
    driverLicense: Union[DriverLicense, dict]
    carData: Union[CarData, dict]
    answers: Union[DriverAnswers, dict]