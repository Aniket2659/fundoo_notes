from django.db import models
from django.conf import settings

class Label(models.Model):
    name = models.CharField(max_length=255, null=False)
    color = models.CharField(max_length=50, null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='labels')

    class Meta:
        db_table = 'label'


    def __str__(self):
        return self.name