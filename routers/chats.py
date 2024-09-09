from models.chats_db import ChatsChatParticipant, ChatsMessage, DataMessageType, ChatsChat, HistoryChatNotification
from fastapi import APIRouter, Request, HTTPException
from models.users_db import UsersUser, UsersUserPhoto
from const.static_data_const import not_user_photo
from const.chats_const import *
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



@router.post("/get_chats",
             responses=generate_responses([get_chats]))
async def get_all_chats(request: Request, item: Union[GetChats, None] = None):
    clear_chat = []
    if item is not None:
        chats = ChatsChatParticipant.filter(id_user=request.user).limit(item.limit).offset(item.offset)
        chats = await chats.all().values("id_chat")
    else:
        chats = await ChatsChatParticipant.filter(id_user=request.user).all().values("id_chat")
    for each in chats:
        if await ChatsChat.filter(id=each["id_chat"], isActive=False).count() != 0:
            clear_chat.append(each)
    for each in clear_chat:
        try:
            chats.remove(each)
        except Exception:
            pass
    count = await ChatsChatParticipant.filter(id_user=request.user).count()
    for chat in chats:
        print(chat)
        id_participant = await ChatsChatParticipant.filter(id_chat=chat["id_chat"],
                                                           id_user__not=request.user).first().values("id_user")
        user = await UsersUser.filter(id=id_participant["id_user"]).first().values("name")
        chat["username"] = user["name"]
        photo = await UsersUserPhoto.filter(id_user=id_participant["id_user"]).first().values()
        chat["photo_path"] = photo["photo_path"] if photo is not None and "photo_path" in photo else not_user_photo
        last_message = await ChatsMessage.filter(id_chat=chat["id_chat"]).order_by("-id").first().values()
        if last_message is not None:
            if "msgType" in last_message and last_message["msgType"] == 1:
                chat["message"] = {"msg": last_message["msg"]}
            else:
                chat["message"]={"msg":(await DataMessageType.filter(id=last_message["msgType"])
                                        .first().values())["title"]}
            chat["message"]["time"] = last_message["timestamp_send"]
            new_message = await HistoryChatNotification.filter(id_user=request.user,
                                                               id_chat=chat["id_chat"], is_readed=False).count()
            chat["message"]["new_message"] = new_message
        else:
            chat["message"] = None
    result = []
    if item is not None and item.search is not None:
        for chat in chats:
            if item.search.lower() in chat["username"].lower() or item.search.lower() == chat["username"].lower():
                result.append(chat)
    else:
        result = chats
    for i in range(len(result) - 1):
        for j in range(len(result) - i - 1):
            if "message" not in result[j] or result[j]["message"] is None and \
                    "message" in result[j+1] or result[j+1]["message"] is not None:
                buff=result[j]
                result[j]=result[j + 1]
                result[j + 1]=buff
            if "message" not in result[j+1] or result[j+1]["message"] is None and \
                    "message" in result[j] or result[j]["message"] is not None:
                buff=result[j]
                result[j]=result[j + 1]
                result[j + 1]=buff
            if "message" not in result[j+1] or result[j+1]["message"] is None and \
                    "message" not in result[j] or result[j]["message"] is None:
                continue
            if result[j]["message"]["time"] > result[j + 1]["message"]["time"]:
                buff = result[j]
                result[j] = result[j + 1]
                result[j + 1] = buff
    print(result)
    return JSONResponse({"status": True,
                         "message": "Success!",
                         "chats": list(reversed(result)),
                         "total": count})


@router.post("/get_chat",
             responses=generate_responses([get_chat]))
async def get_chat_by_id(request: Request, item: GetChat):
    if await ChatsChatParticipant.filter(id_chat=item.id, id_user=request.user).count() == 0:
        raise HTTPException(403, "Forbidden")
    chat = await ChatsChat.filter(id=item.id).first().values()
    mes = await ChatsMessage.filter(id_chat=item.id).order_by("-id").offset(0).limit(10).values()
    await HistoryChatNotification.filter(id_user=request.user,id_chat=chat["id"],is_readed=False).update(is_readed=True)
    for message in mes:
        del message["id"]
        del message["id_chat"]
        message["isMe"] = False
        if message["id_sender"] == request.user:
            message["isMe"] = True
        del message["id_sender"]
    return JSONResponse({"status": True,
                         "message": "Success!",
                         "chat": {
                             "id": chat["id"],
                             "blocked": not chat["isActive"],
                             "reg_date": chat["datetime_create"].isoformat(),
                             "last_messages": mes
                         }})


@router.post("/get_messages",
             responses=generate_responses([get_messages]))
async def get_chat_by_id(request: Request, item: GetMessages):
    if await ChatsChatParticipant.filter(id_chat=item.id_chat, id_user=request.user).count() == 0:
        raise HTTPException(403, "Forbidden")
    chat = await ChatsChat.filter(id=item.id_chat).first().values()
    mes = await ChatsMessage.filter(id_chat=item.id_chat).order_by("-id").offset(item.offset).limit(item.limit).values()
    count = await ChatsMessage.filter(id_chat=item.id_chat).count()
    await HistoryChatNotification.filter(id_user=request.user,id_chat=chat["id"],is_readed=False).update(is_readed=True)
    for message in mes:
        del message["id"]
        del message["id_chat"]
        message["isMe"] = False
        if message["id_sender"] == request.user:
            message["isMe"] = True
        del message["id_sender"]
    return JSONResponse({"status": True,
                         "message": "Success!",
                         "id_chat": chat["id"],
                         "messages": mes,
                         "total": count
                         })