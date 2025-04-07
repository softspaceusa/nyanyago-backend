import datetime
import traceback

from const.orders_const import get_schedules_responses, schedule_not_found, \
    get_today_schedule, WantSchedule, \
    get_driver_schedules, DeclineRoads
from defs import get_date_from_datetime, sendPush, get_time_drive
from models.authentication_db import UsersBearerToken
from models.orders_db import DataSchedule, DataScheduleOtherParametrs, DataScheduleRoad, \
    DataScheduleRoadAddress, \
    DataScheduleRoadDriver, WaitDataScheduleRoadDriver, DataOrder
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
                                       websocket_token=str(uuid.uuid4())+str(uuid.uuid4())+str(uuid.uuid4()), isActive=True)
    return JSONResponse({"status": True,
                         "message": "Success!",
                         "driver-token": data.websocket_token})


@router.get("/get_current_order",
            dependencies=[Depends(has_access_driver)],
            responses=generate_responses([get_current_order]))
async def get_current_order(request: Request):
    data = await DataOrder.filter(id_driver=request.user, isActive=True).all().values("id")
    orders = []
    for order in data:
        orders.append(order["id"])
    return JSONResponse({"status": True,
                         "message": "Success!",
                         "orders": orders})


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
    """
    Эндпоинт для получения всех расписаний

    Args:
        request (Request): Объект запроса
        limit (Union[int, None], optional): Количество расписаний. По умолчанию 30.
        offset (Union[int, None], optional): Смещение. По умолчанию к 0.

    Returns:
        JSONResponse: Ответ с расписаниями
    """
    schedules = await DataSchedule.all().limit(limit).offset(offset).values \
        ("id", "id_user", "title", "description", "children_count",
         "id_tariff", "week_days", "duration")
    valid_schedules = []
    for schedule in schedules:
        stop = False  # Флаг - если он True, значит с маршрутами в расписании что-то не так => расписание не выводится
        photo = await UsersUserPhoto.filter(id_user=schedule["id"]).first().values()
        schedule["user"] = {
            "id_user": schedule["id_user"],
            "name": (await UsersUser.filter(id=schedule["id_user"]).first().values())["name"],
            "photo_path": not_user_photo if photo is None or len(photo) == 0 else photo["photo_path"]
        }
        schedule["week_days"] = [int(x) for x in schedule["week_days"].split(";") if x.isdigit()]
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

        all_price = 0
        available_roads = []
        for road in roads:
            try:
                road["type_drive"] = [int(x) for x in road["type_drive"].split(";") if x.isdigit()]
                addresses = await DataScheduleRoadAddress.filter(id_schedule_road=road["id"]).order_by("id").all().values()
                data_addresses = []
                price_road = road.get("amount", -1)
                if await DataScheduleRoadDriver.filter(id_schedule_road=road["id"], isActive=True).count() > 0:  # Если у маршрута уже есть исполнитель
                    continue

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
                road["salary"] = round(float(price_road), 2)
                all_price += price_road

                road.pop("id_schedule", None)
                road.pop("amount", None)
                road.pop("isActive", None)
                road.pop("datetime_create", None)
                available_roads.append(road)
            except Exception as e:
                stop = True
                break
        if stop:  # Если в расписании что-то не так => расписание не выводится
            continue
        if roads is None or len(available_roads) == 0:  # Если в расписании нет маршрутов => расписание не выводится
            continue
        schedule["roads"] = available_roads
        schedule["all_salary"] = round(float(all_price), 2)  # Ensure total salary is float
        del schedule["id_user"]
        valid_schedules.append(schedule)

    return JSONResponse({"status": True,
                         "message": "Success!",
                         "schedules": valid_schedules}, 200)


@router.get("/get_full_roads_info")
async def get_full_roads_info(request: Request,
                              road_ids: str):  # road_ids как строка вида "1,2,3"
    """
    Эндпоинт для получения информации о конкретных дорогах и их расписаниях

    Example:

        Пример выходных данных:

        {
          "status": true,
          "message": "Success!",
          "schedules": [
            {
              "id": 19,
              "title": "тест",
              "description": "",
              "children_count": 4,
              "id_tariff": 3,
              "week_days": [
                1
              ],
              "duration": 7,
              "user": {
                "id_user": 21,
                "name": "Максим",
                "photo_path": "https://nyanyago.ru/api/v1.0/files/not_user_photo.png"
              },
              "other_parametrs": [],
              "roads": [
                {
                  "id": 43,
                  "type_drive": [
                    0
                  ],
                  "start_time": "19:15",
                  "end_time": "22:15",
                  "week_day": 5,
                  "title": "нг",
                  "addresses": [
                    {
                      "from_address": {
                        "address": "Россия",
                        "location": {
                          "longitude": 105.31875610351562,
                          "latitude": 61.524009704589844
                        }
                      },
                      "to_address": {
                        "address": "Россия",
                        "location": {
                          "longitude": 105.31875610351562,
                          "latitude": 61.524009704589844
                        }
                      }
                    }
                  ],
                  "salary": 355.35
                },
                {
                  "id": 45,
                  "type_drive": [
                    0
                  ],
                  "start_time": "05:00",
                  "end_time": "10:00",
                  "week_day": 1,
                  "title": "в лес",
                  "addresses": [
                    {
                      "from_address": {
                        "address": "Лесной, Свердловская обл., Россия",
                        "location": {
                          "longitude": 59.790401458740234,
                          "latitude": 58.63566589355469
                        }
                      },
                      "to_address": {
                        "address": "Плёс, Ивановская обл., Россия",
                        "location": {
                          "longitude": 41.512271881103516,
                          "latitude": 57.46049499511719
                        }
                      }
                    }
                  ],
                  "salary": 150
                }
              ],
              "all_salary": 505.35
            }
          ]
        }

    Args:
        request (Request): Объект запроса
        road_ids (str): Строка с ID дорог, разделенных запятыми (например, "1,2,3")

    Returns:
        JSONResponse: Ответ с информацией о дорогах и их расписаниях
    """
    try:
        # Преобразуем строку road_ids в список целых чисел
        road_id_list = [int(x) for x in road_ids.split(",") if x.isdigit()]
        if not road_id_list:
            return JSONResponse(
                {"status": False, "message": "No valid road IDs provided"}, 400)

        # Получаем все дороги по указанным ID (без фильтра isActive)
        roads = await DataScheduleRoad.filter(id__in=road_id_list).order_by(
            "id").all().values()
        if not roads:
            return JSONResponse({"status": False, "message": "No roads found"}, 404)

        valid_schedules = {}
        # Группируем дороги по расписаниям
        for road in roads:
            schedule_id = road["id_schedule"]
            if schedule_id not in valid_schedules:
                # Получаем данные расписания
                schedule = await DataSchedule.filter(id=schedule_id).first().values(
                    "id", "id_user", "title", "description", "children_count",
                    "id_tariff", "week_days", "duration"
                )
                if not schedule:
                    schedule = {
                        "id": schedule_id,
                        "title": "Unknown schedule",
                        "description": "No description",
                        "children_count": 0,
                        "id_tariff": None,
                        "week_days": "1",
                        "duration": 0
                    }

                # Добавляем информацию о пользователе
                photo = await UsersUserPhoto.filter(
                    id_user=schedule["id"]).first().values()
                user_data = await UsersUser.filter(
                    id=schedule["id_user"]).first().values() if schedule.get(
                    "id_user") else None
                schedule["user"] = {
                    "id_user": schedule.get("id_user", 0),
                    "name": user_data["name"] if user_data else "Unknown user",
                    "photo_path": not_user_photo if photo is None or len(
                        photo) == 0 else photo.get("photo_path", not_user_photo)
                }
                schedule["week_days"] = [int(x) for x in
                                         schedule["week_days"].split(";") if
                                         x.isdigit()] if schedule["week_days"] else [1]

                # Получаем дополнительные параметры
                other_parametrs = await DataScheduleOtherParametrs.filter(
                    id_schedule=schedule_id, isActive=True
                ).order_by("id").all().values()
                schedule["other_parametrs"] = [{
                    "parametr": parametr["id_other_parametr"] if parametr.get(
                        "id_other_parametr") else 0,
                    "count": parametr["amount"] if parametr.get(
                        "amount") is not None else 0
                } for parametr in other_parametrs] if other_parametrs else []

                schedule["roads"] = []
                valid_schedules[schedule_id] = schedule

            # Обрабатываем данные дороги (в случае ошибки - отправляем моковые данные) (TODO)
            road_data = dict()
            road_data["id"] = road["id"]
            road_data["type_drive"] = [int(x) for x in road["type_drive"].split(";") if
                                       x.isdigit()] if road.get("type_drive") else [0]
            road_data["start_time"] = road["start_time"] if road.get("start_time", 0) is not None else 0
            road_data["end_time"] = road["end_time"] if road.get("end_time", 0) is not None else 0
            road_data["week_day"] = road["week_day"] if road.get("week_day", -1) is not None else -1
            road_data["title"] = road["title"] if road.get("title") else "Unknown road"


            # Получаем адреса
            addresses = await DataScheduleRoadAddress.filter(
                id_schedule_road=road["id"]
            ).order_by("id").all().values()
            data_addresses = []
            for address in addresses:
                address_data = {
                    "from_address": {
                        "address": address["from_address"] if address.get(
                            "from_address") else "Unknown from address",
                        "location": {
                            "longitude": address["from_lon"] if address.get(
                                "from_lon") is not None else 0.0,
                            "latitude": address["from_lat"] if address.get(
                                "from_lat") is not None else 0.0
                        }
                    },
                    "to_address": {
                        "address": address["to_address"] if address.get(
                            "to_address") else "Unknown to address",
                        "location": {
                            "longitude": address["to_lon"] if address.get(
                                "to_lon") is not None else 0.0,
                            "latitude": address["to_lat"] if address.get(
                                "to_lat") is not None else 0.0
                        }
                    }
                }
                data_addresses.append(address_data)
            road_data["addresses"] = data_addresses if data_addresses else [{
                "from_address": {"address": "Unknown",
                                 "location": {"longitude": 0.0, "latitude": 0.0}},
                "to_address": {"address": "Unknown",
                               "location": {"longitude": 0.0, "latitude": 0.0}}
            }]

            price_road = road.get("amount")
            road_data["salary"] = round(float(price_road),
                                        2) if price_road is not None else 0.0
            valid_schedules[schedule_id]["roads"].append(road_data)

        # Финальная обработка и подсчет общей стоимости
        result_schedules = []
        for schedule in valid_schedules.values():
            all_price = sum(road["salary"] for road in schedule["roads"])
            schedule["all_salary"] = round(float(all_price), 2)
            del schedule["id_user"]
            result_schedules.append(schedule)

        return JSONResponse({
            "status": True,
            "message": "Success!",
            "schedules": result_schedules
        }, 200)

    except ValueError:
        return JSONResponse({"status": False, "message": "Invalid road_ids format"},
                            400)
    except Exception as e:
        return JSONResponse({"status": False, "message": f"Error: {str(e)}"}, 500)


@router.get("/get_my_schedules",
             responses=generate_responses([get_driver_schedules,
                                           schedule_not_found,
                                           access_forbidden]))
async def get_my_schedules(request: Request, limit: Union[int, None] = 30, offset: Union[int, None] = 0):
    # TODO: Это не должно работать... См. get_driver_roads
    data = await DataScheduleRoadDriver.filter(id_driver=request.user, isActive=True, isRepeat=True).all().values()
    schedules = await DataScheduleRoadDriver.filter(isActive=True).limit(limit).offset(offset).all().values\
                       ("id", "id_user", "title", "description", "children_count",
                                                        "id_tariff", "week_days", "duration")  # Нет таких данных в `DataScheduleRoadDriver`
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


@router.get("/get_driver_roads")
async def get_driver_roads(request: Request, limit: Union[int, None] = 30, offset: Union[int, None] = 0):
    data = await DataScheduleRoadDriver.filter(id_driver=request.user, isActive=True).limit(limit).offset(offset).all().values()
    return JSONResponse({"status": True,
                         "message": "Success!",
                         "roads_id": [x["id_schedule_road"] for x in data]}, 200)


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


@router.post(
    "/want_schedule_requests",
    responses=generate_responses([success_answer, schedule_not_found]),
)
async def want_schedule_requests(request: Request, item: WantSchedule):
    """
    Эндпоинт для отправки заявки на принятие маршрутов в расписании/контракте.
    В дальнейшем - клиент должен подтвердить (или отклонить) эту заявку с помощью
    `/orders/answer_schedule_responses`.

    Пример запроса:
        {
            "id_schedule": 1,
            "id_road": [1, 2, 3]
        }

    Args:
        request (Request): Объект запроса.
        item (WantSchedule): Объект с данными для отправки заявки.

    Returns:
        JSONResponse: Ответ в формате JSON.
    """
    if await DataSchedule.filter(id=item.id_schedule).count() != 1:
        return schedule_not_found
    schedule, req = (
        await DataSchedule.filter(id=item.id_schedule).first().values(),
        {},
    )
    for each in item.id_road:
        if (
            await DataScheduleRoad.filter(id_schedule=item.id_schedule, id=each).count()
            != 1
        ):
            return JSONResponse(
                {
                    "status": False,
                    "message": "Some of the roads do not belong to this schedule!",
                },
                404,
            )
        if (
            await DataScheduleRoadDriver.filter(
                id_schedule_road=each,
                isActive=True
            ).count()
            != 0
        ):
            return JSONResponse(
                {"status": False, "message": "Some of the roads already have drivers!"},
                404,
            )
        if await WaitDataScheduleRoadDriver.filter(id_road=each, id_driver=request.user, isActive__not=True).count() != 0:
            return JSONResponse(
                {"status": False, "message": "Some of the roads already accepted/declined"},
                404,
            )
    requests = []
    for each in item.id_road:
        req, _ = await WaitDataScheduleRoadDriver.get_or_create(
            id_driver=request.user, id_road=each, id_schedule=item.id_schedule, isActive=True
        )
        requests.append(
            {
                "id": req.id,
                "id_schedule": item.id_schedule,
                "id_road": each,
                "isActive": req.isActive,
            }
        )
    print(schedule["id_user"])
    fbid = (
        await UsersBearerToken.filter(id_user=schedule["id_user"])
        .order_by("-id")
        .first()
        .values()
    )
    print(fbid)
    try:
        await sendPush(
            fbid["fbid"],
            "Получена новая заявка",
            "По вашему контракту получен новый отклик от водителя",
            {"action": "order_request", "id_request": str([r["id"] for r in requests])},
        )
        await HistoryNotification.create(
            id_user=schedule["id_user"],
            title="Получена новая заявка",
            description="По вашему контракту получен новый отклик от водителя",
        )
    except Exception:
        print(traceback.format_exc())

    schedule = (
        await DataSchedule.filter(id=item.id_schedule).first().values()
    )
    schedule.pop("datetime_create", None)
    roads = []
    for each in item.id_road:
        road = await DataScheduleRoad.filter(id=each).first().values()
        road.pop("datetime_create", None)
        road["amount"] = round(float(road.get("amount", 0)), 2)
        roads.append(road)
    return JSONResponse(
        {
            "status": True,
            "message": "Success!",
            "schedule": schedule,
            "roads": roads,
            "requests": requests,
        },
        200,
    )


@router.post("/decline_roads_requests",)
async def decline_roads_requests(request: Request, item: DeclineRoads):
    """
    Эндпоинт для отказа водителем от маршрутов в расписании/контракте.

    Пример запроса:
        {
            "id_road": [1, 2, 3]
        }

    Args:
        request (Request): Объект запроса.
        item (WantSchedule): Объект с данными (id_road: List).

    Returns:
        JSONResponse: Ответ в формате JSON. Может быть сообщение об ошибке ("You do not have access to this road").
    """
    for each in item.id_road:
        if await DataScheduleRoadDriver.filter(id_schedule_road=each, id_driver=request.user).count() == 0:
            return JSONResponse({"status": False, "message": "You do not have access to this road"}, 404)
        await DataScheduleRoadDriver.filter(id_schedule_road=each, id_driver=request.user).update(isActive=False)

    return JSONResponse({"status": True, "message": "Success!"}, 200)
