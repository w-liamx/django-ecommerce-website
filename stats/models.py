from django.db import models
from django.conf import settings
from products.models import Item

# Create your models here.
class PageView(models.Model):
    class Meta:
        abstract = True

    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE,
                             blank=True,
                             null=True)
    date = models.DateTimeField(auto_now=True)
    ip_address = models.GenericIPAddressField()
    tracking_id = models.CharField(max_length=100, default='')

class ItemView(PageView):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)