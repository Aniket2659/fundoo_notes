from django.db import models
from django.conf import settings
from user_auth.models import User
from label.models import Label

# Create your models here.

class Note(models.Model):
    title = models.CharField(max_length=500, null=False, db_index=True)
    description = models.TextField(null=True, blank=True)
    color = models.CharField(max_length=255, null=True, blank=True)
    image = models.ImageField(null=True, blank=True)
    is_archive = models.BooleanField(default=False, db_index=True)
    is_trash = models.BooleanField(default=False, db_index=True)
    reminder = models.DateTimeField(null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    collaborator = models.ManyToManyField(User, related_name="collaborated_notes", through='Collaborator')
    labels = models.ManyToManyField(Label, related_name='notes', blank=True)

    def __str__(self):
        return self.title

class Collaborator(models.Model):
    READ_ONLY = 'read_only'
    READ_WRITE = 'read_write'

    ACCESS_TYPE_CHOICES = [
        (READ_ONLY, 'Read Only'),
        (READ_WRITE, 'Read Write'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    note = models.ForeignKey(Note, on_delete=models.CASCADE, related_name="collaborators_relation")
    access_type = models.CharField(max_length=20, choices=ACCESS_TYPE_CHOICES)

    def __str__(self):
        return f"{self.user.email} - {self.note.title} ({self.access_type})"
