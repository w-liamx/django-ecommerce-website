from django.db import models
from django.shortcuts import reverse
from django.dispatch import receiver
from django.db.models.signals import pre_save, post_save
from django.conf import settings
from django_countries.fields import CountryField
from cstore.utils import unique_slug_generator
import numpy as np

# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class LargeImage(models.Model):
    item_instance = models.ForeignKey('Item', on_delete=models.CASCADE)
    large_image = models.ImageField(upload_to='images/large/', blank=True, null=True)

    def __str__(self):
        return self.item_instance.title

class Thumb_Image(models.Model):
    item_instance = models.ForeignKey('Item', on_delete=models.CASCADE)
    thumb_image = models.ImageField(upload_to='images/thumb/', blank=True, null=True)

    def __str__(self):
        return self.item_instance.title
    
AVALIABILITY_CHOICES = (
    ('1', 'IN STOCK'),
    ('0', 'OUT OF STOCK')
)

class Item(models.Model):
    slug = models.SlugField(blank=True)
    title = models.CharField(max_length=200)
    brand = models.CharField(max_length=50, blank=True, null=True)
    price = models.FloatField()
    discount = models.FloatField('Discount price', blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    description = models.TextField()
    avaliability = models.CharField(max_length=1, default='1', choices=AVALIABILITY_CHOICES)
    quantity_available = models.PositiveIntegerField()
    image = models.ImageField()
    

    def __str__(self):
        return self.title

    def get_avg_rating(self):
        all_ratings = list(map(lambda x: x.rating, self.review_set.all()))
        l = len(all_ratings)
        if l == 0:
            return np.mean([0.5, 0.5])
        return np.mean(all_ratings)

    def get_absolute_url(self):
        return reverse("products:single-product", kwargs={"slug": self.slug})

    def get_add_to_cart_url(self):
        return reverse("products:add-to-cart", kwargs={"slug": self.slug})
    
    def get_remove_from_cart_url(self):
        return reverse("products:remove-from-cart", kwargs={"slug": self.slug})

    def get_percentage_discount(self):
        if self.discount:
            return round(((self.price - self.discount) / self.price) * 100)

def pre_save_item(sender, instance, *args, **kwargs):
    if not instance.slug:
        instance.slug = unique_slug_generator(instance)


pre_save.connect(pre_save_item, sender=Item)    


class Review(models.Model):
    RATING_CHOICES = (
        (1, '1'),
        (2, '2'),
        (3, '3'),
        (4, '4'),
        (5, '5')
    )
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    user_name = models.CharField(max_length=10)
    customer_email = models.CharField(max_length=50)
    comment = models.CharField(max_length=1000)
    rating = models.IntegerField(choices=RATING_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return "%s | %s" %(self.item.title, self.user_name)


class OrderItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                            on_delete=models.CASCADE, blank=True, null=True)
    ordered = models.BooleanField(default=False)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    

    def __str__(self):
        return "%s of %s" %(self.quantity, self.item.title)

    def get_total_order_item_price(self):
        return self.quantity * self.item.price

    def get_total_order_item_discount_price(self):
        return self.quantity * self.item.discount

    def get_total_item_price(self):
        if self.item.discount:
            return self.get_total_order_item_discount_price()
        return self.get_total_order_item_price()



class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                            on_delete=models.CASCADE)
    items = models.ManyToManyField(OrderItem)
    start_date = models.DateTimeField(auto_now_add=True)
    ordered_date = models.DateTimeField()
    ordered = models.BooleanField(default=False)
    billing_address = models.ForeignKey('BillingAddress', 
        on_delete=models.SET_NULL, 
        blank=True, null=True)
    payment = models.ForeignKey('Payment', 
        on_delete=models.SET_NULL, 
        blank=True, null=True)
    coupon = models.ForeignKey('Coupon',
        on_delete=models.SET_NULL, 
        blank=True, null=True)
    being_delivered = models.BooleanField(default=False)
    received = models.BooleanField(default=False)
    refund_requested = models.BooleanField(default=False)
    refund_granted = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

    def get_total(self):
        total = 0
        for order_item in self.items.all():
            total += order_item.get_total_item_price()
        if self.coupon:
            total -= self.coupon.amount
        return total


class BillingAddress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                            on_delete=models.CASCADE)
    street_address = models.CharField(max_length=200)
    apartment_address = models.CharField(max_length=200)
    country = CountryField(multiple=False)
    zip_code = models.CharField(max_length=10)
    
    def __str__(self):
        return self.user.username

class Payment(models.Model):
    stripe_charge_id = models.CharField(max_length=50)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True)
    amount = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username

    
class Coupon(models.Model):
    code = models.CharField(max_length=15)
    amount = models.FloatField()

    def __str__(self):
        return self.code