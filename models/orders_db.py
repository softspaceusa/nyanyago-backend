from tortoise import fields
from tortoise.models import Model


class DataDrivingStatus(Model):
    id = fields.BigIntField(pk=True)
    status = fields.TextField()


    class Meta:
        schema = "data"
        table = "driving_status"

    def __str__(self):
        return self.id


class DataOrder(Model):
    id = fields.BigIntField(pk=True)
    id_user = fields.BigIntField(null=False)
    id_driver = fields.BigIntField(null=True)
    id_status = fields.BigIntField(null=False)
    id_type_order = fields.BigIntField(null=False)
    isActive = fields.BooleanField(default=True)
    datetime_create = fields.DatetimeField(null=True)


    class Meta:
        schema = "data"
        table = "order"

    def __str__(self):
        return self.id


class WaitDataOrder(Model):
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
    id = fields.BigIntField(pk=True)
    id_order = fields.BigIntField(null=False)
    client_lon = fields.FloatField()
    client_lat = fields.FloatField()
    price = fields.DecimalField(10, 2)
    distance = fields.BigIntField()
    duration = fields.BigIntField()
    description = fields.TextField()
    id_tariff = fields.BigIntField(null=False)


    class Meta:
        schema = "data"
        table = "order_info"

    def __str__(self):
        return self.id


class WaitDataOrderInfo(Model):
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
    id = fields.BigIntField(pk=True)
    id_user = fields.BigIntField(null=False)
    title = fields.TextField(null=True)
    description = fields.TextField(null=True)
    duration = fields.BigIntField()
    children_count = fields.BigIntField()
    id_tariff = fields.BigIntField(null=False)
    week_days = fields.TextField()
    isActive = fields.BooleanField(default=False)
    datetime_create = fields.DatetimeField(null=True)


    class Meta:
        schema = "data"
        table = "schedule"

    def __str__(self):
        return self.id


class DataScheduleRoad(Model):
    id = fields.BigIntField(pk=True)
    id_schedule = fields.BigIntField(null=False)
    week_day = fields.BigIntField()
    title = fields.TextField(null=True)
    start_time = fields.TextField()
    end_time = fields.TextField()
    type_drive = fields.TextField()
    isActive = fields.BooleanField(default=True)
    datetime_create = fields.DatetimeField(null=True)
    amount = fields.BigIntField(null=True)


    class Meta:
        schema = "data"
        table = "schedule_road"

    def __str__(self):
        return self.id


class DataScheduleRoadAddress(Model):
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


class DataScheduleRoadDriver(Model):
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


class WaitDataScheduleRoadDriver(Model):
    id = fields.BigIntField(pk=True)
    id_road = fields.BigIntField(null=False)
    id_schedule = fields.BigIntField(null=False)
    id_driver = fields.BigIntField(null=False)
    isActive = fields.BooleanField(default=True)
    datetime_create = fields.DatetimeField(null=True)


    class Meta:
        schema = "wait_data"
        table = "schedule_road_drivers"

    def __str__(self):
        return self.id


class UsersUserOrder(Model):
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



