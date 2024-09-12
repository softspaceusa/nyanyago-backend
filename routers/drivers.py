import datetime
import traceback

from const.orders_const import get_schedules_responses, schedule_not_found, get_today_schedule, WantSchedule, \
    get_driver_schedules
from defs import get_date_from_datetime, sendPush
from models.authentication_db import UsersBearerToken
from models.orders_db import DataSchedule, DataScheduleOtherParametrs, DataScheduleRoad, DataScheduleRoadAddress, \
    DataScheduleRoadDriver, WaitDataScheduleRoadDriver
from models.users_db import UsersUser, UsersUserPhoto, UsersReferalUser, DataDebitCard, DataUserBalance, \
    HistoryNotification
from models.users_db import DataUserBalanceHistory, HistoryRequestPayment
from const.users_const import debit_card_not_found, insufficient_balance, success_answer
from const.static_data_const import not_user_photo, access_forbidden, DictToModel
from models.drivers_db import UsersDriverData, UsersCar, DataDriverMode
from models.static_data_db import DataColor, DataCarModel, DataCarMark
from fastapi import APIRouter, Request, Depends
from const.dependency import has_access_driver
from const.drivers_const import *
import decimal
import json
import uuid


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


#TODO: сделать проверку доступа только админам, родителям заказа, отклика
@router.post("/get_driver",
             responses=generate_responses([access_forbidden,
                                           driver_not_found,
                                           get_driver]))
async def get_driver_by_id(request: Request, item: GetDriver):
    if request.user != item.id and await UsersDriverData.filter(id_driver=item.id).count()>0:
        return access_forbidden
    if await UsersUser.filter(id=item.id).count() == 0 or await UsersDriverData.filter(id_driver=item.id).count() == 0:
        return driver_not_found

    data = DictToModel(await UsersUser.filter(id=item.id).first().values())
    driver_data = DictToModel(await UsersDriverData.filter(id_driver=item.id).first().values())
    photo = await UsersUserPhoto.filter(id_user=item.id).first().values("photo_path")
    photo = photo["photo_path"] if photo is not None and "photo_path" in photo else not_user_photo
    car_data = DictToModel(await UsersCar.filter(id=driver_data.id_car).first().values())
    car = {"mark": (await DataCarMark.filter(id=car_data.id_car_mark).first().values())["title"],
           "model": (await DataCarModel.filter(id=car_data.id_car_model).first().values())["title"],
           "color": (await DataColor.filter(id=car_data.id_color).first().values())["title"],
           "year": car_data.year_create,
           "state_number": car_data.state_number,
           "ctc": car_data.ctc
           }
    return JSONResponse({"status": True,
                         "message": "Success!",
                         "driver": {
                             "surname": data.surname,
                             "name": data.name,
                             "inn": None if hasattr(driver_data, "inn") is True else driver_data.inn,
                             "photo_path": photo,
                             "video_path": driver_data.video_url,
                             "date_reg": data.datetime_create.isoformat(),
                             "carData": car
                         }})


@router.post("/get-my-referals",
             responses=generate_responses([get_my_referals]))
async def get_driver_referals(request: Request, item: GetDriverReferals):
    count = await UsersReferalUser.filter(id_user=request.user).count()
    data = await UsersReferalUser.filter(id_user=request.user).order_by("-id").offset(item.offset).limit(item.limit).values()
    for driver in data:
        photo = await UsersUserPhoto.filter(id_user=driver["id_user_referal"]).first().values("photo_path")
        photo = photo["photo_path"] if photo is not None and "photo_path" in photo else not_user_photo
        driver["photo_path"] = photo
        driver["name"] = (await UsersUser.filter(id=driver["id"]).first().values())["name"]
        driver["status"] = False
        driver["id"] = driver["id_user_referal"]
        del driver["id_user"]
        del driver["id_user_referal"]
    return JSONResponse({"status": True,
                         "message": "Success!",
                         "total": count,
                         "referals": data})


@router.post("/start-driver-mode",
             dependencies=[Depends(has_access_driver)],
             responses=generate_responses([start_current_drive_mode]))
async def start_driver_mode(request: Request, item: NowLocation):
    await DataDriverMode.filter(id_driver=request.user).delete()
    data = await DataDriverMode.create(id_driver=request.user, latitude=item.latitude, longitude=item.longitude,
                                       websocket_token=str(uuid.uuid4())+str(uuid.uuid4())+str(uuid.uuid4()))
    return JSONResponse({"status": True,
                         "message": "Success!",
                         "driver-token": data.websocket_token})


@router.post("/request-payment",
             dependencies=[Depends(has_access_driver)],
             responses=generate_responses([debit_card_not_found,
                                           insufficient_balance,
                                           success_answer]))
async def send_payment_requests(request: Request, item: SendPaymentRequest):
    if await DataDebitCard.filter(id_user=request.user, id=item.id_card).count() == 0:
        return debit_card_not_found
    if await DataUserBalance.filter(id_user=request.user).count() == 0 or \
            await DataUserBalance.filter(id_user=request.user, money__lte=50).count() > 0:
        return insufficient_balance
    if item.type_request == 1:
        money = await DataUserBalance.filter(id_user=request.user).order_by("-id").first().values()
        if (item.amount is not None and decimal.Decimal(item.amount) > money["money"]) or item.amount <= 0:
            return insufficient_balance
        else:
            item.amount = money["money"]
        await DataUserBalance.filter(id_user=request.user).update(money=money["money"]-decimal.Decimal(item.amount))
        history = await DataUserBalanceHistory.create(id_user=request.user, money=decimal.Decimal(-item.amount),
                                                    isComplete=True, description="Заявка на получение ЗП", id_task=-100)
        await HistoryRequestPayment.filter(id_user=request.user, id_card=item.id_card, id_history=history.id,
                                    money=decimal.Decimal(item.amount), isCashback=False, isSuccess=False, isActive=True)
        return success_answer
    else:
        return success_answer


@router.get("/get_schedules_requests",
             responses=generate_responses([get_schedules_responses,
                                           schedule_not_found,
                                           access_forbidden]))
async def get_schedule(request: Request, limit: Union[int, None] = 30, offset: Union[int, None] = 0):
    schedules = await DataSchedule.filter(isActive=False).limit(limit).offset(offset).all().values\
                       ("id", "id_user", "title", "description", "children_count",
                                                        "id_tariff", "week_days", "duration")
    for schedule in schedules:
        photo = await UsersUserPhoto.filter(id_user=schedule["id"]).first().values()
        schedule["user"] = {
            "id_user": schedule["id_user"],
            "name": (await UsersUser.filter(id=schedule["id_user"]).first().values())["name"],
            "photo_path": not_user_photo if photo is None or len(photo) == 0 else photo["photo_path"]
        }
        schedule["week_days"] = [int(x) for x in schedule["week_days"].split(";")]
        other_parametrs = await DataScheduleOtherParametrs.filter(id_schedule=schedule["id"],
                                                                  isActive=True).order_by("id").all().values()
        other_parametrs_data = []
        for parametr in other_parametrs:
            other_parametrs_data.append({
                "parametr": parametr["id_other_parametr"],
                "count": parametr["amount"]
            })
        schedule["other_parametrs"] = other_parametrs_data
        roads = await DataScheduleRoad.filter(id_schedule=schedule["id"], isActive=True).order_by("id").all().values()
        for road in roads:
            road["type_drive"] = [int(x) for x in road["type_drive"].split(";")]
            addresses = await DataScheduleRoadAddress.filter(id_schedule_road=road["id"]).order_by("id").all().values()
            data_addresses = []
            for address in addresses:
                address_data = {
                                    "from_address": {
                                        "address": address["from_address"],
                                        "location": {
                                            "longitude": address["from_lon"],
                                            "latitude": address["from_lat"]
                                        }
                                    },
                                    "to_address": {
                                        "address": address["to_address"],
                                        "location": {
                                            "longitude": address["to_lon"],
                                            "latitude": address["to_lat"]
                                        }
                                    }
                }
                data_addresses.append(address_data)
            road["addresses"] = data_addresses
            road["salary"] = 0
            del road["id_schedule"]
            del road["isActive"]
            del road["datetime_create"]
        schedule["roads"] = roads
        del schedule["id_user"]
        schedule["all_salary"] = 0
    print(schedules)
    return JSONResponse({"status": True,
                         "message": "Success!",
                         "schedules": schedules}, 200)


@router.get("/get_my_schedules",
             responses=generate_responses([get_driver_schedules,
                                           schedule_not_found,
                                           access_forbidden]))
async def get_my_schedules(request: Request, limit: Union[int, None] = 30, offset: Union[int, None] = 0):
    data = await DataScheduleRoadDriver.filter(id_driver=request.user, isActive=True, isRepeat=True).all().values()
    schedules = await DataScheduleRoadDriver.filter(isActive=True).limit(limit).offset(offset).all().values\
                       ("id", "id_user", "title", "description", "children_count",
                                                        "id_tariff", "week_days", "duration")
    for schedule in schedules:
        photo = await UsersUserPhoto.filter(id_user=schedule["id"]).first().values()
        schedule["user"] = {
            "id_user": schedule["id_user"],
            "name": (await UsersUser.filter(id=schedule["id_user"]).first().values())["name"],
            "photo_path": not_user_photo if photo is None or len(photo) == 0 else photo["photo_path"]
        }
        schedule["week_days"] = [int(x) for x in schedule["week_days"].split(";")]
        other_parametrs = await DataScheduleOtherParametrs.filter(id_schedule=schedule["id"],
                                                                  isActive=True).order_by("id").all().values()
        other_parametrs_data = []
        for parametr in other_parametrs:
            other_parametrs_data.append({
                "parametr": parametr["id_other_parametr"],
                "count": parametr["amount"]
            })
        schedule["other_parametrs"] = other_parametrs_data
        roads = await DataScheduleRoad.filter(id_schedule=schedule["id"], isActive=True).order_by("id").all().values()
        for road in roads:
            road["type_drive"] = [int(x) for x in road["type_drive"].split(";")]
            addresses = await DataScheduleRoadAddress.filter(id_schedule_road=road["id"]).order_by("id").all().values()
            data_addresses = []
            for address in addresses:
                address_data = {
                                    "from_address": {
                                        "address": address["from_address"],
                                        "location": {
                                            "longitude": address["from_lon"],
                                            "latitude": address["from_lat"]
                                        }
                                    },
                                    "to_address": {
                                        "address": address["to_address"],
                                        "location": {
                                            "longitude": address["to_lon"],
                                            "latitude": address["to_lat"]
                                        }
                                    }
                }
                data_addresses.append(address_data)
            road["addresses"] = data_addresses
            road["salary"] = 0
            del road["id_schedule"]
            del road["isActive"]
            del road["datetime_create"]
        schedule["roads"] = roads
        del schedule["id_user"]
        schedule["all_salary"] = 0
    print(schedules)
    return JSONResponse({"status": True,
                         "message": "Success!",
                         "schedules": schedules}, 200)


@router.get("/get_today_schedule",
            responses=generate_responses([get_today_schedule]))
async def get_today_schedule(request: Request):
    all_road = await DataScheduleRoadDriver.filter(id_driver=request.user, isActive=True).all().values()
    result, today = [], int(datetime.datetime.now().date().weekday())
    for each in all_road:
        road = await DataScheduleRoad.filter(id=each["id_schedule_road"]).first().values()
        if int(road["week_day"]) != today:
            continue
        parent = await UsersUser.filter(id=(await DataSchedule.filter(
                                                id=road["id_schedule"]).first().values())["id_user"]).first().values()
        response = {
            "id": road["id"],
            "title": road["title"],
            "parent_name": parent["name"],
            "id_parent": parent["id"],
            "time": road["start_time"] + " - " + road["end_time"],
            "date": await get_date_from_datetime(datetime.datetime.now().date())
        }
        result.append(response)

    return JSONResponse({"status": True,
                         "message": "Success!",
                         "schedule": result})


@router.post("/want_schedule_requests",
             responses=generate_responses([success_answer,
                                           schedule_not_found]))
async def want_schedule_requests(request: Request, item: WantSchedule):
    if await DataSchedule.filter(id=item.id_schedule, isActive=False).count() != 1:
        return schedule_not_found
    schedule, req = await DataSchedule.filter(id=item.id_schedule, isActive=False).first().values(), {}
    for each in item.id_road:
        if await DataScheduleRoad.filter(id_schedule=item.id_schedule, id=each).count() != 1:
            return schedule_not_found
        if await DataScheduleRoadDriver.filter(id_schedule_road=each, isRepeat=True).count() != 0:
            return schedule_not_found
        if await WaitDataScheduleRoadDriver.filter(id_road=each,isActive=None,id_schedule=item.id_schedule).count()!=0:
            return schedule_not_found
    for each in item.id_road:
        req=await WaitDataScheduleRoadDriver.create(id_driver=request.user, id_road=each, id_schedule=item.id_schedule)
    print(schedule["id_user"])
    fbid = await UsersBearerToken.filter(id_user=schedule["id_user"]).order_by("-id").first().values()
    print(fbid)
    try:
        await sendPush(fbid["fbid"], "Получена новая заявка",
                       "По вашему контракту получен новый отклик от водителя",
                       {"action": "order_request", "id_request": req.id})
        await HistoryNotification.create(id_user=schedule["id_user"], title="Получена новая заявка",
                                         description="По вашему контракту получен новый отклик от водителя")
    except Exception:
        print(traceback.format_exc())
    return success_answer
