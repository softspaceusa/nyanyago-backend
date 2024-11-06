from tortoise.models import Model
from tortoise import fields


class DataCountry(Model):
    """
    Используется для хранения стран мира (Несмотря на работу проекта только в границах России, права могут быть выданы
     в других странах).
    """
    id = fields.BigIntField(pk=True)
    title = fields.TextField()

    class Meta:
        schema = "data"
        table = "country"

    def __str__(self):
        return self.title


class DataColor(Model):
    """
    Используется для хранения информации об основных цветах окраски автомобилей.
    """
    id = fields.BigIntField(pk=True)
    title = fields.TextField()

    class Meta:
        schema = "data"
        table = "color"

    def __str__(self):
        return self.title


class DataCity(Model):
    """
    Используется для хранения городов России (Проект будет работать только в России).
    """
    id = fields.BigIntField(pk=True)
    title = fields.TextField()

    class Meta:
        schema = "data"
        table = "city"

    def __str__(self):
        return self.title


class DataCarMark(Model):
    """
    Используется для хранения актуальных марок автомобилей.
    """
    id = fields.BigIntField(pk=True)
    title = fields.TextField()

    class Meta:
        schema = "data"
        table = "car_mark"

    def __str__(self):
        return self.title


class DataCarModel(Model):
    """
    Используется для хранения актуальных моделей автомобилей.
    """
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
    """
    Используется для хранения информации о ролях приложения.
    Можно заменить константами.
    """
    id = fields.BigIntField(pk=True)
    title = fields.TextField()

    class Meta:
        schema = "data"
        table = "type_account"

    def __str__(self):
        return self.title


class DataOtherDriveParametr(Model):
    """
    Используется для хранения информации о дополнительных услугах, доступных пользователям при оформлении поездок
    по графику и разовых.
    """
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
    """
    Используется для хранения информации о тарифах.
    Обсуждалось, что у каждой франшизы есть тарифы по умолчанию, но также они могут создавать свои собсвенные,
    стоимость которых будет равна бизнес тарифу.
    Ссылается на модель UsersFranchise.
    """
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
