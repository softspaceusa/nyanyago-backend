from tortoise import fields
from tortoise.models import Model


class ChatsChat(Model):
    """
    Используется для хранения информации о созданом чате.
    Чат создается для поездок и заявок на графики автоматически.
    Не имеет доп. информации, поэтому короткая модель.
    """
    id = fields.BigIntField(pk=True)
    isActive = fields.BooleanField(default=True)
    datetime_create = fields.DatetimeField(null=True)


    class Meta:
        schema = "chats"
        table = "chat"

    def __str__(self):
        return self.id


class ChatsMessage(Model):
    """
    Используется для хранения сообщений чатов.
    Ссылается на модель ChatsChat, UsersUser, DataMessageType.
    """
    id = fields.BigIntField(pk=True)
    id_chat = fields.BigIntField(null=False)
    id_sender = fields.BigIntField(null=False)
    msg = fields.TextField(null=False)
    msgType = fields.IntField(null=False)
    timestamp_send = fields.BigIntField(null=True)


    class Meta:
        schema = "chats"
        table = "message"

    def __str__(self):
        return self.id


class DataMessageType(Model):
    """
    Используется для хранения наименований и типов сообщений.
    Можно удалить, если сделать типы сообщений константами.
    """
    id = fields.BigIntField(pk=True)
    title = fields.TextField()


    class Meta:
        schema = "data"
        table = "message_type"

    def __str__(self):
        return self.id


class ChatsChatParticipant(Model):
    """
    Используется для хранения информации об участниках чата (поддерживает более 2х собеседников, поэтому реализована
    отдельная модель для участников).
    Ссылается на модель UsersUser, ChatsChat.
    """
    id = fields.BigIntField(pk=True)
    id_chat = fields.BigIntField(null=False)
    id_user = fields.BigIntField(null=False)


    class Meta:
        schema = "chats"
        table = "chat_participant"

    def __str__(self):
        return self.id


class ChatsChatParticipantToken(Model):
    """
    Используется для хранения информации о соотношении пользователя и токена для WebSockets.
    Ссылается на модель UsersUser.
    """
    id = fields.BigIntField(pk=True)
    id_user = fields.BigIntField(null=False)
    token = fields.TextField()
    datetime_create = fields.DatetimeField(null=True)


    class Meta:
        schema = "chats"
        table = "chat_participant_token"

    def __str__(self):
        return self.id


class HistoryChatNotification(Model):
    """
    Используется для хранения информации о непрочитанных сообщений.
    Можно оптимизировав, добавив флаг новых сообщений/их количества в модель ChatsChat.
    Ссылается на модель UsersUser, ChatsChat, ChatsMessage
    """
    id = fields.BigIntField(pk=True)
    id_user = fields.BigIntField(null=False)
    id_chat = fields.BigIntField(null=False)
    id_msg = fields.BigIntField(null=False)
    is_readed = fields.BooleanField(default=False)
    datetime_create = fields.DatetimeField(null=True)


    class Meta:
        schema = "history"
        table = "chat_notification"

    def __str__(self):
        return self.id

