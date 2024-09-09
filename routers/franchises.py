from models.drivers_db import UsersDriverCard, UsersDriverData, UsersDriverAnswer, UsersCar
from models.static_data_db import DataCarTariff
from models.users_db import UsersUser, UsersUserPhoto, UsersVerifyAccount, UsersReferalUser, UsersFranchiseUser, \
    DataUserBalance
from models.users_db import HistoryRequestPayment, DataUserBalanceHistory
from models.authentication_db import UsersUserAccount, UsersReferalCode, UsersAuthorizationData, WaitDataVerifyDriver
from const.dependency import has_access_partner, has_access_franchise_admin, has_access_franchise
from const.login_const import uncorrect_phone, user_already_creates
from defs import check_correct_phone, error, get_date_from_datetime
from const.static_data_const import not_user_photo, access_forbidden, get_tariffs
from fastapi import APIRouter, Request, Depends
from const.users_const import success_answer
from const.franchises_const import *
from const.admins_const import *
from smsaero import SmsAero
import traceback
import decimal
import hashlib
import random
import json


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


@router.post("/get-my-referals",
             dependencies=[Depends(has_access_partner)],
             responses=generate_responses([user_not_found,
                                           get_my_referals]))
async def get_partner_by_id(request: Request):
    total_sum, total_percent = 0, 0
    if await UsersUser.filter(isActive=True, id=request.user).count() == 0:
        return user_not_found
    data = await UsersUser.filter(id=request.user).first().values()
    refer = await UsersReferalCode.filter(id_user=request.user).first().values()
    photo = await UsersUserPhoto.filter(id_user=request.user).first().values()
    photo = photo["photo_path"] if photo is not None and "photo_path" in photo else not_user_photo
    referals = await UsersReferalUser.filter(id_user=request.user).order_by("-id").all().values()
    for ref in referals:
        refer_data = await UsersUser.filter(id=ref["id_user_referal"]).first().values()
        refer_photo = await UsersUserPhoto.filter(id_user=ref["id_user_referal"]).first().values()
        refer_photo = refer_photo["photo_path"] if refer_photo is not None and "photo_path" in photo else not_user_photo
        ref["name"] = refer_data["name"]
        ref["surname"] = refer_data["surname"]
        ref["date_reg"] = await get_date_from_datetime(refer_data["datetime_create"])
        ref["photo_path"] = refer_photo
        ref["all_incoming"] = random.randint(0, 99999)
        ref["get_percent"] = float("0."+str(refer["percent"]))*ref["all_incoming"]
        total_sum += ref["all_incoming"]
        total_percent += float("0."+str(refer["percent"]))*ref["all_incoming"]
        del ref["datetime_create"]
        del ref["id"]
        del ref["id_user"]
        ref["id"] = ref["id_user_referal"]
    return JSONResponse({"status": True,
                         "message": "Success!",
                         "partner": {
                             "name": data["name"],
                             "surname": data["surname"],
                             "phone": data["phone"],
                             "photo_path": photo,
                             "referal_code": refer["code"],
                             "referal_percent": refer["percent"],
                             "all_incoming": total_sum,
                             "get_percent": total_percent,
                             "referals": referals
                         }})


@router.post("/new_user",
             dependencies=[Depends(has_access_franchise_admin)],
             responses=generate_responses([success_answer,
                                           uncorrect_phone,
                                           user_already_creates,
                                           unsupported_role,
                                           new_user_message_dont_delivery]))
async def new_user(item: NewUser, request: Request):
    item.phone = await check_correct_phone(item.phone)
    if item.phone is None: return uncorrect_phone
    if await UsersUser.filter(phone=item.phone).count()>0 and item.role != 5:
        return user_already_creates
    if item.role == 5 and item.referal_code is not None and len(item.referal_code) > 0:
        partner = await UsersUser.filter(phone=item.phone).first().values()
        if partner is not None:
            ref = await UsersReferalCode.filter(id_user=partner["id"]).first().values()
            if item.referal_code == ref["code"] and await UsersFranchiseUser.filter(id_user=partner["id"]).count() == 0:
                franchise = await UsersFranchiseUser.filter(id_user=request.user).first().values()
                await UsersFranchiseUser.create(id_user=partner["id"], id_franchise=franchise["id"])
                return success_answer
        return add_partner_not_found
    if item.role not in [3, 4]:
        return unsupported_role
    user = await UsersUser.create(phone=item.phone, name=item.name, surname=item.surname)
    await UsersAuthorizationData.create(id_user=user.id, login=item.phone,
                                            password=str((hashlib.md5(item.password.encode())).hexdigest()))
    await UsersVerifyAccount.create(id_user=user.id)
    await UsersUserAccount.create(id_user=user.id, id_type_account=item.role)
    try:
        api = SmsAero("auto.nyany@yandex.ru", "344334Auto")
        api.send(item.phone, f"Ваши данные для входа в аккаунт АвтоНяни:\n\n"
                             f"Логин: {item.phone}\n"
                             f"Пароль: {item.password}\n")
    except Exception:
        await error(traceback.format_exc())
        return new_user_message_dont_delivery
    return success_answer



@router.get("/get_payment_request",
            responses=generate_responses([payment_requests]))
async def get_payment_requests(request: Request):
    franchise = await UsersFranchiseUser.filter(id_franchise=(await UsersFranchiseUser.filter(id_user=request.user)
                                                                    .first().values())["id_franchise"]).all().values()
    driver, result = [], []
    for x in franchise:
        if await UsersVerifyAccount.filter(id_user=x["id_user"]).count() > 0 and \
                await UsersUserAccount.filter(id_user=x["id_user"], id_type_account=2).count() > 0:
            driver.append(x["id_user"])
    requests = await HistoryRequestPayment.filter(id_user__in=driver, isCashback=False,
                                                  isSuccess=False, isActive=True).order_by("id").all().values()
    for req in requests:
        del req["id_card"]
        del req["id_history"]
        del req["isCashback"]
        del req["isActive"]
        del req["isSuccess"]
        del req["datetime_create"]
        user = await UsersUser.filter(id=req["id_user"]).first().values()
        if user is None or user["isActive"] is not True:
            continue
        req["money"] = "%.2f" % req["money"]
        req["surname"] = user["surname"]
        req["name"] = user["name"]
        photo = await UsersUserPhoto.filter(id_user=req["id_user"]).order_by("-id").first().values()
        req["photo_path"] = photo["photo_path"] if photo is not None and "photo_path" in photo else not_user_photo
        result.append(req)
    return JSONResponse({"status": True,
                         "message": "Success!",
                         "result": result})


@router.get("/get_new_drivers",
            responses=generate_responses([get_new_drivers,
                                          not_found_request]))
async def get_new_drivers_data(request: Request):
    if await WaitDataVerifyDriver.filter().count() == 0:
        return not_found_request
    my_ref = await UsersFranchiseUser.filter(id_user=request.user).order_by("-id").first().values()
    data = await WaitDataVerifyDriver.filter().all().values()
    data = [x["id_driver"] for x in data]
    data = await UsersFranchiseUser.filter(id_franchise=my_ref["id_franchise"], id_user__in=data).all().values()
    result = []
    for driver in data:
        driver_info = await UsersUser.filter(id=driver["id_user"]).first().values()
        driver_info["datetime_create"] = driver_info["datetime_create"].isoformat()
        driver_info["status"] = "Не подтверждён"
        photo = await UsersUserPhoto.filter(id_user=driver_info["id"]).first().values()
        photo = not_user_photo if photo is None else photo["photo_path"]
        driver_info["photo_path"] = photo
        result.append(driver_info)
    return JSONResponse({"status": True,
                         "message": "Success!",
                         "drivers": result})


@router.get("/drivers",
            dependencies=[Depends(has_access_franchise)],
            responses=generate_responses([get_new_drivers]))
async def get_all_drivers(request: Request):
    my_ref = await UsersFranchiseUser.filter(id_user=request.user).order_by("-id").first().values()
    data = [x["id_user"] for x in (await UsersFranchiseUser.filter(id_franchise=my_ref["id_franchise"]).all().values())]
    data = [x["id_user"] for x in (await UsersUserAccount.filter(id_user__in=data, id_type_account=2).all().values())]
    result = []
    for driver in data:
        driver_info = await UsersUser.filter(id=driver).first().values()
        status = await WaitDataVerifyDriver.filter(id_driver=driver).count()
        driver_info["status"] = "Не подтверждён" if status != 0 else "Активен"
        if driver_info["status"] == "Активен":
            if await UsersVerifyAccount.filter(id_user=driver).count() == 0:
                driver_info["status"] = "Заблокирован"
            if driver_info["isActive"] is None:
                driver_info["status"] = "Удалён"
        photo = await UsersUserPhoto.filter(id_user=driver_info["id"]).first().values()
        photo = not_user_photo if photo is None else photo["photo_path"]
        driver_info["photo_path"] = photo
        result.append(driver_info)
    for i in range(len(result) - 1):
        for j in range(len(result) - i - 1):
            if result[j]["datetime_create"] < result[j + 1]["datetime_create"]:
                result[j], result[j + 1] = result[j + 1], result[j]
    for each in result:
        each["datetime_create"] = each["datetime_create"].isoformat()
    return JSONResponse({"status": True,
                         "message": "Success!",
                         "drivers": result})


@router.post("/agree_payment_request",
             responses=generate_responses([not_found_payment_request,
                                           success_answer]))
async def agree_output_payment(item: OutputPayment):
    if await HistoryRequestPayment.filter(id=item.id_payment, id_user=item.id_driver, isCashback=False,
                                            isSuccess=False, isActive=True).count() == 0:
        return not_found_payment_request
    data = await HistoryRequestPayment.filter(id=item.id_payment, id_user=item.id_driver, isCashback=False,
                                                isSuccess=False, isActive=True).first().values()
    await HistoryRequestPayment.filter(id=item.id_payment, id_user=item.id_driver, isCashback=False,
                                 isSuccess=False, isActive=True).update(isSuccess=True, isActive=False)
    await DataUserBalanceHistory.filter(id=data["id_history"]).update(description="Вывод ЗП", id_task=-101)
    return success_answer


@router.get("/tariffs",
            responses=generate_responses([get_tariffs]))
async def get_tariffs(request: Request):
    my_ref = await UsersFranchiseUser.filter(id_user=request.user).first().values()
    data = await DataCarTariff.filter(id_franchise=my_ref["id_franchise"]).order_by("id").\
                                            all().values("id", "title", "amount", "photo_path",
                                                         "description", "isActive")
    for each in data:
        each["amount"] = float(each["amount"])
        each["isAvailable"] = True
    return JSONResponse({"status": True,
                         "message": "Success!",
                         "tariffs": data})


@router.post("/tariff",
             responses=generate_responses([success_answer,
                                           access_forbidden]))
async def new_tariff(request: Request, item: NewTariff):
    if await UsersUserAccount.filter(id_user=request.user, id_type_account=6).count() == 0:
        return access_forbidden
    my_ref = await UsersFranchiseUser.filter(id_user=request.user).first().values()
    data = await DataCarTariff.filter(id_franchise=my_ref["id_franchise"]).order_by("-amount").first().values()
    if data["title"].lower() in ("эконом", "комфорт", "комфорт+", "бизнес", "минивэн"):
        return access_forbidden
    await DataCarTariff.create(title=item.title, id_franchise=my_ref["id_franchise"], description=item.description,
                               amount=data["amount"], photo_path=item.photo_path, percent=None)
    return success_answer


@router.put("/tariff",
             responses=generate_responses([success_answer]))
async def update_tariff(request: Request, item: UpdateTariff):
    if await UsersUserAccount.filter(id_user=request.user, id_type_account=6).count() == 0:
        return access_forbidden
    my_ref = await UsersFranchiseUser.filter(id_user=request.user).first().values()
    if await DataCarTariff.filter(id=item.id_tariff, id_franchise=my_ref["id_franchise"]).count() == 0:
        return access_forbidden
    if item.title is not None and len(item.title) != 0 and item.title.lower() != "":
        if item.title.lower() in ("эконом", "комфорт", "комфорт+", "бизнес", "минивэн"):
            return access_forbidden
        await DataCarTariff.filter(id=item.id_tariff).update(title=item.title)
    if item.description is not None and len(item.description) != 0 and item.description.lower() != "":
        await DataCarTariff.filter(id=item.id_tariff).update(description=item.description)
    if item.photo_path is not None and len(item.photo_path) != 0 and item.photo_path.lower() != "":
        await DataCarTariff.filter(id=item.id_tariff).update(photo_path=item.photo_path)
    return success_answer


@router.delete("/tariff",
             responses=generate_responses([success_answer,
                                           access_forbidden]))
async def new_tariff(request: Request, id: int):
    if await UsersUserAccount.filter(id_user=request.user, id_type_account=6).count() == 0:
        return access_forbidden
    my_ref = await UsersFranchiseUser.filter(id_user=request.user).first().values()
    if await DataCarTariff.filter(id=id, id_franchise=my_ref["id_franchise"]).count() == 0:
        return access_forbidden
    data = await DataCarTariff.filter(id=id, id_franchise=my_ref["id_franchise"]).first().values()
    if data["title"].lower() in ("эконом", "комфорт", "комфорт+", "бизнес", "минивэн"):
        return access_forbidden
    await DataCarTariff.filter(id=id, id_franchise=my_ref["id_franchise"]).update(isActive=False)
    return success_answer


@router.post("/add_bonus_money",
             responses=generate_responses([success_answer,
                                           access_forbidden]))
async def add_bonus_money(request: Request, item: BonusFineDriver):
    my_ref = await UsersFranchiseUser.filter(id_user=request.user).order_by("-id").first().values()
    if await UsersFranchiseUser.filter(id_user=item.id_driver, id_franchise=my_ref["id_franchise"]).count() == 0:
        return access_forbidden
    if await UsersUserAccount.filter(id_user=request.user, id_type_account=6).count() == 0:
        return access_forbidden
    if item.amount <= 0:
        return access_forbidden
    if await DataUserBalance.filter(id_user=item.id_driver).count() == 0:
        await DataUserBalance.create(id_user=item.id_driver, money=0)
    balance = await DataUserBalance.filter(id_user=item.id_driver).first().values()
    await DataUserBalance.filter(id_user=item.id_driver, id=balance["id"]).update(
                                                            money=decimal.Decimal(int(balance["money"])+item.amount))
    await DataUserBalanceHistory.create(id_user=item.id_driver, money=decimal.Decimal(item.amount), id_task=-2,
                                        isComplete=True, description="Зачисление бонусов от Франшизы")
    return success_answer


@router.post("/add_fine_money",
             responses=generate_responses([success_answer,
                                           access_forbidden]))
async def add_bonus_money(request: Request, item: BonusFineDriver):
    my_ref = await UsersFranchiseUser.filter(id_user=request.user).order_by("-id").first().values()
    if await UsersFranchiseUser.filter(id_user=item.id_driver, id_franchise=my_ref["id_franchise"]).count() == 0:
        return access_forbidden
    if await UsersUserAccount.filter(id_user=request.user, id_type_account=6).count() == 0:
        return access_forbidden
    if await DataUserBalance.filter(id_user=item.id_driver).count() == 0:
        await DataUserBalance.create(id_user=item.id_driver, money=0)
    if item.amount <= 0:
        return access_forbidden
    balance = await DataUserBalance.filter(id_user=item.id_driver).first().values()
    await DataUserBalance.filter(id_user=item.id_driver, id=balance["id"]).update(
                                                            money=decimal.Decimal(int(balance["money"])-item.amount))
    await DataUserBalanceHistory.create(id_user=item.id_driver, money=decimal.Decimal(-item.amount), id_task=-3,
                                        isComplete=True, description="Начисление комиссии от Франшизы")
    return success_answer


@router.post("/response_new_driver",
             responses=generate_responses([success_answer,
                                           access_forbidden,
                                           user_not_found]))
async def create_response_new_driver(request: Request, item: ResponseNewDriver):
    if await UsersUserAccount.filter(id_user=request.user, id_type_account__in=[6, 4]).count() == 0:
        return access_forbidden
    my_ref = await UsersFranchiseUser.filter(id_user=request.user).first().values()
    if await UsersUser.filter(id=item.id_driver, isActive=True).count() == 0 or \
        await UsersUserAccount.filter(id_user=item.id_driver, id_type_account=2).count() == 0 or\
        await UsersFranchiseUser.filter(id_user=item.id_driver, id_franchise=my_ref["id_franchise"]).count() == 0 or\
        await WaitDataVerifyDriver.filter(id_driver=item.id_driver).count() == 0:
        return access_forbidden
    if item.success in [False, None]:
        await UsersUserAccount.filter(id_user=item.id_driver, id_type_account=2).delete()
        await WaitDataVerifyDriver.filter(id_driver=item.id_driver).delete()
        data = await UsersDriverData.filter(id_driver=item.id_driver)
        await UsersDriverCard.filter(id=data["id_driver_card"]).delete()
        await UsersDriverAnswer.filter(id=data["id_driver_answer"]).delete()
        await UsersCar.filter(id=data["id_car"]).delete()
        await UsersDriverData.filter(id=data["id"]).delete()
        if item.success is None:
            await UsersUser.filter(id=item.id_driver).update(isActive=False)
        return success_answer
    else:
        await WaitDataVerifyDriver.filter(id_driver=item.id_driver).delete()
        await UsersVerifyAccount.create(id_user=item.id_driver)
        return success_answer

