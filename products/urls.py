from django.urls import path, include
from django.views.generic import RedirectView
from .views import (ProductDetailView, add_to_cart,
                    remove_from_cart, remove_single_item_from_cart,
                    IndexView, CollectionSearch, CartSummaryView,
                    CheckoutView, StripPaymentView, ProductList, 
                    FlutterwavePaymentView, AddCouponView, remove_coupon, show_category, CategoriesView)

app_name = 'products'
urlpatterns = [
    path('', IndexView.as_view(), name="index"),
    path('products/', ProductList.as_view(), name="products-list"),
    path('products/<slug:slug>/',
         ProductDetailView.as_view(),
         name="single-product"),
    path('summary/', CartSummaryView.as_view(), name="cart-summary"),
    path('checkout/', CheckoutView.as_view(), name="checkout"),
    path('add-to-cart/<slug:slug>/', add_to_cart, name="add-to-cart"),
    path('add-coupon/', AddCouponView.as_view(), name="add-coupon"),
    path('remove-coupon/', remove_coupon, name="remove-coupon"),
    path('remove-from-cart/<slug:slug>/',
         remove_from_cart,
         name="remove-from-cart"),
    path('update-quantity-minus/<slug:slug>/',
         remove_single_item_from_cart,
         name="remove_single_item_from_cart"),
    path('update-quantity-plus/<slug:slug>/',
         add_to_cart,
         name="add_single_item_to_cart"),
    path('collections/<slug:slug>/', CollectionSearch.as_view(), name="collection"),
    path('categories/<slug:hierarchy>/', show_category, name="category"),
    path('categories/', CategoriesView.as_view(), name="categories"),
    path('payment/stripe/',
         StripPaymentView.as_view(),
         name="stripe"),
    path('payment/flutterwave/',
         FlutterwavePaymentView.as_view(),
         name="flutterwave"),

]
