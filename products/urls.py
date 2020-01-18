from django.urls import path, include
from django.views.generic import RedirectView
from .views import (
    ProductsView, 
    ProductDetailView, 
    add_to_cart, 
    remove_from_cart,
    remove_single_item_from_cart,
    add_single_item_to_cart,
    IndexView,
    OrderSummaryView,
    CheckoutView,
    PaymentView,
    AddCouponView,
    remove_coupon)


app_name = 'products'
urlpatterns = [
    path('', RedirectView.as_view(url='products/'), name="index"),
    path('products/', ProductsView.as_view(), name="products-list" ),
    path('products/<slug:slug>/', ProductDetailView.as_view(), name="single-product"),
    path('summary/', OrderSummaryView.as_view(), name="order-summary"),
    path('checkout/', CheckoutView.as_view(), name="checkout"),
    path('payment/<slug:payment_option>/', PaymentView.as_view(), name="payment"),
    path('add-to-cart/<slug:slug>/', add_to_cart, name="add-to-cart"),
    path('add-coupon/', AddCouponView.as_view(), name="add-coupon"),
    path('remove-coupon/', remove_coupon, name="remove-coupon"),
    path('remove-from-cart/<slug:slug>/', remove_from_cart, name="remove-from-cart"),
    path('update-quantity-minus/<slug:slug>/', remove_single_item_from_cart, name="remove_single_item_from_cart"),
    path('update-quantity-plus/<slug:slug>/', add_single_item_to_cart, name="add_single_item_to_cart") 
]

