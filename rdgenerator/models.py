from django.db import models
from django.utils import timezone

class GithubRun(models.Model):
    id = models.AutoField(primary_key=True)
    uuid = models.CharField(verbose_name="uuid", max_length=100, unique=True)
    status = models.CharField(verbose_name="status", max_length=200)
    email = models.EmailField(verbose_name="email", max_length=254, blank=True, null=True)
    platform = models.CharField(verbose_name="platform", max_length=50, blank=True, null=True)
    filename = models.CharField(verbose_name="filename", max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.platform} - {self.filename} ({self.status})"


class SavedConfiguration(models.Model):
    """Stores saved rdgen configurations for reuse"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    config_json = models.TextField()  # Store form data as JSON
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name
