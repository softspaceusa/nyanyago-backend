import datetime
import decimal
import json
from fastapi.responses import RedirectResponse, JSONResponse
import requests
from fastapi import APIRouter, HTTPException, Request, Body

from const.admins_const import success_answer
from defs import generate_fb_link
from models.users_db import HistoryPaymentTink, DataUserBalance, DataUserBalanceHistory

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


@router.get("/payments_success",
            responses=generate_responses([]))
async def payments_success(order_id: str):
    terminal_key = "1692261610441"
    content_type = {"Content-Type": "application/json"}
    if await HistoryPaymentTink.filter(id_order=order_id, datetime_create=datetime.datetime.now().date()).count() == 0:
        return RedirectResponse("https://www.youtube.com/watch?v=dQw4w9WgXcQ&feature=youtu.be", 307)

    pay = await HistoryPaymentTink.filter(id_order=order_id,
                                          datetime_create=datetime.datetime.now().date()).first().values()
    data = {
            "TerminalKey": terminal_key,
            "PaymentId": pay["id_payment"],
            "Token": pay["token"],
    }
    x = requests.post("https://securepay.tinkoff.ru/v2/GetState", json=data, headers=content_type).json()
    print(x)
    if x["Status"] not in ["CONFIRMING", "CONFIRMED"]:
        return RedirectResponse("https://www.youtube.com/watch?v=dQw4w9WgXcQ&feature=youtu.be", 307)
    user =  await DataUserBalance.filter(id_user=pay["id_user"]).first().values()
    if user is None:
        await DataUserBalance.create(id_user=pay["id_user"], money=pay["amount"])
    user =  await DataUserBalance.filter(id_user=pay["id_pay"]).first().values()
    await DataUserBalance.filter(id_user=pay["id_user"]).update(money=user["money"]+decimal.Decimal(pay["amount"]))
    await DataUserBalanceHistory.create(id_user=pay["id_user"], money=decimal.Decimal(pay["amount"]), id_task=-1,
                                    isComplete=True, description="Пополнение баланса пользователя с банковской карты")
    return RedirectResponse(await generate_fb_link(), 307)


@router.get("/payments_unsuccessful",
            responses=generate_responses([]))
async def payments_success(order_id: str):
    return RedirectResponse("https://www.youtube.com/watch?v=dQw4w9WgXcQ&feature=youtu.be", 307)


@router.post("/payments_status")
async def get_status_payment(request: Request):
    print(request.client.host)
    print(request.body())
    return JSONResponse("OK", 200)

