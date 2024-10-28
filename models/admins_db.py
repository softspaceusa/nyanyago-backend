from tortoise import fields
from tortoise.models import Model


class AdminMobileSettings(Model):
    id = fields.BigIntField(pk=True)
    biometry = fields.BooleanField()

    class Meta:
        schema = "admin"
        table = "mobile_settings"

    def __str__(self):
        return self.id


