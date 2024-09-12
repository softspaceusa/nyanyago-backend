import time

from const.const import success_answer
from const.dependency import has_access_parent
from const.login_const import forbidden
from models.chats_db import ChatsChatParticipant, ChatsChat
from models.drivers_db import UsersDriverData, UsersCar
from models.static_data_db import DataCarTariff, DataOtherDriveParametr, DataCarMark, DataCarModel, DataColor
from const.orders_const import CurrentDrive, you_have_active_drive, start_current_drive, NewSchedule, get_schedule, \
    schedule_not_found, tariff_by_id_not_found, get_schedules, Road, UpdateRoad, get_schedule_road, \
    get_schedule_responses, AnswerResponse, get_onetime_prices, start_onetime_drive, get_orders
from const.static_data_const import access_forbidden, DictToModel, not_user_photo
from models.users_db import UsersUser, UsersUserPhoto, HistoryNotification, UsersFranchiseUser
from models.authentication_db import UsersUserAccount, UsersBearerToken
from fastapi import APIRouter, Request, Depends
from defs import check_access_schedule, sendPush, get_time_drive, get_order_data
from models.orders_db import *
from const.drivers_const import *
import uuid
import json


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


@router.post("/schedule",
             responses=generate_responses([success_answer,
                                           tariff_by_id_not_found]))
async def create_schedule(request: Request, item: NewSchedule):
    print(item.__dict__)
    #TODO: Проверка на достаточный баланс для создания графика
    if await DataCarTariff.filter(isActive=True, id=item.id_tariff).count() == 0:
        return tariff_by_id_not_found
    schedule = await DataSchedule.create(id_user=request.user, title=item.title,
                                         children_count=item.children_count, duration=item.duration,
                                         id_tariff=item.id_tariff, description=item.description,
                                         week_days=";".join(map(str, item.week_days)))
    for params in item.other_parametrs:
        if await DataOtherDriveParametr.filter(id=params.parametr, isActive=True).count() == 0:
            continue
        await DataScheduleOtherParametrs.create(id_schedule=schedule.id, id_other_parametr=params.parametr,
                                                amount=params.count)
    for road in item.roads:
        new_road = await DataScheduleRoad.create(id_schedule=schedule.id, week_day=road.week_day,
                                                 title=road.title, start_time=road.start_time,
                                                 end_time=road.end_time, type_drive=";".join(map(str, road.type_drive)))
        for address in road.addresses:
            from math import radians, cos, sin, asin, sqrt

            def haversine(lon1, lat1, lon2, lat2):
                """
                Calculate the great circle distance in kilometers between two points
                on the earth (specified in decimal degrees)
                """
                # convert decimal degrees to radians
                lon1, lat1, lon2, lat2=map(radians, [lon1, lat1, lon2, lat2])

                # haversine formula
                dlon=lon2 - lon1
                dlat=lat2 - lat1
                a=sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
                c=2 * asin(sqrt(a))
                r=6371  # Radius of earth in kilometers. Use 3956 for miles. Determines return value units.
                return int(c * r)
            await DataScheduleRoadAddress.create(id_schedule_road=new_road.id,
                                                 from_address=address.from_address.address,
                                                 to_address=address.to_address.address,
                                                 from_lon=address.from_address.location.longitude,
                                                 from_lat=address.from_address.location.latitude,
                                                 to_lon=address.to_address.location.longitude,
                                                 to_lat=address.to_address.location.latitude)
    return success_answer


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


@router.get("/schedules",
             responses=generate_responses([get_schedules,
                                           schedule_not_found,
                                           access_forbidden]))
async def get_schedule(request: Request):
    schedules = await DataSchedule.filter(id_user=request.user, isActive__in=[True, False]
                                         ).all().values("id", "title", "description", "children_count",
                                                        "id_tariff", "week_days", "duration", "id_user")
    for schedule in schedules:
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
            price_road = 0
            data_addresses = []
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
                         "schedules": schedules}, 200)


@router.delete("/schedule/{id}",
               responses=generate_responses([success_answer,
                                             schedule_not_found,
                                             access_forbidden]),
               dependencies=[Depends(has_access_parent)])
async def delete_schedule(request: Request, id: int):
    if await DataSchedule.filter(id=id).count() == 0:
        return schedule_not_found
    if await DataSchedule.filter(id=id, isActive__in=[True, False], id_user=request.user).count() == 0:
        return access_forbidden
    await DataSchedule.filter(id=id).update(isActive=None)
    return success_answer


@router.delete("/schedule_road/{id}",
               responses=generate_responses([success_answer,
                                             schedule_not_found,
                                             access_forbidden]),
               dependencies=[Depends(has_access_parent)])
async def delete_schedule_road(request: Request, id: int):
    if await DataScheduleRoad.filter(id=id, isActive=True).count() == 0:
        return schedule_not_found
    road = await DataScheduleRoad.filter(id=id).first().values()
    if await DataSchedule.filter(id_user=request.user, id=road["id_schedule"], isActive__in=[True, False]).count() == 0:
        return access_forbidden
    if await DataScheduleRoadDriver.filter(id_schedule_road=id, isActive=True).count() > 0:
        road_order = await DataScheduleRoadDriver.filter(id_schedule_road=id, isActive=True).all().values()
    await DataScheduleRoad.filter(id=id, isActive=True).update(isActive=False)
    #if await DataSchedule.filter(id_user=request.user, id=road["id_schedule"], isActive=True).count() > 0:
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
    for address in item.addresses:
        await DataScheduleRoadAddress.create(id_schedule_road=new_road.id,
                                             from_address=address.from_address.address,
                                             to_address=address.to_address.address,
                                             from_lon=address.from_address.location.longitude,
                                             from_lat=address.from_address.location.latitude,
                                             to_lon=address.to_address.location.longitude,
                                             to_lat=address.to_address.location.latitude)
    return JSONResponse({"status": True,
                         "message": "Success!",
                         "id": new_road.id})


@router.put("/schedule_road",
            responses=generate_responses([success_answer,
                                          schedule_not_found]))
async def update_schedule_road(request: Request, item: UpdateRoad):
    road = await DataScheduleRoad.filter(id=item.id, isActive=True).first().values()
    if road is None or len(road) == 0:
        return schedule_not_found
    if await DataSchedule.filter(id=road["id_schedule"], id_user=request.user, isActive__not=None).count() == 0:
        return schedule_not_found
    if item.title is not None and len(item.title) > 0 and road["title"] != item.title:
        await DataScheduleRoad.filter(id=item.id).update(title=item.title)
    if item.start_time is not None and len(item.start_time) > 0 and road["start_time"] != item.start_time:
        await DataScheduleRoad.filter(id=item.id).update(start_time=item.start_time)
    if item.end_time is not None and len(item.end_time) > 0 and road["end_time"] != item.end_time:
        await DataScheduleRoad.filter(id=item.id).update(end_time=item.end_time)
    if item.week_day is not None and len(str(item.week_day)) > 0 and road["week_day"] != item.week_day:
        await DataScheduleRoad.filter(id=item.id).update(week_day=item.week_day)
    if item.type_drive is not None and len(item.type_drive) > 0:
        await DataScheduleRoad.filter(id=item.id).update(type_drive=";".join(map(str, item.type_drive)))
    if item.addresses is not None and len(item.addresses) > 0:
        await DataScheduleRoadAddress.filter(id_schedule=item.id).delete()
        for address in item.addresses:
            await DataScheduleRoadAddress.create(id_schedule_road=item.id,
                                                 from_address=address.from_address.address,
                                                 to_address=address.to_address.address,
                                                 from_lon=address.from_address.location.longitude,
                                                 from_lat=address.from_address.location.latitude,
                                                 to_lon=address.to_address.location.longitude,
                                                 to_lat=address.to_address.location.latitude)
    return success_answer


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
    user = DictToModel(await UsersUser.filter(id=request.user).first().values())
    user_type = DictToModel(await UsersUserAccount.filter(id_user=request.user).first().values())
    if user_type.id_type_account not in [1, 2]:
        return access_forbidden

    current_orders = []

    # Если пользователь — родитель (id_type_account == 1)
    if user_type.id_type_account == 1:
        current_orders = await DataOrder.filter(id_user=request.user, isActive=True).all()

    # Если пользователь — водитель (id_type_account == 2)
    elif user_type.id_type_account == 2:
        current_order = await DataOrder.filter(id_driver=request.user, isActive=True).first()
        if current_order:
            current_orders.append(current_order)

    # Проверка на наличие активных заказов
    if not current_orders:
        return JSONResponse({"status": False, "message": "No active orders found."})

    orders_data = []

    for current_order in current_orders:
        user_info = await UsersUser.filter(id=current_order.id_user).first()
        user_photo = await UsersUserPhoto.filter(id_user=current_order.id_user).first()
        user_photo_url = user_photo.photo_path if user_photo else None

        order_info = await DataOrderInfo.filter(id_order=current_order.id).first()
        order_addresses = await DataOrderAddresses.filter(id_order=current_order.id).all()

        order_data = {
            "id_user": user_info.id,
            "id_order": current_order.id,
            "username": user_info.name if user_info else None,
            "phone": user_info.phone if user_info else None,
            "user_photo": user_photo_url,
            "amount": order_info.price if order_info else 0.0,
            "id_status": current_order.id_status,
            "addresses": [{
                "from": addr.from_address,
                "isFinish": "true" if addr.isArrived else "false",
                "to": addr.to_address,
                "from_lat": addr.from_lat,
                "from_lon": addr.from_lon,
                "to_lat": addr.to_lat,
                "to_lon": addr.to_lon,
                "duration": order_info.duration if order_info else 0
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


@router.get("/get_schedule_responses",
            responses=generate_responses([get_schedule_responses]))
async def get_schedule_responses(request: Request):
    schedules_id = [x["id"] for x in (await DataSchedule.filter(id_user=request.user, isActive=False).all().values())]
    answer, success_driver, roads, i = [], [], {}, 0
    data = await WaitDataScheduleRoadDriver.filter(id_schedule__in=schedules_id,
                                                   isActive=True).order_by("id").all().values()
    print(data)
    for each in data:
        print(each)
        print(roads)
        if len(success_driver) == 0:
            success_driver.append(each["id_driver"])
        if each["id_driver"] not in roads:
            roads[each["id_driver"]]=[each["id_road"]]
        else:
            roads[each["id_driver"]]+=[each["id_road"]]
        if each["id_driver"] != success_driver[-1] or (i==len(data) or i+1==len(data)):
            chats = [x["id_chat"] for x in (await ChatsChatParticipant.filter(id_user=request.user).all().values())]
            if await ChatsChatParticipant.filter(id_user=success_driver[-1], id_chat__in=chats).count() == 0:
                chat = await ChatsChat.create()
                await ChatsChatParticipant.create(id_chat=chat.id, id_user=request.user)
                await ChatsChatParticipant.create(id_chat=chat.id, id_user=success_driver[-1])
                chat_id = chat.id
            else:
                chats = await ChatsChatParticipant.filter(id_user=success_driver[-1], id_chat__in=chats).all().values()
                chat_id = None
                for chat in chats:
                    if await ChatsChat.filter(id=chat["id_chat"], isActive=True).count() > 0:
                        chat_id = chat["id_chat"]
                        break
                if chat_id is None:
                    chat=await ChatsChat.create()
                    await ChatsChatParticipant.create(id_chat=chat.id, id_user=request.user)
                    await ChatsChatParticipant.create(id_chat=chat.id, id_user=success_driver[-1])
                    chat_id=chat.id

            photo = await UsersUserPhoto.filter(id_user=success_driver[-1]).first().values()
            photo = photo["photo_path"] if photo is not None or "photo_path" in photo else not_user_photo
            road_ans = []
            for road in roads[success_driver[-1]]:
                road_info = await DataScheduleRoad.filter(id=road).first().values()
                road_ans.append({"id_road": road, "week_day": road_info["week_day"]})
            ans = {
                "id": each["id"],
                "id_driver": each["id_driver"],
                "name": (await UsersUser.filter(id=success_driver[-1]).first().values())["name"],
                "photo_path": photo,
                "id_schedule": each["id_schedule"],
                "id_chat": chat_id,
                "data": road_ans
            }
            print(ans)
            answer.append(ans)
        success_driver.append(each["id_driver"])
        i += 1
    return JSONResponse({"status": True,
                         "message": "Success!",
                         "responses": answer})


@router.post("/answer_schedule_responses",
             responses=generate_responses([success_answer]))
async def answer_schedule_responses(request: Request, item: AnswerResponse):
    if await DataSchedule.filter(isActive=False, id_user=request.user, id=item.id_schedule).count() == 0:
        return schedule_not_found
    if await WaitDataScheduleRoadDriver.filter(id=item.id_response, isActive=True).count() == 0:
        return schedule_not_found
    data = await WaitDataScheduleRoadDriver.filter(id=item.id_response, isActive=True).first().values()
    id_responses = [x["id"] for x in (await WaitDataScheduleRoadDriver.filter(
                    id_driver=data["id_driver"], id_schedule=data["id_schedule"], isActive=True).all().values())]
    roads = []
    for each in id_responses:
        if item.flag is False:
            await WaitDataScheduleRoadDriver.filter(id=each).update(isActive=False)
        else:
            road = await WaitDataScheduleRoadDriver.filter(id=each).first().values()
            await WaitDataScheduleRoadDriver.filter(id=each).update(isActive=None)
            roads.append(road["id_road"])
            await DataScheduleRoadDriver.create(id_schedule_road=road["id_road"], id_driver=data["id_driver"],
                                                isRepeat=True)
    fbid = await UsersBearerToken.filter(id_user=data["id_driver"]).order_by("-id").first().values()
    if item.flag is True:
        await DataSchedule.filter(id=item.id_schedule).update(isActive=True)
        try:
            await sendPush(fbid["fbid"], "Ваша заявка на контракт одобрена",
                           "Родитель одобрил Вашу кандидатуру на контракт.\n"
                           "Пожалуйста, подтвердите актуальность Вашей заявки в приложении.",
                           {"action": "order_request_success",
                            "id_request": item.id_response,
                            "id_schedule": item.id_schedule})
            await HistoryNotification.create(id_user=data["id_driver"], title="Ваша заявка на контракт одобрена",
                                             description="Родитель одобрил Вашу кандидатуру на контракт.\n"
                                             "Пожалуйста, подтвердите актуальность Вашей заявки в приложении.")
        except Exception:
            pass
    else:
        try:
            await sendPush(fbid["fbid"], "Ваша заявка на контракт отклонена",
                           "К сожалению, родителю не подошла Ваша кандидатура на роль автоняни.",
                           {"action": "order_request_denied"})
            await HistoryNotification.create(id_user=data["id_driver"], title="Ваша заявка на контракт отклонена",
                                             description="К сожалению, родителю не подошла Ваша кандидатура"
                                                         " на роль автоняни.")
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

