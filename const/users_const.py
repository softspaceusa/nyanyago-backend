import re

from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from typing import Union, List
from enum import Enum


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

get_user = JSONResponse(
    {
        "status": True,
        "message": "Success!",
        "user": {
            "id": 0,
            "photo_path": "string",
            "name": "string",
            "surname": "string",
            "phone": "string",
            "isActive": True,
            "datetime_create": "string",
            "type_account": "string",
            "driver_video": "string",
            "driver_inn": "string",
            "car": {
                "mark": "string",
                "model": "string",
                "color": "string",
                "year": 0,
                "state_number": "string",
                "ctc": "string",
            },
        },
    }
)



task_to_text = {
    -1: "Пополнение баланса",
    -2: "Начисление бонусов",
    -3: "Начисление комиссии",
    -100: "Заявка на вывод денежных средств",
    -101: "Вывод денежных средств на карту",
}


class UpdateUserData(BaseModel):
    surname: str = Field(
        min_length=2,
        max_length=50,
        pattern="^[a-zA-Z]+$",
        description="Surname should contain only Latin letters.",
    )
    name: str = Field(
        min_length=2,
        max_length=50,
        pattern="^[a-zA-Z]+$",
        description="Name should contain only Latin letters.",
    )
    photo_path: Union[str, None] = None  # Может быть надо, может нет. Пока оставлю
    phone: str = Field(
        pattern=r"^\+7 \(\d{3}\) \d{3} \d{2} \d{2}$",
        description="Phone format: '+7 (999) 999 99 99'",
    )
    password: str = Field(
        min_length=8,
        description="Password with min 8 characters, containing at least one uppercase letter, one digit, and one special character",
    )

    @field_validator("password")
    def validate_password(cls, value):  # noqa
        if " " in value:
            raise ValueError("Password should not contain spaces")
        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[0-9]", value):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[!#$%&?]", value):
            raise ValueError(
                "Password must contain at least one special character from !#$%&?"
            )
        if not re.search(r"^[A-Za-z0-9!#$%&?]+$", value):
            raise ValueError(
                "Password should only contain Latin letters, digits, and special characters !#$%&?"
            )
        return value


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


class DetailedHistory(BaseModel):
    description: str
    title: str
    date: str = Field(pattern='^\d{1,2}/\d{1,2}$')
    amount: float


class GetUserMoneySuccess(BaseModel):
    status: bool = True
    message: str = "Success!"
    balance: float
    income: List[float]
    expenses: List[float]
    history: List[DetailedHistory]


class Period(str, Enum):
    current_day = "current_day"
    current_week = "current_week"
    current_month = "current_month"
    current_year = "current_year"
