# Create your models here.
from django.db import models
from django.conf import settings
from django.utils.timezone import now

# Create your models here.
class WorkExperience(models.Model):
    role            = models.TextField(default='')
    company         = models.TextField(default='')
    accomplishments = models.JSONField(default=list, blank=True)  
    start_date      = models.DateTimeField(default=now, blank=True)
    end_date        = models.DateTimeField(default=now, blank=True)
    location        = models.TextField(default='')
    posted_by       = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)