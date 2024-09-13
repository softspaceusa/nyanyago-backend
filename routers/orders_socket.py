import math

from starlette.websockets import WebSocketDisconnect

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
        self.active_connections: dict = {}

    async def connect(self, websocket: WebSocket, token: str):
        await websocket.accept()
        self.active_connections[token] = websocket
        print(f"Driver connected: {token}")

    async def disconnect(self, token: str):
        websocket = self.active_connections.get(token)
        if websocket:
            await websocket.close()
            del self.active_connections[token]
            try:
                await DataDriverMode.filter(websocket_token=token).delete()
            except Exception as e:
                print(f"Error during disconnect: {str(e)}")

    @staticmethod
    async def send_personal_message(message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
            print(f"Sent message: {message}")
        except Exception as e:
            print(f"Error sending message: {str(e)}")

    async def broadcast(self, message: str):
        for connection in self.active_connections.values():
            try:
                await connection.send_text(message)
            except Exception as e:
                print(f"Error broadcasting message: {str(e)}")


manager_driver = ConnectionManager()


async def send_message_to_client(id_order, id_status, title):
    """Отправка сообщения клиенту"""
    try:
        # Получаем заказ по id_order
        user_order = await UsersUserOrder.filter(id_order=id_order).first()

        if user_order:
            print(f"Found user_order: {user_order.token}")
            # Проверяем, есть ли токен клиента в словаре clients
            if user_order.token in clients:
                client_socket = clients[user_order.token]

                # Формируем сообщение
                message = json.dumps({"status": True, "id_status": id_status, "message": title})
                print(f"Sending to client: {message}")

                # Отправляем сообщение клиенту
                await manager_client.send_personal_message(message, client_socket)
                print("Message sent to client successfully")
            else:
                print(f"Client socket not found for token {user_order.token}")
                print(f"Available tokens: {list(clients.keys())}")
        else:
            print(f"Order {id_order} not found in UsersUserOrder")
    except Exception as e:
        print(f"Error sending message to client: {str(e)}")
        await error(traceback.format_exc())


@router.websocket("/current-drive-mode/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    try:
        await manager_driver.connect(websocket, token)
        users[token] = websocket
        while True:
            message = await websocket.receive_text()
            print(f"Received message from driver {token}: {message}")
            message = json.loads(message)

            lat = message.get("lat")
            lon = message.get("lon")
            if lat and lon:
                await DataDriverMode.filter(websocket_token=token).update(latitude=lat, longitude=lon)

            flag = message.get("flag")
            id_order = message.get("id_order")
            to_index_address = message.get("to_index_address")
            if not id_order:
                continue

            if flag == "startDrive":
                title_message = "The trip has begun"
                await DataOrder.filter(id=id_order).update(id_status=5)
                await manager_driver.send_personal_message(json.dumps({"status": True, "message": title_message}),
                                                           websocket)
                await send_message_to_client(id_order=id_order, id_status=5, title=title_message)

            if flag == "waiting":
                title_message = "Waiting start"
                await DataOrder.filter(id=id_order).update(id_status=6)
                await manager_driver.send_personal_message(json.dumps({"status": True, "message": title_message}),
                                                           websocket)
                await send_message_to_client(id_order=id_order, id_status=6, title=title_message)

            if flag == "isFinish":
                title_message = "The driver arrived at the point"
                await DataOrder.filter(id=id_order).update(id_status=12)
                await manager_driver.send_personal_message(json.dumps({"status": True, "message": title_message}),
                                                           websocket)
                await send_message_to_client(id_order=id_order, id_status=12, title=title_message)

            if flag == "drive":
                title_message = f"Movement to the point {to_index_address} has begun"
                await DataOrder.filter(id=id_order).update(id_status=5)
                await manager_driver.send_personal_message(json.dumps({"status": True, "message": title_message}),
                                                           websocket)
                await send_message_to_client(id_order=id_order, id_status=5, title=title_message)

            if flag == "finishDrive":
                title_message = "The trip is over"
                await DataOrder.filter(id=id_order).update(id_status=11)
                await manager_driver.send_personal_message(json.dumps({"status": True, "message": title_message}),
                                                           websocket)
                await send_message_to_client(id_order=id_order, id_status=11, title=title_message)

    except Exception as e:
        print(f"Error in websocket handling: {str(e)}")
        await error(traceback.format_exc())
        try:
            await manager_driver.disconnect(token)
        except Exception as e:
            print(f"Error during disconnection: {str(e)}")


class ConnectionManagerClient:
    def __init__(self):
        self.active_connections: dict = {}  # Хранит подключения клиентов по токену

    async def connect(self, websocket: WebSocket, token: str):
        await websocket.accept()
        self.active_connections[token] = websocket
        print(f"Client connected: {token}")

        order = await UsersUserOrder.filter(token=token).first()
        if order:
            order_id = order.id_order
            response = json.dumps({"order_id": order_id})
            await websocket.send_text(response)
            print(f"Sent order_id {order_id} to client {token}")
        else:
            print(f"No order found for token {token}")

    async def disconnect(self, token: str):
        websocket = self.active_connections.get(token)
        if websocket:
            await websocket.close()
            del self.active_connections[token]
            try:
                await WaitDataSearchDriver.filter(token=token).delete()
            except Exception as e:
                print(f"Error during disconnect: {str(e)}")

    @staticmethod
    async def send_personal_message(message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
            print(f"Sent message to client: {message}")
        except Exception as e:
            print(f"Error sending message: {str(e)}")

    async def broadcast(self, message: str):
        for connection in self.active_connections.values():
            try:
                await connection.send_text(message)
            except Exception as e:
                print(f"Error broadcasting message: {str(e)}")


manager_client = ConnectionManagerClient()


@router.websocket("/search-driver/{token}")
async def websocket_endpoint_client(websocket: WebSocket, token: str):
    try:
        await manager_client.connect(websocket, token)
        clients[token] = websocket
        print(f"Клиент подключен: {token}")

        # Получаем id_order для данного токена
        user_order = await UsersUserOrder.filter(token=token, isActive=True).first()
        if not user_order:
            print(f"Активный заказ не найден для токена {token}")
            return

        while True:
            try:
                message = await websocket.receive_text()
                print(f"Получено сообщение от клиента {token}: {message}")

                # Проверяем, является ли сообщение валидным JSON
                try:
                    message_data = json.loads(message)
                except json.JSONDecodeError as json_error:
                    print(f"Ошибка разбора JSON: {str(json_error)}")
                    print(f"Исходное сообщение: {message}")
                    continue  # Пропускаем это сообщение и продолжаем цикл

                # Если клиент отправляет сообщение о закрытии соединения
                if message_data.get("status") == True and message_data.get("id_status") == 3:
                    print(f"Клиент {token} запросил закрытие соединения")

                    # Отправляем сообщение водителю
                    await send_message_to_driver(user_order.id_order, message_data)

                    # Закрываем соединение
                    await websocket.close(code=1000)  # Код 1000 обозначает нормальное завершение
                    print(f"Соединение клиента {token} закрыто")
                    break

                # Добавляем id_order к сообщению
                message_data["id_order"] = user_order.id_order

                # Отправляем сообщение водителю
                await send_message_to_driver(user_order.id_order, message_data)

            except WebSocketDisconnect:
                print(f"WebSocket соединение закрыто клиентом {token}")
                break
            except Exception as e:
                print(f"Ошибка при обработке сообщения от клиента: {str(e)}")
                await error(traceback.format_exc())

    except Exception as e:
        print(f"Ошибка в обработке клиентского веб-сокета: {str(e)}")
        await error(traceback.format_exc())
    finally:
        await manager_client.disconnect(token)
        print(f"Клиент отключен: {token}")


def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Радиус Земли в километрах

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) * math.sin(dlat / 2) +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) * math.sin(dlon / 2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c

    return distance


async def send_message_to_driver(id_order, message_data):
    """Отправка сообщения водителю"""
    try:
        # Получаем заказ по id_order
        order = await DataOrder.filter(id=id_order, isActive=True).first()

        if order and order.id_driver:
            # Получаем токен водителя
            driver_mode = await DataDriverMode.filter(id_driver=order.id_driver).first()

            if driver_mode and driver_mode.websocket_token in manager_driver.active_connections:
                driver_socket = manager_driver.active_connections[driver_mode.websocket_token]

                # Формируем сообщение
                message = json.dumps(message_data)
                print(f"Отправка сообщения водителю: {message}")

                # Отправляем сообщение водителю
                await manager_driver.send_personal_message(message, driver_socket)
                print("Сообщение успешно отправлено водителю")
            else:
                print(f"Сокет водителя не найден для заказа {id_order}")
                print(f"Возможные токены водителей: {list(manager_driver.active_connections.keys())}")
        else:
            print(f"Заказ {id_order} не найден или не назначен водитель")
    except Exception as e:
        print(f"Ошибка при отправке сообщения водителю: {str(e)}")
        await error(traceback.format_exc())


async def send_order_to_driver(id_order: int):
    try:
        order = await DataOrder.filter(id=id_order, isActive=True).first().values()
        if order is None or len(order) == 0:
            return

        order_info = await DataOrderInfo.filter(id_order=id_order).first()
        if order_info is None:
            return

        answer = await get_order_data(order)

        # Получаем всех активных водителей
        active_drivers = await DataDriverMode.filter(isActive=True).all()

        for driver in active_drivers:
            # Проверяем расстояние между водителем и клиентом
            distance = calculate_distance(driver.latitude, driver.longitude,
                                          order_info.client_lat, order_info.client_lon)

            # Если расстояние менее 3 км, отправляем заказ водителю
            if distance <= 3:
                driver_socket = users.get(driver.token)
                if driver_socket:
                    message = json.dumps(answer)
                    await manager_driver.send_personal_message(message, driver_socket)

    except Exception:
        await error(traceback.format_exc())


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
