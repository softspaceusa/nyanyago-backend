from tortoise import fields
from tortoise.models import Model


class UsersDriverData(Model):
    id = fields.BigIntField(pk=True)
    id_driver = fields.BigIntField(null=False)
    id_city = fields.BigIntField(null=False)
    description = fields.TextField(null=True)
    age = fields.BigIntField(null=True)
    video_url = fields.TextField(null=True)
    id_driver_card = fields.BigIntField(null=False)
    id_car = fields.BigIntField(null=False)
    id_driver_answer = fields.BigIntField(null=False)
    isActive = fields.BooleanField(default=False)
    inn = fields.TextField(null=True)
    datetime_create = fields.DatetimeField(null=True)


    class Meta:
        schema = "users"
        table = "driver_data"

    def __str__(self):
        return self.id


class UsersDriverAnswer(Model):
    id = fields.BigIntField(pk=True)
    first_answer = fields.TextField(null=True)
    second_answer = fields.TextField(null=True)
    third_answer = fields.TextField(null=True)
    four_answer = fields.TextField(null=True)
    five_answer = fields.TextField(null=True)
    six_answer = fields.TextField(null=True)
    seven_answer = fields.TextField(null=True)


    class Meta:
        schema = "users"
        table = "driver_answer"

    def __str__(self):
        return self.id


class UsersCar(Model):
    id = fields.BigIntField(pk=True)
    id_car_mark = fields.BigIntField(null=False)
    id_car_model = fields.BigIntField(null=False)
    id_color = fields.BigIntField(null=False)
    year_create = fields.IntField(bull=False)
    state_number = fields.TextField()
    ctc = fields.TextField()


    class Meta:
        schema = "users"
        table = "car"

    def __str__(self):
        return self.id


class UsersDriverCard(Model):
    id = fields.BigIntField(pk=True)
    id_country = fields.BigIntField(null=False)
    license = fields.TextField()
    date_of_issue = fields.DateField()


    class Meta:
        schema = "users"
        table = "driver_card"

    def __str__(self):
        return self.id


class DataDriverMode(Model):
    id = fields.BigIntField(pk=True)
    id_driver = fields.BigIntField(null=False)
    latitude = fields.FloatField()
    longitude = fields.FloatField()
    websocket_token = fields.TextField()
    datetime_create = fields.DatetimeField(null=True)


    class Meta:
        schema = "data"
        table = "driver_mode"

    def __str__(self):
        return self.id


