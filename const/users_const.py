import re

from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator, validator
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
                          "income": [0],
                          "expenses": [0],
                          "history": [
                                        {
                                            "title": "string",
                                            "amount": "string",
                                            "description": "string",
                                            "date": "string"
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

user_not_found = JSONResponse({"status": False,
                               "message": "User not found!"}, 404)


task_to_text = {
    -1: "Пополнение баланса",
    -2: "Начисление бонусов",
    -3: "Начисление комиссии",
    -4: "Списание половины стоимости заказа (из-за отмены)",
    -100: "Заявка на вывод денежных средств",
    -101: "Вывод денежных средств на карту",
}


class UpdateUserData(BaseModel):
    surname: Union[str, None]
    name: Union[str, None]
    photo_path: Union[str, None] = None  # Может быть надо, может нет. Пока оставлю
    phone: Union[str, None] = Field(
        pattern=r"^\+7 \(\d{3}\) \d{3} \d{2} \d{2}$",
        description="Phone format: '+7 (999) 999 99 99'",
    )
    password: Union[str, None] = Field(
        default=None,
        min_length=8,
        description="Password with min 8 characters",
    )


class NewDebitCard(BaseModel):
    card_number: str
    exp_date: str
    name: str

    @field_validator('card_number')
    @classmethod
    def validate_card_number(cls, value: str) -> str:
        # Удаляем все пробелы и проверяем, что это 16 цифр
        cleaned_number = ''.join(filter(str.isdigit, value))  # noqa
        if not cleaned_number.isdigit() or len(cleaned_number) != 16:
            raise ValueError('Card number must be exactly 16 digits')
        return value

    @field_validator('exp_date')
    @classmethod
    def validate_exp_date(cls, value: str) -> str:
        pattern = r'^(0[1-9]|1[0-2])\/\d{2}$'
        if not re.match(pattern, value):
            raise ValueError('Expiration date must be in MM/YY format (e.g., 03/26)')

        # Дополнительная проверка на валидность месяца
        month = int(value.split('/')[0])
        if month < 1 or month > 12:
            raise ValueError('Month must be between 01 and 12')
        return value

    @field_validator('name')
    @classmethod
    def validate_name(cls, value: str) -> str:
        # Проверяем, что имя состоит из двух слов на английском через пробел
        pattern = r'^[A-Za-z]+\s[A-Za-z]+$'
        if not re.match(pattern, value):
            raise ValueError(
                'Name must consist of two English words separated by a space')
        return value


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
