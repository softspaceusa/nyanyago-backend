import time

from models.chats_db import (
    ChatsChatParticipant,
    ChatsMessage,
    ChatsChatParticipantToken,
    HistoryChatNotification,
)
from models.authentication_db import UsersBearerToken
from const.static_data_const import DictToModel
from fastapi import APIRouter, WebSocket
from typing import List
from defs import error, sendPush
import traceback
import json

from models.users_db import HistoryNotification

router = APIRouter()
users = {}


class ConnectionManager:
    """
    Класс для управления WebSocket-соединениями.

    Отвечает за установку, отключение соединений и отправку сообщений
    всем подключенным клиентам или индивидуальным пользователям.
    """

    def __init__(self):
        """
        Инициализация ConnectionManager.

        Создает пустой список для хранения активных WebSocket-соединений.
        """
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """
        Устанавливает новое WebSocket-соединение.

        Принимает соединение от клиента и добавляет его в список активных соединений.

        Args:
            websocket (WebSocket): WebSocket-соединение клиента.
        """
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        """
        Отключает WebSocket-соединение.

        Удаляет соединение из списка активных соединений и удаляет соответствующий
        токен из словаря пользователей.

        Args:
            websocket (WebSocket): WebSocket-соединение клиента, которое нужно отключить.
        """
        self.active_connections.remove(websocket)
        try:
            token_to_remove = next(
                (token for token, ws in users.items() if ws == websocket), None
            )
            if token_to_remove:
                del users[token_to_remove]
        except Exception:
            pass

    @staticmethod
    async def send_personal_message(message: str, websocket: WebSocket):
        """
        Отправляет личное сообщение конкретному пользователю через его WebSocket-соединение.

        Args:
            message (str): Сообщение в формате JSON.
            websocket (WebSocket): WebSocket-соединение получателя.
        """
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        """
        На текущий момент метод не используется.
        Отправляет сообщение всем активным WebSocket-соединениям.

        Args:
            message (str): Сообщение в формате JSON.
        """
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


@router.websocket("/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    """
    Обрабатывает WebSocket-соединение для пользователя.

    Принимает сообщение от клиента, проверяет его, отправляет в чат и уведомляет
    другого пользователя через WebSocket или пуш-уведомление.

    Формат сообщения:

            {
                "id": 789, /* Поле следует отправить с фронта ТОЛЬКО при редактировании сообщения */
                "id_chat": 123,
                "msg": "string",
                "msgType": 1, /* 1 - текст, 2 - картинка, 3 - видео(или гифка), 4 - файл */
                "timestamp_send": 1702051285.1831043, /* unix timestamp - Поле отправляется ТОЛЬКО сервером */
                "isMe": False, /* Поле отправляется ТОЛЬКО сервером */
                "edited": True /* Поле отправляется ТОЛЬКО сервером и оно всегда либо True, либо поля просто нет*/
            }

    Args:
        websocket (WebSocket): WebSocket-соединение клиента.
        token (str): Уникальный токен пользователя, использующийся для идентификации.
    """
    try:
        await manager.connect(websocket)
        if token not in users:
            users[token] = websocket
        while True:
            mes = await websocket.receive_text()
            data = json.loads(mes)
            data = DictToModel(data)
            id_user = (
                await ChatsChatParticipantToken.filter(token=token).first().values()
            )["id_user"]
            if (
                await ChatsChatParticipant.filter(
                    id_chat=data.id_chat, id_user=id_user
                ).count()
                == 0
            ):
                continue
            receiver = (
                await ChatsChatParticipant.filter(
                    id_chat=data.id_chat, id_user__not=id_user
                )
                .first()
                .values()
            )
            receiver = DictToModel(receiver)
            rec_tok = (
                await ChatsChatParticipantToken.filter(id_user=receiver.id_user)
                .order_by("-id")
                .first()
                .values()
            )
            rec_tok = DictToModel(rec_tok)

            if data.id:  # Редактирование сообщения
                message_to_edit = await ChatsMessage.filter(
                    id=data.id, id_chat=data.id_chat, id_sender=id_user
                ).first()
                if message_to_edit:
                    await ChatsMessage.filter(id=data.id).update(
                        msg=data.msg,
                        msgType=data.msgType,
                    )
                    data_update_rec = {
                        "id": data.id,
                        "id_chat": data.id_chat,
                        "msg": data.msg,
                        "msgType": data.msgType,
                        "timestamp_send": message_to_edit.timestamp_send,
                        "isMe": False,
                        "edited": True,
                    }

                    data_update_me = {
                        "id": data.id,
                        "id_chat": data.id_chat,
                        "msg": data.msg,
                        "msgType": data.msgType,
                        "timestamp_send": message_to_edit.timestamp_send,
                        "isMe": True,
                        "edited": True,
                    }

                    if rec_tok.token in users:
                        try:
                            await manager.send_personal_message(
                                json.dumps(data_update_rec), users[rec_tok.token]
                            )
                        except Exception:
                            await error(traceback.format_exc())

                    try:
                        await manager.send_personal_message(
                            json.dumps(data_update_me), users[token]
                        )
                    except Exception:
                        await error(traceback.format_exc())

                    continue

                else:
                    continue

            message_new = await ChatsMessage.create(
                id_chat=data.id_chat,
                id_sender=id_user,
                msg=data.msg,
                msgType=data.msgType,
                timestamp_send=time.time(),
            )
            await HistoryChatNotification.filter(
                id_user=id_user, id_chat=data.id_chat
            ).update(is_readed=True)
            await HistoryChatNotification.create(
                id_user=receiver.id_user, id_chat=data.id_chat, id_msg=message_new.id
            )
            data_rec = {
                "id": message_new.id,
                "id_chat": data.id_chat,
                "msg": data.msg,
                "msgType": data.msgType,
                "timestamp_send": time.time(),
                "isMe": False,
            }
            data_me = {
                "id": message_new.id,
                "id_chat": data.id_chat,
                "msg": data.msg,
                "msgType": data.msgType,
                "timestamp_send": time.time(),
                "isMe": True,
            }
            if rec_tok.token in users:
                try:
                    try:
                        await manager.send_personal_message(
                            json.dumps(data_rec), users[rec_tok.token]
                        )
                    except Exception:
                        await error(traceback.format_exc())
                        if rec_tok.token in users:
                            if users[rec_tok.token] is not None:
                                manager.disconnect(users[rec_tok.token])
                            del users[rec_tok.token]
                    try:
                        fbid = (
                            await UsersBearerToken.filter(id_user=receiver.id_user)
                            .order_by("-id")
                            .first()
                            .values()
                        )
                        msg_notification = (
                            data.msg if len(data.msg) <= 50 else data.msg[:47] + "..."
                        )
                        await sendPush(  # TODO: Наверное отправлять Push надо, если пользователь не подключен к веб-сокету. Сейчас вроде бы наоборот.
                            fbid["fbid"],
                            "Новое сообщение",
                            msg_notification,
                            {"action": "message", "id": data.id_chat},
                        )
                        await HistoryNotification.create(
                            id_user=receiver.id_user,
                            title="Новое сообщение",
                            description=msg_notification,
                        )
                    except Exception:
                        await error(traceback.format_exc())
                except Exception:
                    await error(traceback.format_exc())
            try:
                try:
                    await manager.send_personal_message(
                        json.dumps(data_me), users[token]
                    )
                except Exception:
                    await error(traceback.format_exc())
                    if token in users:
                        del users[token]
                    if websocket is not None:
                        manager.disconnect(websocket)
            except Exception:
                await error(traceback.format_exc())
    except Exception:
        await error(traceback.format_exc())
        try:
            if websocket is not None:
                manager.disconnect(websocket)
        except Exception:
            pass
