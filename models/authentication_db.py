from datetime import datetime as default_datetime
from tortoise import fields
from tortoise.models import Model


class UsersAuthorizationData(Model):
    id = fields.BigIntField(pk=True)
    login = fields.TextField()
    password = fields.TextField()
    id_user = fields.BigIntField(null=False)

    class Meta:
        schema = "users"
        table = "authorization_data"

    def __str__(self):
        return self.login


class UsersReferalCode(Model):
    id = fields.BigIntField(pk=True)
    id_user = fields.BigIntField(null=False)
    code = fields.TextField()
    percent = fields.IntField(null=True)

    class Meta:
        schema = "users"
        table = "referal_code"

    def __str__(self):
        return self.id


class UsersBearerToken(Model):
    id = fields.BigIntField(pk=True)
    id_user = fields.BigIntField(null=False)
    fbid = fields.TextField(null=True)
    token = fields.TextField()
    datetime_create = fields.DatetimeField(default=default_datetime.now())

    class Meta:
        schema = "users"
        table = "bearer_authorization"

    def __str__(self):
        return self.id


class HistoryBearerToken(Model):
    id = fields.BigIntField(pk=True)
    id_user = fields.BigIntField(null=False)
    fbid = fields.TextField(null=True)
    token = fields.TextField()
    datetime_create = fields.DatetimeField(null=True)

    class Meta:
        schema = "history"
        table = "old_token"

    def __str__(self):
        return self.id


class WaitDataVerifyCode(Model):
    id = fields.BigIntField(pk=True)
    phone = fields.TextField()
    code = fields.TextField()


    class Meta:
        schema = "wait_data"
        table = "verify_code"

    def __str__(self):
        return self.id


class WaitDataVerifyDriver(Model):
    id = fields.BigIntField(pk=True)
    id_driver = fields.BigIntField(null=False)

    class Meta:
        schema = "wait_data"
        table = "verify_driver"

    def __str__(self):
        return self.id


class UsersMobileAuthentication(Model):
    id = fields.BigIntField(pk=True)
    id_user = fields.BigIntField(null=False)
    code = fields.TextField()

    class Meta:
        schema = "users"
        table = "mobile_authentication"

    def __str__(self):
        return self.id


class UsersUserAccount(Model):
    id = fields.BigIntField(pk=True)
    id_user = fields.BigIntField(null=False)
    id_type_account = fields.BigIntField(null=False)

    class Meta:
        schema = "users"
        table = "user_account"

    def __str__(self):
        return self.id
