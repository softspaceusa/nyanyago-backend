import math

from const.login_const import forbidden
from const.orders_const import start_onetime_drive, CurrentDrive, JSONResponse, you_have_active_drive, \
    cant_decline_in_drive_mode
from const.static_data_const import not_user_photo
from const.users_const import order_not_found, success_answer
from models.authentication_db import UsersUserAccount, UsersBearerToken
from models.chats_db import ChatsChatParticipant, ChatsChat
from models.drivers_db import DataDriverMode
from fastapi import APIRouter, WebSocket
from models.orders_db import *
from fastapi import Request
from typing import List
from defs import error, get_time_drive, get_order_data, sendPush
import traceback
import time
import uuid
import json

from models.static_data_db import DataCarTariff
from models.users_db import UsersUser, UsersUserPhoto

router = APIRouter()
users = {}
clients = {}


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


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    async def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        try:
            del users[list(users.keys())[list(users.values()).index(websocket)]]
            await DataDriverMode.filter(token=list(users.keys())[list(users.values()).index(websocket)]).delete()
        except Exception:
            pass

    @staticmethod
    async def send_personal_message(message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


async def send_message_to_client(id_order, id_status, title):
    """ Отправка сообщения клиенту"""
    order = await DataOrder.filter(id=id_order).first()
    if order:
        user_order = await UsersUserOrder.filter(id_order=id_order).first()
        if user_order and user_order.token in clients:
            client_socket = clients[user_order.token]
            await manager_client.send_personal_message(
                json.dumps({"status": True, "id_status": id_status, "message": title}),
                client_socket
            )


@router.websocket("/current-drive-mode/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    try:
        await manager.connect(websocket)
        if token not in users:
            users[token] = websocket
        while True:
            message = await websocket.receive_text()
            message = json.loads(message)

            # Обновление местоположения водителя
            lat = message.get("lat")
            lon = message.get("lon")
            if lat and lon:
                await DataDriverMode.filter(token=token).update(lat=lat, lon=lon)

            # Обработка сообщения с типом "order" и флагом "startDrive"
            if message.get("type") == "order" and message.get("flag") == "startDrive":
                id_order = message.get("id_order")
                title_message = "The trip has begun"

                await DataOrder.filter(id=id_order).update(id_status=5)
                await manager.send_personal_message(json.dumps({"status": True, "message": title_message}),
                                                    websocket)
                await send_message_to_client(id_order=id_order, id_status=5, title=title_message)

            # Обработка сообщения с типом "order" и флагом "waiting"
            if message.get("flag") == "waiting":
                id_order = message.get("id_order")
                index_address = message.get("index_address")
                title_message = "Waiting start"

                await DataOrder.filter(id=id_order).update(id_status=6)
                await manager.send_personal_message(json.dumps({"status": True, "message": title_message}),
                                                    websocket)
                await send_message_to_client(id_order=id_order, id_status=6, title=title_message)

            # Обработка сообщения с флагом "isFinish"
            if message.get("flag") == "isFinish":
                id_order = message.get("id_order")
                index_address = message.get("index_address")
                title_message = "The driver arrived at the point"

                await DataOrder.filter(id=id_order).update(id_status=12)
                await DataOrderAddresses.filter(id_order=id_order, index_address=index_address).update(isArrived=True)
                await manager.send_personal_message(json.dumps({"status": True, "message": title_message}),
                                                    websocket)
                await send_message_to_client(id_order=id_order, id_status=12, title=title_message)

            # Обработка сообщения с флагом "drive"
            if message.get("flag") == "drive":
                id_order = message.get("id_order")
                to_index_address = message.get("to_index_address")
                title_message = f"Movement to the point {to_index_address} has begun"
                await DataOrder.filter(id=id_order).update(id_status=5)
                await manager.send_personal_message(
                    json.dumps({"status": True, "message": title_message}), websocket)
                await send_message_to_client(id_order=id_order, id_status=5, title=title_message)

            # Обработка сообщения с флагом "finishDrive"
            if message.get("flag") == "finishDrive":
                id_order = message.get("id_order")
                title_message = "The trip is over"
                await DataOrder.filter(id=id_order).update(isActive=False, id_status=11)
                await manager.send_personal_message(json.dumps({"status": True, "message": title_message}),
                                                    websocket)
                await send_message_to_client(id_order=id_order, id_status=12, title=title_message)

    except Exception:
        await error(traceback.format_exc())
        try:
            if websocket is not None:
                await manager.disconnect(websocket)
                await DataDriverMode.filter(token=token).delete()
        except Exception:
            pass


class ConnectionManagerClient:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    async def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        try:
            del clients[list(clients.keys())[list(clients.values()).index(websocket)]]
            await WaitDataSearchDriver.filter(token=list(clients.keys())[list(clients.values()).index(websocket)]).delete()
        except Exception:
            pass

    @staticmethod
    async def send_personal_message(message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                await error(traceback.format_exc())


manager_client = ConnectionManagerClient()


@router.websocket("/search-driver/{token}")
async def websocket_endpoint_client(websocket: WebSocket, token: str):
    try:
        await manager_client.connect(websocket)
        if token not in clients:
            clients[token] = websocket
        while True:
            message = await websocket.receive_text()
            message = json.loads(message)
            if "cancel" in message and message["cancel"] is True:
                order = await UsersUserOrder.filter(token=token, isActive=True).first().values()
                if order is None or len(order) == 0:
                    await manager_client.disconnect(websocket)
                    del clients[websocket]
                    return
                await DataOrder.filter(id_user=order["id_user"], id=order["id_order"]).update(isActive=False, id_status=3)
                #await DataOrder.filter(id_user=order["id_user"], id=order["id_order"]).update(id_status=3) # Дублирование кода

                try:
                    # Отправка сообщения в клиентский сокет
                    await manager_client.send_personal_message('{"status": True, "id_status": 3}', clients[token])
                    await manager_client.disconnect(websocket)

                    # Отправка сообщения водителю
                    driver_token = await DataDriverMode.filter(id_order=order["id_order"]).first().values("token")
                    if driver_token and driver_token["token"] in users:
                        driver_socket = users[driver_token["token"]]
                        await manager.send_personal_message(
                            '{"status": True, "message": "The client has canceled the order"}', driver_socket)

                except Exception:
                    await error(traceback.format_exc())
    except Exception:
        await error(traceback.format_exc())
        try:
            if websocket is not None:
                try:
                    await manager_client.disconnect(websocket)
                except Exception:
                    await error(traceback.format_exc())
                    # await WaitDataSearchDriver.filter(token=token).delete()
        except Exception:
            pass


def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Радиус Земли в километрах

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat/2) * math.sin(dlat/2) +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon/2) * math.sin(dlon/2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = R * c

    return distance


async def send_order_to_driver(id_order: int): #TODO: Проверка на радиус 3 км
    try:
        order = await DataOrder.filter(id=id_order, isActive=True).first().values()
        if order is None or len(order) == 0:
            return
        answer = await get_order_data(order)
        message = json.dumps(answer)
        await manager.broadcast(message)
    except Exception:
        await error(traceback.format_exc())


# async def send_order_to_driver(id_order: int):
#     try:
#         order = await DataOrder.filter(id=id_order, isActive=True).first().values()
#         if order is None or len(order) == 0:
#             return
#
#         order_info = await DataOrderInfo.filter(id_order=id_order).first()
#         if order_info is None:
#             return
#
#         answer = await get_order_data(order)
#
#         # Получаем всех активных водителей
#         active_drivers = await DataDriverMode.filter(isActive=True).all()
#
#         for driver in active_drivers:
#             # Проверяем расстояние между водителем и клиентом
#             distance = calculate_distance(driver.latitude, driver.longitude,
#                                           order_info.client_lat, order_info.client_lon)
#
#             # Если расстояние менее 3 км, отправляем заказ водителю
#             if distance <= 3:
#                 driver_socket = users.get(driver.token)
#                 if driver_socket:
#                     message = json.dumps(answer)
#                     await manager.send_personal_message(message, driver_socket)
#
#     except Exception:
#         await error(traceback.format_exc())


@router.post("/accept_order",
             responses=generate_responses([forbidden,
                                           you_have_active_drive]))
async def accept_order(request: Request, id_order: int):
    if await UsersUserAccount.filter(id_user=request.user, id_type_account=2).count() == 0:
        return forbidden
    if await DataOrder.filter(id_driver=request.user, isActive=True).count() > 0:
        return you_have_active_drive
    order = await DataOrder.filter(id=id_order, isActive=True, id_driver=None, id_status=4).first().values()
    if order is None or len(order) == 0:
        return order_not_found
    await DataOrder.filter(id=id_order).update(id_driver=request.user, id_status=13)
    #await DataOrder.filter(id=id_order).update(id_status=13) # Дублирование кода
    try:
        message = {
            "id_status": 13,
            "id_driver": request.user
        }
        token = await UsersUserOrder.filter(id_user=order["id_user"]).first().values()
        await manager_client.send_personal_message(json.dumps(message), clients[token["token"]])
    except Exception:
        await error(traceback.format_exc())
    answer = await get_order_data(order)
    chats = [x["id_chat"] for x in (await ChatsChatParticipant.filter(id_user=order["id_user"]).all().values())]
    chat = await ChatsChatParticipant.filter(id_user=request.user, id_chat__in=chats).first().values()
    if (chat is None or len(chat) == 0) or (await ChatsChat.filter(id=chat["id_chat"], isActive=True).count() == 0):
        new_chat = await ChatsChat.create()
        await ChatsChatParticipant.create(id_user=order["id_user"], id_chat=new_chat.id)
        await ChatsChatParticipant.create(id_user=request.user, id_chat=new_chat.id)
        chat = {"id_chat": new_chat.id}
    answer["id_chat"] = chat["id_chat"]
    driver_geo = await DataDriverMode.filter(id_driver=request.user).order_by("-id").first().values()
    _, duration = get_time_drive(driver_geo["latitude"], driver_geo["longitude"],
                                 answer["addresses"][0]["from_lat"], answer["addresses"][0]["from_lon"], 0)
    fbid = await UsersBearerToken.filter(id_user=order["id_user"]).first().values("fbid")
    await sendPush(fbid["fbid"], "Водитель найден!", f"Водитель будет через {duration} минут",
                   {"action": "driver-found", "id": order["id"]})
    try:
        token
    except Exception:
        await error(traceback.format_exc())
    return JSONResponse({"status": True,
                         "message": "Success!",
                         "order_data": answer})


@router.post("/decline_order",
             responses=generate_responses([cant_decline_in_drive_mode,
                                           forbidden,
                                           success_answer]))
async def decline_order(request: Request, id_order: int):
    if await UsersUserAccount.filter(id_user=request.user, id_type_account=2).count() == 0:
        return forbidden
    if await DataOrder.filter(id=id_order, id_driver=request.user, isActive=True).count() == 0:
        return forbidden
    order = await DataOrder.filter(id=id_order, isActive=True, id_status__not=13).first().values()
    if order is None or len(order) == 0:
        return cant_decline_in_drive_mode
    await DataOrder.filter(id=id_order).update(id_driver=None)
    await DataOrder.filter(id=id_order).update(id_status=4)
    await send_order_to_driver(id_order)
    chats = [x["id_chat"] for x in (await ChatsChatParticipant.filter(id_user=order["id_user"]).all().values())]
    chat = await ChatsChatParticipant.filter(id_user=request.user, id_chat__in=chats).first().values()
    await ChatsChat.filter(id=chat["id_chat"]).update(isActive=False)
    fbid = await UsersBearerToken.filter(id_user=order["id_user"]).first().values("fbid")
    await sendPush(fbid["fbid"], "Поиск водителя", f"Водитель отказался от поездки.\nПродолжаем поиск автоняни",
                   {"action": "decline-drive", "id": order["id"]})
    return success_answer


@router.post("/start_onetime_drive",
             responses=generate_responses([start_onetime_drive]))
async def start_onetime_drive(request: Request, item: CurrentDrive):
    order = await DataOrder.create(id_user=request.user, id_status=1, id_type_order=1)
    await DataOrderInfo.create(id_order=order.id, client_lon=item.my_location.longitude, price=item.price,
                               client_lat=item.my_location.latitude, distance=item.distance, duration=item.duration,
                               id_tariff=item.idTariff)
    for each in item.addresses:
        await DataOrderAddresses.create(id_order=order.id, from_address=each.from_address.address,
                                        to_address=each.to_address.address,
                                        from_lat=each.from_address.location.latitude,
                                        from_lon=each.from_address.location.longitude,
                                        to_lat=each.to_address.location.latitude,
                                        to_lon=each.to_address.location.longitude)
    if item.other_parametrs is not None and len(item.other_parametrs) > 0:
        for each in item.other_parametrs:
            pass
    token = str(uuid.uuid4()) + str(uuid.uuid4())
    while await UsersUserOrder.filter(token=token, isActive=True).count() > 1:
        token = str(uuid.uuid4()) + str(uuid.uuid4())
    await UsersUserOrder.create(id_user=request.user, token=token, id_order=order.id)
    await send_order_to_driver(order.id)
    await DataOrder.filter(id=order.id).update(id_status=4)
    return JSONResponse({"status": True,
                         "message": "Success!",
                         "token": token,
                         "id_order": order.id,
                         "time": str(time.time())})
