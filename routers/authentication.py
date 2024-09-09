from models.authentication_db import UsersMobileAuthentication, UsersBearerToken, UsersUserAccount, UsersReferalCode
from models.authentication_db import UsersAuthorizationData, WaitDataVerifyCode, WaitDataVerifyDriver
from models.users_db import UsersUser, WaitDataVerifyRegistration, UsersVerifyAccount, UsersUserPhoto, \
    UsersFranchiseUser, UsersReferalUser
from models.drivers_db import UsersDriverData, UsersDriverAnswer, UsersCar, UsersDriverCard
from defs import check_correct_phone, update_bearer_token, error, generate_fb_link
from fastapi import APIRouter, Request, HTTPException, Depends
from models.users_db import UsersUserYandex, UsersUserVk
from const.static_data_const import DictToModel
from fastapi.responses import RedirectResponse
from const.dependency import has_access
from const.login_const import *
from smsaero import SmsAero
from random import randint
import traceback
import requests
import datetime
import base64
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



@router.post("/login",
             responses=generate_responses([uncorrect_phone,
                                           user_not_found,
                                           forbidden,
                                           user_not_verify,
                                           password_uncorrect,
                                           login_answer]))
async def login(item: LoginApp):
    item.login = await check_correct_phone(item.login)
    if item.login is None: return uncorrect_phone
    if await UsersAuthorizationData.filter(login=item.login.lower()).count() == 0:
        return user_not_found
    if await UsersUser.filter(phone=item.login, isActive__in=[None, False]).count() > 0:
        return forbidden
    row=DictToModel(await UsersAuthorizationData.filter(login=item.login.lower()).first().values("password", "id_user"))
    if await UsersVerifyAccount.filter(id_user=row.id_user).count() == 0 or \
            await WaitDataVerifyDriver.filter(id_driver=row.id_user).count()>0:
        return user_not_verify
    if row.password != item.password:
        return password_uncorrect
    token = await update_bearer_token(item.fbid, row.id_user)
    return JSONResponse({"status": True,
                         "token": token,
                         "message": "Success!"}, 200)


@router.post("/reload_access",
             dependencies=[Depends(has_access)],
             responses=generate_responses([forbidden,
                                           login_answer]))
async def update_token(request: Request):
    try:
        if await UsersUser.filter(id=request.user, isActive__in=[None, False]).count()>0:
            return forbidden
        data = DictToModel(await UsersBearerToken.filter(id_user=request.user).order_by("-id").first().values())
        token = await update_bearer_token(data.fbid, request.user)
        return JSONResponse({"status": True,
                             "token": token,
                             "message": "Success!"}, 200)
    except Exception:
        raise HTTPException(401, "Unauthorized")


@router.post("/get_registration_code",
             responses=generate_responses([success_answer,
                                           uncorrect_phone,
                                           user_already_creates]))
async def registartion_parent(item: VerifyMobilePhone):
    item.phone = await check_correct_phone(item.phone)
    if item.phone is None: return uncorrect_phone
    if await UsersUser.filter(phone=item.phone).count() > 0:
        return user_already_creates
    code = randint(1000, 9999)
    try:
        api = SmsAero("auto.nyany@yandex.ru", "344334Auto")
        api.send(item.phone, f"Ваш код подтверждения: {code}")
    except Exception:
        await error(traceback.format_exc())
    await WaitDataVerifyCode.filter(phone=item.phone).delete()
    await WaitDataVerifyCode.create(phone=item.phone, code=code)
    return success_answer


@router.post("/check_registration_code",
             responses=generate_responses([uncorrect_phone,
                                           uncorrect_code,
                                           success_answer]))
async def registartion_parent(item: VerifyCodeMobilePhone):
    item.phone = await check_correct_phone(item.phone)
    if item.phone is None: return uncorrect_phone
    data = await WaitDataVerifyCode.filter(phone=item.phone).first().values()
    if data is None:
        return uncorrect_phone
    if data["code"] != item.code:
        return uncorrect_code
    await WaitDataVerifyCode.filter(phone=item.phone).delete()
    await WaitDataVerifyRegistration.create(phone=item.phone)
    return success_answer


@router.post("/register_parent",
             responses=generate_responses([user_already_creates,
                                          uncorrect_phone,
                                          success_answer]))
async def registartion_parent(item: RegistrationParent):
    item.phone = await check_correct_phone(item.phone)
    if item.phone is None: return uncorrect_phone
    if await UsersUser.filter(phone=item.phone).count()>0:
        return user_already_creates
    if await WaitDataVerifyRegistration.filter(phone=item.phone).count() == 0:
        return uncorrect_phone
    await WaitDataVerifyRegistration.filter(phone=item.phone).delete()
    user = await UsersUser.create(surname=item.surname, name=item.name,
                                    phone=item.phone)
    await UsersAuthorizationData.create(login=item.phone, password=item.password, id_user=user.id)
    await UsersVerifyAccount.create(id_user=user.id)
    await UsersUserAccount.create(id_user=user.id, id_type_account=1)
    return success_answer


@router.post("/register_driver",
             responses=generate_responses([user_already_creates,
                                           uncorrect_phone,
                                           success_answer]))
async def registartion_driver(item: RegistrationDriver):
    item.phone = await check_correct_phone(item.phone)
    if item.phone is None: return uncorrect_phone
    if await UsersUser.filter(phone=item.phone, isActive__in=[True, False]).count() > 0:
        data_check = await UsersUser.filter(phone=item.phone, isActive__in=[True, False]).first().values()
        if await UsersUserAccount.filter(id_user=data_check["id"], id_type_account=2).count() > 0:
            return user_already_creates
    if await WaitDataVerifyRegistration.filter(phone=item.phone).count() == 0:
        return uncorrect_phone
    await WaitDataVerifyRegistration.filter(phone=item.phone).delete()
    if await UsersUser.filter(phone=item.phone, isActive__in=[True, False]).count() == 0:
        user = await UsersUser.create(surname=item.surname, name=item.name, phone=item.phone)
        await UsersAuthorizationData.create(login=item.phone, password=item.password, id_user=user.id)
    else:
        user = DictToModel(await UsersUser.filter(phone=item.phone, isActive__in=[True, False]).first().values())
    id_car = await UsersCar.create(
                                   id_car_mark=item.carData.autoMark, id_car_model=item.carData.autoModel,
                                   id_color=item.carData.autoColor, year_create=item.carData.releaseYear,
                                   state_number=item.carData.state_number, ctc=item.carData.ctc)
    id_driver_card = await UsersDriverCard.create(
                                    id_country=item.driverLicense.receiveCountry,
                                    date_of_issue=datetime.datetime.strptime(item.driverLicense.receiveDate,
                                                                             "%d.%m.%Y"),
                                    license=item.driverLicense.license)
    id_answers = await UsersDriverAnswer.create(
                                                first_answer=item.answers.first, second_answer=item.answers.second,
                                                third_answer=item.answers.third, four_answer=item.answers.fourth,
                                                five_answer=item.answers.fifth, six_answer=item.answers.sixth,
                                                seven_answer=item.answers.seventh)
    await UsersDriverData.create(
                                 id_car=id_car.id, id_driver_card=id_driver_card.id, id_driver=user.id,
                                 id_driver_answer=id_answers.id, id_city=item.city, description=item.description,
                                 age=item.age, video_url=item.videoUrl, inn=item.inn_data)
    if await UsersUserPhoto.filter(id_user=user.id).count() == 0:
        await UsersUserPhoto.create(id_user=user.id, photo_path=item.photoUrl)
    else:
        await UsersUserPhoto.filter(id_user=user.id).delete()
        await UsersUserPhoto.create(id_user=user.id, photo_path=item.photoUrl)
    await WaitDataVerifyDriver.create(id_driver=user.id)
    await UsersUserAccount.create(id_user=user.id, id_type_account=2)
    if await UsersReferalCode.filter(id_user=user.id).count() == 0:
        code = randint(100000, 999999999)
        while await UsersReferalCode.filter(code=code).count() > 0:
            code=randint(100000, 999999999)
        await UsersReferalCode.create(id_user=user.id, code=code, percent=5)
    try:
        if item.refCode is None:
            await UsersFranchiseUser.create(id_user=user.id, id_franchise=1)
        else:
            partners = [x["id_user"] for x in (await UsersUserAccount.filter(id_type_account=5).all().values())]
            if await UsersReferalCode.filter(id_user__in=partners, code=item.refCode).count() > 0:
                partners = await UsersReferalCode.filter(id_user__in=partners, code=item.refCode).first().values()
                await UsersReferalUser.create(id_user=partners["id_user"], id_user_referal=user.id)
                franchise = await UsersFranchiseUser.filter(id_user=partners["id_user"]).first().values()
                await UsersFranchiseUser.create(id_user=user.id, id_franchise=franchise["id_franchise"])
            else:
                await UsersFranchiseUser.create(id_user=user.id, id_franchise=1)
    except Exception:
        await UsersFranchiseUser.create(id_user=user.id, id_franchise=1)
    return success_answer


@router.post("/reset-password",
             responses=generate_responses([success_answer,
                                           uncorrect_phone,
                                           user_already_creates]))
async def reset_password(item: VerifyMobilePhone):
    item.phone = await check_correct_phone(item.phone)
    if item.phone is None: return uncorrect_phone
    user = await UsersUser.filter(phone=item.phone).first().values()
    if user is None:
        return user_already_creates
    code = randint(1000, 9999)
    api = SmsAero("auto.nyany@yandex.ru", "344334Auto")
    api.send(item.phone, f"Ваш код подтверждения: {code}")
    await WaitDataVerifyCode.filter(phone=item.phone).delete()
    await WaitDataVerifyCode.create(phone=item.phone, code=code)
    return success_answer


@router.post("/check-reset-password",
             responses=generate_responses([uncorrect_phone,
                                           uncorrect_code,
                                           user_not_found,
                                           success_answer]))
async def registartion_parent(item: VerifyCodeMobilePhone):
    item.phone = await check_correct_phone(item.phone)
    if item.phone is None: return uncorrect_phone
    data = await WaitDataVerifyCode.filter(phone=item.phone).first().values()
    if data is None:
        return uncorrect_phone
    if data["code"] != item.code:
        return uncorrect_code
    if await UsersUser.filter(phone=item.phone).count() == 0:
        return user_not_found
    await WaitDataVerifyCode.filter(phone=item.phone).delete()
    if await UsersUser.filter(phone=item.phone).count() == 0:
        await WaitDataVerifyRegistration.filter(phone=item.phone).delete()
        await WaitDataVerifyRegistration.create(phone=item.phone)
    return success_answer


@router.post("/verify-reset-password",
             responses=generate_responses([user_not_found,
                                           uncorrect_phone,
                                           success_answer]))
async def verify_reset_password(item: VerifyResetPassword):
    item.phone = await check_correct_phone(item.phone)
    if item.phone is None: return uncorrect_phone
    if await UsersUser.filter(phone=item.phone).count() == 0:
        return user_not_found
    await UsersAuthorizationData.filter(login=item.phone).update(password=item.password)
    return success_answer


@router.post("/new_mobile_authentication",
             dependencies=[Depends(has_access)],
             responses=generate_responses([success_answer]))
async def new_mobile_authentication(request: Request, item: NewMobileAuthentication):
    try:
        if await UsersMobileAuthentication.filter(id_user=request.user).count()>0:
            await UsersMobileAuthentication.filter(id_user=request.user).delete()
        await UsersMobileAuthentication.create(id_user=request.user, code=item.code)
        return success_answer
    except Exception:
        await error(traceback.format_exc())
        raise HTTPException(401, "Unauthorized")


@router.post("/check_mobile_authentication",
             dependencies=[Depends(has_access)],
             responses=generate_responses([success_answer,
                                           mobile_authentication_unsuccessful]))
async def check_mobile_authentication(request: Request, item: NewMobileAuthentication):
    try:
        user_data = await UsersMobileAuthentication.filter(id_user=request.user).first().values()
        if item.code == user_data["code"]:
            return success_answer
        else:
            return mobile_authentication_unsuccessful
    except Exception:
        raise HTTPException(401, "Unauthorized")


@router.post("/logout",
             dependencies=[Depends(has_access)],
             responses=generate_responses([success_answer]))
async def logout(request: Request):
    try:
        await UsersBearerToken.filter(id_user=request.user).delete()
        return success_answer
    except Exception:
        raise HTTPException(401, "Unauthorized")


@router.get("/oauth_yandex")
async def yandex_registration(code: str):
    sample_string="05f788e3a4ff44b08e387ab58b083442:9822204a74604952b33df366982f1ec4"
    sample_string_bytes=sample_string.encode("ascii")
    base64_bytes=base64.b64encode(sample_string_bytes)
    base64_string=base64_bytes.decode("ascii")
    headers={
        "Content-type": "application/x-www-form-urlencoded",
        "Authorization": "Basic " + base64_string
    }
    data={
        "code": code,
        "grant_type": "authorization_code"
    }
    x=requests.post(f"https://oauth.yandex.ru/token", headers=headers, data=data)
    print(x.json())
    headers={
        "Authorization": "Oauth " + x.json()["access_token"]
    }
    user=requests.get("https://login.yandex.ru/info?format=json", headers=headers).json()
    if await UsersUser.filter(phone=user["default_phone"]["number"]).count() == 0 and \
            await UsersUserYandex.filter(yandex_id=user["id"]).count() == 0:

        user_data=await UsersUser.create(surname=user["last_name"], name=user["first_name"],
                                    phone=user["default_phone"]["number"])
        await UsersUserYandex.create(id_user=user_data.id, yandex_id=user["id"])
        await UsersVerifyAccount.create(id_user=user_data.id)
        await UsersUserAccount.create(id_user=user_data.id, id_type_account=1)
        await UsersAuthorizationData.create(login=user["default_phone"]["number"],
                                            password="", id_user=user_data.id)


    user_data = await UsersUser.filter(phone=user["default_phone"]["number"], isActive=True).first().values()
    if await UsersUserYandex.filter(yandex_id=user["id"]).count() == 0:
        await UsersUserYandex.create(yandex_id=user["id"], id_user=user_data["id"])
    if user_data is None or len(user_data) == 0:
        user_data = await UsersUserYandex.filter(yandex_id=user["id"]).first().values()
        user_data = await UsersUser.filter(id=user_data["id_user"], isAcrive=True).first().values()
    token = await update_bearer_token("fbid", user_data["id"])
    refresh_token =""
    link = await generate_fb_link(auth=True, ref=token, refresh_token=refresh_token)
    print(link)
    return RedirectResponse(link, 307)


@router.get("/oauth_vk")
async def vk_registration(code: str):
    url=f"https://oauth.vk.com/access_token?client_id=51865735&client_secret=SlqM1fKELOOMpPysifr6&" \
        f"redirect_uri=https://nyanyago.ru/api/v1.0/auth/oauth_vk&code={code}"
    vk=requests.get(url)
    print(vk.json())
    headers={
        "Authorization": f"Bearer {vk.json()['access_token']}"
    }
    user=requests.get("https://api.vk.com/method/account.getProfileInfo?v=5.131", headers=headers).json()
    if await UsersUser.filter(phone=str(user["response"]["id"])).count() == 0 and \
            await UsersUserVk.filter(vk_id=user["response"]["id"]).count() == 0:
        user_data = await UsersUser.create(surname=user["response"]["last_name"],
                                           name=user["response"]["first_name"],
                                           phone=user["response"]["id"])
        await UsersAuthorizationData.create(id_user=user_data.id, login=str(user["response"]["id"]), password="")
        await UsersVerifyAccount.create(id_user=user_data.id)
        await UsersUserAccount.create(id_user=user_data.id, id_type_account=1)
        await UsersUserVk.create(id_user=user_data.id, vk_id=str(user["response"]["id"]))
    user_data = await UsersUser.filter(phone=user["response"]["id"], isActive=True).first().values()
    if user_data is None or len(user_data) == 0:
        user_data = await UsersUserVk.filter(vk_id=user["response"]["id"]).first().values()
        user_data = await UsersUser.filter(id=user_data["id_user"], isActive=True).first().values()
    token = await update_bearer_token("fbid", user_data["id"])
    refresh_token = ""
    link = await generate_fb_link(auth=True, ref=token, refresh_token=refresh_token)
    print(link)
    return RedirectResponse(link, 307)




