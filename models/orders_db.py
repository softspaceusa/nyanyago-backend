from tortoise import fields
from tortoise.models import Model
from datetime import datetime as default_datetime


class DataDrivingStatus(Model):
    """
    Используется для хранения статусов поездок.
    Можно заменить на константы.
    """
    id = fields.BigIntField(pk=True)
    status = fields.TextField()

    class Meta:
        schema = "data"
        table = "driving_status"

    def __str__(self):
        return self.id


class DataOrder(Model):
    """
    Основная модель поездки.
    Используется для хранения информации о заказе.
    """
    id = fields.BigIntField(pk=True)
    id_user = fields.BigIntField(null=False)
    id_driver = fields.BigIntField(null=True)
    id_status = fields.BigIntField(null=False)
    id_type_order = fields.BigIntField(null=False)
    isActive = fields.BooleanField(default=True)
    datetime_create = fields.DatetimeField(null=True)
    type_drive = fields.TextField(
        default="0")  # Тип поездки: в одну сторону, туда-обратно, с промежуточными точками (0, 1, 2)

    class Meta:
        schema = "data"
        table = "order"

    def __str__(self):
        return self.id


class WaitDataOrder(Model):
    """
    Модель не используется. Удалить.
    """
    id = fields.BigIntField(pk=True)
    id_user = fields.BigIntField(null=False)
    id_status = fields.BigIntField(null=False)
    id_type_order = fields.BigIntField(null=False)
    isActive = fields.BooleanField(default=True)
    datetime_create = fields.DatetimeField(null=True)

    class Meta:
        schema = "wait_data"
        table = "order_data"

    def __str__(self):
        return self.id


class DataOrderAddresses(Model):
    """
    Используется для хранения информации о промежуточных точках заказа.
    Данные не шифруются.
    Ссылается на модель DataOrder.
    """
    id = fields.BigIntField(pk=True)
    id_order = fields.BigIntField(null=False)
    from_address = fields.TextField()
    to_address = fields.TextField()
    from_lon = fields.FloatField()
    from_lat = fields.FloatField()
    to_lon = fields.FloatField()
    to_lat = fields.FloatField()
    isFinish = fields.BooleanField(default=False)

    class Meta:
        schema = "data"
        table = "order_addresses"

    def __str__(self):
        return self.id


class WaitDataOrderAddresses(Model):
    """
    Модель не используется. Удалить.
    """
    id = fields.BigIntField(pk=True)
    id_order = fields.BigIntField(null=False)
    from_address = fields.TextField()
    to_address = fields.TextField()
    from_lon = fields.FloatField()
    from_lat = fields.FloatField()
    to_lon = fields.FloatField()
    to_lat = fields.FloatField()
    isFinish = fields.BooleanField(default=False)

    class Meta:
        schema = "wait_data"
        table = "order_addresses_data"

    def __str__(self):
        return self.id


class DataOrderInfo(Model):
    """
    Используется для хранения дополнительной информации о заказе.
    Геолокация клиента в модели необязательна, можно удалить.
    Ссылается на модель DataOrder.
    """
    id = fields.BigIntField(pk=True)
    id_order = fields.BigIntField(null=False)
    client_lon = fields.FloatField()
    client_lat = fields.FloatField()
    price = fields.DecimalField(10, 2)
    distance = fields.BigIntField()  # Расстояние в метрах
    duration = fields.BigIntField()  # Время в секундах
    description = fields.TextField()
    id_tariff = fields.BigIntField(null=False)

    class Meta:
        schema = "data"
        table = "order_info"

    def __str__(self):
        return self.id


class WaitDataOrderInfo(Model):
    """
    Модель не используется. Удалить.
    """
    id = fields.BigIntField(pk=True)
    id_order = fields.BigIntField(null=False)
    client_lon = fields.FloatField()
    client_lat = fields.FloatField()
    price = fields.DecimalField(10, 2)
    distance = fields.BigIntField()
    duration = fields.BigIntField()
    description = fields.TextField()
    id_tariff = fields.BigIntField(null=False)
    id_type_drive = fields.BigIntField(null=False)

    class Meta:
        schema = "wait_data"
        table = "order_info_data"

    def __str__(self):
        return self.id


class WaitDataSearchDriver(Model):
    """
    Старая модель для хранения токена WebSocket для подключения клиента к поиску водителя.
    Удалить.
    Ссылается на UsersUser, DataOrder.
    """
    id = fields.BigIntField(pk=True)
    id_user = fields.BigIntField(null=False)
    id_order = fields.BigIntField(null=False)
    token = fields.TextField()

    class Meta:
        schema = "wait_data"
        table = "search_driver"

    def __str__(self):
        return self.id


class DataSchedule(Model):
    """
    Основная модель графика поездок.
    Ссылается на UsersUser, DataCarTariff.
    """
    id = fields.BigIntField(pk=True)
    id_user = fields.BigIntField(null=False)
    title = fields.TextField(null=True)
    description = fields.TextField(null=True)
    duration = fields.BigIntField()
    children_count = fields.BigIntField()
    id_tariff = fields.BigIntField(null=False)
    week_days = fields.TextField()
    isActive = fields.BooleanField(
        default=False)  # Либо True/False (если присутствует), либо None (если удалено). Логика при True и False сейчас не отличается никак.
    datetime_create = fields.DatetimeField(null=True)

    class Meta:
        schema = "data"
        table = "schedule"

    def __str__(self):
        return self.id


class DataScheduleRoad(Model):
    """
    Используется для хранения информации о маршрутах графиков поездок.
    Ссылается на модель DataSchedule.
    """
    id = fields.BigIntField(pk=True)
    id_schedule = fields.BigIntField(null=False)
    week_day = fields.BigIntField()
    title = fields.TextField(null=True)
    start_time = fields.TextField()  # Время в формате HH:MM - часовой пояс UTC
    end_time = fields.TextField()  # Время в формате HH:MM - часовой пояс UTC
    type_drive = fields.TextField()  # Тип поездки: в одну сторону, туда-обратно, с промежуточными точками (0, 1, 2)
    isActive = fields.BooleanField(default=True)
    datetime_create = fields.DatetimeField(null=True)
    amount = fields.DecimalField(10, 2)

    class Meta:
        schema = "data"
        table = "schedule_road"

    def __str__(self):
        return self.id


class DataScheduleRoadAddress(Model):
    """
    Используется для хранения информации об адрессах маршрутов графика.
    Ссылается на модель DataScheduleRoad.
    """
    id = fields.BigIntField(pk=True)
    id_schedule_road = fields.BigIntField(null=False)
    from_address = fields.TextField()
    to_address = fields.TextField()
    from_lon = fields.FloatField()
    from_lat = fields.FloatField()
    to_lon = fields.FloatField()
    to_lat = fields.FloatField()

    class Meta:
        schema = "data"
        table = "schedule_road_address"

    def __str__(self):
        return self.id


class DataScheduleOtherParametrs(Model):
    """
    Используется для хранения дополнительных параметров графика (доп услуги).
    Ссылается на DataSchedule, DataOtherParametrs
    """
    id = fields.BigIntField(pk=True)
    id_schedule = fields.BigIntField(null=False)
    id_other_parametr = fields.BigIntField(null=False)
    amount = fields.BigIntField()
    isActive = fields.BooleanField(default=True)
    datetime_create = fields.DatetimeField(null=True)

    class Meta:
        schema = "data"
        table = "schedule_other_parametrs"

    def __str__(self):
        return self.id


class DataOrderOtherParametrs(Model):
    """
    Таблица для хранения дополнительных параметров заказов (доп. услуги).
    Ссылается на DataOrder и DataOtherParametrs.
    """
    id = fields.BigIntField(pk=True)
    id_order = fields.BigIntField(null=False)
    id_other_parametr = fields.BigIntField(null=False)
    amount = fields.BigIntField()
    isActive = fields.BooleanField(default=True)
    datetime_create = fields.DatetimeField(null=True)

    class Meta:
        schema = "data"
        table = "order_other_parametrs"

    def __str__(self):
        return str(self.id)


class DataScheduleRoadDriver(Model):
    """
    Используется для связи графиков и маршрутов графиков с водителем.
    Содержит информацию о типе поездки.
    Ссылается на UsersUser, DataScheduleRoad.
    id_order удалить, не требуется в алгоритме и модели.
    """
    id = fields.BigIntField(pk=True)
    id_schedule_road = fields.BigIntField(null=False)
    id_driver = fields.BigIntField(null=False)
    isRepeat = fields.BooleanField(default=True)
    # id_order = fields.BigIntField(null=True)
    isActive = fields.BooleanField(default=True)
    datetime_create = fields.DatetimeField(null=True)

    class Meta:
        schema = "data"
        table = "schedule_road_driver"

    def __str__(self):
        return self.id


class DataScheduleRoadContact(Model):
    """
    Используется хранения информации о контактном лице маршрутов графиков.
    """
    id = fields.BigIntField(pk=True)
    id_schedule_road = fields.BigIntField(null=False)
    surname = fields.TextField(null=True)
    name = fields.TextField(null=True)
    patronymic = fields.TextField(null=True)
    contact_phone = fields.TextField(null=True)
    isActive = fields.BooleanField(default=True)
    datetime_create = fields.DatetimeField(null=True)

    class Meta:
        schema = "data"
        table = "schedule_road_contact"

    def __str__(self):
        return self.id


class DataScheduleRoadChild(Model):
    """
    Используется хранения информации о ребёнке маршрута.
    """
    id = fields.BigIntField(pk=True)
    id_schedule_road = fields.BigIntField(null=False)
    id_child = fields.BigIntField(null=False)
    isActive = fields.BooleanField(default=True)
    datetime_create = fields.DatetimeField(null=True)

    class Meta:
        schema = "data"
        table = "schedule_road_child"

    def __str__(self):
        return self.id


class WaitDataScheduleRoadDriver(Model):
    """
    Используется для хранения заявок водителей на принятие маршрутов графиков.
    Ссылается на UsersUser, DataSchedule, DataScheduleRoad.
    """
    id = fields.BigIntField(pk=True)
    id_road = fields.BigIntField(null=False)
    id_schedule = fields.BigIntField(null=False)
    id_driver = fields.BigIntField(null=False)
    isActive = fields.BooleanField(
        default=True)  # False - отклонено, True - активно, None - уже одобрено
    datetime_create = fields.DatetimeField(default=default_datetime.now())
    full_time = fields.BooleanField(default=True)  # НЕ ИСПОЛЬЗУЕТСЯ

    class Meta:
        schema = "wait_data"
        table = "schedule_road_drivers"

    def __str__(self):
        return self.id


class UsersUserOrder(Model):
    """
    Используется для хранения токена WebSocket и связи между пользователем и заказом.
    """
    id = fields.BigIntField(pk=True)
    id_user = fields.BigIntField(null=False)
    id_order = fields.BigIntField(null=False)
    token = fields.TextField(null=False)
    isActive = fields.BooleanField(default=True)

    class Meta:
        schema = "users"
        table = "user_order"

    def __str__(self):
        return self.id
