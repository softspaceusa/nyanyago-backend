from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Union


chat_not_found_answer = JSONResponse({"status": False,
                                      "message": "Chat not found!"}, 404)
success_answer = JSONResponse({"status": True,
                               "message": "Success!"})
card_already_added = JSONResponse({"status": False,
                                   "message": "Card already added!"}, 406)
uncorrect_card_number = JSONResponse({"status": False,
                                      "message": "Uncorrect card number!"}, 404)
uncorrect_card_bank = JSONResponse({"status": False,
                                    "message": "Uncorrect card bank!"}, 405)
uncorrect_exp_date = JSONResponse({"status": False,
                                   "message": "Uncorrect experience date!"}, 407)
uncorrect_name_card = JSONResponse({"status": False,
                                    "message": "Uncorrect name card's!"}, 408)
debit_card_not_found = JSONResponse({"status": False,
                                     "message": "Debit card is not found!"}, 404)
insufficient_balance = JSONResponse({"status": False,
                                     "message": "Insufficient balance"}, 405)
order_not_found = JSONResponse({"status": False,
                                "message": "Payment order not found"}, 404)
get_money = JSONResponse({"status": True,
                          "message": "Success!",
                          "balance": 0.0,
                          "history": [
                                        {
                                            "title": "string",
                                            "amount": "string",
                                            "description": "string"
                                        }
                                    ]
                          })
add_card = JSONResponse({"status": True,
                         "message": "Success!",
                         "card_id": 0})
get_my_card = JSONResponse({"status": True,
                         "message": "Success!",
                         "cards": [
                                    {
                                        "id": 0,
                                        "card_number": "string",
                                        "full_number": "string",
                                        "exp_date": "string",
                                        "name": "string",
                                        "isActive": True,
                                    }
                         ],
                         "total": 0})
start_sbp_answer = JSONResponse({"status": True,
                                 "message": "Success!",
                                 "payment":
                                            {
                                                "PaymentId": 0,
                                                "payment_url": "string",
                                                "amount": 0
                                 }
                                })


task_to_text = {
    -1: "Пополнение баланса",
    -2: "Начисление бонусов",
    -3: "Начисление комиссии",
    -100: "Заявка на вывод денежных средств",
    -101: "Вывод денежных средств на карту",
}


class UpdateUserData(BaseModel):
    surname: Union[str, None] = None
    name: Union[str, None] = None
    photo_path: Union[str, None] = None
    password: Union[str, None] = None


class NewDebitCard(BaseModel):
    card_number: str
    exp_date: str
    name: str


class DeleteDebitCard(BaseModel):
    id: int


class AddMoney(BaseModel):
    amount: float
    payment_id: int


class UserDataPayment(BaseModel):
    ip: Union[str, None] = None
    amount: int
    card_data: str
    email: Union[str, None] = None
    phone: str
    recurrent: Union[str, None] = None


class SbpPayment(BaseModel):
    amount: int
    email: Union[str, None] = None
    phone: Union[str, None]


class ConfirmPayment(BaseModel):
    PaymentId: int
    DATA: dict
    email: Union[str, None] = None


class StartPayment(BaseModel):
    email: str
    phone: str
    amount: int
    card: str
    recurrent: Union[str, None] = None
    ip: Union[str, None] = None


class LimitOffset(BaseModel):
    limit: Union[int, None] = 30
    offset: Union[int, None] = 0


