from tortoise import fields
from tortoise.models import Model


class UsersUser(Model):
    """
    Используется для хранения информации о пользователях.
    Номер телефона не шифруется, но приведен к общему стандарту.
    """
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
    """
    Используется для хранения информации о рефералах пользователей (партнера и водителя).
    Ссылается на модель UsersUser.
    """
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
    """
    Используется для хранении информации о пользователях, которые могут авторизововаться в приложении (Подтвержденные).
    Ссылается на модель UsersUser.
    """
    id = fields.BigIntField(pk=True)
    id_user = fields.BigIntField(null=False)


    class Meta:
        schema = "users"
        table = "verify_account"

    def __str__(self):
        return self.id


class UsersUserPhoto(Model):
    """
    Используется для хранении пользовательской аватарки.
    Ссылается на модель UsersUser.
    """
    id = fields.BigIntField(pk=True)
    id_user = fields.BigIntField(null=False)
    photo_path = fields.TextField()


    class Meta:
        schema = "users"
        table = "user_photo"

    def __str__(self):
        return self.id


class WaitDataVerifyRegistration(Model):
    """
    Используется для хранении номеров, которые проходят этап регистрации, но не были подтверждены кодом.
    """
    id = fields.BigIntField(pk=True)
    phone = fields.TextField()


    class Meta:
        schema = "wait_data"
        table = "verify_registration"

    def __str__(self):
        return self.id


class DataTaskBalanceHistory(Model):
    """
    Модель используется для хранения типов платежных операций.
    Можно заменить на константы.
    """
    id = fields.BigIntField(pk=True)
    title = fields.TextField()


    class Meta:
        schema = "data"
        table = "task_balance_history"

    def __str__(self):
        return self.id


class DataUserBalance(Model):
    """
    Используется для храненя текущего баланса пользователей (Клиент, Водитель, Партнёр).
    Ссылается на модель UsersUser.
    """
    id = fields.BigIntField(pk=True)
    id_user = fields.BigIntField(null=False)
    money = fields.DecimalField(10, 2)


    class Meta:
        schema = "data"
        table = "user_balance"

    def __str__(self):
        return self.id


class DataUserBalanceHistory(Model):
    """
    Используется для хранения историй платежей пользоватей.
    Ссылается на модель UsersUser,
    """
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
    """
    Модель должна использоваться для хранения части информации банковских карт (последних цифр карты, срока годности).
    Ссылается на модель UsersUser.
    """
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
    """
    Используется для хранения истории платежей (выплаты).
    Удалить ссылку на карту пользователя.
    Изменить логику и подстроить модель данных.
    Ссылается на модель UsersUser.
    """
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
    """
    Используется для хранения информации о принадлежании пользователя к франшизе.
    Ссылается на модель UsersUser, UsersFranchise
    """
    id = fields.BigIntField(pk=True)
    id_user = fields.BigIntField(null=False)
    id_franchise = fields.BigIntField(null=False)


    class Meta:
        schema = "users"
        table = "franchise_user"

    def __str__(self):
        return self.id


class HistoryPaymentTink(Model):
    """
    Удалить модель. Не имеем права так делать. Реализовать логику платежей с нуля.
    """
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
    """
    Удалить модель. Не имеем права так делать. Реализовать логику платежей с нуля.
    """
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
    """
    Используется для хранения информации о франшизах проекта.
    """
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
    """
    Используется для связи города и франшизы (многие ко многим).
    Ссылается на модель DataCity, UsersFranchise.
    """
    id = fields.BigIntField(pk=True)
    id_franchise = fields.BigIntField(null=False)
    id_city = fields.BigIntField(null=False)


    class Meta:
        schema = "users"
        table = "franchise_city"

    def __str__(self):
        return self.id


class HistoryNotification(Model):
    """
    Используется для хранения информации об ранее отправленных push уведомлений пользователям.
    Не требуется по ТЗ, можно удалить.
    """
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
    """
    Используется для хранения информации о связи пользователя и авторизации через ВКонтакте.
    Ссылается на UsersUser.
    Можно оптимизировать, объединив модель с данными UsersUserYandex, ддобавив флаг на тип сервиса.
    """
    id = fields.BigIntField(pk=True)
    id_user = fields.BigIntField(null=False)
    vk_id = fields.TextField(null=True)


    class Meta:
        schema = "users"
        table = "user_vk"

    def __str__(self):
        return self.id


class UsersUserYandex(Model):
    """
    Используется для хранения информации о связи пользователя и авторизации через Яндекс.
    Ссылается на UsersUser.
    Можно оптимизировать, объединив модель с данными UsersUserVk, ддобавив флаг на тип сервиса.
    """

    id = fields.BigIntField(pk=True)
    id_user = fields.BigIntField(null=False)
    yandex_id = fields.TextField(null=True)


    class Meta:
        schema = "users"
        table = "user_yandex"

    def __str__(self):
        return self.id


class UsersPaymentClient(Model):
    """
    Необходима для хранения ключей оплаты для автопополнения баланса по запросу пользователя.
    Ссылается на UsersUser.
    Данные не шифруются.
    """
    id = fields.BigIntField(pk=True)
    id_user = fields.BigIntField(null=False)
    customer_key = fields.TextField(null=False)
    datetime_create = fields.DatetimeField(null=True)


    class Meta:
        schema = "users"
        table = "payment_client"

    def __str__(self):
        return self.id



