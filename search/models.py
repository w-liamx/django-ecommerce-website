from django.db import models
from django.conf import settings

# Create your models here.
class SearchTerm(models.Model):
    query = models.CharField(max_length=100)
    search_date = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()
    tracking_id = models.CharField(max_length=50, default='')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.query