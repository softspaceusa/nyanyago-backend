from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Union


chat_not_found_answer = JSONResponse({"status": False,
                                      "message": "Chat not found!"}, 404)
get_chats = JSONResponse({"status": True,
                         "message": "Success!",
                         "chats": [
                                    {
                                        "id_chat": 0,
                                        "username": "string",
                                        "photo_path": "string",
                                        "message": {
                                                    "msg": "string",
                                                    "time": 0
                                        }
                                    }],
                         "total": 0})
get_chat = JSONResponse({"status": True,
                         "message": "Success!",
                         "chat": {
                                    "id": 0,
                                    "blocked": False,
                                    "reg_date": "string",
                                    "last_messages": [
                                                        {
                                                            "msg": "string",
                                                            "msgType": 0,
                                                            "timestamp_send": 0,
                                                            "isMe": True
                                                        }
                                    ]
                                }
                        })
get_messages = JSONResponse({"status": True,
                             "message": "Success!",
                             "id_chat": 1,
                             "messages": [
                                            {
                                                "id": 0,
                                                "msg": "string",
                                                "msgType": 0,
                                                "timestamp_send": 0,
                                                "isMe": True
                                            }
                             ],
                             "total": 0})


class GetChats(BaseModel):
    offset: Union[int, None] = 0
    limit: Union[int, None] = 50
    search: Union[str, None] = ""


class GetChat(BaseModel):
    id: int


class GetMessages(BaseModel):
    id_chat: int
    offset: Union[int, None] = 0
    limit: Union[int, None] = 10