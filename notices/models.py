from django.db import models

class Notice(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    original_link = models.CharField(max_length=255)
    date_posted = models.DateField()
    time_posted = models.TimeField()
    source_school = models.CharField(max_length=255)