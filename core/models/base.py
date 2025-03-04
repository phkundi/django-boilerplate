import uuid
from django.db import models


def upload_path(instance=None, filename=None, prefix=False):
    """
    Create unique name for image or file
    """
    image_folder_name = getattr(instance, "image_folder_name", "images")
    new_name = str(uuid.uuid4().int)
    parts = filename.split(".")
    f = parts[-1]
    filename = new_name + "." + f
    return "%s/%s" % (image_folder_name, filename)


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(
        auto_now_add=True, null=True, verbose_name="Creation date"
    )
    updated_at = models.DateTimeField(
        auto_now=True, null=True, verbose_name="Modification date"
    )

    class Meta:
        abstract = True
