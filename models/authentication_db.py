from datetime import datetime as default_datetime
from tortoise import fields
from tortoise.models import Model


class UsersAuthorizationData(Model):
    """
    Используется для хранения авторизационных данных пользователей в системе.
    Пароль на данный момент в базе - md5.
     Ссылается на модель UsersUser.
    """
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
    """
    Используется для хранения информации об реферальном коде пользователя (водителя и партнера), а также его проценте.
    Процент задается в коде, так как является статичным.
    Ссылается на модель UsersUser.
    """
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
    """
    Данная модель не должна использоваться в коде, так как она не требуется. Необходимо удалить ее использоании
    в коде, изменить место хранения fbid, удалить проверку наличия токена в файле dependency.
    Ссылается на модель UsersUser.
    """
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
    """
    Данная модель не должна использоваться в коде, так как она не требуется. Необходимо удалить ее использоании
    в коде.
    Ссылается на модель UsersUser.
    """
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
    """
    Используется для хранения кода для потверждения регистрации аккаунта, сброса пароля от аккаунта.
    """
    id = fields.BigIntField(pk=True)
    phone = fields.TextField()
    code = fields.TextField()


    class Meta:
        schema = "wait_data"
        table = "verify_code"

    def __str__(self):
        return self.id


class WaitDataVerifyDriver(Model):
    """
    Используется для хранения ссылок на пользователей, которые ожидают подтверждения регистрации на роль
    водителя (от франшизы)
    """
    id = fields.BigIntField(pk=True)
    id_driver = fields.BigIntField(null=False)

    class Meta:
        schema = "wait_data"
        table = "verify_driver"

    def __str__(self):
        return self.id


class UsersMobileAuthentication(Model):
    """
    Используется для хранения пин-кода от приложения, если такой задан пользователем.
    Хранится в формате, который передает фронт (md5).
    Ссылается на модель UsersUser.
    """
    id = fields.BigIntField(pk=True)
    id_user = fields.BigIntField(null=False)
    code = fields.TextField()

    class Meta:
        schema = "users"
        table = "mobile_authentication"

    def __str__(self):
        return self.id


class UsersUserAccount(Model):
    """
    Исползуется для хранения роли пользователя. Связь многие ко многим в виду того, что клиент может быть водителем
    и наоборот.
    Ссылается на модель UsersUser, DataTypeAccount
    """
    id = fields.BigIntField(pk=True)
    id_user = fields.BigIntField(null=False)
    id_type_account = fields.BigIntField(null=False)

    class Meta:
        schema = "users"
        table = "user_account"

    def __str__(self):
        return self.id
