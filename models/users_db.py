from tortoise import fields
from tortoise.models import Model


class UsersUser(Model):
    id = fields.BigIntField(pk=True)
    surname = fields.TextField(null=True)
    name = fields.TextField(null=True)
    phone = fields.TextField()
    isActive = fields.BooleanField(default=True)
    datetime_create = fields.DatetimeField(null=True)


    class Meta:
        schema = "users"
        table = "user"

    def __str__(self):
        return self.id


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


class UsersVerifyAccount(Model):
    id = fields.BigIntField(pk=True)
    id_user = fields.BigIntField(null=False)


    class Meta:
        schema = "users"
        table = "verify_account"

    def __str__(self):
        return self.id


class UsersUserPhoto(Model):
    id = fields.BigIntField(pk=True)
    id_user = fields.BigIntField(null=False)
    photo_path = fields.TextField()


    class Meta:
        schema = "users"
        table = "user_photo"

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


class DataTaskBalanceHistory(Model):
    id = fields.BigIntField(pk=True)
    title = fields.TextField()


    class Meta:
        schema = "data"
        table = "task_balance_history"

    def __str__(self):
        return self.id


class DataUserBalance(Model):
    id = fields.BigIntField(pk=True)
    id_user = fields.BigIntField(null=False)
    money = fields.DecimalField(10, 2)


    class Meta:
        schema = "data"
        table = "user_balance"

    def __str__(self):
        return self.id


class DataUserBalanceHistory(Model):
    id = fields.BigIntField(pk=True)
    id_user = fields.BigIntField(null=False)
    id_task = fields.BigIntField(null=True)
    description = fields.TextField(null=True)
    money = fields.DecimalField(10, 2)
    datetime_create = fields.DatetimeField(null=True)
    isComplete = fields.BooleanField(null=True)


    class Meta:
        schema = "data"
        table = "user_balance_history"

    def __str__(self):
        return self.id


class DataDebitCard(Model):
    id = fields.BigIntField(pk=True)
    id_user = fields.BigIntField(null=False)
    card_number = fields.TextField()
    exp_date = fields.TextField()
    name = fields.TextField()
    isActive = fields.BooleanField(default=True)
    datetime_create = fields.DatetimeField(null=True)


    class Meta:
        schema = "data"
        table = "debit_card"

    def __str__(self):
        return self.id


class HistoryRequestPayment(Model):
    id = fields.BigIntField(pk=True)
    id_user = fields.BigIntField(null=False)
    id_card = fields.BigIntField(null=False)
    id_history = fields.BigIntField(null=False)
    money = fields.DecimalField(10, 2)
    isCashback = fields.BooleanField(default=False)
    isSuccess = fields.BooleanField(default=False)
    isActive = fields.BooleanField(default=True)
    datetime_create = fields.DatetimeField(null=True)


    class Meta:
        schema = "history"
        table = "request_payment"

    def __str__(self):
        return self.id


class UsersFranchiseUser(Model):
    id = fields.BigIntField(pk=True)
    id_user = fields.BigIntField(null=False)
    id_franchise = fields.BigIntField(null=False)


    class Meta:
        schema = "users"
        table = "franchise_user"

    def __str__(self):
        return self.id


class HistoryPaymentTink(Model):
    id = fields.BigIntField(pk=True)
    id_user = fields.BigIntField(null=False)
    id_payment = fields.TextField()
    id_order = fields.TextField()
    amount = fields.BigIntField()
    ip = fields.TextField(null=True)
    token = fields.TextField(null=True)
    card_data = fields.TextField(null=True)
    datetime_create = fields.DatetimeField(null=True)


    class Meta:
        schema = "history"
        table = "payment_tink"

    def __str__(self):
        return self.id


class WaitDataPaymentTink(Model):
    id = fields.BigIntField(pk=True)
    id_user = fields.BigIntField(null=False)
    id_payment = fields.TextField()
    id_order = fields.TextField()
    amount = fields.BigIntField()
    ip = fields.TextField()
    token = fields.TextField()
    card_data = fields.TextField()
    TdsServerTransID = fields.TextField()
    datetime_create = fields.DatetimeField(null=True)


    class Meta:
        schema = "wait_data"
        table = "payment_tink_data"

    def __str__(self):
        return self.id


class UsersFranchise(Model):
    id = fields.BigIntField(pk=True)
    title = fields.TextField(null=True)
    description = fields.TextField(null=True)
    isActive = fields.BooleanField(default=True)
    datetime_create = fields.DatetimeField(null=True)


    class Meta:
        schema = "users"
        table = "franchise"

    def __str__(self):
        return self.id


class UsersFranchiseCity(Model):
    id = fields.BigIntField(pk=True)
    id_franchise = fields.BigIntField(null=False)
    id_city = fields.BigIntField(null=False)


    class Meta:
        schema = "users"
        table = "franchise_city"

    def __str__(self):
        return self.id


class HistoryNotification(Model):
    id = fields.BigIntField(pk=True)
    id_user = fields.BigIntField(null=False)
    title = fields.TextField(null=True)
    description = fields.TextField(null=True)
    is_readed = fields.BooleanField(default=False)
    datetime_create = fields.DatetimeField(null=True)


    class Meta:
        schema = "history"
        table = "notification"

    def __str__(self):
        return self.id


class UsersUserVk(Model):
    id = fields.BigIntField(pk=True)
    id_user = fields.BigIntField(null=False)
    vk_id = fields.TextField(null=True)


    class Meta:
        schema = "users"
        table = "user_vk"

    def __str__(self):
        return self.id


class UsersUserYandex(Model):
    id = fields.BigIntField(pk=True)
    id_user = fields.BigIntField(null=False)
    yandex_id = fields.TextField(null=True)


    class Meta:
        schema = "users"
        table = "user_yandex"

    def __str__(self):
        return self.id


class UsersPaymentClient(Model):
    id = fields.BigIntField(pk=True)
    id_user = fields.BigIntField(null=False)
    customer_key = fields.TextField(null=False)
    datetime_create = fields.DatetimeField(null=True)


    class Meta:
        schema = "users"
        table = "payment_client"

    def __str__(self):
        return self.id



