import time

from models.chats_db import ChatsChatParticipant, ChatsMessage, ChatsChatParticipantToken, HistoryChatNotification
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
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        try:
            del users[list(users.keys())[list(users.values()).index(websocket)]]
        except Exception:
            pass

    @staticmethod
    async def send_personal_message(message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


@router.websocket("/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    try:
        await manager.connect(websocket)
        if token not in users:
            users[token] = websocket
        while True:
            mes = await websocket.receive_text()
            data = json.loads(mes)
            data = DictToModel(data)
            id_user = (await ChatsChatParticipantToken.filter(token=token).first().values())["id_user"]
            if await ChatsChatParticipant.filter(id_chat=data.id_chat, id_user=id_user).count() == 0:
                return
            receiver = await ChatsChatParticipant.filter(id_chat=data.id_chat, id_user__not=id_user).first().values()
            receiver = DictToModel(receiver)
            rec_tok = await ChatsChatParticipantToken.filter(id_user=receiver.id_user).order_by("-id").first().values()
            rec_tok = DictToModel(rec_tok)
            message_new = await ChatsMessage.create(id_chat=data.id_chat, id_sender=id_user, msg=data.msg,
                                                        msgType=data.msgType, timestamp_send=time.time())
            await HistoryChatNotification.filter(id_user=id_user, id_chat=data.id_chat).update(is_readed=True)
            await HistoryChatNotification.create(id_user=receiver.id_user, id_chat=data.id_chat, id_msg=message_new.id)
            data_rec = {
                "id_chat": data.id_chat,
                "msg": data.msg,
                "msgType": data.msgType,
                "timestamp_send": time.time(),
                "isMe": False
            }
            data_me = {
                "id_chat": data.id_chat,
                "msg": data.msg,
                "msgType": data.msgType,
                "timestamp_send": time.time(),
                "isMe": True
            }
            if rec_tok.token in users:
                try:
                    try:
                        await manager.send_personal_message(json.dumps(data_rec), users[rec_tok.token])
                    except Exception:
                        await error(traceback.format_exc())
                        if rec_tok.token in users:
                            if users[rec_tok.token] is not None:
                                manager.disconnect(users[rec_tok.token])
                            del users[rec_tok.token]
                    try:
                        fbid = await UsersBearerToken.filter(id_user=receiver.id_user).order_by("-id").first().values()
                        msg_notification = data.msg if len(data.msg) <= 50 else data.msg[:47]+"..."
                        await sendPush(fbid["fbid"], "Новое сообщение",
                                       msg_notification, {"action":"message","id":data.id_chat})
                        await HistoryNotification.create(id_user=receiver.id_user, title="Новое сообщение",
                                                         description=msg_notification)
                    except Exception:
                        await error(traceback.format_exc())
                except Exception:
                    await error(traceback.format_exc())
            try:
                try:
                    await manager.send_personal_message(json.dumps(data_me), users[token])
                except Exception:
                    await error(traceback.format_exc())
                    if token in users: del users[token]
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