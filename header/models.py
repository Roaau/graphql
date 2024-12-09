# Create your models here.
from django.db import models
from django.conf import settings
from django.utils.timezone import now

# Create your models here.
class Header(models.Model):
    name         = models.TextField(default='')
    description  = models.TextField(default='')
    image_url    = models.URLField(max_length=500, blank=True, null=True)
    email        = models.EmailField(max_length=254, unique=True, blank=False)
    phone_number = models.CharField(max_length=20, blank=True)
    location     = models.TextField(default='')
    github       = models.TextField(default='')
    posted_by    = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE) 