import datetime
import math
from decimal import Decimal

import pytz
from tortoise.exceptions import DoesNotExist

from const.const import success_answer
from const.cost_formulas import get_total_cost_of_the_trip
from const.dependency import has_access_parent, has_access_franchise
from const.login_const import forbidden
from models.chats_db import ChatsChatParticipant, ChatsChat
from models.drivers_db import UsersDriverData, UsersCar, DataDriverMode
from models.static_data_db import DataCarTariff, DataOtherDriveParametr, DataCarMark, DataCarModel, DataColor
from const.orders_const import CurrentDrive, you_have_active_drive, start_current_drive, \
    NewSchedule, get_schedule, \
    schedule_not_found, tariff_by_id_not_found, get_schedules, Road, UpdateRoad, \
    get_schedule_road, \
    get_schedule_responses, AnswerResponse, get_onetime_prices, get_orders, \
    OneTimeOrder, GetTotalPrice, get_total_price, UpdateSchedule
from const.static_data_const import access_forbidden, DictToModel, not_user_photo
from models.users_db import UsersUser, UsersUserPhoto, HistoryNotification, \
    UsersFranchiseUser, DataUserBalance, DataUserBalanceHistory
from models.authentication_db import UsersUserAccount, UsersBearerToken
from fastapi import APIRouter, Request, Depends, HTTPException
from defs import check_access_schedule, sendPush, get_time_drive, get_order_data
from models.orders_db import *
from const.drivers_const import *
import uuid
import json

from sevice.google_maps_api import get_lat_lon, get_distance_and_duration

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


@router.put("/schedule")
async def update_schedule(request: Request, item: UpdateSchedule):
    """
    Обновляет расписание. Во входных данных обязателен только id.

    Args:
        request (Request): Запрос
        item (UpdateSchedule): Данные

    Example:

        Пример входных данных:

            {
              "id": 33,
              "title": "test_change_sch",
              "description": "test_change_sch_des",
              "duration": 7,
              "children_count": 3,
              "id_tariff": 1
            }

    Returns:
        JSONResponse: Ответ
    """
    if await DataCarTariff.filter(isActive=True, id=item.id_tariff).count() == 0:
        return tariff_by_id_not_found
    schedule = await DataSchedule.filter(id=item.id, id_user=request.user).first()
    if schedule is None:
        return schedule_not_found
    if item.title is not None and len(item.title) > 0:
        await DataSchedule.filter(id=item.id).update(title=item.title)
    if item.description is not None and len(item.description) > 0:
        await DataSchedule.filter(id=item.id).update(description=item.description)
    if item.duration is not None and len(str(item.duration)) > 0:
        await DataSchedule.filter(id=item.id).update(duration=item.duration)
    if item.children_count is not None and len(str(item.children_count)) > 0:
        await DataSchedule.filter(id=item.id).update(children_count=item.children_count)
    if item.week_days is not None and len(item.week_days) > 0:
        await DataSchedule.filter(id=item.id).update(
            week_days=";".join(map(str, item.week_days))
        )
    if item.id_tariff is not None and len(str(item.id_tariff)) > 0:
        await DataSchedule.filter(id=item.id).update(id_tariff=item.id_tariff)

    if item.other_parametrs is not None and len(item.other_parametrs) > 0:
        for params in item.other_parametrs:
            if (
                await DataOtherDriveParametr.filter(
                    id=params.parametr, isActive=True
                ).count()
                == 0
            ):
                continue

            if (
                await DataScheduleOtherParametrs.filter(
                    id_schedule=schedule.id, id_other_parametr=params.parametr
                ).count()
                > 0
            ):
                await DataScheduleOtherParametrs.filter(
                    id_schedule=schedule.id, id_other_parametr=params.parametr
                ).update(amount=params.count)
                continue

            await DataScheduleOtherParametrs.create(
                id_schedule=schedule.id,
                id_other_parametr=params.parametr,
                amount=params.count,
            )

    return success_answer



@router.post(
    "/schedule", responses=generate_responses([success_answer, tariff_by_id_not_found])
)
async def create_schedule(request: Request, item: NewSchedule):
    """
    Создаёт график/расписание/контракт, а также его маршруты.

    Args:
        request (Request): Запрос.
        item (NewSchedule): График/расписание/контракт.

    Examples:

        Пример входных данных:

            {
              "title": "test_create_sch1",
              "description": "test_create_sch1",
              "duration": 7,
              "children_count": 1,
              "week_days": [
                "1"
              ],
              "id_tariff": 1,
              "other_parametrs": [],
              "roads": [
                {
                  "week_day": 1,
                  "start_time": "11:11",
                  "end_time": "12:12",
                  "addresses": [
                    {
                      "from_address": {
                        "address": "Метро Красные Ворота, Москва",
                        "location": {
                          "latitude": 0,
                          "longitude": 0
                        }
                      },
                      "to_address": {
                        "address": "Останкинская телебашня, Москва",
                        "location": {
                          "latitude": 0,
                          "longitude": 0
                        }
                      }
                    }
                  ],
                  "title": "road_for_test_sch1",
                  "type_drive": [
                    "0"
                  ]
                }
              ]
            }

    Returns:
        JSONResponse: Ответ.
    """
    print(item.__dict__)
    # TODO: Проверка на достаточный баланс для создания графика
    if await DataCarTariff.filter(isActive=True, id=item.id_tariff).count() == 0:
        return tariff_by_id_not_found
    schedule = await DataSchedule.create(
        id_user=request.user,
        title=item.title,
        children_count=item.children_count,
        duration=item.duration,
        id_tariff=item.id_tariff,
        description=item.description,
        week_days=";".join(map(str, item.week_days)),
        # isActive=True,
    )
    for params in item.other_parametrs:
        if (
            await DataOtherDriveParametr.filter(
                id=params.parametr, isActive=True
            ).count()
            == 0
        ):
            continue
        await DataScheduleOtherParametrs.create(
            id_schedule=schedule.id,
            id_other_parametr=params.parametr,
            amount=params.count,
        )

    all_roads = []

    for road in item.roads:
        new_road = await DataScheduleRoad.create(
            id_schedule=schedule.id,
            week_day=road.week_day,
            title=road.title,
            start_time=road.start_time,
            end_time=road.end_time,
            type_drive=";".join(map(str, road.type_drive)),
        )

        tariff_amount_dict: dict = (
            await DataCarTariff.filter(id=item.id_tariff).first().values("amount")
        )

        if not tariff_amount_dict:
            return JSONResponse({"status": False, "message": "Tariff not found!"}, 404)

        tariff_amount: int = tariff_amount_dict["amount"]

        total_price: float = 0.0  # Общая стоимость поездки

        all_addresses = []

        for address in road.addresses:
            from_lat, from_lon = (
                address.from_address.location.latitude,
                address.from_address.location.longitude,
            )
            to_lat, to_lon = (
                address.to_address.location.latitude,
                address.to_address.location.longitude,
            )
            if (
                address.from_address.location.longitude == 0
                and address.from_address.location.latitude == 0
            ):
                from_lat, from_lon = await get_lat_lon(address.from_address.address)
            if (
                address.to_address.location.longitude == 0
                and address.to_address.location.latitude == 0
            ):
                to_lat, to_lon = await get_lat_lon(address.to_address.address)

            distance, duration = await get_distance_and_duration(
                from_address={"lat": from_lat, "lng": from_lon},
                to_address={"lat": to_lat, "lng": to_lon},
            )

            total_price += get_total_cost_of_the_trip(
                M=tariff_amount, S2=distance, To=duration
            )

            all_addresses.append(
                {
                    "from_address": address.from_address.address,
                    "to_address": address.to_address.address,
                    "from_lat": from_lat,
                    "from_lon": from_lon,
                    "to_lat": to_lat,
                    "to_lon": to_lon,
                }
            )

            await DataScheduleRoadAddress.create(
                id_schedule_road=new_road.id,
                from_address=address.from_address.address,
                to_address=address.to_address.address,
                from_lon=from_lon,
                from_lat=from_lat,
                to_lon=to_lon,
                to_lat=to_lat,
            )

        if 1 in list(map(int, road.type_drive)):
            total_price *= 2

        await DataScheduleRoad.filter(id=new_road.id).update(amount=total_price)

        total_price_from_db = (
            await DataScheduleRoad.filter(id=new_road.id).first().values("amount")
        )

        total_price_from_db = str(total_price_from_db["amount"])

        all_roads.append(
            {
                "id": new_road.id,
                "title": road.title,
                "week_day": road.week_day,
                "start_time": road.start_time,
                "end_time": road.end_time,
                "type_drive": ";".join(map(str, road.type_drive)),
                "addresses": all_addresses,
                "price": total_price_from_db,
            }
        )

    return JSONResponse(
        {
            "status": True,
            "message": "Success!",
            "created_schedule": {
                "id_user": request.user,
                "title": item.title,
                "children_count": item.children_count,
                "duration": item.duration,
                "id_tariff": item.id_tariff,
                "description": item.description,
                "week_days": ";".join(map(str, item.week_days)),
                "all_roads": all_roads,
            },
        },
        200,
    )


@router.get("/schedule/{id}",
             responses=generate_responses([get_schedule,
                                           schedule_not_found,
                                           access_forbidden]))
async def get_schedule(request: Request, id: int):
    #TODO: Проверка на доступ админам и водителям по этому графику/заявкам
    if await DataSchedule.filter(id=id, isActive=None).count() > 0:
        return schedule_not_found
    schedule = await DataSchedule.filter(id=id).first().values("id", "children_count", "id_tariff", "title",
                                                               "description", "week_days", "duration", "id_user")
    if schedule is None or "id_user" not in schedule:
        return schedule_not_found
    if await check_access_schedule(request.user, schedule["id_user"]) is False:
        return access_forbidden
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
    tariff = (await DataCarTariff.filter(id=schedule["id_tariff"]).first().values())["amount"]
    all_price = 0
    roads = await DataScheduleRoad.filter(id_schedule=schedule["id"], isActive=True).order_by("id").all().values()
    for road in roads:
        road["type_drive"] = [int(x) for x in road["type_drive"].split(";")]
        addresses = await DataScheduleRoadAddress.filter(id_schedule_road=road["id"]).order_by("id").all().values()
        data_addresses = []
        price_road = 0
        for address in addresses:
            info, _ = await get_time_drive(address["from_lat"], address["from_lon"],
                                               address["to_lat"], address["to_lon"], tariff)
            price_road += info
            all_price += price_road
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
        road["amount"] = price_road
        road["addresses"] = data_addresses
        del road["id_schedule"]
        del road["isActive"]
        del road["datetime_create"]
    schedule["roads"] = roads
    schedule["amount"] = all_price
    return JSONResponse({"status": True,
                         "message": "Success!",
                         "schedule": schedule}, 200)


@router.get(
    "/schedules",
    responses=generate_responses([get_schedules, schedule_not_found, access_forbidden]),
)
async def get_schedule(request: Request):
    """
    Возвращает все графики/расписания текущего пользователя.

    Args:
        request (Request): Объект запроса

    Returns:
        JSONResponse: Ответ в формате JSON

    Example:

        Пример успешного ответа:

            {
              "status": true,
              "message": "Success!",
              "schedules": [
                {
                  "id": 34,
                  "title": "По кайфу",
                  "description": "",
                  "children_count": 1,
                  "id_tariff": 2,
                  "week_days": [
                    0,
                    2,
                    3,
                    5
                  ],
                  "duration": 365,
                  "id_user": 21,
                  "isActive": true,
                  "datetime_create": "2025-01-17 16:26:09.763770+00:00",
                  "other_parametrs": [
                    {
                      "parametr": 1,
                      "count": 1
                    },
                    {
                      "parametr": 2,
                      "count": 1
                    }
                  ],
                  "roads": [
                    {
                      "id": 82,
                      "week_day": 5,
                      "title": "паывпы",
                      "start_time": "09:45",
                      "end_time": "12:45",
                      "type_drive": [
                        0
                      ],
                      "amount": 56802.81,
                      "addresses": [
                        {
                          "from_address": {
                            "address": "Москва, Россия",
                            "location": {
                              "longitude": 37.6172981262207,
                              "latitude": 55.75582504272461
                            }
                          },
                          "to_address": {
                            "address": "Санкт-Петербург, Россия",
                            "location": {
                              "longitude": 30.360910415649414,
                              "latitude": 59.93105697631836
                            }
                          }
                        }
                      ]
                    }
                  ],
                  "amount": 56802.81
                }
              ]
            }
    """

    schedules = (
        await DataSchedule.filter(id_user=request.user, isActive__in=[True, False])
        .all()
        .values(
            "id",
            "title",
            "description",
            "children_count",
            "id_tariff",
            "week_days",
            "duration",
            "id_user",
            "isActive",
            "datetime_create",
        )
    )
    for schedule in schedules:
        week_days_raw = schedule.get("week_days", "")
        if week_days_raw:
            schedule["week_days"] = [
                int(x) for x in week_days_raw.split(";") if x.isdigit()
            ]
        else:
            schedule["week_days"] = []

        schedule["datetime_create"] = (
            str(schedule["datetime_create"]) if schedule["datetime_create"] else None
        )

        other_parametrs = (
            await DataScheduleOtherParametrs.filter(
                id_schedule=schedule["id"], isActive=True
            )
            .order_by("id")
            .all()
            .values()
        )

        other_parametrs_data = []
        for parametr in other_parametrs:
            other_parametrs_data.append(
                {"parametr": parametr["id_other_parametr"], "count": parametr["amount"]}
            )
        schedule["other_parametrs"] = other_parametrs_data

        all_price = 0
        roads = (
            await DataScheduleRoad.filter(id_schedule=schedule["id"], isActive=True)
            .order_by("id")
            .all()
            .values()
        )

        for road in roads:
            type_drive_raw = road.get("type_drive", "")
            if type_drive_raw:
                road["type_drive"] = [
                    int(x) for x in type_drive_raw.split(";") if x.isdigit()
                ]
            else:
                road["type_drive"] = []

            addresses = (
                await DataScheduleRoadAddress.filter(id_schedule_road=road["id"])
                .order_by("id")
                .all()
                .values()
            )

            price_road = road.get("amount", -1)
            all_price += price_road
            data_addresses = []
            for address in addresses:
                from_lat = address.get("from_lat")
                from_lon = address.get("from_lon")
                to_lat = address.get("to_lat")
                to_lon = address.get("to_lon")

                address_data = {
                    "from_address": {
                        "address": address["from_address"],
                        "location": {"longitude": from_lon, "latitude": from_lat},
                    },
                    "to_address": {
                        "address": address["to_address"],
                        "location": {"longitude": to_lon, "latitude": to_lat},
                    },
                }
                data_addresses.append(address_data)

            road["amount"] = round(float(price_road), 2)
            road["addresses"] = data_addresses

            road.pop("id_schedule", None)
            road.pop("isActive", None)
            road.pop("datetime_create", None)

        schedule["roads"] = roads
        schedule["amount"] = round(float(all_price), 2)

    return JSONResponse(
        {"status": True, "message": "Success!", "schedules": schedules}, 200
    )


@router.delete(
    "/schedule/{id}",
    responses=generate_responses(
        [success_answer, schedule_not_found, access_forbidden]
    ),
    dependencies=[Depends(has_access_parent)],
)
async def delete_schedule(request: Request, id: int):
    """
    Удаляет расписание с данным ID. Если в расписании есть маршруты, до начала которых
    меньше получаса - возвращает 202 код, и сумму, которая будет списана
    (половина от стоимости этого маршрута).

    Args:
        request (Request): Объект запроса
        id (int): ID расписания

    Returns:
        JSONResponse: JSON-ответ
    """

    if await DataSchedule.filter(id=id).count() == 0:
        return schedule_not_found
    if (
        await DataSchedule.filter(
            id=id, isActive__in=[True, False], id_user=request.user
        ).count()
        == 0
    ):
        return access_forbidden

    roads = await DataScheduleRoad.filter(id_schedule=id).all()

    london_now = datetime.datetime.now(pytz.timezone("Europe/London"))
    current_week_day = london_now.weekday()

    for road in roads:
        target_time_str = road.start_time  # 'HH:MM'
        target_week_day_str = (
            road.week_day
        )  # '0'-'6' (0 - Понедельник, 6 - Воскресенье)

        # Преобразуем start_time в datetime с текущей датой
        target_time = datetime.datetime.strptime(target_time_str, "%H:%M").time()
        target_week_day = int(target_week_day_str)

        # Определяем, на сколько дней вперед запланирована поездка
        days_difference = (target_week_day - current_week_day) % 7

        # Создаем datetime для поездки с правильным днем недели
        target_datetime = london_now + datetime.timedelta(days=days_difference)
        target_datetime = target_datetime.replace(
            hour=target_time.hour, minute=target_time.minute, second=0, microsecond=0
        )

        # Если поездка на следующий день
        if target_week_day != current_week_day:
            # Определяем разницу дней (учитываем переход через неделю)
            days_difference = (target_week_day - current_week_day) % 7

            # Если поездка "в ближайшие 24 часа", добавляем день к времени
            if days_difference == 1 and london_now.time() > target_time:
                target_datetime += datetime.timedelta(days=1)

        # Считаем разницу во времени
        time_difference = target_datetime - london_now

        # Проверка на интервал в 30 минут
        if (
            datetime.timedelta(minutes=0)
            <= time_difference
            <= datetime.timedelta(minutes=30)
        ):
            debit_amount_data = (
                await DataScheduleRoad.filter(id=road.id).first().values("amount")
            )
            debit_amount = float(debit_amount_data["amount"]) / 2
            debit_amount = math.floor(debit_amount * 100) / 100
            return JSONResponse(
                {
                    "status": False,
                    "message": "До одной из поездок в маршруте осталось менее 30 минут."
                    "Для удаления - отправьте запрос на /schedule_cancel_with_debit/{id}"
                    "С query-параметром debit_amount (сумма, которая будет списана)",
                    "debit_amount": debit_amount,
                },
                202,
            )

    await DataSchedule.filter(id=id).update(isActive=None)
    return success_answer


@router.delete(
    "/schedule_cancel_with_debit/{id}",
    responses=generate_responses(
        [success_answer, schedule_not_found, access_forbidden]
    ),
    dependencies=[Depends(has_access_parent)],
)
async def delete_schedule(request: Request, id: int, debit_amount: float):
    """
    Удаляет расписание и списывает деньги.

    Args:
        request (Request): Объект запроса
        id (int): ID расписания
        debit_amount (float): Сумма, которая будет списана

    Returns:
        JSONResponse: JSON-ответ
    """

    if await DataSchedule.filter(id=id).count() == 0:
        return schedule_not_found
    if (
        await DataSchedule.filter(
            id=id, isActive__in=[True, False], id_user=request.user
        ).count()
        == 0
    ):
        return access_forbidden

    user_balance_data = (
        await DataUserBalance.filter(id_user=request.user).first().values()
    )
    if user_balance_data is None:
        return JSONResponse(
            {"status": False, "message": "User balance not found!"}, 404
        )
    user_balance = float(user_balance_data["money"])
    if user_balance < debit_amount:
        return JSONResponse({"status": False, "message": "Insufficient balance"}, 409)

    money = round(user_balance - debit_amount, 2)
    if money < -0.01:
        return JSONResponse({"status": False, "message": "Insufficient balance"}, 409)
    if money < 0:
        money = 0
    await DataUserBalance.filter(id_user=request.user).update(money=money)
    await DataUserBalanceHistory.create(
        id_user=request.user,
        id_task=-4,
        description="Списание половины стоимости заказа (из-за отмены)",
        money=-debit_amount,
        isComplete=False,
    )
    await DataSchedule.filter(id=id).update(isActive=None)
    return success_answer


@router.delete(
    "/schedule_road/{id}",
    responses=generate_responses(
        [success_answer, schedule_not_found, access_forbidden]
    ),
    dependencies=[Depends(has_access_parent)],
)
async def delete_schedule_road(request: Request, id: int):
    """
    Удаляет маршрут с данным ID из расписания/графика/контракта (заодно делая связь
    маршрут-водитель неактивной)

    Args:
        request (Request): Объект запроса
        id (int): ID маршрута

    Returns:
        JSONResponse: Ответ в формате JSON
    """

    if await DataScheduleRoad.filter(id=id, isActive=True).count() == 0:
        return schedule_not_found
    road = await DataScheduleRoad.filter(id=id).first().values()
    if (
        await DataSchedule.filter(
            id_user=request.user, id=road["id_schedule"], isActive__in=[True, False]
        ).count()
        == 0
    ):
        return access_forbidden
    await DataScheduleRoad.filter(id=id, isActive=True).update(isActive=False)
    await DataScheduleRoadDriver.filter(id_schedule_road=id, isActive=True).update(
        isActive=False
    )
    return success_answer


@router.post("/schedule_road/{id}",
             responses=generate_responses([success_answer,
                                           schedule_not_found]))
async def create_schedule_road(request: Request, id: int, item: Road):
    if await DataSchedule.filter(id=id, id_user=request.user, isActive__in=[True, False]).count() == 0:
        print((await DataSchedule.filter(id=id, id_user=request.user, isActive__not=None).count()))
        print((await DataSchedule.filter(id=id, id_user=request.user, isActive__in=[True, False]).count()))
        print(id)
        print(request.user)
        print(item.__dict__)
        return schedule_not_found
    new_road=await DataScheduleRoad.create(id_schedule=id, week_day=item.week_day,
                                           title=item.title, start_time=item.start_time,
                                           end_time=item.end_time, type_drive=";".join(map(str, item.type_drive)))

    id_tariff_data = await DataSchedule.filter(id=id).first().values("id_tariff")
    if id_tariff_data:
        id_tariff = id_tariff_data["id_tariff"]
    else:
        return JSONResponse({"status": False, "message": "Tariff for schedule not found!"}, 404)

    tariff_amount_dict: dict = (
        await DataCarTariff.filter(id=id_tariff).first().values("amount")
    )

    if not tariff_amount_dict:
        return JSONResponse({"status": False, "message": "Tariff not found!"}, 404)

    tariff_amount: int = tariff_amount_dict["amount"]

    total_price: float = 0.0  # Общая стоимость поездки

    all_addresses = []

    for address in item.addresses:
        from_lat, from_lon = (
            address.from_address.location.latitude,
            address.from_address.location.longitude,
        )
        to_lat, to_lon = (
            address.to_address.location.latitude,
            address.to_address.location.longitude,
        )
        if (
            address.from_address.location.longitude == 0
            and address.from_address.location.latitude == 0
        ):
            from_lat, from_lon = await get_lat_lon(address.from_address.address)
        if (
            address.to_address.location.longitude == 0
            and address.to_address.location.latitude == 0
        ):
            to_lat, to_lon = await get_lat_lon(address.to_address.address)

        distance, duration = await get_distance_and_duration(
            from_address={"lat": from_lat, "lng": from_lon},
            to_address={"lat": to_lat, "lng": to_lon},
        )

        total_price += get_total_cost_of_the_trip(
            M=tariff_amount, S2=distance, To=duration
        )

        all_addresses.append(
            {
                "from_address": address.from_address.address,
                "to_address": address.to_address.address,
                "from_lat": from_lat,
                "from_lon": from_lon,
                "to_lat": to_lat,
                "to_lon": to_lon,
            }
        )

        await DataScheduleRoadAddress.create(
            id_schedule_road=new_road.id,
            from_address=address.from_address.address,
            to_address=address.to_address.address,
            from_lon=from_lon,
            from_lat=from_lat,
            to_lon=to_lon,
            to_lat=to_lat,
        )

    if 1 in list(map(int, item.type_drive)):
        total_price *= 2

    await DataScheduleRoad.filter(id=new_road.id).update(amount=total_price)

    total_price_from_db = (
        await DataScheduleRoad.filter(id=new_road.id).first().values("amount")
    )

    total_price_from_db = str(total_price_from_db["amount"])

    return JSONResponse({"status": True,
                         "message": "Success!",
                         "id": new_road.id,
                         "price": total_price_from_db})


@router.post(
    "/get_total_price",
    responses=generate_responses([get_total_price]),
)
async def get_total_price(item: GetTotalPrice):
    """
    Возвращает общую стоимость поездки.
    Если задать координаты адресов как ноль (0), то координаты для адресов
    будут получаться с помощью GoogleMapsAPI.
    Если поездка туда-обратно - надо будет домножить на 2 (api вручную этого не делает).

    Значение поля accurately равно True только когда на вход подаётся одна пара адресов.
    Так как если пар несколько - то может быть неточность, связанная с тем, что с течением
    времени могут возникнуть пробки, либо наоборот и тд.


    Пример тарифов (взято из БД 20.12.2024):
        - 78 руб/км - эконом - id=1
        - 108 руб/км - комфорт - id=2
        - 138 руб/км - бизнес - id=4
        - 198 руб/км - минивэн - id=5
        - 243 руб/км - премиум - id=6



    Example:

        Пример входных данных:

            {
              "id_tariff": 1,
              "addresses": [
                {
                  "from_address": {
                    "address": "Кремль, Москва",
                    "location": {
                      "latitude": 0,
                      "longitude": 0
                    }
                  },
                  "to_address": {
                    "address": "ВДНХ, Москва",
                    "location": {
                      "latitude": 0,
                      "longitude": 0
                    }
                  }
                }
              ]
            }


    Args:
        item (GetTotalPrice): Данные поездки

    Returns:
        JSONResponse: Ответ в формате JSON
    """

    total_price: float = 0.0

    tariff_amount_dict: dict = await DataCarTariff.filter(
        id=item.id_tariff).first().values("amount")

    if not tariff_amount_dict:
        return JSONResponse({"status": False,
                             "message": "Tariff not found!"}, 404)

    tariff_amount: int = tariff_amount_dict["amount"]

    for address in item.addresses:
        from_lat, from_lon = (
            address.from_address.location.latitude,
            address.from_address.location.longitude,
        )
        to_lat, to_lon = (
            address.to_address.location.latitude,
            address.to_address.location.longitude,
        )
        if (
                address.from_address.location.longitude == 0
                and address.from_address.location.latitude == 0
        ):
            from_lat, from_lon = await get_lat_lon(address.from_address.address)
        if (
                address.to_address.location.longitude == 0
                and address.to_address.location.latitude == 0
        ):
            to_lat, to_lon = await get_lat_lon(address.to_address.address)

        distance, duration = await get_distance_and_duration(from_address={"lat": from_lat, "lng": from_lon},
                                                             to_address={"lat": to_lat, "lng": to_lon})

        total_price += get_total_cost_of_the_trip(M=tariff_amount, S2=distance, To=duration)

    return JSONResponse({"status": True,
                         "message": "Success!",
                         "total_price": str(round(total_price, 2)),
                         "accurately": len(item.addresses) == 1})


@router.put(
    "/schedule_road", responses=generate_responses([success_answer, schedule_not_found])
)
async def update_schedule_road(request: Request, item: UpdateRoad):
    """
    Обновляет маршрут с данным ID в расписании/графике/контракте.
    Во входных данных обязателен только id.

    Если задать координаты адресов как ноль (0), то координаты для адресов
    будут получаться с помощью GoogleMapsAPI.

    ПОКА ЧТО ВО ИЗБЕЖАНИЕ ОШИБОК - "type_drive": ["string"] -
    ДОЛЖЕН СОДЕРЖАТЬ ТОЛЬКО 1 ЭЛЕМЕНТ (0, 1, 2) - Тип поездки: в одну сторону, туда-обратно, с промежуточными точками.



    Args:
        request (Request): Объект запроса
        item (UpdateRoad): Данные маршрута

    Example:

        Пример входных данных:

            {
              "id": 0,
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
                "string"
              ]
            }

    Returns:
        JSONResponse: Ответ в формате JSON
    """

    road = await DataScheduleRoad.filter(id=item.id, isActive=True).first().values()
    if road is None or len(road) == 0:
        return schedule_not_found
    if (
        await DataSchedule.filter(
            id=road["id_schedule"], id_user=request.user, isActive=True
        ).count()
        == 0
    ):
        return schedule_not_found
    if item.title is not None and len(item.title) > 0 and road["title"] != item.title:
        await DataScheduleRoad.filter(id=item.id).update(title=item.title)
    if (
        item.start_time is not None
        and len(item.start_time) > 0
        and road["start_time"] != item.start_time
    ):
        await DataScheduleRoad.filter(id=item.id).update(start_time=item.start_time)
    if (
        item.end_time is not None
        and len(item.end_time) > 0
        and road["end_time"] != item.end_time
    ):
        await DataScheduleRoad.filter(id=item.id).update(end_time=item.end_time)
    if (
        item.week_day is not None
        and len(str(item.week_day)) > 0
        and road["week_day"] != item.week_day
    ):
        await DataScheduleRoad.filter(id=item.id).update(week_day=item.week_day)
    if item.type_drive is not None and len(item.type_drive) > 0:
        await DataScheduleRoad.filter(id=item.id).update(
            type_drive=";".join(map(str, item.type_drive))
        )

    id_tariff_data = await DataSchedule.filter(id=road["id_schedule"]).values("id_tariff")
    if id_tariff_data:
        id_tariff = id_tariff_data[0]["id_tariff"]
    else:
        return schedule_not_found

    tariff_amount_dict: dict = await DataCarTariff.filter(
        id=id_tariff).first().values("amount")

    if not tariff_amount_dict:
        return JSONResponse({"status": False,
                             "message": "Tariff not found!"}, 404)

    tariff_amount: int = tariff_amount_dict["amount"]

    total_price: float = 0.0  # Общая стоимость поездки

    all_addresses = []

    if item.addresses is not None and len(item.addresses) > 0:
        await DataScheduleRoadAddress.filter(id_schedule_road=item.id).delete()
        for address in item.addresses:
            from_lat, from_lon = (
                address.from_address.location.latitude,
                address.from_address.location.longitude,
            )
            to_lat, to_lon = (
                address.to_address.location.latitude,
                address.to_address.location.longitude,
            )
            if (
                address.from_address.location.longitude == 0
                and address.from_address.location.latitude == 0
            ):
                from_lat, from_lon = await get_lat_lon(address.from_address.address)
            if (
                address.to_address.location.longitude == 0
                and address.to_address.location.latitude == 0
            ):
                to_lat, to_lon = await get_lat_lon(address.to_address.address)

            distance, duration = await get_distance_and_duration(
                from_address={"lat": from_lat, "lng": from_lon},
                to_address={"lat": to_lat, "lng": to_lon})

            total_price += get_total_cost_of_the_trip(M=tariff_amount, S2=distance, To=duration)

            all_addresses.append({
                "from_address": address.from_address.address,
                "to_address": address.to_address.address,
                "from_lat": from_lat,
                "from_lon": from_lon,
                "to_lat": to_lat,
                "to_lon": to_lon,
            })

            await DataScheduleRoadAddress.create(
                id_schedule_road=item.id,
                from_address=address.from_address.address,
                to_address=address.to_address.address,
                from_lon=from_lon,
                from_lat=from_lat,
                to_lon=to_lon,
                to_lat=to_lat,
            )

    if 1 in list(map(int, item.type_drive)):
        total_price *= 2

    await DataScheduleRoad.filter(id=item.id).update(
        amount=total_price)

    total_price_from_db = await DataScheduleRoad.filter(id=item.id).first().values("amount")

    total_price_from_db = str(total_price_from_db["amount"])

    return JSONResponse({"status": True,
                         "message": "Success!",
                         "updated_road": {
                             "price": total_price_from_db,
                             "id": item.id,
                             "road_addresses": all_addresses
                         }
                         }, 200)


@router.get("/schedule_road/{id}",
            responses=generate_responses([schedule_not_found,
                                          get_schedule_road]))
async def get_schedule_road(id: int):
    road = await DataScheduleRoad.filter(id=id, isActive=True).first().values()
    if road is None or len(road) == 0:
        return schedule_not_found
    if await DataSchedule.filter(id=road["id_schedule"], isActive__not=None).count() == 0:
        return schedule_not_found
    road = await DataScheduleRoad.filter(id_schedule=id, isActive=True).order_by("id").first().values()
    road["type_drive"] = [int(x) for x in road["type_drive"].split(";")]
    addresses = await DataScheduleRoadAddress.filter(id_schedule_road=road["id"]).order_by("id").all().values()
    data_addresses = []
    price_road = 0
    schedule = await DataSchedule.filter(id=road["id_schedule"]).first().values("id_tariff")
    tariff = (await DataCarTariff.filter(id=schedule["id_tariff"]).first().values())["amount"]
    for address in addresses:
        info, _ = await get_time_drive(address["from_lat"], address["from_lon"],
                                       address["to_lat"], address["to_lon"], tariff)
        price_road += info
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
    road["amount"] = price_road
    del road["id_schedule"]
    del road["isActive"]
    del road["datetime_create"]
    return JSONResponse({"status": True,
                         "message": "Success!",
                         "schedule_road": road}, 200)


@router.get("/get_current_order",
            responses=generate_responses([access_forbidden, get_orders]))
async def get_current_order_data(request: Request):
    """ Получение всех активных заказов """
    user = await UsersUser.filter(id=request.user).first()

    if not user:
        return access_forbidden

    user_types = await UsersUserAccount.filter(id_user=request.user).all()

    if not user_types or not any(user_type.id_type_account in [1, 2] for user_type in user_types):
        return access_forbidden

    current_orders = []

    current_orders += await DataOrder.filter(id_user=request.user, isActive=True).all()
    current_orders += await DataOrder.filter(id_driver=request.user, isActive=True).all()

    if not current_orders:
        return JSONResponse({"status": False, "message": "No active orders found."})

    orders_data = []

    for current_order in current_orders:
        if not current_order:
            continue

        user_info = await UsersUser.filter(id=current_order.id_user).first()
        if not user_info:
            continue

        user_photo = await UsersUserPhoto.filter(id_user=current_order.id_user).first()
        order_info = await DataOrderInfo.filter(id_order=current_order.id).first()
        order_addresses = await DataOrderAddresses.filter(id_order=current_order.id).all()
        other_params = []
        order_other_params = await DataOrderOtherParametrs.filter(id_order=current_order.id).all()
        for other_param in order_other_params:
            if other_param.isActive:
                name_dict = await DataOtherDriveParametr.filter(id=other_param.id_other_parametr).first().values("title", "amount")
                if name_dict:
                    name = name_dict["title"]
                    value = float(name_dict["amount"])
                    other_params.append({
                        "id": other_param.id_other_parametr,
                        "name": name,
                        "value": float(other_param.amount * value)
                    })

        if not order_info or not order_addresses:
            continue

        order_data = {
            "id_order": current_order.id,
            "id_user": user_info.id,
            "username": user_info.name,
            "phone": user_info.phone,
            "user_photo": user_photo.photo_path if user_photo else None,
            "amount": float(order_info.price),
            "id_status": current_order.id_status,
            "type_drive": current_order.type_drive,
            "other_params": other_params,
            "addresses": [{
                "from": addr.from_address,
                "isFinish": addr.isFinish,
                "to": addr.to_address,
                "from_lat": addr.from_lat,
                "from_lon": addr.from_lon,
                "to_lat": addr.to_lat,
                "to_lon": addr.to_lon,
                "duration": order_info.duration
            } for addr in order_addresses]
        }

        orders_data.append(order_data)

    return JSONResponse({
        "status": True,
        "message": "Success",
        "orders": orders_data
    })


@router.post("/start-current-drive",
             responses=generate_responses([start_current_drive,
                                           you_have_active_drive]))
async def start_one_current_drive(request: Request, item: CurrentDrive):
    if await DataOrder.filter(id_status__not=11, id_user=request.user, isActive=True).count() > 0 or\
            await WaitDataSearchDriver.filter(id_user=request.user).count() > 0:
        return you_have_active_drive
    token = str(uuid.uuid4()) + str(uuid.uuid4())
    return token


@router.get(
    "/get_schedule_responses", responses=generate_responses([get_schedule_responses])
)
async def get_schedule_responses(request: Request):
    """
    Функция возвращает список водителей, готовых к выполнению расписаний текущего пользователя,
    и подробной информации о них.

    Args:
        request (Request): Объект запроса.

    Returns:
        JSONResponse: JSON-ответ с информацией о водителях.

    Example:

        Пример ответа:

            {
              "status": true,
              "message": "Success!",
              "responses": [
                {
                  "id_driver": 14,
                  "name": "Евген",
                  "photo_path": "https://nyanyago.ru/api/v1.0/files/9b75f2b1-4768-483f-b220-f5463f511ac5104edf9e-83c7-4347-bd12-3d1e886761501728468831.0238381000072405",
                  "id_schedule": "9, 10",
                  "id_chat": 21,
                  "full_time": true,
                  "data": [
                    {
                      "id_road": 17,
                      "week_day": 0
                    },
                    {
                      "id_road": 18,
                      "week_day": 0
                    },
                  ]
                }
              ]
            }
    """
    async def get_user_schedules(user):
        """
        Получает 'расписания' текущего пользователя, которые есть в БД, но они не активны.
        Т.е. как-бы ещё не выполняются ('ждут', пока за них возьмутся водители).

        Args:
            user (int): ID пользователя.

        Returns:
            list: Список ID расписаний.
        """
        return [
            x["id"]
            for x in await DataSchedule.filter(id_user=user, isActive=False).values()
        ]

    async def get_active_data(schedules_id):
        """
        Получает данные из таблицы 'заявок водителей' для расписаний текущего пользователя.

        Args:
            schedules_id (list): Список ID расписаний.

        Returns:
            list: Список из данных об активных заявках водителей.
        """
        return (
            await WaitDataScheduleRoadDriver.filter(
                id_schedule__in=schedules_id, isActive=True
            )
            .order_by("id_driver")
            .values()
        )

    async def get_or_create_chat(user, driver):
        """
        Создаёт чат между указанным пользователем и водителем, если его нет.

        Args:
            user (int): ID пользователя.
            driver (int): ID водителя.

        Returns:
            int: ID чата.
        """
        chats = [
            x["id_chat"]
            for x in await ChatsChatParticipant.filter(id_user=user).values()
        ]
        existing_chats = await ChatsChatParticipant.filter(
            id_user=driver, id_chat__in=chats
        ).values()

        for chat in existing_chats:
            if await ChatsChat.filter(id=chat["id_chat"], isActive=True).exists():
                return chat["id_chat"]

        # Создать новый чат, если его нет
        new_chat = await ChatsChat.create()
        await ChatsChatParticipant.create(id_chat=new_chat.id, id_user=user)
        await ChatsChatParticipant.create(id_chat=new_chat.id, id_user=driver)
        return new_chat.id

    async def get_driver_info(driver_id):
        """
        Получает информацию о водителе (имя и фото).

        Args:
            driver_id (int): ID водителя.

        Returns:
            dict: Информация о водителе.
        """
        user = await UsersUser.filter(id=driver_id).first()
        photo = await UsersUserPhoto.filter(id_user=driver_id).first()
        return {
            "name": user.name if user else "Unknown",
            "photo_path": (
                photo.photo_path if photo and photo.photo_path else not_user_photo
            ),
        }

    async def get_roads_info(road_ids):
        """
        Получает информацию о маршрутах (ID, день недели).

        Args:
            road_ids (list): Список ID маршрутов.

        Returns:
            list: Информация о маршрутах.
        """
        roads = []
        for road_id in road_ids:
            road = await DataScheduleRoad.filter(id=road_id).first()
            if road:
                roads.append({"id_road": road_id, "week_day": road.week_day})
        return roads

    async def get_drivers_schedules(driver_id):
        """
        Возвращает список из ID расписаний, на которые откликнулся водитель.

        Args:
            driver_id (int): ID водителя.

        Returns:
            set: Список ID расписаний.
        """
        schedules_set = set()
        for row in await WaitDataScheduleRoadDriver.filter(
                id_driver=driver_id, id_schedule__in=schedules_id
        ).all():
            schedules_set.add(row.id_schedule)
        return schedules_set

    async def is_full_time_driver(driver_id):
        row = await WaitDataScheduleRoadDriver.filter(
            id_driver=driver_id, id_schedule__in=schedules_id
        ).first()
        return row.full_time

    schedules_id = await get_user_schedules(request.user)

    data = await get_active_data(schedules_id)

    answer = []
    driver_roads = {}
    previous_driver = None

    for each in data:
        driver_id = each["id_driver"]
        road_id = each["id_road"]

        if driver_id not in driver_roads:
            driver_roads[driver_id] = set()
        driver_roads[driver_id].add(road_id)

        if driver_id != previous_driver:
            if previous_driver is not None:
                chat_id = await get_or_create_chat(request.user, previous_driver)
                driver_info = await get_driver_info(previous_driver)
                road_info = await get_roads_info(list(driver_roads[previous_driver]))
                schedules = await get_drivers_schedules(previous_driver)
                is_full_time = await is_full_time_driver(previous_driver)

                answer.append(
                    {
                        "id_driver": previous_driver,
                        "name": driver_info["name"],
                        "photo_path": driver_info["photo_path"],
                        "id_schedule": ', '.join(str(x) for x in schedules),
                        "id_chat": chat_id,
                        "full_time": is_full_time,
                        "data": road_info,
                    }
                )

            previous_driver = driver_id

    if previous_driver:
        chat_id = await get_or_create_chat(request.user, previous_driver)
        driver_info = await get_driver_info(previous_driver)
        road_info = await get_roads_info(list(driver_roads[previous_driver]))
        schedules = await get_drivers_schedules(previous_driver)
        is_full_time = await is_full_time_driver(previous_driver)

        answer.append(
            {
                "id_driver": previous_driver,
                "name": driver_info["name"],
                "photo_path": driver_info["photo_path"],
                "id_schedule": ', '.join(str(x) for x in schedules),
                "id_chat": chat_id,
                "full_time": is_full_time,
                "data": road_info,
            }
        )

    return JSONResponse({"status": True, "message": "Success!", "responses": answer})


@router.post(
    "/answer_schedule_responses", responses=generate_responses([success_answer])
)
async def answer_schedule_responses(request: Request, item: AnswerResponse):
    """
    Эндпоинт для ответа клиентом на принятую заявку водителя.
    (Водитель принимает заявку с помощью эндпоинта `/drivers/want_schedule_requests`).

    Args:
        request (Request): Объект запроса.
        item (AnswerResponse): Объект с данными для ответа клиентом.

    Returns:
        JSONResponse: Ответ с информацией об успешном ответе.
    """
    if (
            await DataSchedule.filter(
                isActive=False, id_user=request.user, id=item.id_schedule
            ).count()
            == 0
    ):
        return schedule_not_found
    if (
            await WaitDataScheduleRoadDriver.filter(
                id=item.id_response, isActive=True
            ).count()
            == 0
    ):
        return schedule_not_found
    data = (
        await WaitDataScheduleRoadDriver.filter(id=item.id_response, isActive=True)
        .first()
        .values()
    )
    id_responses = [
        x["id"]
        for x in (
            await WaitDataScheduleRoadDriver.filter(
                id_driver=data["id_driver"],
                id_schedule=data["id_schedule"],
                isActive=True,
            )
            .all()
            .values()
        )
    ]
    roads = []
    for each in id_responses:
        if item.flag is False:
            await WaitDataScheduleRoadDriver.filter(id=each).update(isActive=False)
        else:
            road = await WaitDataScheduleRoadDriver.filter(id=each).first().values()
            await WaitDataScheduleRoadDriver.filter(id=each).update(isActive=None)
            roads.append(road["id_road"])
            await DataScheduleRoadDriver.create(
                id_schedule_road=road["id_road"],
                id_driver=data["id_driver"],
                isRepeat=True,
            )
    fbid = (
        await UsersBearerToken.filter(id_user=data["id_driver"])
        .order_by("-id")
        .first()
        .values()
    )
    if item.flag is True:
        await DataSchedule.filter(id=item.id_schedule).update(isActive=True)
        try:
            await sendPush(
                fbid["fbid"],
                "Ваша заявка на контракт одобрена",
                "Родитель одобрил Вашу кандидатуру на контракт.\n"
                "Пожалуйста, подтвердите актуальность Вашей заявки в приложении.",
                {
                    "action": "order_request_success",
                    "id_request": item.id_response,
                    "id_schedule": item.id_schedule,
                },
            )
            await HistoryNotification.create(
                id_user=data["id_driver"],
                title="Ваша заявка на контракт одобрена",
                description="Родитель одобрил Вашу кандидатуру на контракт.\n"
                            "Пожалуйста, подтвердите актуальность Вашей заявки в приложении.",
            )
        except Exception:
            pass
    else:
        try:
            await sendPush(
                fbid["fbid"],
                "Ваша заявка на контракт отклонена",
                "К сожалению, родителю не подошла Ваша кандидатура на роль автоняни.",
                {"action": "order_request_denied"},
            )
            await HistoryNotification.create(
                id_user=data["id_driver"],
                title="Ваша заявка на контракт отклонена",
                description="К сожалению, родителю не подошла Ваша кандидатура"
                            " на роль автоняни.",
            )
        except Exception:
            pass
    return success_answer


@router.post("/get_driver",
             responses=generate_responses([access_forbidden,
                                           driver_not_found,
                                           get_driver]))
async def get_driver_by_id(request: Request, item: GetDriver):
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
                             "photo_path": photo,
                             "video_path": driver_data.video_url,
                             "date_reg": data.datetime_create.isoformat(),
                             "carData": car
                         }})


@router.get("/get_onetime_prices",
            responses=generate_responses([get_onetime_prices]))
async def get_onetime_prices(request: Request, duration: int, distance: int):
    """
    Вроде как deprecated функция.
    См. const -> cost_formulas.py -> get_total_cost_of_the_trip().
    """
    my_ref, result = await UsersFranchiseUser.filter(id_user=request.user).first().values(), []
    data = await DataCarTariff.filter(id_franchise=my_ref["id_franchise"],
                                      isActive=True).order_by("id").all().values("id", "amount")
    for each in data:
        each["isAvailable"] = True
        T = duration
        T1 = 7
        S1 = 3
        S2 = distance
        S = S1 + S2
        M = float(each["amount"])
        k = 1
        J = 1
        F1 = 0.03
        X5 = 0.01
        Kc = 0.02
        cost_without_cashback = ((T / T1) * S * M * k) / J
        P___ = Kc * cost_without_cashback / 100
        cost_with_cashback = cost_without_cashback + (F1 * cost_without_cashback / 100) + \
                             (X5 * cost_without_cashback / 100) + P___
        result.append({"id_tariff": each["id"], "amount": cost_without_cashback, "amount_cash": cost_with_cashback})
    return JSONResponse({"status": True,
                         "message": "Success!",
                         "tariffs": result})


@router.get("/get_price_by_road",
            responses=generate_responses([success_answer,
                                          access_forbidden]))
async def get_price_by_road(request: Request, id_tariff: int, duration: int, distance: int):
    """
    Вроде как deprecated функция.
    См. const -> cost_formulas.py -> get_total_cost_of_the_trip().
    """
    my_ref = await UsersFranchiseUser.filter(id_user=request.user).first().values()
    if await DataCarTariff.filter(id=id_tariff, id_franchise=my_ref["id_franchise"], isActive=True).count() == 0:
        return access_forbidden
    tariff = await DataCarTariff.filter(id=id_tariff).first().values()
    T = duration
    T1 = 7
    S1 = 3
    S2 = distance
    S = S1 + S2
    M = float(tariff["amount"])
    k = 1
    J = 1
    F1 = 0.03
    Kc = 0.02
    cost_without_cashback = ((T / T1) * S * M * k) / J
    P___ = Kc * cost_without_cashback / 100
    cost_with_cashback = cost_without_cashback + (F1 * cost_without_cashback / 100) + P___
    return JSONResponse({"status": True,
                         "message": "Success!",
                         "amount": cost_without_cashback,
                         "amount_with_cashback": cost_with_cashback})


@router.get("/get_orders",
            responses=generate_responses([forbidden,
                                          get_orders]))
async def get_onetime_orders(request: Request, type_order: int):
    if await UsersUserAccount.filter(id_user=request.user, id_type_account=2).count() == 0 or type_order not in [1, 2]:
        return forbidden
    answer, orders = [], await DataOrder.filter(id_status__in=[1, 4], isActive=True).order_by("-id").all().values()
    for each in orders:
        info = await get_order_data(each)
        if info is None or info == {}:
            continue
        answer.append(info)
    return JSONResponse({"status": True,
                         "message": "Success!",
                         "orders": answer})


@router.get("/get_driver_token")
async def get_driver_token(request: Request):
    try:
        driver_mode = await DataDriverMode.filter(id_driver=request.user).first()
        if not driver_mode:
            raise HTTPException(status_code=404, detail="Driver token not found")

        return JSONResponse({"websocket_token": driver_mode.websocket_token})

    except DoesNotExist:
        raise HTTPException(status_code=404, detail="Driver not found")


@router.get("/get_client_token")
async def get_client_token(request: Request):
    try:
        user_orders = await UsersUserOrder.filter(id_user=request.user).all()
        if not user_orders:
            raise HTTPException(status_code=404, detail="Client tokens not found")

        result = []
        for user_order in user_orders:
            result.append({
                "websocket_token": user_order.token,
                "id_order": user_order.id_order
            })

        return JSONResponse({"orders": result})

    except DoesNotExist:
        raise HTTPException(status_code=404, detail="Client not found")


@router.post("/new_order",
             # dependencies=[Depends(has_access_franchise)],
             responses=generate_responses([success_answer]))
async def new_order(request: Request, one_time_order: OneTimeOrder):
    """
    Создаёт новый единоразовый заказ для данного водителя.

    Валидаторы - адрес больше 5 букв, в адресе 2 или более запятые.

    Адрес надо указывать так, чтоб было понятно - он потом преобразуется в координаты
    с помощью GoogleMapsAPI. В идеале: "улица Петровка, 2, Москва, Россия, 125009".

    Args:
        request (Request): Запрос.
        one_time_order (OneTimeOrder): Данные нового единоразового заказа.

    Example:

        Пример входных данных:

            {
                "id_driver": 5,
                "from_address": "улица Воздвиженка, 3/5с2, Москва, Россия, 119019",
                "to_address": "улица Петровка, 2, Москва, Россия, 125009",
                "from_time": "2024-11-21T09:00:00",
                "to_time": "2024-11-21T10:00:00",
                "id_tariff": 5,
            }
    """
    data_order = DataOrder(
        id_driver=one_time_order.id_driver,
        id_user=one_time_order.id_driver,  # Т.к. на вход не подаётся id клиента - пусть им будет id водителя
        id_status=1,  # 1 = Создан
        id_type_order=1,  # 1 = Единоразовый
        isActive=False,  # False = Не активен (мб это значит что заказ создан, но не начался)
    )

    tariff_amount_dict: dict = await DataCarTariff.filter(id=one_time_order.id_tariff).first().values("amount")

    if not tariff_amount_dict:
        raise HTTPException(status_code=400, detail="Tariff not found")

    tariff_amount: int = tariff_amount_dict["amount"]

    from_lat, from_lon = await get_lat_lon(one_time_order.from_address)
    to_lat, to_lon = await get_lat_lon(one_time_order.to_address)

    if from_lat is None or from_lon is None or to_lat is None or to_lon is None:
        raise HTTPException(status_code=400, detail="Invalid address")

    distance_meters, duration_seconds = await get_distance_and_duration(
                from_address={"lat": from_lat, "lng": from_lon},
                to_address={"lat": to_lat, "lng": to_lon})

    await data_order.save()

    await DataOrderAddresses.create(
        id_order=data_order.id,
        from_address=one_time_order.from_address,
        to_address=one_time_order.to_address,
        from_lat=from_lat,
        from_lon=from_lon,
        to_lat=to_lat,
        to_lon=to_lon,
        isFinish=True  # как я понял - указывает, что адрес конечный в данном заказе.
    )

    await DataOrderInfo.create(
        id_order=data_order.id,
        distance=distance_meters,
        duration=duration_seconds,
        id_tariff=one_time_order.id_tariff,
        price=get_total_cost_of_the_trip(M=tariff_amount, S2=distance_meters,
                                         To=duration_seconds),
        start_time=one_time_order.from_time,
    )

    return success_answer

