from models.orders_db import DataDrivingStatus
from models.static_data_db import DataCountry, DataColor, DataCity, DataCarMark, DataCarModel, DataOtherDriveParametr, \
    DataCarTariff
from models.authentication_db import UsersBearerToken
from models.admins_db import AdminMobileSettings
from fastapi import APIRouter, Depends, Request
from const.dependency import has_access
from const.static_data_const import *
import json

from models.users_db import UsersFranchiseUser

router = APIRouter()


def generate_responses(answers: list):
    answer = {}
    for data in answers:
        description = json.loads(data.body.decode('utf-8'))
        if "message" in description:
            description = description["message"]
        elif "detail" in description:
            description = description["detail"]
        else:
            description = "Response"
        answer[data.status_code] = {
                                    "content": {
                                        "application/json": {
                                            "example": json.loads(data.body.decode("utf-8"))
                                        }
                                    },
                                    "description": description
        }
    return answer


@router.get("/country/",
            responses=generate_responses([country]))
async def get_country_data(id: Union[int, None] = None, title: Union[str, None] = None):
    answer = {"status": True, "message": "Success!"}
    if title is None and id is None:
        answer["countries"] = await DataCountry().filter().order_by("id").all().values()
    else:
        answer["countries"] = await DataCountry().filter(id=id).all().values() if id is not None \
                                else await DataCountry().filter(title__icontains=title).order_by("id").all().values()
    return JSONResponse(answer)


@router.get("/color/",
            responses=generate_responses([color]))
async def get_color_data(id: Union[int, None] = None, title: Union[str, None] = None):
    answer = {"status": True, "message": "Success!"}
    if title is None and id is None:
        answer["colors"] = await DataColor().filter().order_by("id").all().values()
    else:
        answer["colors"] = await DataColor().filter(id=id).all().values() if id is not None \
                                else await DataColor().filter(title__icontains=title).order_by("id").all().values()
    return JSONResponse(answer)


@router.get("/city/",
            responses=generate_responses([city]))
async def get_city_data(id: Union[int, None] = None, title: Union[str, None] = None):
    answer = {"status": True, "message": "Success!"}
    if title is None and id is None:
        answer["cities"] = await DataCity().filter().order_by("id").all().values()
    else:
        answer["cities"] = await DataCity().filter(id=id).all().values() if id is not None \
                                else await DataCity().filter(title__icontains=title).order_by("id").all().values()
    return JSONResponse(answer)


@router.get("/car-mark/",
            responses=generate_responses([car_mark]))
async def get_car_mark_data(id: Union[int, None] = None, title: Union[str, None] = None):
    answer = {"status": True, "message": "Success!"}
    if title is None and id is None:
        answer["marks"] = await DataCarMark().filter().order_by("id").all().values()
    else:
        answer["marks"] = await DataCarMark().filter(id=id).all().values() if id is not None \
                                else await DataCarMark().filter(title__icontains=title).order_by("id").all().values()
    return JSONResponse(answer)


@router.get("/car-model/",
            responses=generate_responses([car_model]))
async def get_car_model_data(id: Union[int, None]=None, title: Union[str, None]=None, id_mark: Union[int, None]=None):
    answer = {"status": True, "message": "Success!"}
    if title is None and id is None and id_mark is None:
        models = await DataCarModel().filter().order_by("id").all().values()
    elif id_mark is not None and (id is None and title is None):
        models = await DataCarModel().filter(id_car_mark=id_mark).order_by("-id").all().values()
    elif title is not None and (id is None and id_mark is None):
        models = await DataCarModel().filter(title__icontains=title).order_by("-id").all().values()
    else:
        models = await DataCarModel().filter(id=id).all().values() if id is not None else \
                  await DataCarModel().filter(title__icontains=title, id_car_mark=id_mark).order_by("id").all().values()
    for model in models:
        if model['releaseYear'] is not None: model["title"] = f"{model['title']} ({model['releaseYear']})"
    answer["models"] = models
    return JSONResponse(answer)


@router.post("/get-biometric-settings",
             dependencies=[Depends(has_access)],
             responses=generate_responses([biometric_setting]))
async def get_now_settings_of_biometric_authentication():
    return JSONResponse({"status": True,
                         "message": "Success!",
                         "value": (await AdminMobileSettings.filter().order_by("-id").first().values())["biometry"]})


@router.get("/other-parametrs-of-drive",
            dependencies=[Depends(has_access)],
            responses=generate_responses([drive_params]))
async def get_other_drive_params():
    data = await DataOtherDriveParametr.filter().order_by("id").all().values("id", "title", "amount", "isActive")
    for each in data:
        each["amount"] = float(each["amount"])
    return JSONResponse({"status": True,
                         "message": "Success!",
                         "data": data})


@router.get("/tariffs",
            dependencies=[Depends(has_access)],
            responses=generate_responses([get_tariffs]))
async def get_tariffs(request: Request):
    my_ref = await UsersFranchiseUser.filter(id_user=request.user).first().values()
    data = await DataCarTariff.filter(id_franchise=my_ref["id_franchise"],
                                      isActive=True).order_by("id").all().values("id", "title", "description",
                                                                                 "amount", "photo_path")
    for each in data:
        each["amount"] = float(each["amount"])
        each["isAvailable"] = True
    return JSONResponse({"status": True,
                         "message": "Success!",
                         "tariffs": data})


@router.get("/drive_statuses",
            dependencies=[Depends(has_access)],
            responses=generate_responses([drive_statuses]))
async def get_drive_statuses(request: Request):
    statuses = await DataDrivingStatus.filter().order_by("id").all().values()
    for each in statuses:
        each["title"] = each["status"]
        del each["status"]
    return JSONResponse({"status": True,
                         "message": "Success!",
                         "drive_statuses": statuses})

