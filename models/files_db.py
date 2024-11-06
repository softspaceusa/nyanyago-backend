from tortoise.models import Model
from tortoise import fields


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