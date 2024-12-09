# Create your models here.
from django.db import models
from django.conf import settings
from django.utils.timezone import now

# Create your models here.
class Certificate(models.Model):
    title       = models.TextField(default='')
    date        = models.DateTimeField(default=now, blank=True)
    description = models.TextField(default='')
    posted_by   = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)