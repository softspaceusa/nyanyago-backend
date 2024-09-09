import json

import requests
from firebase_dynamic_links import DynamicLinks

from const.static_data_const import not_user_photo
from models.authentication_db import UsersBearerToken, HistoryBearerToken, UsersUserAccount
from models.chats_db import ChatsChatParticipantToken
from const.dependency import create_access_token
from datetime import datetime as date
from uuid import uuid4
import phonenumbers
import traceback

from models.orders_db import DataScheduleRoadDriver, DataOrderInfo, DataOrderAddresses
from models.users_db import UsersUser, UsersUserPhoto


async def error(err):
    try:
        import os
        file=open("log_error.txt", "a", encoding='utf-8')
        file.write(f"\n\n###########{err}\n"
                   f"\n{date.now()}\n###########\n\n")
        file.close()
    except Exception:
        print(traceback.format_exc())


async def generate_file_name(filename):
    try:
        filename = str(filename).replace("/", ".")
        filename = str(uuid4()) + str(uuid4()) + str(date.now().timestamp()) + filename
        return filename
    except Exception:
        await error(traceback.format_exc())


async def check_correct_phone(phone):
    try:
        try:
            phone=phonenumbers.format_number(phonenumbers.parse(phone, "RU"),
                                                  phonenumbers.PhoneNumberFormat.E164)
            if len(phone) > 12 or len(phone) < 12:
                return None
        except Exception:
            return None
        return phone
    except Exception:
        await error(traceback.format_exc())


async def update_bearer_token(fbid, id_user):
    try:
        data = {
                "fbid": fbid,
                "id_user": id_user
                }
        token = await create_access_token(data)
        if await UsersBearerToken.filter(id_user=id_user).count() > 0:
            row = await UsersBearerToken.filter(id_user=id_user).first().values("fbid", "token", "datetime_create")
            await UsersBearerToken.filter(id_user=id_user).delete()
            await HistoryBearerToken.create(id_user=id_user, fbid=row["fbid"],
                                            token=row["token"])
        event = await UsersBearerToken.create(id_user=id_user, fbid=fbid, token=token)
        return event.token
    except Exception:
        await error(traceback.format_exc())


async def get_websocket_token(id_user):
    try:
        token_socket = str(uuid4()) + str(uuid4())
        while await ChatsChatParticipantToken.filter(token=token_socket).count()>0:
            token_socket = str(uuid4()) + str(uuid4())
        await ChatsChatParticipantToken.filter(id_user=id_user).delete()
        await ChatsChatParticipantToken.create(id_user=id_user, token=token_socket)
        return token_socket
    except Exception:
        await error(traceback.format_exc())


async def get_date_from_datetime(datetime_create):
    try:
        day = datetime_create.day if datetime_create.day >= 10 else "0" + str(datetime_create.day)
        month = datetime_create.month if datetime_create.month >= 10 else "0" + str(datetime_create.month)
        year = datetime_create.year if datetime_create.year >= 10 else "0" + str(datetime_create.year)
        return f"{day}.{month}.{year}"
    except Exception:
        await error(traceback.format_exc())
        return str(datetime_create)


async def validate_credit_card(card_number: str) -> bool:
    card_number = [int(num) for num in card_number]
    checkDigit = card_number.pop(-1)
    card_number.reverse()
    card_number = [num * 2 if idx % 2 == 0
                   else num for idx, num in enumerate(card_number)]
    card_number = [num - 9 if idx % 2 == 0 and num > 9
                   else num for idx, num in enumerate(card_number)]
    card_number.append(checkDigit)
    checkSum = sum(card_number)
    return checkSum % 10 == 0


FB_TOKEN = "AAAAbynLWdY:APA91bGpqTDPKviGxu3qng6_D_mDCuhUDQZfGNtanjepGyVgWWowPr6MF0Yq" \
           "Fs6ngjQ8eUghx1JjmwKddpR7DEin4CHb1GLGJftOfblbMHG0iTqxOKoTzNIzn2TnXoOwmv8_LrjRsO9Y"
headers={'Authorization':'key='+str(FB_TOKEN), 'Content-Type': 'application/json'}
async def sendPush(device_token, title, text, data):
    try:
        body = {
            'notification': {
                'title': title,
                'body': text
            },
            "data": data if data is not None else {},
            'to': device_token,
            'priority': 'high'
        }

        response = requests.post("https://fcm.googleapis.com/fcm/send", headers = headers, data=json.dumps(body))
        print(response.status_code)
        print()
        print()
        print()
        print(body)
        print()
        print()
        print()
        print(response.text)
        print()
        print()
    except Exception:
        await error(traceback.format_exc())


async def generate_fb_link(auth=False, ref="", refresh_token=""):
    try:
        if auth is True:
            link = f"https://nyanyago.ru/auth?ref={ref}&refresh_token={refresh_token}"
        else:
            link = "https://nyanyago.ru"
        api_key='AIzaSyBzjbCQeCwtYudcuXmlYkeTJy8BYb75KwA'
        domain='https://nyago.page.link'
        dl=DynamicLinks(api_key, domain, 10)
        params={
            "androidInfo": {
                "androidPackageName": 'com.nyanyago.nanny_client'
            },
            "iosInfo": {
                "iosBundleId": "com.nyanyago.nanny_client"}
        }
        return dl.generate_dynamic_link(link, False, params)
    except Exception:
        print(traceback.format_exc())


async def check_access_schedule(id_user, id_owner):
    try:
        if id_user == id_owner:
            return True
        if await UsersUserAccount.filter(id_user=id_user, id_type_account=7).count() > 0:
            return True
        if await UsersUserAccount.filter(id_user=id_user, id_type_account=2).count() > 0:
            if await DataScheduleRoadDriver.filter(id_driver=id_user).count() > 0:
                pass
        if id_user != id_owner:
            return False
        return False
    except Exception:
        await error(traceback.format_exc())
        return None


async def get_price_road(duration, distance, amount):
    try:
        T = duration
        T1 = 7
        S1 = 3
        S2 = distance
        S = S1 + S2
        M = float(amount)
        k = 1
        J = 1
        F1 = 0.03
        X5 = 0.01
        Kc = 0.02
        cost_without_cashback = ((T / T1) * S * M * k) / J
        P___ = Kc * cost_without_cashback / 100
        cost_with_cashback = cost_without_cashback + (F1 * cost_without_cashback / 100) + \
                             (X5 * cost_without_cashback / 100) + P___
        return cost_without_cashback
    except Exception:
        await error(traceback.format_exc())
        return 0


async def get_time_drive(latitude_a, longitude_a, latitude_b, longitude_b, amount):
    try:
        import googlemaps

        # Ваш API ключ Google Maps
        API_KEY = 'AIzaSyAal05yap1WdDdZrF0KrrqzcdvY3E8-D68'

        # Инициализация клиента Google Maps
        gmaps = googlemaps.Client(key=API_KEY)

        # Задаем начальные и конечные координаты
        origin = (latitude_a, longitude_a)
        destination = (latitude_b, longitude_b)

        # Получаем направление между двумя точками
        directions_result = gmaps.directions(origin, destination, mode="driving")

        # Выводим маршрут
        # for step in directions_result[0]['legs'][0]['steps']:
        #     print(step['html_instructions'])

        # Если вам нужно получить более подробную информацию, такую как расстояние или время:
        def get_time_from_google(durations):
            durations = durations.split(" ")
            times = int(float(durations[0]))
            if durations[1].lower() in ("hour", "hours"):
                times *= 60
            if durations[1].lower() in ("day", "days"):
                times *= 60 * 24
            if durations[1].lower() in ("week", "weeks"):
                times *= 60 * 24 * 7
            if durations[1].lower() in ("month", "months"):
                times *= 60 * 24 * 30
            if len(durations) == 2:
                return times
            if durations[3].lower() in ("hour", "hours"):
                times += 60 * int(float(durations[2]))
            if durations[3].lower() in ("day", "days"):
                times += 60 * 24 * int(float(durations[2]))
            if durations[3].lower() in ("week", "weeks"):
                times += 60 * 24 * 7 * int(float(durations[2]))
            if durations[3].lower() in ("month", "months"):
                times += 60 * 24 * 30 * int(float(durations[2]))
            if len(durations) == 4:
                return times
            if durations[5].lower() in ("hour", "hours"):
                times += 60 * int(float(durations[4]))
            if durations[5].lower() in ("day", "days"):
                times += 60 * 24 * int(float(durations[4]))
            if durations[5].lower() in ("week", "weeks"):
                times += 60 * 24 * 7 * int(float(durations[4]))
            if durations[5].lower() in ("month", "months"):
                times += 60 * 24 * 30 * int(float(durations[4]))
            return times

        if len(directions_result) == 0:
            return 0, 0
        distance = directions_result[0]['legs'][0]['distance']['text']
        duration = directions_result[0]['legs'][0]['duration']['text']

        print(f"Расстояние: {distance}")
        print(f"Время в пути: {duration}")
        if "," in distance:
            distance = str(distance).replace(",", "")
        duration = get_time_from_google(duration)
        distance = float(str(distance).split(" ")[0])
        x = await get_price_road(int(duration), int(distance), int(amount))
        return x, int(duration)
    except Exception:
        await error(traceback.format_exc())
        return None


async def get_order_data(order):
    try:
        user = await UsersUser.filter(id=order["id_user"], isActive=True).first().values()
        try:
            user_photo = (await UsersUserPhoto.filter(id_user=order["id_user"]).first().values())["photo_path"]
        except Exception:
            user_photo = not_user_photo
        answer = {
            "id_order": order["id"],
            "username": user["name"],
            "phone": user["phone"],
            "user_photo": user_photo,
            "amount": float((await DataOrderInfo.filter(id_order=order["id"]).first().values())["price"]),
            "id_status": order["id_status"]
        }
        addresses = await DataOrderAddresses.filter(id_order=order["id"]).order_by("id").all().values()
        for each in addresses:
            _, duration = await get_time_drive(each["from_lat"], each["from_lon"],
                                               each["to_lat"], each["to_lon"], 0)
            if "addresses" not in answer:
                answer["addresses"] = [{"from": each["from_address"], "isFinish": each["isFinish"],
                                        "to": each["to_address"], "from_lat": each["from_lat"],
                                        "from_lon": each["from_lon"], "to_lat": each["to_lat"],
                                        "to_lon": each["to_lon"], "duration": duration}]
            else:
                answer["addresses"].append({"from": each["from_address"], "isFinish": each["isFinish"],
                                            "to": each["to_address"], "from_lat": each["from_lat"],
                                            "from_lon": each["from_lon"], "to_lat": each["to_lat"],
                                            "to_lon": each["to_lon"],"duration": duration})
        return answer
    except Exception:
        await error(traceback.format_exc())

