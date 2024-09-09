from tortoise import fields
from tortoise.models import Model


class ChatsChat(Model):
    id = fields.BigIntField(pk=True)
    isActive = fields.BooleanField(default=True)
    datetime_create = fields.DatetimeField(null=True)


    class Meta:
        schema = "chats"
        table = "chat"

    def __str__(self):
        return self.id


class ChatsMessage(Model):
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
    id = fields.BigIntField(pk=True)
    title = fields.TextField()


    class Meta:
        schema = "data"
        table = "message_type"

    def __str__(self):
        return self.id


class ChatsChatParticipant(Model):
    id = fields.BigIntField(pk=True)
    id_chat = fields.BigIntField(null=False)
    id_user = fields.BigIntField(null=False)


    class Meta:
        schema = "chats"
        table = "chat_participant"

    def __str__(self):
        return self.id


class ChatsChatParticipantToken(Model):
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

