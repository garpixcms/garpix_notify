from django.db import models


class NotifyMethodsMixin(models.Model):

    class Meta:
        abstract = True
