from django.db import models

class FamousPerson(models.Model):
    name = models.CharField(max_length=255)

class Storage(models.Model):
    file = models.FileField(upload_to="media")

    def get_file_url(self):
        return self.file.url
