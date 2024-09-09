from const.static_data_const import not_user_photo, not_found_other_parametr,OtherDriveParametr,UpdateOtherDriveParametr
from models.authentication_db import UsersUserAccount, UsersReferalCode, UsersAuthorizationData, UsersBearerToken
from models.users_db import UsersUser, UsersVerifyAccount, UsersUserPhoto, UsersReferalUser, UsersFranchise, \
    UsersFranchiseCity
from models.users_db import UsersFranchiseUser
from const.login_const import uncorrect_phone, user_already_creates
from defs import check_correct_phone, error, get_date_from_datetime
from models.chats_db import ChatsChatParticipant, ChatsChat
from models.static_data_db import DataOtherDriveParametr, DataCity, DataCarTariff
from models.admins_db import AdminMobileSettings
from models.drivers_db import UsersDriverData
from fastapi.responses import FileResponse
from fastapi import APIRouter, Request
from const.admins_const import *
from tortoise.models import Q
from smsaero import SmsAero
import traceback
import hashlib
import decimal
import json


router = APIRouter()


def generate_responses(answers: list):
    answer = {}
    for data in answers:
        answer[data.status_code] = {
                                    "content": {
                                        "application/json": {
                                            "example": json.loads(data.body.decode("utf-8"))
                                        }
                                    },
                                    "description": f"{json.loads(data.body.decode('utf-8'))['message']}"
        }
    return answer


@router.post("/new_user",
             responses=generate_responses([success_answer,
                                           uncorrect_phone,
                                           user_already_creates,
                                           unsupported_role,
                                           new_user_message_dont_delivery]))
async def new_user(item: NewUser):
    item.phone = await check_correct_phone(item.phone)
    if item.phone is None: return uncorrect_phone
    if await UsersUser.filter(phone=item.phone).count()>0:
        return user_already_creates
    if item.role not in [3, 4, 5, 6]:
        return unsupported_role
    if item.role == 5:
        user = await UsersUser.create(phone=item.phone, name=item.name, surname=item.surname)
        await UsersAuthorizationData.create(id_user=user.id, login=item.phone,
                                                password=str((hashlib.md5(item.password.encode())).hexdigest()))
        await UsersVerifyAccount.create(id_user=user.id)
        await UsersUserAccount.create(id_user=user.id, id_type_account=item.role)
        if item.referal_code is not None and len(item.referal_code) > 0:
            await UsersReferalCode.create(id_user=user.id, code=item.referal_code, percent=30)
        try:
            api = SmsAero("auto.nyany@yandex.ru", "344334Auto")
            api.send(item.phone, f"Ваши данные для входа в аккаунт АвтоНяни:\n\n"
                                 f"Логин: {item.phone}\n"
                                 f"Пароль: {item.password}\n")
        except Exception:
            await error(traceback.format_exc())
            return new_user_message_dont_delivery
    else:
        franchise = await UsersFranchise.create(description=f"Франшиза {item.phone}")
        for each in item.id_city:
            if await DataCity.filter(id=each).count() == 0:
                continue
            await UsersFranchiseCity.create(id_franchise=franchise.id, id_city=each)
        await DataCarTariff.create(title="Эконом", amount=78, id_franchise=franchise.id,
                                   photo_path="https://nyanyago.ru/api/v1.0/files/econom.png")
        await DataCarTariff.create(title="Комфорт", amount=108, id_franchise=franchise.id,
                                   photo_path="https://nyanyago.ru/api/v1.0/files/comfort.png")
        await DataCarTariff.create(title="Комфорт+", amount=115, id_franchise=franchise.id,
                                   photo_path="https://nyanyago.ru/api/v1.0/files/comfort_plus.png")
        await DataCarTariff.create(title="Бизнес", amount=138, id_franchise=franchise.id,
                                   photo_path="https://nyanyago.ru/api/v1.0/files/econom.png")
        await DataCarTariff.create(title="Минивэн", amount=198, id_franchise=franchise.id,
                                   photo_path="https://nyanyago.ru/api/v1.0/files/comfort_plus.png")
        await DataCarTariff.create(title="Премиум", amount=243, id_franchise=franchise.id,
                                   photo_path="https://nyanyago.ru/api/v1.0/files/econom.png")
        user = await UsersUser.create(phone=item.phone, name=item.name, surname=item.surname)
        await UsersFranchiseUser.create(id_user=user.id, id_franchise=franchise.id)
        await UsersAuthorizationData.create(id_user=user.id, login=item.phone,
                                                password=str((hashlib.md5(item.password.encode())).hexdigest()))
        await UsersVerifyAccount.create(id_user=user.id)
        if item.role != 6:
            await UsersUserAccount.create(id_user=user.id, id_type_account=6)
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


@router.post("/get_partners",
             responses=generate_responses([get_partners]))
async def get_partners(item: Union[GetPartners, None] = None):
    if item is not None:
        data=await UsersUserAccount.filter(id_type_account=5).order_by("-id").offset(item.offset).limit(item.limit).values()
    else:
        data = await UsersUserAccount.filter(id_type_account=2).order_by("-id").all().values()
    users = []
    for ids in data:
        users.append(ids["id_user"])
    result = await UsersUser.filter(id__in=users).order_by("-id").all().values()
    for partner in result:
        photo = await UsersUserPhoto.filter(id_user=partner["id"]).first().values()
        photo = not_user_photo if photo is None or "photo_path" not in photo else photo["photo_path"]
        partner["photo_path"] = photo
        partner["datetime_create"] = await get_date_from_datetime(partner["datetime_create"])
        del partner["phone"]
    partners = []
    if item is not None and item.search is not None:
        for partner in result:
            if (partner["name"] is not None and partner["surname"] is not None) and \
                (item.search.lower() in partner["name"].lower() or item.search.lower() == partner["name"].lower() or
                item.search.lower() in partner["surname"].lower() or item.search.lower() == partner["surname"].lower()):
                partners.append(partner)
    return JSONResponse({"status": True,
                         "message": "Success!",
                         "partners": partners})


@router.post("/get_partner",
             responses=generate_responses([partner_not_found, get_partner]))
async def get_partner_by_id(item: GetPartner):
    if await UsersUser.filter(id=item.id).count() == 0 or \
            await UsersUserAccount.filter(id_user=item.id, id_type_account=5).count() == 0:
        return partner_not_found
    data = await UsersUser.filter(id=item.id).first().values()
    refer = await UsersReferalCode.filter(id_user=item.id).first().values()
    photo = await UsersUserPhoto.filter(id_user=item.id).first().values()
    photo = photo["photo_path"] if photo is not None and "photo_path" in photo else not_user_photo
    referals = await UsersReferalUser.filter(id_user=item.id).order_by("-id").all().values()
    for ref in referals:
        refer_data = await UsersUser.filter(id=ref["id_user_referal"]).first().values()
        ref["name"] = refer_data["name"]
        ref["surname"] = refer_data["surname"]
        ref["date_reg"] = await get_date_from_datetime(refer_data["datetime_create"])
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
                             "referals": referals
                         }})


@router.post("/get_partners_referal",
             responses=generate_responses([partners_referal_not_found, get_partners_referal]))
async def get_partners_referal_by_id(item: GetPartner):
    if await UsersReferalUser.filter(id_user_referal=item.id).count() == 0 or \
        await UsersUserAccount.filter(id_user=item.id, id_type_account=2).count()==0 or\
         await UsersUser.filter(id=item.id).count() == 0:
        return partners_referal_not_found
    user = await UsersUser.filter(id=item.id).first().values()
    photo = await UsersUserPhoto.filter(id_user=item.id).first().values()
    photo = photo["photo_path"] if photo is not None and "photo_path" in photo else not_user_photo
    partner = await UsersReferalUser.filter(id_user_referal=item.id).first().values()
    partner = await UsersReferalCode.filter(id_user=partner["id_user"]).first().values()
    return JSONResponse({"status": True,
                         "message": "Success!",
                         "data": {
                             "name": user["name"],
                             "surname": user["surname"],
                             "date_reg": await get_date_from_datetime(user["datetime_create"]),
                             "phone": user["phone"],
                             "photo_path": photo,
                             "partner_percent": partner["percent"]
                         }})


@router.post("/get_users",
             responses=generate_responses([get_users]))
async def get_all_user(item: GetUsers):
    total, result, data = 0, [], UsersUser.filter(id__not=-1, isActive__in=[False, True]).order_by("-id")
    total = await UsersUser.filter(id__not=-1, isActive__in=[False, True]).count()
    if item is not None:
        data = UsersUser.filter(id__not=-1, isActive__in=[False, True])
        total = await data.count()
        data = data.filter(Q(name__icontains=item.search)|Q(surname__icontains=item.search)|Q(phone__icontains=item.search))
        data = data.offset(item.offset).limit(item.limit)
    data = await data.all().values()
    for user in data:
        photo = await UsersUserPhoto.filter(id_user=user["id"]).first().values()
        photo = not_user_photo if photo is None or "photo_path" not in photo else photo["photo_path"]
        user["photo_path"] = photo
        role = [x["id_type_account"] for x in (await UsersUserAccount.filter(id_user=user["id"]).all().values())]
        roles = []
        if 1 in role:
            roles.append("Родитель")
        if 2 in role:
            roles.append("Водитель")
        if 3 in role:
            roles.append("Оператор")
        if 4 in role:
            roles.append("Менеджер")
        if 5 in role:
            roles.append("Партнёр")
        if 6 in role:
            roles.append("Администратор франшизы")
        if 7 in role:
            roles.append("Администратор")
        user["role"] = roles
        user["status"] = "Активен" if user["isActive"] is True else "Заблокирован"
        user["datetime_create"] = await get_date_from_datetime(user["datetime_create"])
        del user["isActive"]
    return JSONResponse({"status": True,
                         "message": "Success!",
                         "users": data,
                         "total": total})


@router.post("/ban-user",
             responses=generate_responses([success_answer, user_not_found]))
async def delete_user(item: GetUser, request: Request):
    if request.user == item.id:
        return JSONResponse({"status": False, "message": "Can't delete main admin!"}, 404)
    user = await UsersUser.filter(id=item.id).first().values()
    if user is None:
        return user_not_found
    if await UsersUser.filter(id=item.id, isActive=False).count() > 0:
        await UsersUser.filter(id=item.id).update(isActive=True)
        await UsersVerifyAccount.create(id_user=item.id)
        if await UsersDriverData.filter(id_driver=item.id).count() > 0:
            await UsersDriverData.filter(id_driver=item.id).update(isActive=True)
        chats=[x["id_chat"] for x in (await ChatsChatParticipant.filter(id_user=item.id).all().values())]
        for each in chats:
            await ChatsChat.filter(id=each).update(isActive=True)

    else:
        await UsersUser.filter(id=item.id).update(isActive=False)
        await UsersVerifyAccount.filter(id_user=item.id).delete()
        await UsersBearerToken.filter(id_user=item.id).delete()
        chats=[x["id_chat"] for x in (await ChatsChatParticipant.filter(id_user=item.id).all().values())]
        for each in chats:
            await ChatsChat.filter(id=each).update(isActive=False)
        if await UsersDriverData.filter(id_driver=item.id).count() > 0:
            await UsersDriverData.filter(id_driver=item.id).update(isActive=False)
    return success_answer


@router.post("/delete-user",
             responses=generate_responses([success_answer, user_not_found]))
async def delete_user(item: GetUser, request: Request):
    if request.user == item.id:
        return JSONResponse({"status": False, "message": "Can't delete main admin!"}, 404)
    user = await UsersUser.filter(id=item.id).first().values()
    if user is None:
        return user_not_found
    try:
        await UsersUser.filter(id=item.id).update(isActive=None, phone=user["phone"]+"__delete")
    except Exception:
        pass
    chats = [x["id_chat"] for x in (await ChatsChatParticipant.filter(id_user=item.id).all().values())]
    for each in chats:
        await ChatsChat.filter(id=each).update(isActive=False)
    await UsersAuthorizationData.filter(id_user=item.id).delete()
    await UsersBearerToken.filter(id_user=item.id).delete()
    if await UsersDriverData.filter(id_driver=item.id).count() > 0:
        await UsersDriverData.filter(id_driver=item.id).update(isActive=False)
    return success_answer


@router.get("/change-biometry-settings",
            responses=generate_responses([success_answer]))
async def change_state_of_activity_biometry_settings():
    settings = await AdminMobileSettings.filter().order_by("-id").first().values()
    if settings["biometry"] is True:
        await AdminMobileSettings.filter(id=settings["id"]).update(biometry=False)
    else:
        await AdminMobileSettings.filter(id=settings["id"]).update(biometry=True)
    return success_answer


@router.delete("/other-parametrs-of-drive",
               responses=generate_responses([success_answer, not_found_other_parametr]))
async def delete_other_parametr_of_drive(item: GetUser):
    if await DataOtherDriveParametr.filter(isActive=True, id=item.id).count() == 0:
        return not_found_other_parametr
    await DataOtherDriveParametr.filter(isActive=True, id=item.id).update(isActive=False)
    return success_answer


@router.put("/other-parametrs-of-drive",
            responses=generate_responses([success_answer, not_found_other_parametr]))
async def update_other_parametr_of_drive(item: UpdateOtherDriveParametr):
    if await DataOtherDriveParametr.filter(isActive=True, id=item.id).count() == 0:
        return not_found_other_parametr
    if item.title is not None and len(item.title) > 0:
        await DataOtherDriveParametr.filter(isActive=True, id=item.id).update(title=item.title)
    if item.amount is not None and len(str(item.amount)) > 0:
        await DataOtherDriveParametr.filter(isActive=True, id=item.id).update(amount=decimal.Decimal(item.amount))
    return success_answer


@router.post("/other-parametrs-of-drive",
             responses=generate_responses([success_answer]))
async def create_other_parametr_of_drive(item: OtherDriveParametr):
    await DataOtherDriveParametr.create(title=item.title, amount=decimal.Decimal(item.amount))
    return success_answer


@router.get("/report_sales",
            responses=generate_responses([]))
async def get_report_sales(request: Request, period: int, type_period):
    return success_answer


@router.get("/report_users",
            responses=generate_responses([]))
async def get_report_users(request: Request, period: int, type_period):
    return success_answer


@router.post("/report_sales",
             responses=generate_responses([]))
async def get_file_report_sales(request: Request, period: int, type_period):
    return "root/files/ChildrenPorpularVideo.mp4"


@router.post("/report_users",
             responses=generate_responses([]),
             response_class=FileResponse)
async def get_file_report_users(request: Request, period: int, type_period):
    return "root/files/ChildrenPorpularVideo.mp4"


