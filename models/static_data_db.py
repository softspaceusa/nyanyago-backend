from tortoise.models import Model
from tortoise import fields


class DataCountry(Model):
    id = fields.BigIntField(pk=True)
    title = fields.TextField()

    class Meta:
        schema = "data"
        table = "country"

    def __str__(self):
        return self.title


class DataColor(Model):
    id = fields.BigIntField(pk=True)
    title = fields.TextField()

    class Meta:
        schema = "data"
        table = "color"

    def __str__(self):
        return self.title


class DataCity(Model):
    id = fields.BigIntField(pk=True)
    title = fields.TextField()

    class Meta:
        schema = "data"
        table = "city"

    def __str__(self):
        return self.title


class DataCarMark(Model):
    id = fields.BigIntField(pk=True)
    title = fields.TextField()

    class Meta:
        schema = "data"
        table = "car_mark"

    def __str__(self):
        return self.title


class DataCarModel(Model):
    id = fields.BigIntField(pk=True)
    title = fields.TextField()
    id_car_mark = fields.BigIntField(null=False)
    releaseYear = fields.IntField(null=True)

    class Meta:
        schema = "data"
        table = "car_model"

    def __str__(self):
        return self.title


class DataTypeAccount(Model):
    id = fields.BigIntField(pk=True)
    title = fields.TextField()

    class Meta:
        schema = "data"
        table = "type_account"

    def __str__(self):
        return self.title


class DataOtherDriveParametr(Model):
    id = fields.BigIntField(pk=True)
    title = fields.TextField()
    amount = fields.DecimalField(10, 2)
    isActive = fields.BooleanField(default=True)


    class Meta:
        schema = "data"
        table = "other_drive_parametr"

    def __str__(self):
        return self.title


class DataCarTariff(Model):
    id = fields.BigIntField(pk=True)
    title = fields.TextField()
    description = fields.TextField(null=True)
    amount = fields.BigIntField(null=True)
    percent = fields.BigIntField(null=True)
    photo_path = fields.TextField(null=True)
    id_franchise = fields.BigIntField(null=False)
    isActive = fields.BooleanField(default=True)
    datetime_create = fields.DatetimeField(null=True)


    class Meta:
        schema = "data"
        table = "car_tariff"

    def __str__(self):
        return self.title
