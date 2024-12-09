# Create your models here.
from django.db import models
from django.conf import settings
from django.utils.timezone import now

# Create your models here.
class Skill(models.Model):
    skill      = models.TextField(default='')
    level      = models.IntegerField(default=0)
    posted_by  = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)

class Meta:
        db_table = 'skills_skills'