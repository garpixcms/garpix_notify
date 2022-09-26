from django.db import models


class NotifyMixin(models.Model):

    class Meta:
        abstract = True


class NotifyMethodsMixin(models.Model):
    class Meta:
        abstract = True
