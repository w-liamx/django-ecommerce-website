from django.db import models
from django.shortcuts import reverse
from django.dispatch import receiver
from django.db.models.signals import pre_save, post_save
from django.conf import settings
from django_countries.fields import CountryField
from cstore.utils import unique_slug_generator, store_url_slug_generator
import numpy as np
from django.contrib.auth import login
from django.contrib.auth.signals import user_logged_in
from django.utils import timezone
from django.contrib import messages
from django.shortcuts import get_object_or_404
import uuid

# class CategoryQueryset(models.query.QuerySet):
#     def active(self):
#         return self.filter(active=True)

#     def featured(self):
#         return self.filter(featured=True)\
#             .filter(featured_start_date_lt=timezone.now())\
#             .filter(featured_end_date_gte=timezone.now())
        
#     def add_to_carousel(self):
#         return self.filter(add_to_carousel=True)

class CategoryManager(models.Manager):
    # def get_queryset(self):
    #     return CollectionQueryset(self.model, using=self._db)

    def parent(self):
        return self.filter(parent=None)


class Category(models.Model):
    slug = models.SlugField(blank=True)
    title = models.CharField(max_length=50)
    show_in_homepage = models.BooleanField(default=False)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, related_name='children')

    objects = CategoryManager()

    class Meta:
        verbose_name_plural = "categories"


    def __str__(self):
        full_path = [self.title]
        k = self.parent
        while k is not None:
            full_path.append(k.title)
            k = k.parent
        return ' > '.join(full_path[::-1])


class LargeImage(models.Model):
    item_instance = models.ForeignKey('Item', on_delete=models.CASCADE)
    large_image = models.ImageField(upload_to='images/large/',
                                    blank=True,
                                    null=True)

    def __str__(self):
        return self.item_instance.title


class Thumb_Image(models.Model):
    item_instance = models.ForeignKey('Item', on_delete=models.CASCADE)
    thumb_image = models.ImageField(upload_to='images/thumb/',
                                    blank=True,
                                    null=True)

    def __str__(self):
        return self.item_instance.title


AVALIABILITY_CHOICES = (('1', 'IN STOCK'), ('0', 'OUT OF STOCK'))
    

class VarCategoryValues(models.Model):
    name = models.CharField(max_length=50)
    frontend_value = models.CharField(max_length=50, blank=True, null=True)
    image = models.ImageField(upload_to='images/variations/', blank=True, null=True)
    price = models.FloatField('Variation price', blank=True, null=True)
    active = models.BooleanField(default=True)
    updated = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
class Variation(models.Model):
    name = models.CharField(max_length=50)
    values = models.ManyToManyField(VarCategoryValues)
    active = models.BooleanField(default=True)
    updated = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Brand(models.Model):
    slug = models.SlugField(blank=True)
    title = models.CharField('Name', max_length=50)
    category = models.CharField(max_length=50)
    address = models.CharField(max_length=100, blank=False, null=False)
    logo = models.ImageField()
    website = models.CharField(max_length=50)

    def __str__(self):
        return self.title
       


class Item(models.Model):
    slug = models.SlugField(blank=True)
    title = models.CharField(max_length=100)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, blank=True, null=True)
    price = models.FloatField()
    discount = models.FloatField('Discount price', blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    collections = models.ManyToManyField('Collection')
    description = models.TextField()
    avaliability = models.CharField(max_length=1,
                                    default='1',
                                    choices=AVALIABILITY_CHOICES)
    quantity_available = models.PositiveIntegerField()
    image = models.ImageField()
    variations = models.ManyToManyField(Variation, blank=True)

    def __str__(self):
        return self.title

    def get_cat_list(self):
        k = self.category
        breadcrumb = ["dummy"]
        while k is not None:
            breadcrumb.append(k.slug)
            k = k.parent
        for i in range(len(breadcrumb)-1):
            breadcrumb[i] = '/'.join(breadcrumb[-1:i-1:-1])
        return breadcrumb[-1:0:-1]

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

class CollectionQueryset(models.query.QuerySet):
    def active(self):
        return self.filter(active=True)

    def featured(self):
        return self.filter(featured=True)\
            .filter(featured_start_date_lt=timezone.now())\
            .filter(featured_end_date_gte=timezone.now())
        
    def add_to_carousel(self):
        return self.filter(add_to_carousel=True)

class CollectionManager(models.Manager):
    def get_queryset(self):
        return CollectionQueryset(self.model, using=self._db)

    def collections(self):
        return self.get_queryset().active().filter(add_to_carousel=False)

    def promos(self):
        return self.get_queryset().active().filter(is_promo=True)[:2]

    def all(self):
        return self.get_queryset().active()

    def featured(self):
        return self.get_queryset().active().featured()
    
    def carousels(self):
        return self.get_queryset().active().add_to_carousel()


TEXT_COLOR_CHOICES = (
    ('primary-color', 'Theme-color'),
    ('white-color', 'white-color'),
    ('black-color', 'black-color')
)
POSITION_CHOICES  = (
    ('text-center', 'text-center'),
    ('left', 'left')
)
    

class Collection(models.Model):
    slug = models.SlugField(blank=True)
    title = models.CharField(max_length=30)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, blank=True, null=True)
    header_text = models.CharField(max_length=100)
    header_text_color = models.CharField(max_length=20, default='primary-color', choices=TEXT_COLOR_CHOICES)
    brief_description = models.TextField(max_length=500)
    text_position = models.CharField(max_length=20, default='text-center', choices=POSITION_CHOICES) 
    image = models.ImageField()
    large_image = models.BooleanField(default=False)
    featured = models.BooleanField(default=False)
    featured_start_date = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    featured_end_date = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    active = models.BooleanField(default=False)
    add_to_carousel = models.BooleanField(default=False)
    is_promo = models.BooleanField(default=False)
    countdown_start_date = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    countdown_end_date = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)

    objects = CollectionManager()

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("products:collection", kwargs={"slug": self.slug})


class Review(models.Model):
    RATING_CHOICES = ((1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5'))
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    user_name = models.CharField(max_length=10)
    customer_email = models.CharField(max_length=50)
    comment = models.CharField(max_length=1000)
    rating = models.IntegerField(choices=RATING_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return "%s | %s" % (self.item.title, self.user_name)

class CartItemManager(models.Manager):
    def get_or_new(self, request, slug):
        cart_item_id = request.session.get("cart_item_id", None)
        item = get_object_or_404(Item, slug=slug)
        qs = self.get_queryset().filter(id=cart_item_id)
        if qs.exists():
            created = False
            cart_item = qs[0]
            if request.user.is_authenticated and cart_item.user is None:
                user = request.user
                cart_item.user = user
                cart_item.ordered = False
                cart_qs = Cart.objects.filter(user=user, ordered=False)
                if cart_qs.exists():
                    cart = cart_qs[0]
                    if cart.items.filter(item__slug=item.slug):
                        cart_item.quantity += 1
                        cart_item.save()
                        messages.info(request, "Quantity updated")
                    else:
                        messages.info(request, "Item added to cart")
                        cart.items.add(cart_item)
                else:
                    cart = Cart.objects.create(user=user, ordered=False)
                    cart.items.add(cart_item)
                    messages.info(request, "Item added to cart")
        else:
            cart_item = CartItem.objects.new(user=request.user, slug=item.slug)
            created = True
            request.session['cart_item_id'] = cart_item.id
        return cart_item, created

    def new(self, user=None, slug=None):
        user_obj = None
        item = get_object_or_404(Item, slug=slug)
        if user is not None:
            if user.is_authenticated:
                user_obj = user
        return self.model.objects.create(user=user_obj, item=item)


class CartItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE,
                             blank=True,
                             null=True)
    unique_id = models.UUIDField(auto_created=True, default=uuid.uuid4, blank=True)
    ordered = models.BooleanField(default=False)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

    objects = CartItemManager()

    def __str__(self):
        return "%s of %s" % (self.quantity, self.item.title)

    def get_total_order_item_price(self):
        total = self.quantity * self.item.price
        return round(total, 2)

    def get_total_order_item_discount_price(self):
        total = self.quantity * self.item.discount
        return round(total, 2)

    def get_total_item_price(self):
        if self.item.discount:
            return round(self.get_total_order_item_discount_price(), 2)
        return round(self.get_total_order_item_price(), 2)


class Cart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE, blank=True, null=True)
    items = models.ManyToManyField(CartItem)
    start_date = models.DateTimeField(auto_now_add=True)
    ordered = models.BooleanField(default=False)
    coupon = models.ForeignKey('Coupon',
                               on_delete=models.SET_NULL,
                               blank=True,
                               null=True)

    def __str__(self):
        return str(self.id)

    def get_total(self):
        total = 0
        for order_item in self.items.all():
            total += order_item.get_total_item_price()
        if self.coupon:
            total -= self.coupon.amount
        return round(total, 2)

class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    items = models.OneToOneField(Cart, on_delete=models.CASCADE)
    start_date = models.DateTimeField(auto_now_add=True)
    ordered_date = models.DateTimeField()
    ordered = models.BooleanField(default=False)
    billing_address = models.ForeignKey('Address',
                                        on_delete=models.SET_NULL,
                                        related_name='billing_address',
                                        blank=True,
                                        null=True)
    shipping_address = models.ForeignKey('Address',
                                        on_delete=models.SET_NULL,
                                        related_name='shipping_address',
                                        blank=True,
                                        null=True)
    payment = models.ForeignKey('Payment',
                                on_delete=models.SET_NULL,
                                blank=True,
                                null=True)
    being_delivered = models.BooleanField(default=False)
    received = models.BooleanField(default=False)
    refund_requested = models.BooleanField(default=False)
    refund_granted = models.BooleanField(default=False)

    def __str__(self):
        return str(self.id)

ADDRESS_CHOICES = (
    ('B', 'Billing'),
    ('S', 'Shipping'),
)
class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    street_address = models.CharField(max_length=200)
    apartment_address = models.CharField(max_length=200)
    country = CountryField(multiple=False)
    zip_code = models.CharField(max_length=10)
    address_type = models.CharField(max_length=1, choices=ADDRESS_CHOICES)
    default_address = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username


class Payment(models.Model):
    stripe_charge_id = models.CharField(max_length=50)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.SET_NULL,
                             blank=True,
                             null=True)
    amount = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username


class Coupon(models.Model):
    code = models.CharField(max_length=15)
    amount = models.FloatField()

    def __str__(self):
        return self.code

def pre_save_item(sender, instance, *args, **kwargs):
    if not instance.slug:
        instance.slug = unique_slug_generator(instance)

def pre_save_slug(sender, instance, *args, **kwargs):
    if not instance.slug:
        instance.slug = store_url_slug_generator(instance)

pre_save.connect(pre_save_slug, sender=Collection)
pre_save.connect(pre_save_slug, sender=Brand)
pre_save.connect(pre_save_slug, sender=Category)
pre_save.connect(pre_save_item, sender=Item)



def attach_cart(sender, **kwargs):
    user = kwargs.get('user')
    user.backend = 'django.contrib.auth.backends.ModelBackend'
    session = kwargs.get('request').session
    cart_id = session.get('cart_id')
    if cart_id:
        '''
        A user may have old items left in his cart from last login.
        Therefore, we check if the user has added items from an anonymous window. 
        If True, we check for dupicate items that may have appeared in both the user's old cart and 
        new cart using the items' slugs. If they exist, we keep one.
        We add the items from the new cart to the old one, assign the logged in user to each of them
        and then delete the order he created when the user was anonymous.
        If 
        '''
        cart = None
        try:
            old_cart = Cart.objects.get(user=user)
            new_cart = Cart.objects.get(id=cart_id)
            # We check if there was an old cart.
            # If there is, we iterate through the items in the cart to know if the user has added a clone of an old item in the new cart
            if old_cart:
                for item in new_cart.items.all():
                    if old_cart.items.all().filter(item__slug=item.item.slug).exists(): #If the item exists, we delete that item from the new cart else we add it to the old cart.
                        item.delete()
                    else:
                        item.user_id = user.id
                        item.save()
                        old_cart.items.add(item)
                cart = old_cart
                new_cart.delete() # we delete the cart that was created with session after adding new items to user's cart             
            else:
                new_cart.user_id = user.id
                new_cart.save()
                cart = new_cart
        except Cart.DoesNotExist:
            cart = Cart.objects.get(id=cart_id)
        cart.user_id = user.id
        cart.save()


user_logged_in.connect(attach_cart)