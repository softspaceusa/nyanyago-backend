import math
import json
import uuid
import time
import traceback
from fastapi import APIRouter, WebSocket, Request
from starlette.websockets import WebSocketDisconnect
import logging

from models.authentication_db import UsersUserAccount, UsersBearerToken
from models.chats_db import ChatsChatParticipant, ChatsChat
from models.drivers_db import DataDriverMode
from models.orders_db import UsersUserOrder, DataOrder, DataOrderInfo, DataOrderAddresses, WaitDataSearchDriver
from const.login_const import forbidden
from const.orders_const import start_onetime_drive, CurrentDrive, JSONResponse, you_have_active_drive, \
    cant_decline_in_drive_mode
from const.users_const import order_not_found, success_answer
from defs import error, get_time_drive, get_order_data, sendPush, get_order_data_for_socket, get_order_data_socket

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        self.active_orders: dict = {}

    async def connect(self, websocket: WebSocket, token: str):
        await websocket.accept()
        self.active_connections[token] = websocket
        logger.info(f"Driver connected: {token}")
        await self.notify_clients_about_driver(token)

        # Отправляем водителю все активные заявки клиентов
        if token in self.active_orders:
            order = self.active_orders[token]
            message = json.dumps(order, ensure_ascii=False)
            await self.send_personal_message(message, websocket)

    async def disconnect(self, token: str):
        websocket = self.active_connections.pop(token, None)
        if websocket:
            try:
                await websocket.close()
                #await DataDriverMode.filter(websocket_token=token).delete()
            except Exception as e:
                logger.info(f"Error during disconnect: {str(e)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
            logger.info(f"Sent message: {message}")
        except Exception as e:
            logger.info(f"Error sending message: {str(e)}")

    async def notify_clients_about_driver(self, driver_token: str):
        # Получаем данные водителя
        driver_data = await self.get_driver_data(driver_token)
        if not driver_data:
            return

        # Проходим по всем активным клиентам и проверяем расстояние
        for client_token, client_socket in manager_client.active_connections.items():
            # Получаем данные о клиенте и его заказе
            user_order = await UsersUserOrder.filter(token=client_token, isActive=True).first()
            if user_order:
                order_info = await DataOrderInfo.filter(id_order=user_order.id_order).first()
                if order_info and is_valid_coordinate(order_info.client_lat, order_info.client_lon):
                    # Вычисляем расстояние между водителем и клиентом
                    distance = calculate_distance(
                        driver_data["latitude"], driver_data["longitude"],
                        order_info.client_lat, order_info.client_lon
                    )
                    logger.info(f"Расстояние от водителя {driver_data['id_driver']} до клиента: {distance:.2f} км")

                    # Если расстояние меньше или равно 3 км, отправляем данные водителя клиенту
                    if distance <= 3:
                        message = json.dumps({"type": "driver_update", "data": driver_data}, ensure_ascii=False)
                        await manager_client.send_personal_message(message, client_socket)
                        logger.info(f"Отправлены данные водителя {driver_data['id_driver']} клиенту {client_token}")
                    else:
                        logger.info(f"Водитель {driver_data['id_driver']} исключен из-за расстояния ({distance:.2f} км)")

    async def notify_clients_about_driver_disconnect(self, driver_token: str):
        message = json.dumps({"type": "driver_disconnect", "driver_token": driver_token}, ensure_ascii=False)
        for client_socket in manager_client.active_connections.values():
            await manager_client.send_personal_message(message, client_socket)

    async def get_driver_data(self, token: str):
        try:
            # Получаем данные водителя
            driver = await DataDriverMode.filter(websocket_token=token).first()
            if not driver:
                return {}

            return {
                "id_driver": driver.id_driver,
                "latitude": driver.latitude,
                "longitude": driver.longitude
            }
        except Exception as e:
            logger.info(f"Error fetching driver data: {str(e)}")
            return {}


manager_driver = ConnectionManager()


async def send_active_orders_to_driver(websocket: WebSocket):
    """
    Отправляет водителю все активные заявки клиентов, которые подключены к клиентским сокетам
    """
    try:
        # Получаем всех клиентов, подключенных к сокетам
        for token, client_socket in clients.items():
            user_order = await UsersUserOrder.filter(token=token, isActive=True).first()
            if user_order:
                # Получаем информацию о заказе для сокета
                order_info = await get_order_data_for_socket(user_order.id_order)

                # Проверяем наличие данных заказа
                if order_info:
                    # Получаем местоположение клиента
                    client_lat = order_info.get('client_lat')
                    client_lon = order_info.get('client_lon')

                    # Получаем местоположение водителя
                    driver_mode = await DataDriverMode.filter(websocket_token=websocket.cookies.get('token')).first()
                    if driver_mode and is_valid_coordinate(client_lat, client_lon) and is_valid_coordinate(
                            driver_mode.latitude, driver_mode.longitude):
                        # Вычисляем расстояние между клиентом и водителем
                        distance = calculate_distance(driver_mode.latitude, driver_mode.longitude, client_lat,
                                                      client_lon)

                        # Если расстояние меньше или равно 3 км, отправляем заявку водителю
                        if distance <= 3:
                            message = json.dumps(order_info, ensure_ascii=False)
                            await manager_driver.send_personal_message(message, websocket)
                        else:
                            logger.info(f"Заявка {user_order.id_order} не отправлена водителю из-за превышения радиуса.")
                    else:
                        logger.info(f"Некорректные координаты для водителя или клиента.")
                else:
                    logger.info(f"Ошибка: get_order_data вернул null для заказа ID: {user_order.id_order}")
            else:
                logger.info(f"No active orders found for client with token: {token}")
    except Exception as e:
        logger.info(f"Error sending active orders to driver: {str(e)}")
        await error(traceback.format_exc())


async def send_message_to_client(id_order, status):
    """Отправка сообщения клиенту"""
    try:
        user_order = await UsersUserOrder.filter(id_order=id_order).first()

        if user_order and user_order.token in clients:
            client_socket = clients[user_order.token]
            message = json.dumps({"status": status})
            await manager_client.send_personal_message(message, client_socket)
        else:
            logger.info(f"Client socket not found for token {user_order.token if user_order else 'unknown'}")
    except Exception as e:
        logger.info(f"Error sending message to client: {str(e)}")
        await error(traceback.format_exc())


@router.websocket("/current-drive-mode/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    """ Сокет для водителей """
    status_mapping = {
        7: [5],
        6: [7],
        14: [6, 7, 8, 9, 10],
        11: [15],
        15: [14],
    }
    try:
        await manager_driver.connect(websocket, token)
        users[token] = websocket

        # Получаем данные о местоположении водителя
        driver_mode = await DataDriverMode.filter(websocket_token=token).first()
        if not driver_mode or not is_valid_coordinate(driver_mode.latitude, driver_mode.longitude):
            return

        # Обрабатываем активные заказы до цикла while
        await process_active_orders(driver_mode, websocket, token)

        while True:
            try:
                message = await websocket.receive_text()
                message_data = json.loads(message)
            except json.JSONDecodeError:
                await manager_driver.send_personal_message(json.dumps({"error": "Invalid JSON format"}), websocket)
                continue

            # Обновление координат водителя
            lat, lon, duration = message_data.get("lat"), message_data.get("lon"), message_data.get("duration")
            if lat is not None and lon is not None:
                await DataDriverMode.filter(websocket_token=token).update(latitude=lat, longitude=lon)
                driver_mode.latitude, driver_mode.longitude = lat, lon

                # Отправка обновленных координат клиенту, если водитель выполняет заказ
                active_order = await DataOrder.filter(id_driver=driver_mode.id_driver, isActive=True).first()
                if active_order:
                    client_token = await UsersUserOrder.filter(id_order=active_order.id).first().values('token')
                    if client_token and client_token['token'] in clients:
                        client_socket = clients[client_token['token']]
                        location_update = {
                            "lat": lat,
                            "lon": lon
                        }
                        if duration:
                            location_update["duration"] = duration
                        await manager_client.send_personal_message(json.dumps(location_update), client_socket)

                    # Автоматическая смена статуса при приближении к точке назначения
                    # await check_and_update_status_auto(driver_mode, websocket, active_order)

            # Обработка статусов водителя
            status = message_data.get("status")
            id_order = message_data.get("id_order")
            if not id_order:
                continue

            if message_data.get("type") == "order":
                cancel = message_data.get("cancel")

                if isinstance(cancel, str) and cancel.lower() == "true":
                    cancel = True

                if cancel:
                    id_order = message_data.get("id_order")
                    if not id_order:
                        continue

                    current_order = await DataOrder.filter(id=id_order, id_driver=driver_mode.id_driver).first()
                    if not current_order:
                        await manager_driver.send_personal_message(json.dumps({
                            "status": "error",
                            "message": "You are not authorized to update this order"
                        }), websocket)
                        continue

                    await DataOrder.filter(id=id_order).update(id_status=4, id_driver=None)
                    await send_message_to_client(id_order, 2)
                    await manager_driver.send_personal_message(json.dumps({"status": 2, "message": "Order canceled"}),
                                                               websocket)
                    continue

            # Проверка связи водителя с заказом
            current_order = await DataOrder.filter(id=id_order, id_driver=driver_mode.id_driver).first()
            if not current_order:
                await manager_driver.send_personal_message(json.dumps({
                    "status": "error",
                    "message": "You are not authorized to update this order"
                }), websocket)
                continue

            elif status in status_mapping:
                allowed_statuses = status_mapping[status]
                if current_order.id_status in allowed_statuses:
                    await DataOrder.filter(id=id_order).update(id_status=status)
                    if status == 11:
                        await DataOrder.filter(id=id_order).update(isActive=False)
                    await send_message_to_client(id_order, status)
                    await manager_driver.send_personal_message(json.dumps({"status": status}), websocket)
                else:
                    await manager_driver.send_personal_message(json.dumps({
                        "status": "error",
                        "message": f"Updating the status of a trip by {status} is possible with the status: {', '.join(map(str, allowed_statuses))}"
                    }), websocket)

            elif status in [5, 8, 9, 10, 12]:
                await DataOrder.filter(id=id_order).update(id_status=status)
                status_message = json.dumps({"status": status})
                await manager_driver.send_personal_message(status_message, websocket)
                await send_message_to_client(id_order, status)

    except Exception as e:
        await error(traceback.format_exc())
    finally:
        await manager_driver.disconnect(token)


async def process_active_orders(driver_mode, websocket, token):
    """ Отправляет все активные заказы в радиусе 3км водителю в сокет """
    for client_token, client_socket in manager_client.active_connections.items():
        user_order = await UsersUserOrder.filter(token=client_token, isActive=True).first()
        if user_order:
            addresses = await DataOrderAddresses.filter(id_order=user_order.id_order).first()
            if addresses and is_valid_coordinate(addresses.from_lat, addresses.from_lon):
                distance = calculate_distance(driver_mode.latitude, driver_mode.longitude,
                                              addresses.from_lat, addresses.from_lon)
                if distance <= 3:  # Проверка на расстояние не более 3 км
                    order = await get_order_data_for_socket(user_order.id_order)
                    if order:
                        message = json.dumps(order, ensure_ascii=False)
                        await manager_driver.send_personal_message(message, websocket)


async def check_and_update_status_auto(driver_mode, websocket, current_order):
    """
    Проверяет и обновляет статус автоматически при обновлении координат водителя.
    Проверка была отключена так как выполняется на фронте
    """
    if current_order.id_status == 14:  # Проверка, что заказ в статусе "в пути"
        addresses = await DataOrderAddresses.filter(id_order=current_order.id).first()
        if addresses and is_valid_coordinate(addresses.to_lat, addresses.to_lon):
            distance_to_destination = calculate_distance(driver_mode.latitude, driver_mode.longitude,
                                                         addresses.to_lat, addresses.to_lon)
            if distance_to_destination < 0.1:  # Если расстояние меньше 50 метров
                await DataOrder.filter(id=current_order.id).update(id_status=15, isActive=False)
                status_message = json.dumps({"status": 15})
                await manager_driver.send_personal_message(status_message, websocket)
                await send_message_to_client(current_order.id, 15)


class ConnectionManagerClient:
    def __init__(self):
        self.active_connections: dict = {}
        self.client_orders: dict = {}

    async def connect(self, websocket: WebSocket, token: str):
        await websocket.accept()
        self.active_connections[token] = websocket
        await self.send_drivers_to_client()

        user_order = await UsersUserOrder.filter(token=token, isActive=True).first()
        if user_order:
            self.client_orders[token] = user_order
            response = json.dumps({"order_id": user_order.id_order})
            await websocket.send_text(response)

    async def disconnect(self, token: str):
        websocket = self.active_connections.pop(token, None)
        if websocket:
            await websocket.close()
            try:
                await WaitDataSearchDriver.filter(token=token).delete()
            except Exception as e:
                logger.info(f"Error during disconnect: {str(e)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.info(f"Error sending message: {str(e)}")

    async def send_drivers_to_client(self):
        for token, client_socket in self.active_connections.items():
            user_order = await UsersUserOrder.filter(token=token, isActive=True).first()
            if user_order:
                order_info = await DataOrderInfo.filter(id_order=user_order.id_order).first()
                if order_info and is_valid_coordinate(order_info.client_lat, order_info.client_lon):
                    drivers = []
                    for driver_token in manager_driver.active_connections:
                        driver_data = await self.get_driver_data(driver_token)
                        if driver_data and is_valid_coordinate(driver_data["latitude"], driver_data["longitude"]):
                            distance = calculate_distance(driver_data["latitude"], driver_data["longitude"],
                                                          order_info.client_lat, order_info.client_lon)
                            if distance <= 3:
                                drivers.append(driver_data)

                    message = json.dumps({"type": "drivers_update", "drivers": drivers}, ensure_ascii=False)
                    await self.send_personal_message(message, client_socket)

    async def get_driver_data(self, token: str):
        try:
            # Получаем данные водителя
            driver = await DataDriverMode.filter(websocket_token=token).first()
            if not driver:
                return {}

            return {
                "id_driver": driver.id_driver,
                "latitude": driver.latitude,
                "longitude": driver.longitude
            }
        except Exception as e:
            return {}


manager_client = ConnectionManagerClient()


@router.websocket("/search-driver/{token}")
async def websocket_endpoint_client(websocket: WebSocket, token: str):
    """ Клиентский сокет """
    try:
        await manager_client.connect(websocket, token)
        clients[token] = websocket

        user_order = await UsersUserOrder.filter(token=token, isActive=True).first()
        if not user_order:
            logger.info(f"Active order not found for token {token}")
            return

        # Получаем информацию о заказе
        order_info = await DataOrderInfo.filter(id_order=user_order.id_order).first()
        if not order_info or not is_valid_coordinate(order_info.client_lat, order_info.client_lon):
            return

        # Отправляем активные заказы водителям с учетом расстояния
        for driver_token, driver_socket in manager_driver.active_connections.items():
            driver_mode = await DataDriverMode.filter(websocket_token=driver_token).first()
            if driver_mode and is_valid_coordinate(driver_mode.latitude, driver_mode.longitude):
                distance = calculate_distance(driver_mode.latitude, driver_mode.longitude,
                                              order_info.client_lat, order_info.client_lon)
                if distance <= 3:  # Проверка на расстояние не более 3 км
                    order = await get_order_data_for_socket(user_order.id_order)
                    if order:
                        message = json.dumps(order, ensure_ascii=False)
                        await manager_driver.send_personal_message(message, driver_socket)

        while True:
            try:
                message = await websocket.receive_text()
                try:
                    message_data = json.loads(message)
                except json.JSONDecodeError as e:
                    await manager_driver.send_personal_message(json.dumps({"error": "Invalid JSON format"}), websocket)
                    continue

                if message_data.get("status") == "exit":
                    await send_message_to_driver(user_order.id_order, message_data)
                if message_data.get("status") == 3:
                    await send_message_to_driver(user_order.id_order, message_data)
                    await update_order_status(user_order.id_order)
                    await websocket.send_text(json.dumps({"message": "Order cancelled"}))
                    await websocket.close(code=1000)
                    break

                # message_data["id_order"] = user_order.id_order
                # await send_message_to_driver(user_order.id_order, message_data)

            except WebSocketDisconnect:
                break

            except Exception as e:
                await error(traceback.format_exc())
    finally:
        await manager_client.disconnect(token)


def is_valid_coordinate(lat, lon):
    return -90 <= lat <= 90 and -180 <= lon <= 180


def calculate_distance(lat1, lon1, lat2, lon2):
    if not (is_valid_coordinate(lat1, lon1) and is_valid_coordinate(lat2, lon2)):
        return float('inf')  # Возвращаем бесконечность для некорректных координат

    R = 6371  # Радиус Земли в километрах
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    logger.info(f"Расстояние между точками: {distance:.2f} км")
    return distance


async def send_message_to_driver(id_order, message_data):
    """ Отправка сообщения водителю """
    try:
        order = await DataOrder.filter(id=id_order, isActive=True).first()

        if order and order.id_driver:
            driver_mode = await DataDriverMode.filter(id_driver=order.id_driver).first()

            if driver_mode and driver_mode.websocket_token in manager_driver.active_connections:
                driver_socket = manager_driver.active_connections[driver_mode.websocket_token]
                message = json.dumps(message_data)
                await manager_driver.send_personal_message(message, driver_socket)
                await DataOrder.filter(id=id_order).update(id_status=3, isActive=False)
    except Exception as e:
        await error(traceback.format_exc())


async def send_order_to_driver(id_order: int):
    try:
        order = await DataOrder.filter(id=id_order, isActive=True).first()
        if not order:
            return
        order_info = await DataOrderInfo.filter(id_order=id_order).first()
        if not order_info or not is_valid_coordinate(order_info.client_lat, order_info.client_lon):
            return

        active_drivers = await DataDriverMode.filter(isActive=True).all()

        for driver in active_drivers:
            if is_valid_coordinate(driver.latitude, driver.longitude):
                distance = calculate_distance(driver.latitude, driver.longitude,
                                              order_info.client_lat, order_info.client_lon)
                if distance <= 3:
                    driver_socket = users.get(driver.websocket_token)
                    if driver_socket:
                        message = json.dumps(await get_order_data(order.id))
                        await manager_driver.send_personal_message(message, driver_socket)

    except Exception as e:
        await error(traceback.format_exc())


@router.post("/accept_order", responses=generate_responses([forbidden, you_have_active_drive]))
async def accept_order(request: Request, id_order: int):
    """
    Роут для принятия заявки водителем. Принимает id_order и текущего пользователя.
    """
    result = {"status": True, "message": [], "order_data": None}

    is_driver = await UsersUserAccount.filter(id_user=request.user, id_type_account=2).exists()
    if not is_driver:
        return forbidden

    active_drive_exists = await DataOrder.filter(id_driver=request.user, isActive=True).exists()
    if active_drive_exists:
        return you_have_active_drive

    order = await DataOrder.filter(id=id_order, isActive=True, id_driver=None, id_status=4).first()
    if order is None:
        return order_not_found

    await DataOrder.filter(id=id_order).update(id_driver=request.user, id_status=13)
    result["message"].append("The driver is assigned to the order.")

    try:
        # Отправка сообщения клиенту в сокет
        message = {"id_status": 13, "id_driver": request.user}
        token = await UsersUserOrder.filter(id_user=order.id_user).first().values("token")

        if token and token["token"] in clients:
            await manager_client.send_personal_message(json.dumps(message), clients[token["token"]])
            result["message"].append("The message has been sent to the client.")
        else:
            result["status"] = False
            result["message"].append("The WebSocket connection to the client was not found.")

    except Exception as e:
        result["status"] = False
        result["message"].append(f"Error when sending a message to the client: {str(e)}")

    # Получение данных о заказе

    answer = await get_order_data_socket(order)
    if answer is None:
        logger.error(f"get_order_data returned None for order {order.id}")
        result["status"] = False
        result["message"].append("Failed to retrieve order data")
        return JSONResponse(result)

    result["order_data"] = answer

    # Логика по чату между клиентом и водителем
    chats = [x["id_chat"] for x in await ChatsChatParticipant.filter(id_user=order.id_user).all().values("id_chat")]
    chat = await ChatsChatParticipant.filter(id_user=request.user, id_chat__in=chats).first()

    if not chat or not await ChatsChat.filter(id=chat.id_chat, isActive=True).exists():
        new_chat = await ChatsChat.create()
        await ChatsChatParticipant.create(id_user=order.id_user, id_chat=new_chat.id)
        await ChatsChatParticipant.create(id_user=request.user, id_chat=new_chat.id)
        result["message"].append("A new chat has been created.")
        chat_id = new_chat.id
    else:
        result["message"].append("An active chat has been found.")
        chat_id = chat.id_chat

    answer["id_chat"] = chat_id

    # Геоданные водителя и расчет времени прибытия
    driver_geo = await DataDriverMode.filter(id_driver=request.user).order_by("-id").first()
    if driver_geo:
        _, duration = await get_time_drive(driver_geo.latitude, driver_geo.longitude, answer["addresses"][0]["from_lat"],
                                     answer["addresses"][0]["from_lon"], 0)
        fbid = await UsersBearerToken.filter(id_user=order.id_user).first().values("fbid")

        if fbid:
            await sendPush(fbid["fbid"], "Водитель найден!", f"Водитель будет через {duration} минут",
                           {"action": "driver-found", "id": order.id})
            result["message"].append("The push notification has been sent.")
        else:
            result["message"].append("The fbid was not found for the user.")
    else:
        result["message"].append("The driver's geodata was not found.")

    return JSONResponse(result)


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


async def update_order_status(id_order: int):
    """Обновляет статус заказа и делает его неактивным"""
    await DataOrder.filter(id=id_order).update(id_status=3, isActive=False)
    logger.info(f"Order {id_order} updated: status=3, isActive=False")


@router.post("/cancel_order")
async def update_order_status_route(request: Request, id_order: int):
    """Роут для обновления статуса заказа"""
    try:
        order = await DataOrder.filter(id=id_order).first()
        if not order:
            return JSONResponse({"status": False, "message": "Order not found"}, status_code=404)
        if order.id_user != request.user:
            return JSONResponse(
                {"status": False, "message": "Forbidden: You don't have permission to update this order"},
                status_code=403)

        await update_order_status(id_order)
        return JSONResponse({"status": True, "message": f"Order {id_order} cancelled"})
    except Exception as e:
        logger.error(f"Error updating order status: {str(e)}")
        return JSONResponse({"status": False, "message": "Internal server error"}, status_code=500)
