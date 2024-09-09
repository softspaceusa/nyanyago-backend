from tortoise import fields
from tortoise.models import Model


class UsersUser(Model):
    id = fields.BigIntField(pk=True)
    surname = fields.TextField()
    name = fields.TextField()
    phone = fields.TextField()
    isActive = fields.BooleanField(default=True)
    datetime_create = fields.DatetimeField(null=True)


    class Meta:
        schema = "users"
        table = "user"

    def __str__(self):
        return self.id


class DataUploadedFile(Model):
    id = fields.BigIntField(pk=True)
    id_user = fields.BigIntField(null=False)
    files_path = fields.TextField(null=False)
    datetime_create = fields.DatetimeField(null=True)

    class Meta:
        schema = "data"
        table = "uploaded_file"

    def __str__(self):
        return self.id


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



class UsersReferalUser(Model):
    id = fields.BigIntField(pk=True)
    id_user = fields.BigIntField(null=False)
    id_user_referal = fields.BigIntField(null=False)
    datetime_create = fields.DatetimeField(null=True)


    class Meta:
        schema = "users"
        table = "referal_user"

    def __str__(self):
        return self.id_user


class UsersReferalCode(Model):
    id = fields.BigIntField(pk=True)
    id_user = fields.BigIntField(null=False)
    code = fields.TextField()
    datetime_create = fields.DatetimeField(null=True)

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
    datetime_create = fields.DatetimeField(null=True)

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


class UsersVerifyAccount(Model):
    id = fields.BigIntField(pk=True)
    id_user = fields.BigIntField(null=False)


    class Meta:
        schema = "users"
        table = "verify_account"

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


class WaitDataVerifyRegistration(Model):
    id = fields.BigIntField(pk=True)
    phone = fields.TextField()


    class Meta:
        schema = "wait_data"
        table = "verify_registration"

    def __str__(self):
        return self.id











