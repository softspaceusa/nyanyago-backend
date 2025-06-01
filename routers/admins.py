import os

from const.static_data_const import not_user_photo, not_found_other_parametr,OtherDriveParametr,UpdateOtherDriveParametr
from models.authentication_db import UsersUserAccount, UsersReferalCode, UsersAuthorizationData, UsersBearerToken
from models.users_db import UsersVerifyAccount, UsersUserPhoto, UsersReferalUser, \
    UsersFranchiseUser, UsersChild
from models.users_db import HistoryPaymentTink, UsersUser
from const.login_const import uncorrect_phone, user_already_creates, error_create_user
from defs import check_correct_phone, error, get_date_from_datetime
from models.chats_db import ChatsChatParticipant, ChatsChat
from models.static_data_db import DataOtherDriveParametr
from models.admins_db import AdminMobileSettings
from models.drivers_db import UsersDriverData
from sevice.admin_service import ReportMaker, create_franchise_user, create_partner_user

from common.logger import logger

from fastapi.responses import FileResponse
from fastapi import APIRouter, Request, Depends
from starlette.background import BackgroundTask
from const.admins_const import *
from tortoise.models import Q
from tortoise import Tortoise
from smsaero import SmsAero
import traceback
import decimal
import json


router = APIRouter()
router_for_franchise_admin = APIRouter()


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
                                           new_user_message_dont_delivery,
                                           error_create_user]))
async def new_user(item: NewUser):
    item.phone = await check_correct_phone(item.phone)
    if item.phone is None: return uncorrect_phone
    if await UsersUser.filter(phone=item.phone).count()>0:
        return user_already_creates
    if item.role not in [3, 4, 5, 6]:
        return unsupported_role
    if item.role == 5:
        try:
            await create_partner_user(item)
        except:
            logger.error("Can't create user in DB")
            return error_create_user
    else:
        try:
            await create_franchise_user(item)
        except Exception:
            logger.error("Can't create user in DB")
            return error_create_user

    try:
        api = SmsAero("auto.nyany@yandex.ru", "344334Auto")
        api.send(item.phone, f"Ваши данные для входа в аккаунт АвтоНяни:\n\n"
                                 f"Логин: {item.phone}\n"
                                 f"Пароль: {item.password}\n")
    except Exception:
        await error(traceback.format_exc())
        return new_user_message_dont_delivery
    return success_answer


@router.get("/franchise_admins")
async def get_franchise_admins() -> SuccessGetFranchiseAdmins:
    """
    Возвращает информацию об администраторах франшизы
    """
    response_data = {}

    SQL_REQUEST = ('SELECT u.id, u.phone, fc.id_city, c.title FROM "users".user AS u '
                   'JOIN "users".user_account AS ua ON u.id=ua.id_user '
                   'JOIN "users".franchise_user as fu ON u.id=fu.id_user '
                   'LEFT JOIN "users".franchise_city fc ON fu.id_franchise=fc.id_franchise '
                   'LEFT JOIN "data".city as c ON fc.id_city=c.id '
                   'WHERE ua.id_type_account=6;')
    #users = await UsersUser.filter(user_accounts__id_type_account="6").all().values("id", "phone", "franchise_users__id_franchise__franchise_cities__id_city__id", "franchise_users__id_franchise__franchise_cities__id_city__title")
    conn = Tortoise.get_connection("default")
    users = await conn.execute_query_dict(SQL_REQUEST)
    logger.debug(users)
    for user in users:
        if user["id"] not in users: #user_id key help to add double row with cities
            try:
                response_data[user["id"]] = FranchiseAdmin(
                    id= user["id"],
                    phone= user["phone"],
                    cities=[City(
                        id= user["id_city"],
                        title= user["title"]
                    )] if user["id_city"] else None
                )
            except Exception:
                logger.error(f"Row: {user} has incorrect format")
        else:
            try:
                response_data[user["id"]].cities.append(City(
                    id=user["id_city"],
                    title=user["title"]
                ))
            except Exception:
                logger.error(f"Row: {user} has incorrect format")
    logger.debug(response_data)
    validate=FranchiseAdmins(response_data.values())
    return SuccessGetFranchiseAdmins(franchise_admins=validate)


"""
@router.post("/get_partners",
             responses=generate_responses([get_partners]))
async def get_partners(item: Union[GetPartners, None] = None):
    if item is not None:
        data = await UsersUserAccount.filter(id_type_account=5).order_by("-id").offset(item.offset).limit(item.limit).values()
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
"""

@router.post("/get_partners",
             responses=generate_responses([get_partners]))
async def get_partners(item: Union[GetPartners, None] = None):
    SQL_REQUEST = ('SELECT u.id, u.surname, u.name, u.datetime_create, u.phone, ua.id_type_account FROM users.user AS u '
                   'LEFT JOIN users.user_account AS ua ON u.id=ua.id_user '
                   'INNER JOIN users.referal_code AS rc ON u.id=rc.id_user '
                   'WHERE ua.id_type_account=5 '
                   f'LIMIT {item.limit} OFFSET {item.offset};')
    conn = Tortoise.get_connection("default")
    logger.debug(SQL_REQUEST)
    users = await conn.execute_query_dict(SQL_REQUEST)
    logger.debug(users)
    for partner in users:
        photo = await UsersUserPhoto.filter(id_user=partner["id"]).first().values()
        photo = not_user_photo if photo is None or "photo_path" not in photo else photo["photo_path"]
        partner["photo_path"] = photo
        partner["datetime_create"] = await get_date_from_datetime(partner["datetime_create"])
        partner["role"] = [partner["id_type_account"]]
        del partner["id_type_account"]
        del partner["phone"]
    partners = []
    if item is not None and item.search is not None:
        for partner in users:
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
        ref_roles = await UsersUserAccount.filter(id_user=ref["id_user_referal"]).values("id_type_account")
        ref["name"] = refer_data["name"]
        ref["surname"] = refer_data["surname"]
        ref["date_reg"] = await get_date_from_datetime(refer_data["datetime_create"])
        ref["role"] = [next(iter(role.values())) for role in ref_roles] # get values from list of dictonaries
        logger.debug(ref["role"])
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


@router.get("/get_user_children")
async def get_user_children(request: Request, user_id: int):
    """
    Получить список детей пользователя.

    Args:
        request (Request): Запрос.
        user_id (int): ID пользователя-родителя.

    Returns:
        JSONResponse: Ответ в формате JSON с данными детей.
    """
    # Проверяем существование пользователя
    if not await UsersUser.filter(id=user_id, isActive=True).exists():
        return JSONResponse(
            {"status": False, "message": "User not found or inactive"},
            status_code=404
        )

    # Получаем всех активных детей пользователя
    children = await UsersChild.filter(
        id_user=user_id,
        is_active=True
    ).order_by("-datetime_create").values(
        "id",
        "surname",
        "name",
        "patronymic",
        "child_phone",
        "contact_phone",
    )

    return JSONResponse({
        "status": True,
        "message": "Success",
        "data": children,
        "count": len(children)
    })


@router_for_franchise_admin.post(
    "/ban-user",
    responses=generate_responses([success_answer, user_not_found])
)
async def ban_user(item: GetUser, request: Request):
    """
    Блокирует/разблокирует пользователя в зависимости от его текущего статуса.

    Этот эндпоинт управляет блокировкой и снятием блокировки пользователей. Когда пользователя
    блокируют, — его учетная запись деактивируется, а связанные с ней данные, такие как участие в чате и
    данные водителя обновляются соответствующим образом.
    Если пользователь уже заблокирован, это действие отменяет запрет и повторно активирует
    учетную запись и связанные с ней данные.

    Args:
        item (GetUser): {"id": 1} - ID пользователя, которого нужно заблокировать/разблокировать.
        request (Request): Объект запроса

    Returns:
        JSONResponse - ответ, содержащий статус и сообщение операции.
    """
    if request.user == item.id:
        return JSONResponse(
            {"status": False, "message": "Can't delete main admin!"}, 404
        )
    type_account = await UsersUserAccount.filter(id_user=item.id).first().values()
    if type_account is None:
        return user_not_found
    if type_account["id_type_account"] == 6:
        req_user_franchise = await UsersFranchiseUser.filter(id_user=request.user).first().values()
        req_user_franchise_id = req_user_franchise["id_franchise"]
        ban_user_franchise = await UsersFranchiseUser.filter(id_user=item.id).first().values()
        ban_user_franchise_id = ban_user_franchise["id_franchise"]
        if req_user_franchise_id != ban_user_franchise_id:
            return JSONResponse({"status": False, "message": "You don't have access to this user!"}, 404)
    user = await UsersUser.filter(id=item.id).first().values()
    if user is None:
        return user_not_found
    if await UsersUser.filter(id=item.id, isActive=False).count() > 0:
        await UsersUser.filter(id=item.id).update(isActive=True)
        await UsersVerifyAccount.create(id_user=item.id)
        if await UsersDriverData.filter(id_driver=item.id).count() > 0:
            await UsersDriverData.filter(id_driver=item.id).update(isActive=True)
        chats = [
            x["id_chat"]
            for x in (await ChatsChatParticipant.filter(id_user=item.id).all().values())
        ]
        for each in chats:
            await ChatsChat.filter(id=each).update(isActive=True)

    else:
        await UsersUser.filter(id=item.id).update(isActive=False)
        await UsersVerifyAccount.filter(id_user=item.id).delete()
        await UsersBearerToken.filter(id_user=item.id).delete()
        chats = [
            x["id_chat"]
            for x in (await ChatsChatParticipant.filter(id_user=item.id).all().values())
        ]
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


@router.get("/report_sales")
async def get_report_sales(request: Request, start_date: date, end_date: date) -> SuccessGetSalary:
    reporter = ReportMaker(HistoryPaymentTink, "Salary", report_type="sum")
    report = await reporter.create_report_by_period(start_date, end_date)
    salary = Report(report)
    response = SuccessGetSalary(salary=salary)
    return response


@router.post("/report_sales",
             responses=generate_responses([]),
             response_class=FileResponse)
async def get_file_report_sales(request: Request, start_date: date, end_date: date):
    reporter = ReportMaker(HistoryPaymentTink, "Salary", report_type="sum")
    await reporter.create_report_by_period(start_date, end_date)
    report_file_path = await reporter.save_report_to_pdf(title="salary_report")
    _, file_name = report_file_path.rsplit('/', 1)
    return FileResponse(report_file_path, media_type="application/pdf", filename=file_name, background=BackgroundTask(os.remove, report_file_path))


@router.get("/report_users")
async def get_report_users(request: Request, start_date: date, end_date: date) -> SuccessGetUserReport:
    try:
        reporter = ReportMaker(UsersUser, "User register", report_type="count")
        report = await reporter.create_report_by_period(start_date, end_date)
        users = Report(report)
    except:
        logger.error("Can't to create report")
    else:
        response = SuccessGetUserReport(user_report=users)
        return response


@router.post("/report_users",
             responses=generate_responses([]),
             response_class=FileResponse)
async def get_file_report_users(request: Request, start_date: date, end_date: date):
    try:
        reporter = ReportMaker(UsersUser, "User register", report_type="count")
        await reporter.create_report_by_period(start_date, end_date)
        report_file_path = await reporter.save_report_to_pdf(title="user_report")
        _, file_name = report_file_path.rsplit('/', 1)
    except:
        logger.error("Can't to create report and report file")
    else:
        return FileResponse(report_file_path, media_type="application/pdf", filename=file_name, background=BackgroundTask(os.remove, report_file_path))


