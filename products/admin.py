from django.contrib import admin
from .models import Category, Item, OrderItem, Order, Payment, Coupon, LargeImage, Thumb_Image, Review

class OrderAdmin(admin.ModelAdmin):
    list_display = ['user', 
                    'ordered', 
                    'being_delivered', 
                    'received', 
                    'refund_requested', 
                    'refund_granted', 
                    'billing_address', 
                    'payment', 
                    'coupon']
    list_display_links = ['user', 'billing_address', 'payment', 'coupon']
    list_filter = ['ordered', 'being_delivered', 'received', 'refund_requested', 'refund_granted']

class LargeImagesCreateInline(admin.TabularInline):
    model = LargeImage
    extra = 4

class ThumbImagesCreateInline(admin.TabularInline):
    model = Thumb_Image
    extra = 4

class ItemAdmin(admin.ModelAdmin):
    inlines = [LargeImagesCreateInline, ThumbImagesCreateInline]

# Register your models here.
admin.site.register(Category)
admin.site.register(Item, ItemAdmin)
admin.site.register(Review)
admin.site.register(OrderItem)
admin.site.register(Order, OrderAdmin)
admin.site.register(Payment)
admin.site.register(Coupon)

