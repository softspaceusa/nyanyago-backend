from typing import Optional

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


@router.post(
    "/get_chats",
    responses=generate_responses([get_chats])
)
async def get_all_chats(request: Request,
                        item: Union[GetChats, None] = None) -> JSONResponse:
    """Получает и возвращает список чатов пользователя с дополнительной информацией."""

    async def get_user_chats() -> list[dict]:
        """Получает список чатов пользователя с учетом пагинации."""
        query = ChatsChatParticipant.filter(id_user=request.user)
        if item is not None:
            query = query.limit(item.limit).offset(item.offset)
        return await query.all().values("id_chat")

    async def is_chat_active(chat_id: int) -> bool:
        """Проверяет, активен ли чат."""
        return await ChatsChat.filter(id=chat_id, isActive=False).count() == 0

    async def get_chat_participant(chat_id: int) -> Optional[dict]:
        """Получает информацию о собеседнике (о том, кто общается с request.user) в чате."""
        return await ChatsChatParticipant.filter(
            id_chat=chat_id,
            id_user__not=request.user
        ).first().values("id_user")

    async def get_user_info(user_id: int) -> dict:
        """Получает основную информацию о пользователе."""
        return await UsersUser.filter(id=user_id).first().values("name")

    async def get_user_photo(user_id: int) -> dict:
        """Получает фото пользователя."""
        photo = await UsersUserPhoto.filter(id_user=user_id).first().values()
        return photo.get("photo_path", not_user_photo)

    async def get_last_message(chat_id: int) -> Optional[dict]:
        """Получает последнее сообщение в чате."""
        return await ChatsMessage.filter(id_chat=chat_id).order_by(
            "-id").first().values()

    async def prepare_message_data(message: dict) -> dict:
        """Форматирует данные сообщения."""
        if message.get("msgType") == 1:
            return {
                "msg": message["msg"],
                "time": message["timestamp_send"]
            }

        message_type = await DataMessageType.filter(
            id=message["msgType"]).first().values("title")
        return {
            "msg": message_type["title"],
            "time": message["timestamp_send"]
        }

    async def get_unread_count(chat_id: int) -> int:
        """Считает непрочитанные сообщения."""
        return await HistoryChatNotification.filter(
            id_user=request.user,
            id_chat=chat_id,
            is_readed=False
        ).count()

    def apply_search(chats: list[dict]) -> list[dict]:
        """Фильтрует чаты по поисковому запросу (по вхождению в username собеседника)."""
        if not item or not item.search:
            return chats

        search_lower = item.search.lower()
        return [
            chat for chat in chats
            if "username" in chat and search_lower in chat["username"].lower()
        ]

    def sort_chats(chats: list[dict]) -> list[dict]:
        """Сортирует чаты по времени последнего сообщения."""

        def get_sort_key(chat):
            if not chat.get("message"):
                return 0
            return chat["message"].get("time", 0)

        return sorted(chats, key=get_sort_key, reverse=True)

    # 1. Получаем чаты пользователя
    user_chats = await get_user_chats()

    # 2. Фильтруем активные чаты
    active_chats = []
    for chat in user_chats:
        if await is_chat_active(chat["id_chat"]):
            active_chats.append(chat)

    # 3. Обогащаем информацию о чатах
    enriched_chats = []
    for chat in active_chats:
        chat_id = chat["id_chat"]
        result_chat = {"id_chat": chat_id}

        # Информация о собеседнике
        participant = await get_chat_participant(chat_id)
        if participant:
            user_info = await get_user_info(participant["id_user"])
            result_chat["username"] = user_info["name"]
            result_chat["photo_path"] = await get_user_photo(participant["id_user"])

        # Последнее сообщение
        last_message = await get_last_message(chat_id)
        if last_message:
            message_data = await prepare_message_data(last_message)
            message_data["new_message"] = await get_unread_count(chat_id)
            result_chat["message"] = message_data
        else:
            result_chat["message"] = None

        enriched_chats.append(result_chat)

    # 4. Применяем поиск
    filtered_chats = apply_search(enriched_chats)

    # 5. Сортируем чаты
    sorted_chats = sort_chats(filtered_chats)

    # 6. Получаем общее количество чатов
    total_chats = await ChatsChatParticipant.filter(id_user=request.user).count()

    return JSONResponse({
        "status": True,
        "message": "Success!",
        "chats": sorted_chats,
        "total": total_chats
    })


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


@router.post("/get_messages", responses=generate_responses([get_messages]))
async def get_chat_by_id(request: Request, item: GetMessages):
    """
    Возвращает сообщения из указанного чата.

    Args:
        request (Request): Объект запроса, содержащий информацию о пользователе.
        item (GetMessages): Данные запроса, содержащие идентификатор чата, смещение и лимит.

    Example:

        Пример запроса:

            {
                "id_chat": 1,
                "offset": 0,
                "limit": 10
            }

    Returns:
        JSONResponse: Ответ, содержащий статус операции, ID чата, список сообщений и общее количество сообщений.
    """
    if (
        await ChatsChatParticipant.filter(
            id_chat=item.id_chat, id_user=request.user
        ).count()
        == 0
    ):
        raise HTTPException(403, "Forbidden")
    chat = await ChatsChat.filter(id=item.id_chat).first().values()
    mes = (
        await ChatsMessage.filter(id_chat=item.id_chat)
        .order_by("-id")
        .offset(item.offset)
        .limit(item.limit)
        .values()
    )
    count = await ChatsMessage.filter(id_chat=item.id_chat).count()
    await HistoryChatNotification.filter(
        id_user=request.user, id_chat=chat["id"], is_readed=False
    ).update(is_readed=True)
    for message in mes:
        del message["id_chat"]
        message["isMe"] = False
        if message["id_sender"] == request.user:
            message["isMe"] = True
        del message["id_sender"]
    return JSONResponse(
        {
            "status": True,
            "message": "Success!",
            "id_chat": chat["id"],
            "messages": mes,
            "total": count,
        }
    )
