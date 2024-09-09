from const.users_const import UpdateUserData, success_answer, SbpPayment, start_sbp_answer, StartPayment, LimitOffset, \
    task_to_text
from const.users_const import DeleteDebitCard, AddMoney, UserDataPayment, order_not_found, ConfirmPayment, get_money
from const.users_const import debit_card_not_found, get_my_card
from models.users_db import UsersUser, UsersUserPhoto, UsersVerifyAccount, DataDebitCard, DataUserBalance, \
    UsersPaymentClient
from models.users_db import DataUserBalanceHistory, HistoryPaymentTink, WaitDataPaymentTink
from models.authentication_db import UsersUserAccount, UsersReferalCode, UsersAuthorizationData, \
    UsersMobileAuthentication
from models.static_data_db import DataColor, DataCarModel, DataCarMark, DataTypeAccount
from const.static_data_const import not_user_photo, access_forbidden, DictToModel
from defs import get_websocket_token
from models.drivers_db import UsersDriverData, UsersCar
from fastapi import APIRouter, Request, HTTPException
from const.drivers_const import *
import requests
import datetime
import hashlib
import decimal
import random
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


@router.get("/get_me",
            responses=generate_responses([access_forbidden,
                                         get_driver]))
async def get_me(request: Request):
    data = DictToModel(await UsersUser.filter(id=request.user).first().values())
    account = await UsersUserAccount.filter(id_user=request.user).all().values()
    type_account = [x["id_type_account"] for x in account]
    if await UsersVerifyAccount.filter(id_user=request.user).count() == 0 or data.isActive in [False, None]:
        return access_forbidden
    if 2 in type_account and len(type_account) == 1:
        driver_data = DictToModel(await UsersDriverData.filter(id_driver=request.user).first().values())
        referal_code = DictToModel(await UsersReferalCode.filter(id_user=request.user).first().values())
        photo = await UsersUserPhoto.filter(id_user=request.user).first().values("photo_path")
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
                             "me": {
                                 "token": await get_websocket_token(request.user),
                                 "referal_code": referal_code.code,
                                 "surname": data.surname,
                                 "name": data.name,
                                 "phone": data.phone,
                                 "role": ["Водитель"],
                                 "inn": None if hasattr(driver_data, "inn") is True else driver_data.inn,
                                 "photo_path": photo,
                                 "video_path": driver_data.video_url,
                                 "date_reg": data.datetime_create.isoformat(),
                                 "carData": car,
                                 "hasAuth": False if await UsersMobileAuthentication.filter(
                                                id_user=request.user).count() == 0 else True
                            }})
    else:
        photo = await UsersUserPhoto.filter(id_user=request.user).first().values("photo_path")
        photo = photo["photo_path"] if photo is not None and "photo_path" in photo else not_user_photo
        role = await DataTypeAccount.filter(id__in=type_account).all().values()
        return JSONResponse({"status": True,
                             "message": "Success!",
                             "me": {
                                 "token": await get_websocket_token(request.user),
                                 "surname": data.surname,
                                 "name": data.name,
                                 "phone": data.phone,
                                 "role": [x["title"] for x in role],
                                 "photo_path": photo,
                                 "date_reg": data.datetime_create.isoformat(),
                                 "hasAuth": False if await UsersMobileAuthentication.filter(
                                     id_user=request.user).count() == 0 else True
                             }})


@router.put("/update_me",
            responses=generate_responses([success_answer,
                                          access_forbidden]))
async def update_me_data(request: Request, item: UpdateUserData):
    user = DictToModel(await UsersUser.filter(id=request.user).first().values())
    user_photo = await UsersUserPhoto.filter(id_user=request.user).first().values()
    if item is not None:
        if item.surname != user.surname and item.surname is not None and len(item.surname) > 0:
            await UsersUser.filter(id=request.user).update(surname=item.surname)
        if item.name != user.name and item.name is not None and len(item.name) > 0:
            await UsersUser.filter(id=request.user).update(name=item.name)
        if item.password is not None and len(item.password) > 0:
            await UsersAuthorizationData.filter(id_user=request.user).update(password=item.password)
        if item.photo_path is not None and len(item.photo_path) > 0:
            if user_photo is not None and "photo_path" in user_photo and item.photo_path != user_photo["photo_path"]:
                await UsersUserPhoto.filter(id_user=request.user).delete()
            await UsersUserPhoto.create(id_user=request.user, photo_path=item.photo_path)
        return success_answer
    return access_forbidden


@router.post("/money",
             responses=generate_responses([get_money]))
async def get_my_money(request: Request, item: Union[LimitOffset, None] = None):
    balance = await DataUserBalance.filter(id_user=request.user).first().values()
    if balance is None or len(balance) == 0:
        await DataUserBalance.create(id_user=request.user, money=decimal.Decimal(0.0))
        balance = {"money": 0.0}
    if item is not None:
        history = await DataUserBalanceHistory.filter(id_user=request.user, isComplete=True
                                                      ).offset(item.offset).limit(item.limit).all().values()
    else:
        history = await DataUserBalanceHistory.filter(id_user=request.user, isComplete=True).all().values()
    for each in history:
        each["title"] = task_to_text[each["id_task"]]
        each["date"] = f"{each['datetime_create'].date().day}/{each['datetime_create'].date().month}"
        each["amount"] = str(each["money"])
        del each["id"]
        del each["money"]
        del each["id_task"]
        del each["id_user"]
        del each["isComplete"]
        del each["datetime_create"]

    return JSONResponse({"status": True,
                         "message": "Success!",
                         "balance": float(balance["money"]),
                         "history": history})


@router.post("/get-my-card",
             responses=generate_responses([get_my_card]))
async def get_my_debit_card(request: Request):
    data = await DataDebitCard.filter(id_user=request.user, isActive__in=[True, False]).order_by("-id").all().values()
    for card in data:
        if int(card["card_number"][0]) in [5, 6]:
            card["bank"] = "MasterCard"
        elif int(card["card_number"][0]) == 4:
            card["bank"] = "Visa"
        elif int(card["card_number"][0]) == 2:
            card["bank"] = "Mir"
        else:
            card["bank"] = "Your Bank"
        card_date = card["exp_date"].split("/")
        if card["isActive"] is True and ((int("20"+card_date[1]) < datetime.datetime.now().year) or
            (int("20"+card_date[1])==datetime.datetime.now().year and int(card_date[0])<datetime.datetime.now().month)):
            await DataDebitCard.filter(id=card["id"]).update(isActive=False)
            card["isActive"] = False
        card["full_number"] = card["card_number"]
        card["card_number"] = f"****{card['card_number'][-4]}{card['card_number'][-3]}" \
                              f"{card['card_number'][-2]}{card['card_number'][-1]}"
        del card["id_user"]
        del card["datetime_create"]
    return JSONResponse({"status": True,
                         "message": "Success!",
                         "cards": data,
                         "total": len(data)})


@router.post("/delete-my-card",
             responses=generate_responses([success_answer,
                                           debit_card_not_found]))
async def delete_debit_card(request: Request, item: DeleteDebitCard):
    if await DataDebitCard.filter(id=item.id, id_user=request.user).count() == 0:
        return debit_card_not_found
    await DataDebitCard.filter(id=item.id).update(isActive=None)
    return success_answer


@router.post("/start_sbp_payment",
             responses=generate_responses([start_sbp_answer]))
async def start_sbp_payment(request: Request, item: SbpPayment):
    content_type = {"Content-Type": "application/json"}
    order_id = hashlib.md5(str(("%032x" % random.getrandbits(128))+str(request.user)).encode()).hexdigest()
    data = {
              "TerminalKey": "1692261610441",
              "Amount": item.amount,
              "OrderId": order_id,
              "Description": "Пополнение баланса аккаунта АвтоНяня",
              "PayType": "O",
              "DATA": {
                 "Phone": item.phone,
                 "Email": item.email,
                 "TinkoffPayWeb": "true",
                 "Device": "Mobile",
                 "DeviceOs": "Android",
                 "DeviceWebView": "true",
                 "DeviceBrowser": "Chrome",
                 "notificationEnableSource": "sbpqr"
              }
    }
    init_data = requests.post("https://securepay.tinkoff.ru/v2/Init", json=data, headers=content_type).json()
    if init_data["Success"] is False:
        print(init_data)
        raise HTTPException(505, detail=init_data)
    qr_data = {
        "PaymentId": init_data["PaymentId"],
        "TerminalKey": "1692261610441",
        "Token": hashlib.sha256(f"{item.amount}cz9mvi6nawsft86w"
                                f"{init_data['PaymentId']}1692261610441".encode()).hexdigest(),

    }
    sbp = requests.post("https://securepay.tinkoff.ru/v2/GetQr", headers=content_type, json=qr_data)
    await HistoryPaymentTink.create(id_user=request.user, id_payment=init_data["PaymentId"], id_order=order_id,
                                    amount=item.amount)
    return JSONResponse({"status": True,
                         "message": "Success!",
                         "payment": {
                             "amount": item.amount,
                             "PaymentId": init_data["PaymentId"],
                             "payment_url": sbp.json()["Data"]
                         }})


@router.post("/start_payment")
async def generate_url_for_payment(request: Request, item: UserDataPayment):
    print(item.__dict__)
    content_type = {"Content-Type": "application/json"}
    order_id = hashlib.md5(str(("%032x" % random.getrandbits(128))+str(request.user)).encode()).hexdigest()
    data = {
              "TerminalKey": "1692261610441",
              "Amount": item.amount,
              "OrderId": order_id,
              "Description": "Пополнение баланса аккаунта АвтоНяня",
              "SuccessURL": f"https://nynyago.ru/api/v1.0/payments/payments_success?order_id={order_id}",
              "NotificationURL": f"https://nynyago.ru/api/v1.0/payments/payments_status/{order_id}",
              "FailURL": "https://nynyago.ru/api/v1.0/payments/payments_unsuccessful?order_id={order_id}",
              "PayType": "O",
              "DATA": {
                 "Phone": item.phone,
                 "Email": item.email,
                 "TinkoffPayWeb": "true",
                 "Device": "Mobile",
                 "DeviceOs": "Android",
                 "DeviceWebView": "true",
                 "DeviceBrowser": "Chrome"
              }
            }
    init_data = requests.post("https://securepay.tinkoff.ru/v2/Init", json=data, headers=content_type).json()
    if init_data["Success"] is False:
        print(init_data)
        raise HTTPException(505, detail=init_data)
    check_data = {
                  "PaymentId": init_data["PaymentId"],
                  "TerminalKey": "1692261610441",
                  "CardData": item.card_data,
                  "Token": hashlib.sha256(f"{item.amount}cz9mvi6nawsft86w"
                                          f"{init_data['PaymentId']}1692261610441".encode()).hexdigest()
                }
    check_3ds_data = requests.post("https://securepay.tinkoff.ru/v2/Check3dsVersion", json=check_data, headers=content_type).json()
    if item.ip is None:
        item.ip = "02a3:06f0:0004:0000:0000:0000:0000:0edf"
    if check_3ds_data["Success"] is False:
        print(check_3ds_data)
        raise HTTPException(506, detail=check_3ds_data)
    if check_3ds_data["Version"] == "2.1.0":
        await WaitDataPaymentTink.create(id_user=request.user, id_payment=init_data["PaymentId"], id_order=order_id,
                                         card_data=item.card_data, ip=item.ip, amount=item.amount,
                                         token=hashlib.sha256(f"{item.amount}cz9mvi6nawsft86w{init_data['PaymentId']}"
                                                              f"1692261610441".encode()).hexdigest(),
                                         TdsServerTransID=check_3ds_data["TdsServerTransID"])
        return JSONResponse({"is3DsVersion2": True,
                             "TerminalKey": "1692261610441",
                             "PaymentId": init_data["PaymentId"],
                             "serverTransId": check_3ds_data["TdsServerTransID"],
                             "ThreeDSMethodURL": check_3ds_data["ThreeDSMethodURL"]})
    confirm_payment = {
                        "PaymentId": init_data["PaymentId"],
                        "TerminalKey": "1692261610441",
                        "Token": hashlib.sha256(f"{item.amount}cz9mvi6nawsft86w"
                                                f"{init_data['PaymentId']}1692261610441".encode()).hexdigest(),
                        "IP": item.ip,
                        "CardData": item.card_data,
                        "Amount": item.amount,
                        "deviceChannel": "02"
    }
    if item.email is not None and len(item.email) > 0:
        confirm_payment["SendEmail"] = True
        confirm_payment["InfoEmail"] = item.email
    confirm_payment_data = requests.post("https://securepay.tinkoff.ru/v2/FinishAuthorize", json=confirm_payment, headers=content_type).json()
    token = hashlib.sha256(f"{item.amount}cz9mvi6nawsft86w{init_data['PaymentId']}1692261610441".encode()).hexdigest()
    await HistoryPaymentTink.create(id_order=order_id, amount=item.amount, id_user=request.user, ip=item.ip,
                                card_data=item.card_data, token=token, id_payment=init_data["PaymentId"])
    if confirm_payment_data["Success"] is False:
        print(confirm_payment_data)
        raise HTTPException(507, detail=confirm_payment_data)
    return JSONResponse({"status": True,
                         "message": "Success!",
                         "is3DsVersion2": True if check_3ds_data["Version"] == "2.1.0" else False\
                                            if check_3ds_data["Version"] == "1.0.0" else None,
                         "serverTransId": check_3ds_data["TdsServerTransID"] if "TdsServerTransID" in check_3ds_data \
                                            and check_3ds_data["TdsServerTransID"] is not None else None,
                         "acsUrl": confirm_payment_data["ACSUrl"],
                         "md": confirm_payment_data["MD"],
                         "paReq": confirm_payment_data["PaReq"],
                         "TerminalKey": "1692261610441",
                         "acsTransId": None if "AcsTransId" not in confirm_payment_data or \
                                    confirm_payment_data["AcsTransId"] is None else confirm_payment_data["AcsTransId"]})


@router.post("/confirm_payment")
async def confirm_payment_3dsV2(request: Request, item: ConfirmPayment):
    content_type = {"Content-Type": "application/json"}
    data = await WaitDataPaymentTink.filter(id_user=request.user, id_payment=item.PaymentId).first().values()
    if data is None:
        return order_not_found
    await WaitDataPaymentTink.filter(id_user=request.user, id_payment=item.PaymentId).delete()
    confirm_payment = {
                        "PaymentId": item.PaymentId,
                        "TerminalKey": "1692261610441",
                        "Token": hashlib.sha256(f"{data['amount']}cz9mvi6nawsft86w"
                                                f"{item.PaymentId}1692261610441".encode()).hexdigest(),
                        "IP": data["ip"],
                        "CardData": data["card_data"],
                        "Amount": data["amount"],
                        "deviceChannel": "02",
                        "DATA": item.DATA
    }
    if item.email is not None and len(item.email) > 0:
        confirm_payment["SendEmail"] = True
        confirm_payment["InfoEmail"] = item.email
    confirm_payment_data = requests.post("https://securepay.tinkoff.ru/v2/FinishAuthorize", json=confirm_payment, headers=content_type).json()
    token = hashlib.sha256(f"{data['amount']}cz9mvi6nawsft86w{item.PaymentId}1692261610441".encode()).hexdigest()
    await HistoryPaymentTink.create(id_order=data["id_order"], amount=data["amount"], id_user=request.user, ip=data["ip"],
                                card_data=data["card_data"], token=token, id_payment=item.PaymentId)
    print(confirm_payment_data)
    if confirm_payment_data["Success"] is False:
        print(confirm_payment_data)
        raise HTTPException(507, detail=confirm_payment_data)
    return JSONResponse({"status": True,
                         "message": "Success!",
                         "is3DsVersion2": True,
                         "serverTransId": confirm_payment_data["TdsServerTransId"],
                         "acsUrl": confirm_payment_data["ACSUrl"] if "ACSUrl" in confirm_payment_data else None,
                         "md": confirm_payment_data["MD"] if "MD" in confirm_payment_data else None,
                         "paReq": confirm_payment_data["PaReq"] if "PaReq" in confirm_payment_data else None,
                         "TerminalKey": "1692261610441",
                         "acsTransId": None if "AcsTransId" not in confirm_payment_data or \
                                    confirm_payment_data["AcsTransId"] is None else confirm_payment_data["AcsTransId"]})



@router.post("/add_money",
             responses=generate_responses([success_answer]))
async def add_money(request: Request, item: AddMoney):
    content_type = {"Content-Type": "application/json"}
    if await HistoryPaymentTink.filter(id_user=request.user, id_payment=item.payment_id) == 0:
        raise HTTPException(404, "Payment id not found or not your!")

    pay = await HistoryPaymentTink.filter(id_user=request.user, id_payment=item.payment_id).first().values()
    data = {
            "TerminalKey": "1692261610441",
            "PaymentId": item.payment_id,
            "Token": pay["token"],
    }
    x = requests.post("https://securepay.tinkoff.ru/v2/GetState", json=data, headers=content_type).json()
    print(x)
    if x["Status"] not in ["CONFIRMING", "CONFIRMED"]:
        raise HTTPException(402, "Unsuccessful update balance!")
    user =  await DataUserBalance.filter(id_user=request.user).first().values()
    if user is None:
        await DataUserBalance.create(id_user=request.user, money=item.amount)
    user =  await DataUserBalance.filter(id_user=request.user).first().values()
    await DataUserBalance.filter(id_user=request.user).update(money=user["money"]+decimal.Decimal(item.amount))
    await DataUserBalanceHistory.create(id_user=request.user, money=decimal.Decimal(item.amount), id_task=-1,
                                    isComplete=True, description="Пополнение баланса пользователя с банковской карты")
    return success_answer


@router.post("/start-payment",
             responses=generate_responses([success_answer]))
async def start_tinkoff_payment(request: Request, item: StartPayment):
    print(item.__dict__)
    terminal_key = "1692261610441"
    password = "cz9mvi6nawsft86w"
    content_type = {"Content-Type": "application/json"}
    order_id = hashlib.md5(str(("%032x" % random.getrandbits(128))+str(request.user)).encode()).hexdigest()
    token = hashlib.sha256(f"{item.amount}{order_id}{password}{terminal_key}".encode()).hexdigest()
    if await UsersPaymentClient.filter(id_user=request.user).count() == 0:
        customer_key = hashlib.md5((str(uuid.uuid4())+str(request.user)+str(uuid.uuid4())).encode()).hexdigest()
        while await UsersPaymentClient.filter(customer_key=customer_key).count() > 0:
            customer_key = hashlib.md5(str(uuid.uuid4()) + request.user + str(uuid.uuid4())).hexdigest()
        client = {
            "TerminalKey": terminal_key,
            "CustomerKey": customer_key,
            "Email": item.email,
            "Phone": item.phone,
            "Token": token
        }
        new_client = requests.post("https://securepay.tinkoff.ru/v2/AddCustomer", json=client, headers=content_type)
        if new_client.json()["Success"] is True:
            await UsersPaymentClient.create(id_user=request.user, customer_key=customer_key)
        else:
            return access_forbidden
    client = await UsersPaymentClient.filter(id_user=request.user).first().values()
    data = {
        "TerminalKey": terminal_key,
        "Amount": item.amount,
        "OrderId": order_id,
        "CustomerKey": client["CustomerKey"],
        "Description": "Пополнение баланса аккаунта Няня Го",
        "Recurrent": item.recurrent,
        "PayType": "O",
        "SuccessURL": f"https://nynyago.ru/api/v1.0/payments/payments_success?order_id={order_id}",
        "NotificationURL": f"https://nynyago.ru/api/v1.0/payments/payments_status/{order_id}",
        "FailURL": "https://nynyago.ru/api/v1.0/payments/payments_unsuccessful?order_id={order_id}",
        "DATA": {
            "Phone": item.phone,
            "Email": item.email,
            "TinkoffPayWeb": "true",
            "Device": "Mobile",
            "DeviceOs": "Android",
            "DeviceWebView": "true",
            "DeviceBrowser": "Chrome"
        }
    }
    init_data = requests.post("https://securepay.tinkoff.ru/v2/Init", json=data, headers=content_type).json()
    if init_data["Success"] is False:
        print(init_data)
        raise HTTPException(505, detail=init_data)
    check_data = {
        "PaymentId": init_data["PaymentId"],
        "TerminalKey": terminal_key,
        "CardData": item.card_data,
        "Token": hashlib.sha256(f"{item.amount}{password}{init_data['PaymentId']}{terminal_key}".encode()).hexdigest()
    }
    check_3ds_data = requests.post("https://securepay.tinkoff.ru/v2/Check3dsVersion",
                                                json=check_data, headers=content_type).json()
    if item.ip is None:
        item.ip = "02a3:06f0:0004:0000:0000:0000:0000:0edf"
    if check_3ds_data["Success"] is False:
        print(check_3ds_data)
        raise HTTPException(506, detail=check_3ds_data)
    if check_3ds_data["Version"] == "2.1.0":
        await WaitDataPaymentTink.create(id_user=request.user, id_payment=init_data["PaymentId"], id_order=order_id,
                                         card_data=item.card_data, ip=item.ip, amount=item.amount,
                                         token=hashlib.sha256(f"{item.amount}{password}{init_data['PaymentId']}"
                                                              f"{terminal_key}".encode()).hexdigest(),
                                         TdsServerTransID=check_3ds_data["TdsServerTransID"])
        return JSONResponse({"is3DsVersion2": True,
                             "TerminalKey": terminal_key,
                             "PaymentId": init_data["PaymentId"],
                             "serverTransId": check_3ds_data["TdsServerTransID"],
                             "ThreeDSMethodURL": check_3ds_data["ThreeDSMethodURL"]})
    confirm_payment = {
        "PaymentId": init_data["PaymentId"],
        "TerminalKey": terminal_key,
        "Token": hashlib.sha256(f"{item.amount}{password}{init_data['PaymentId']}{terminal_key}".encode()).hexdigest(),
        "IP": item.ip,
        "CardData": item.card_data,
        "Amount": item.amount,
        "deviceChannel": "02"
    }
    if item.email is not None and len(item.email) > 0:
        confirm_payment["SendEmail"] = True
        confirm_payment["InfoEmail"] = item.email
    confirm_payment_data = requests.post("https://securepay.tinkoff.ru/v2/FinishAuthorize",
                                                    json=confirm_payment, headers=content_type).json()
    token = hashlib.sha256(f"{item.amount}{password}{init_data['PaymentId']}{terminal_key}".encode()).hexdigest()
    await HistoryPaymentTink.create(id_order=order_id, amount=item.amount, id_user=request.user, ip=item.ip,
                                    card_data=item.card_data, token=token, id_payment=init_data["PaymentId"])
    if confirm_payment_data["Success"] is False:
        print(confirm_payment_data)
        raise HTTPException(507, detail=confirm_payment_data)
    return JSONResponse({"status": True,
                         "message": "Success!",
                         "is3DsVersion2": True if check_3ds_data["Version"] == "2.1.0" else False \
                             if check_3ds_data["Version"] == "1.0.0" else None,
                         "serverTransId": check_3ds_data["TdsServerTransID"] if "TdsServerTransID" in check_3ds_data \
                                                        and check_3ds_data["TdsServerTransID"] is not None else None,
                         "acsUrl": confirm_payment_data["ACSUrl"],
                         "md": confirm_payment_data["MD"],
                         "paReq": confirm_payment_data["PaReq"],
                         "TerminalKey": terminal_key,
                         "acsTransId": None if "AcsTransId" not in confirm_payment_data or \
                                    confirm_payment_data["AcsTransId"] is None else confirm_payment_data["AcsTransId"]})


