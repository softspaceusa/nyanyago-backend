import math
import json
import uuid
import time
import traceback
from fastapi import APIRouter, WebSocket, Request
from starlette.websockets import WebSocketDisconnect

from models.authentication_db import UsersUserAccount, UsersBearerToken
from models.chats_db import ChatsChatParticipant, ChatsChat
from models.drivers_db import DataDriverMode, UsersDriverData, UsersCar
from models.orders_db import UsersUserOrder, DataOrder, DataOrderInfo, DataOrderAddresses, WaitDataSearchDriver
from models.static_data_db import DataCarMark, DataCarModel, DataColor
from const.login_const import forbidden
from const.orders_const import start_onetime_drive, CurrentDrive, JSONResponse, you_have_active_drive, cant_decline_in_drive_mode
from const.users_const import order_not_found, success_answer
from defs import error, get_time_drive, get_order_data, sendPush, get_order_data_for_socket

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
        print(f"Driver connected: {token}")
        await self.notify_clients_about_driver(token)

        if token in self.active_orders:
            order = self.active_orders[token]
            message = json.dumps(order, ensure_ascii=False)
            await self.send_personal_message(message, websocket)

    async def disconnect(self, token: str):
        websocket = self.active_connections.pop(token, None)
        if websocket:
            try:
                await websocket.close()
                await DataDriverMode.filter(websocket_token=token).delete()
            except Exception as e:
                print(f"Error during disconnect: {str(e)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
            print(f"Sent message: {message}")
        except Exception as e:
            print(f"Error sending message: {str(e)}")

    async def notify_clients_about_driver(self, driver_token: str):
        # Получаем данные водителя
        driver_data = await self.get_driver_data(driver_token)
        if not driver_data:
            return

        # Проходим по всем активным клиентам и проверяем расстояние
        for client_token, client_socket in manager_client.active_connections.items():
            user_order = await UsersUserOrder.filter(token=client_token, isActive=True).first()
            if user_order:
                order_info = await DataOrderInfo.filter(id_order=user_order.id_order).first()
                if order_info and is_valid_coordinate(order_info.client_lat, order_info.client_lon):
                    # Вычисляем расстояние между водителем и клиентом
                    distance = calculate_distance(
                        driver_data["latitude"], driver_data["longitude"],
                        order_info.client_lat, order_info.client_lon
                    )
                    print(f"Расстояние от водителя {driver_data['id_driver']} до клиента: {distance:.2f} км")

                    # Если расстояние меньше или равно 3 км, отправляем данные водителя клиенту
                    if distance <= 3:
                        message = json.dumps({"type": "driver_update", "data": driver_data}, ensure_ascii=False)
                        await manager_client.send_personal_message(message, client_socket)
                        print(f"Отправлены данные водителя {driver_data['id_driver']} клиенту {client_token}")
                    else:
                        print(f"Водитель {driver_data['id_driver']} исключен из-за расстояния ({distance:.2f} км)")

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

            # Получаем данные о водителе
            driver_data = await UsersDriverData.filter(id_driver=driver.id_driver).first()
            if not driver_data:
                return {}

            # Получаем данные о машине
            car = await UsersCar.filter(id=driver_data.id_car).first()
            if not car:
                return {}

            # Получаем значения из связанных таблиц
            car_mark = await DataCarMark.filter(id=car.id_car_mark).first()
            car_model = await DataCarModel.filter(id=car.id_car_model).first()
            color = await DataColor.filter(id=car.id_color).first()

            return {
                "id_driver": driver.id_driver,
                "latitude": driver.latitude,
                "longitude": driver.longitude,
                "car": {
                    "car_mark": car_mark.title if car_mark else "",
                    "car_model": car_model.title if car_model else "",
                    "color": color.title if color else "",
                    "year_create": car.year_create,
                    "state_number": car.state_number,
                    "CTC": car.ctc
                }
            }
        except Exception as e:
            print(f"Error fetching driver data: {str(e)}")
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
                        print(f"Расстояние до клиента: {distance:.2f} км")

                        # Если расстояние меньше или равно 3 км, отправляем заявку водителю
                        if distance <= 3:
                            message = json.dumps(order_info, ensure_ascii=False)
                            print(f"Sending active order {user_order.id_order} to driver: {message}")
                            await manager_driver.send_personal_message(message, websocket)
                        else:
                            print(f"Заявка {user_order.id_order} не отправлена водителю из-за превышения радиуса.")
                    else:
                        print(f"Некорректные координаты для водителя или клиента.")
                else:
                    print(f"Ошибка: get_order_data вернул null для заказа ID: {user_order.id_order}")
            else:
                print(f"No active orders found for client with token: {token}")
    except Exception as e:
        print(f"Error sending active orders to driver: {str(e)}")
        await error(traceback.format_exc())


async def send_message_to_client(id_order, id_status, title):
    """Отправка сообщения клиенту"""
    try:
        user_order = await UsersUserOrder.filter(id_order=id_order).first()

        if user_order and user_order.token in clients:
            client_socket = clients[user_order.token]
            message = json.dumps({"status": True, "id_status": id_status, "message": title})
            await manager_client.send_personal_message(message, client_socket)
        else:
            print(f"Client socket not found for token {user_order.token if user_order else 'unknown'}")
    except Exception as e:
        print(f"Error sending message to client: {str(e)}")
        await error(traceback.format_exc())


@router.websocket("/current-drive-mode/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    """ Сокет для водителей """
    try:
        await manager_driver.connect(websocket, token)
        users[token] = websocket

        # Получаем данные о местоположении водителя
        driver_mode = await DataDriverMode.filter(websocket_token=token).first()
        if not driver_mode or not is_valid_coordinate(driver_mode.latitude, driver_mode.longitude):
            print(f"Invalid driver data or coordinates for driver {token}")
            return

        # Отправляем водителю все активные заявки подключённых клиентов с учетом расстояния
        for client_token, client_socket in manager_client.active_connections.items():
            user_order = await UsersUserOrder.filter(token=client_token, isActive=True).first()
            if user_order:
                order_info = await DataOrderInfo.filter(id_order=user_order.id_order).first()
                if order_info and is_valid_coordinate(order_info.client_lat, order_info.client_lon):
                    distance = calculate_distance(driver_mode.latitude, driver_mode.longitude,
                                                  order_info.client_lat, order_info.client_lon)
                    if distance <= 3:
                        order = await get_order_data_for_socket(user_order.id_order)
                        if order:
                            message = json.dumps(order, ensure_ascii=False)
                            await manager_driver.send_personal_message(message, websocket)
                            print(f"Sent order {user_order.id_order} to driver {token}. Distance: {distance:.2f} km")
                    else:
                        print(f"Order {user_order.id_order} excluded due to distance: {distance:.2f} km")
                else:
                    print(f"Invalid order info or coordinates for order {user_order.id_order}")

        while True:
            message = await websocket.receive_text()
            print(f"Received message from driver {token}: {message}")
            message_data = json.loads(message)

            lat, lon = message_data.get("lat"), message_data.get("lon")
            if lat and lon:
                await DataDriverMode.filter(websocket_token=token).update(latitude=lat, longitude=lon)

            flag = message_data.get("flag")
            id_order = message_data.get("id_order")
            to_index_address = message_data.get("to_index_address")
            if not id_order:
                continue

            status_mapping = {
                "startDrive": {"status": 5, "message": "The trip has begun"},
                "waiting": {"status": 6, "message": "Waiting start"},
                "isFinish": {"status": 12, "message": "The driver arrived at the point"},
                "drive": {"status": 5, "message": f"Movement to the point {to_index_address} has begun"},
                "finishDrive": {"status": 11, "message": "The trip is over"}
            }

            if flag in status_mapping:
                status_info = status_mapping[flag]
                await DataOrder.filter(id=id_order).update(id_status=status_info["status"])
                await manager_driver.send_personal_message(json.dumps({"status": True, "message": status_info["message"]}), websocket)
                await send_message_to_client(id_order, status_info["status"], status_info["message"])

    except Exception as e:
        print(f"Error in websocket handling: {str(e)}")
        await error(traceback.format_exc())
    finally:
        await manager_driver.disconnect(token)


class ConnectionManagerClient:
    def __init__(self):
        self.active_connections: dict = {}
        self.client_orders: dict = {}

    async def connect(self, websocket: WebSocket, token: str):
        await websocket.accept()
        self.active_connections[token] = websocket
        await self.send_drivers_to_client()
        print(f"Client connected: {token}")

        user_order = await UsersUserOrder.filter(token=token, isActive=True).first()
        if user_order:
            self.client_orders[token] = user_order
            response = json.dumps({"order_id": user_order.id_order})
            await websocket.send_text(response)
        else:
            print(f"No order found for token {token}")

    async def disconnect(self, token: str):
        websocket = self.active_connections.pop(token, None)
        if websocket:
            await websocket.close()
            try:
                await WaitDataSearchDriver.filter(token=token).delete()
            except Exception as e:
                print(f"Error during disconnect: {str(e)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
            print(f"Sent message to client: {message}")
        except Exception as e:
            print(f"Error sending message: {str(e)}")

    async def send_drivers_to_client(self):
        for token, client_socket in self.active_connections.items():
            user_order = await UsersUserOrder.filter(token=token, isActive=True).first()
            if user_order:
                order_info = await DataOrderInfo.filter(id_order=user_order.id_order).first()
                if order_info and is_valid_coordinate(order_info.client_lat, order_info.client_lon):
                    print(f"Информация о заказе: lat={order_info.client_lat}, lon={order_info.client_lon}")
                    drivers = []
                    for driver_token in manager_driver.active_connections:
                        driver_data = await self.get_driver_data(driver_token)
                        if driver_data and is_valid_coordinate(driver_data["latitude"], driver_data["longitude"]):
                            distance = calculate_distance(driver_data["latitude"], driver_data["longitude"],
                                                          order_info.client_lat, order_info.client_lon)
                            print(f"Водитель {driver_data['id_driver']}: расстояние {distance:.2f} км")
                            if distance <= 3:
                                drivers.append(driver_data)
                            else:
                                print(f"Водитель {driver_data['id_driver']} исключен из-за расстояния")

                    print(f"Отправка {len(drivers)} водителей клиенту")
                    message = json.dumps({"type": "drivers_update", "drivers": drivers}, ensure_ascii=False)
                    await self.send_personal_message(message, client_socket)
                else:
                    print(f"Некорректные координаты заказа: {order_info.client_lat}, {order_info.client_lon}")

    async def get_driver_data(self, token: str):
        try:
            driver = await DataDriverMode.filter(websocket_token=token).first()
            if not driver:
                return {}

            driver_data = await UsersDriverData.filter(id_driver=driver.id_driver).first()
            if not driver_data:
                return {}

            car = await UsersCar.filter(id=driver_data.id_car).first()
            if not car:
                return {}

            car_mark = await DataCarMark.filter(id=car.id_car_mark).first()
            car_model = await DataCarModel.filter(id=car.id_car_model).first()
            color = await DataColor.filter(id=car.id_color).first()

            return {
                "id_driver": driver.id_driver,
                "latitude": driver.latitude,
                "longitude": driver.longitude,
                "car": {
                    "car_mark": car_mark.title if car_mark else "",
                    "car_model": car_model.title if car_model else "",
                    "color": color.title if color else "",
                    "year_create": car.year_create,
                    "state_number": car.state_number,
                    "CTC": car.ctc
                }
            }
        except Exception as e:
            print(f"Error fetching driver data: {str(e)}")
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
            print(f"Active order not found for token {token}")
            return

        # Получаем информацию о заказе
        order_info = await DataOrderInfo.filter(id_order=user_order.id_order).first()
        if not order_info or not is_valid_coordinate(order_info.client_lat, order_info.client_lon):
            print(f"Invalid order info or coordinates for order {user_order.id_order}")
            return

        # Отправляем активные заказы водителям с учетом расстояния
        for driver_token, driver_socket in manager_driver.active_connections.items():
            driver_mode = await DataDriverMode.filter(websocket_token=driver_token).first()
            if driver_mode and is_valid_coordinate(driver_mode.latitude, driver_mode.longitude):
                distance = calculate_distance(driver_mode.latitude, driver_mode.longitude,
                                              order_info.client_lat, order_info.client_lon)
                if distance <= 3:
                    order = await get_order_data_for_socket(user_order.id_order)
                    if order:
                        message = json.dumps(order, ensure_ascii=False)
                        await manager_driver.send_personal_message(message, driver_socket)
                        print(f"Sent order {user_order.id_order} to driver {driver_token}. Distance: {distance:.2f} km")
                else:
                    print(f"Driver {driver_token} excluded due to distance: {distance:.2f} km")
            else:
                print(f"Invalid driver data or coordinates for driver {driver_token}")

        while True:
            try:
                message = await websocket.receive_text()
                message_data = json.loads(message)
                if message_data.get("flag") == "cancel":
                    await send_message_to_driver(user_order.id_order, message_data)
                    await websocket.close(code=1000)
                    break
                message_data["id_order"] = user_order.id_order
                await send_message_to_driver(user_order.id_order, message_data)
            except WebSocketDisconnect:
                break
            except Exception as e:
                print(f"Error processing message from client: {str(e)}")
                await error(traceback.format_exc())
    finally:
        await manager_client.disconnect(token)


def is_valid_coordinate(lat, lon):
    return -90 <= lat <= 90 and -180 <= lon <= 180


def calculate_distance(lat1, lon1, lat2, lon2):
    if not (is_valid_coordinate(lat1, lon1) and is_valid_coordinate(lat2, lon2)):
        print(f"Некорректные координаты: ({lat1}, {lon1}) - ({lat2}, {lon2})")
        return float('inf')  # Возвращаем бесконечность для некорректных координат

    R = 6371  # Радиус Земли в километрах
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    print(f"Расстояние между точками: {distance:.2f} км")
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
            else:
                print(f"Driver socket not found for order {id_order}")
    except Exception as e:
        print(f"Error sending message to driver: {str(e)}")
        await error(traceback.format_exc())


async def send_order_to_driver(id_order: int):
    try:
        order = await DataOrder.filter(id=id_order, isActive=True).first()
        if not order:
            print(f"Заказ {id_order} не найден")
            return
        order_info = await DataOrderInfo.filter(id_order=id_order).first()
        if not order_info or not is_valid_coordinate(order_info.client_lat, order_info.client_lon):
            print(f"Информация о заказе {id_order} не найдена или координаты некорректны")
            return

        print(f"Информация о заказе {id_order}: lat={order_info.client_lat}, lon={order_info.client_lon}")

        active_drivers = await DataDriverMode.filter(isActive=True).all()
        print(f"Найдено {len(active_drivers)} активных водителей")

        for driver in active_drivers:
            if is_valid_coordinate(driver.latitude, driver.longitude):
                distance = calculate_distance(driver.latitude, driver.longitude,
                                              order_info.client_lat, order_info.client_lon)
                print(f"Водитель {driver.id_driver}: расстояние {distance:.2f} км")
                if distance <= 3:
                    driver_socket = users.get(driver.websocket_token)
                    if driver_socket:
                        message = json.dumps(await get_order_data(order.id))
                        await manager_driver.send_personal_message(message, driver_socket)
                        print(f"Отправлен заказ водителю {driver.id_driver}")
                    else:
                        print(f"Сокет водителя не найден для токена {driver.websocket_token}")
                else:
                    print(f"Водитель {driver.id_driver} исключен из-за расстояния")
            else:
                print(f"Некорректные координаты водителя {driver.id_driver}: {driver.latitude}, {driver.longitude}")
    except Exception as e:
        print(f"Ошибка при отправке заказа водителю: {str(e)}")
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
