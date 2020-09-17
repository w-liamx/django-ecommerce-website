from django.contrib import admin
from .models import (Category, Item, CartItem, Cart, Order, Payment, Coupon,
                     ProductImage, Review, Variation, VarCategoryValues,
                     Collection, Brand, Address)


class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'ordered', 'being_delivered', 'received', 'refund_requested',
        'refund_granted', 'billing_address', 'shipping_address', 'payment'
    ]
    list_display_links = [
        'user', 'billing_address', 'shipping_address', 'payment'
    ]
    list_filter = [
        'ordered', 'being_delivered', 'received', 'refund_requested',
        'refund_granted'
    ]


class AddressAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'street_address', 'apartment_address', 'country', 'zip_code',
        'address_type', 'default_address'
    ]


class ProductImageCreateInline(admin.TabularInline):
    model = ProductImage
    extra = 1


class ItemAdmin(admin.ModelAdmin):
    inlines = [ProductImageCreateInline]


# Register your models here.
admin.site.register(Category)
admin.site.register(Collection)
admin.site.register(Brand)
admin.site.register(Item, ItemAdmin)
admin.site.register(Variation)
admin.site.register(VarCategoryValues)
admin.site.register(Review)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Order, OrderAdmin)
admin.site.register(Payment)
admin.site.register(Coupon)
admin.site.register(Address, AddressAdmin)
