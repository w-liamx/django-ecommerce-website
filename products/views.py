from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import View, ListView, DetailView
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from .models import Item, OrderItem, Order, Payment, BillingAddress, Coupon, Review
from .forms import CheckoutForm, CouponForm, ReviewForm
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

import stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

# Create your views here.
# def products(request):
#     items = Item.objects.all()
#     order = Order.objects.get(user=self.request.user, ordered=False)

#     context = {
#         "items": items,
#         "object": order
#     }
#     return render(request, "products/products.html", context)

class ProductsView(ListView):
    model = Item
    paginate_by = 12
    template_name  = "products/products.html"

class IndexView(View):
    pass

class OrderSummaryView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)

            context = {
                'object': order,
                'couponform':CouponForm()
            }
            return render(self.request, 'products/cart.html', context)
        except ObjectDoesNotExist:
            messages.warning(self.request, "You have not ordered anything yet")
            return redirect ("/products")

class ProductDetailView(View):
    def get(self, request, slug, *args, **kwargs):
        item = Item.objects.get(slug=slug)
        form = ReviewForm()   
        reviews = item.review_set.all()
        paginator = Paginator(reviews, 5)

        page = request.GET.get('page')
        try:
            reviews = paginator.page(page)
        except PageNotAnInteger:
            reviews = paginator.page(1)
        except EmptyPage:
            reviews = paginator.page(paginator.num_pages)

        context = {
            'item': item,
            'object': item,
            'form': form,
            'reviews': reviews
        }
        return render(self.request, "products/product-page.html", context)

    def post(self, request, slug, *args, **kwargs):
        form = ReviewForm(self.request.POST or None)
        if form.is_valid():
            user_name = form.cleaned_data.get('user_name')
            customer_email = form.cleaned_data.get('customer_email')
            comment = form.cleaned_data.get('comment')
            rating = form.cleaned_data.get('rating')
            
            review = Review(
                item = get_object_or_404(Item, slug=slug),
                user_name = user_name,
                customer_email = customer_email,
                comment = comment,
                rating = rating,
                created_at = timezone.now()    
            )

            review.save()
            messages.success(self.request, "Thanks for the feedback!!")
            return redirect("products:single-product", slug=slug)
        messages.warning(self.request, 'Your feedback was not submitted, please fill the form and try again.')
        return redirect('products:single-product', slug=slug)
        
        context = {
            'form': form
        }
        return render(self.request, "products/product-page.html", context)


class CheckoutView(View):
    def get(self, *args, **kwargs):
        form = CheckoutForm()
        context = {
            'form': form
        }

        return render(self.request, "products/checkout.html", context)

    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            if form.is_valid():
                street_address = form.cleaned_data.get('street_address')
                apartment_address = form.cleaned_data.get('apartment_address')
                country = form.cleaned_data.get('country')
                zip_code = form.cleaned_data.get('zip_code')
                # same_billing_address = form.cleaned_data.get('same_billing_address')
                # save_info = form.cleaned_data.get('save_info')
                payment_option = form.cleaned_data.get('payment_option')
                billing_address = BillingAddress(
                    user=self.request.user,
                    street_address=street_address,
                    apartment_address=apartment_address,
                    country=country,
                    zip_code=zip_code
                )
                billing_address.save()
                order.billing_address = billing_address
                order.save()

                if payment_option == 'S':
                    return redirect('products:payment', payment_option='stripe')
                elif payment_option == 'P':
                    return redirect('products:payment', payment_option='paypal')
                else:
                    messages.warning(self.request, "Invalid payment option")
                    return redirect('products:checkout')
            messages.warning(self.request, 'Failed to checkout, please try again. If the issue persists, please contact customer care.')
            return redirect('products:checkout')
        except ObjectDoesNotExist:
            messages.warning(self.request, "You have not ordered anything yet")
            return redirect ("/products")   

class PaymentView(View):
    def get(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        if order.billing_address:
            context = {
                'order': order 
            }
            return render(self.request, 'products/payment.html', context)
        messages.warning(self.request, "You have not added a billing address")
        return redirect ('products:checkout') 
    
    def post(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        token = self.request.POST.get('stripeToken')
        amount = int(order.get_total() * 100) #cents
        try:
            charge = stripe.Charge.create(
                ammount=amount, 
                currency="usd",
                source=token
            )

            payment = Payment()
            payment.stripe_charge_id = charge['id']
            payment.user = self.request.user
            payment.amount = order.get_total()
            payment.save()

            #assign payment to order
            order_items = order.items.all()
            order_items.update(ordered=True)
            for item in order_items:
                item.save()

            order.ordered = True
            order.payment = payment
            order.save()

            messages.success(self.request, "Your order was successful.  ")
            return redirect("/products")

        except stripe.error.CardError as e:
            # Since it's a decline, stripe.error.CardError will be caught
            body = e.json_body
            err = body.get('error', {})
            messages.warning(self.request,"%s" %(err.get('message')))
            return redirect("/products")

        except stripe.error.RateLimitError as e:
            # Too many requests made to the API too quickly
            messages.warning(self.request,"Rate limit error")
            return redirect("/products")

        except stripe.error.InvalidRequestError as e:
            # Invalid parameters were supplied to Stripe's API
            messages.warning(self.request,"Invalid parameters")
            return redirect("/products")

        except stripe.error.AuthenticationError as e:
            # Authentication with Stripe's API failed
            # (maybe you changed API keys recently)
            messages.warning(self.request,"Not authenticated")
            return redirect("/products")

        except stripe.error.APIConnectionError as e:
            # Network communication with Stripe failed
            messages.warning(self.request,"Network error")
            return redirect("/products")

        except stripe.error.StripeError as e:
            # Display a very generic error to the user, and maybe send
            # yourself an email
            messages.warning(self.request,"Something went wrong. Don't worry, you were not charged. Please try again.")
            return redirect("/products")

        except Exception as e:
            # Something else happened, completely unrelated to Stripe
            #send email to admin
            messages.warning(self.request,"A serious error occured. We have been notified")
            return redirect("/products")



@login_required
def add_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_item, created = OrderItem.objects.get_or_create(item=item, user=request.user, ordered=False)
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__slug=item.slug):
            order_item.quantity += 1
            order_item.save()
            messages.info(request, "Quantity updated")

        else:
            messages.info(request, "Item added to cart")
            order.items.add(order_item)
    else:
        ordered_date = timezone.now()
        order = Order.objects.create(user=request.user, ordered_date=ordered_date)
        order.items.add(order_item)
        messages.info(request, "Item added to cart")


    return redirect("products:products-list")

@login_required
def remove_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(item=item, user=request.user, ordered=False)[0]
            order.items.remove(order_item)
            messages.info(request, "Item removed from cart")

            return redirect("products:order-summary")
        else:
            messages.info(request, "Item not found in cart")

            return redirect("products:single-product", slug=slug)
    else:
        messages.info(request, "You do not have an active order")

        return redirect("products:single-product", slug=slug)

@login_required
def remove_single_item_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(item=item, user=request.user, ordered=False)[0]
            if order_item.quantity > 1:
                order_item.quantity -= 1
            else:
                order.items.remove(order_item)
            order_item.save()
            messages.info(request, "Quantity updated")
            return redirect("products:order-summary")
        else:
            messages.info(request, "Item not found in cart")

            return redirect("products:single-product", slug=slug)
    else:
        messages.info(request, "You do not have an active order")

        return redirect("products:single-product", slug=slug)

@login_required
def add_single_item_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(item=item, user=request.user, ordered=False)[0]
            order_item.quantity += 1
            order_item.save()
            messages.info(request, "Quantity updated")
            return redirect("products:order-summary")
        else:
            messages.info(request, "Item not found in cart")

            return redirect("products:single-product", slug=slug)
    else:
        messages.info(request, "You do not have an active order")

        return redirect("products:products-list")
    

def get_coupon(request, code):
    try:
        coupon = Coupon.objects.get(code=code)
        return coupon
    except ObjectDoesNotExist:
        messages.info(request, "Coupon does not exist")
        return redirect("products:order-summary")

class AddCouponView(View):
    def post(self, *args, **kwargs):
        form = CouponForm(self.request.POST or None)
        if form.is_valid():
            try:
                code = form.cleaned_data.get('code')
                order = Order.objects.get(user=self.request.user, ordered=False)
                order.coupon = get_coupon(self.request, code)
                order.save()
                messages.success(self.request, "Coupon added")
                return redirect("products:order-summary")
            except ObjectDoesNotExist:
                messages.info(self.request, "You do not have an active order")
                return redirect("products:order-summary")
        messages.warning(self.request, "Invalid Coupon")
        return redirect("products:order-summary")
        