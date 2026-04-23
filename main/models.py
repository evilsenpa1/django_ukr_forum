from django.db import models

 # Create your models here.


class Visitor(models.Model):
    ip = models.CharField(max_length=45)
    last_visit = models.DateTimeField(auto_now=True)
    user_agent = models.CharField(max_length=255, blank=True, null=True)
    session_key = models.CharField(max_length=40, unique=True)

    def __str__(self):
        return f"{self.ip} ({self.last_visit})"
    
