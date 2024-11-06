from tortoise import fields
from tortoise.models import Model


class AdminMobileSettings(Model):
    """
    Используется для хранения настроек приложений, заданных главным администратором
    """
    id = fields.BigIntField(pk=True)
    biometry = fields.BooleanField()

    class Meta:
        schema = "admin"
        table = "mobile_settings"

    def __str__(self):
        return self.id


