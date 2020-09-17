from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import View, ListView, DetailView
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from .models import Item, CartItem, Cart, Payment, Address, Coupon, Review, Order, Collection, Category
from search.models import SearchTerm
from .forms import CheckoutForm, CouponForm, ReviewForm
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import uuid
from stats import stats
from search.filter import ProductsSearch, SortForm
from django.db.models import Q

import stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


def is_valid_form(values):
    valid = True
    for field in values:
        if field == '':
            valid = False
    return valid


def show_category(request, hierarchy=None):
    category_slug = hierarchy.split('/')
    category_queryset = list(Category.objects.all())
    all_slugs = [x.slug for x in category_queryset]
    parent = None
    for slug in category_slug:
        if slug in all_slugs:
            parent = get_object_or_404(Category, slug=slug, parent=parent)
        else:
            instance = get_object_or_404(Item, slug=slug)
            breadcrumbs_link = instance.get_cat_list()
            category_name = [
                ' '.join(i.split('/')[-1].split('-')) for i in breadcrumbs_link
            ]
            breadcrumbs = zip(breadcrumbs_link, category_name)
            return render(request, "products/product-page.html", {
                'instance': instance,
                'breadcrumbs': breadcrumbs
            })
        return render(
            request, "products/categories.html", {
                "item_set": parent.item_set.all(),
                'sub_categories': parent.children.all()
            })


class ProductList(View):
    def get(self, request, *args, **kwargs):
        sortForm = SortForm(request.GET or None)
        value = request.GET.get('query', '')
        sort_by = request.GET.get('sort_by', '')
        # store search query in the database
        if len(value) > 2:
            term = SearchTerm()
            term.query = value
            term.ip_address = request.META.get('REMOTE_ADDR')
            term.tracking_id = stats.tracking_id(request)
            term.user = None
            if request.user.is_authenticated:
                term.user = request.user
            term.save()
        products = ProductsSearch(request.GET or None,
                                  queryset=Item.objects.all())
        if sort_by:
            results_qs = products.qs.order_by(sort_by)
        else:
            results_qs = products.qs.order_by('price')
        print(request.get_full_path)
        paginator = Paginator(results_qs, 1)

        page = request.GET.get('page')
        try:
            results = paginator.page(page)
        except PageNotAnInteger:
            results = paginator.page(1)
        except EmptyPage:
            results = paginator.page(paginator.num_pages)

        context = {
            'object_list': products,
            'sortform': sortForm,
            'page': page,
            'results': results
        }
        return render(request, "products/products.html", context)


class CategoriesView(ListView):
    model = Category
    template_name = "products/all_categories_view.html"


class IndexView(View):
    def get(self, request, *args, **kwargs):
        search_recommendations = stats.recommended_from_search(self.request)
        latest = Item.objects.all()[:5]
        carousels = Collection.objects.carousels()[:5]
        collections = Collection.objects.collections()[:2]
        promos = Collection.objects.promos()[:10]
        recently_viewed = stats.get_recently_viewed(self.request)[:6]
        context = {
            "carousels": carousels,
            "collections": collections,
            "promos": promos,
            "latest": latest,
            "recently_viewed": recently_viewed,
            "search_recommendations": search_recommendations
        }
        return render(self.request, "products/index.html", context)


class CollectionSearch(View):
    def get(self, request, slug):
        collection = get_object_or_404(Collection, slug=slug)
        products = ProductsSearch(
            request.GET, queryset=collection.item_set.all())

        context = {"object_list": products}
        return render(self.request, "products/search-results.html", context)


class CartSummaryView(View):
    def get(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            try:
                cart = Cart.objects.get(user=self.request.user, ordered=False)

                context = {'object': cart, 'couponform': CouponForm()}
                return render(self.request, 'products/cart.html', context)
            except ObjectDoesNotExist:
                messages.warning(
                    self.request,
                    "Your cart is empty. Please add some items to your cart.")
                return redirect("/products")
        else:
            try:
                cart_id = self.request.session.get("cart_id")
                cart = Cart.objects.get(id=cart_id, ordered=False)

                context = {'object': cart}
                return render(self.request, 'products/cart.html', context)
            except ObjectDoesNotExist:
                messages.warning(
                    self.request,
                    "Your cart is empty. Please add some items to your cart.")
                return redirect("/products")


class ProductDetailView(View):
    def get(self, request, slug, *args, **kwargs):
        from stats import stats
        item = Item.objects.get(slug=slug)
        stats.log_item_view(self.request, item)
        form = ReviewForm()
        reviews = item.review_set.all()
        related_products = Item.objects.filter(
            Q(category=item.category)
            | Q(collections__in=item.collections.all())).distinct().exclude(
                slug=item.slug)
        paginator = Paginator(reviews, 1)

        page = request.GET.get('page')
        try:
            reviews = paginator.page(page)
        except PageNotAnInteger:
            reviews = paginator.page(1)
        except EmptyPage:
            reviews = paginator.page(paginator.num_pages)

        breadcrumbs_link = item.get_cat_list()
        category_name = [
            ' '.join(i.split('/')[-1].split('-')) for i in breadcrumbs_link
        ]
        breadcrumbs = zip(breadcrumbs_link, category_name)

        context = {
            'item': item,
            'object': item,
            'form': form,
            'reviews': reviews,
            'breadcrumbs': breadcrumbs,
            'related_products': related_products
        }
        return render(self.request, "products/product-page.html", context)

    def post(self, request, slug, *args, **kwargs):
        form = ReviewForm(self.request.POST or None)
        if form.is_valid():
            user_name = form.cleaned_data.get('user_name')
            customer_email = form.cleaned_data.get('customer_email')
            comment = form.cleaned_data.get('comment')
            rating = form.cleaned_data.get('rating')

            review = Review(item=get_object_or_404(Item, slug=slug),
                            user_name=user_name,
                            customer_email=customer_email,
                            comment=comment,
                            rating=rating,
                            created_at=timezone.now())

            review.save()
            messages.success(self.request, "Thanks for the feedback!!")
            return redirect("products:single-product", slug=slug)
        messages.warning(
            self.request,
            'Your feedback was not submitted, please fill the form and try again.'
        )
        return redirect('products:single-product', slug=slug)

        context = {'form': form}
        return render(self.request, "products/product-page.html", context)


class CheckoutView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        form = CheckoutForm()
        cart_qs = Cart.objects.filter(user=self.request.user, ordered=False)
        if cart_qs.exists():
            cart = cart_qs[0]
            order_qs = Order.objects.filter(user=self.request.user,
                                            items=cart,
                                            ordered=False)
            ordered_date = timezone.now()
            if order_qs.exists():
                order = order_qs[0]
                order.ordered_date = ordered_date
                order.save()
            else:
                order = Order.objects.create(user=self.request.user,
                                             items=cart,
                                             ordered=False,
                                             ordered_date=ordered_date)
                order.save()
        else:
            messages.warning(self.request, "You do not have an active order")
            return redirect("/products")
        context = {'form': form}

        shipping_address_qs = Address.objects.filter(user=self.request.user,
                                                     address_type='S',
                                                     default_address=True)

        if shipping_address_qs.exists():
            context.update(
                {'default_shipping_address': shipping_address_qs[0]})

        billing_address_qs = Address.objects.filter(user=self.request.user,
                                                    address_type='B',
                                                    default_address=True)

        if billing_address_qs.exists():
            context.update({'default_billing_address': billing_address_qs[0]})

        return render(self.request, "products/checkout.html", context)

    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            if form.is_valid():
                use_default_billing = form.cleaned_data.get(
                    'use_default_billing')
                if use_default_billing:
                    address_qs = Address.objects.filter(user=self.request.user,
                                                        address_type='B',
                                                        default_address=True)
                    if address_qs.exists():
                        billing_address = address_qs[0]
                        order.billing_address = billing_address
                        order.save()
                    else:
                        messages.info(
                            self.request,
                            'No address available. Please create one')
                        return redirect('products:checkout')
                else:
                    billing_street_address = form.cleaned_data.get(
                        'billing_street_address')
                    billing_apartment_address = form.cleaned_data.get(
                        'billing_apartment_address')
                    billing_country = form.cleaned_data.get('billing_country')
                    billing_zip_code = form.cleaned_data.get(
                        'billing_zip_code')

                    if is_valid_form([
                            billing_street_address, billing_country,
                            billing_zip_code
                    ]):

                        billing_address = Address(
                            user=self.request.user,
                            street_address=billing_street_address,
                            apartment_address=billing_apartment_address,
                            country=billing_country,
                            zip_code=billing_zip_code,
                            address_type='B')
                        billing_address.save()
                        order.billing_address = billing_address
                        order.save()

                        set_default_billing = form.cleaned_data.get(
                            'set_default_billing')
                        if set_default_billing:
                            billing_address.default_address = True
                            billing_address.save()
                    else:
                        messages.warning(
                            self.request,
                            "Please, enter a valid Billing address...")
                        return redirect('products:checkout')

                use_default_shipping = form.cleaned_data.get(
                    'use_default_shipping')
                same_billing_address = form.cleaned_data.get(
                    'same_billing_address')

                if same_billing_address:
                    shipping_address = billing_address
                    shipping_address.pk = None
                    shipping_address.save()
                    shipping_address.address_type = 'S'
                    shipping_address.save()
                    order.shipping_address = shipping_address
                    order.save()

                elif use_default_shipping:
                    address_qs = Address.objects.filter(user=self.request.user,
                                                        address_type='S',
                                                        default_address=True)
                    if address_qs.exists():
                        shipping_address = address_qs[0]
                        order.shipping_address = shipping_address
                        order.save()
                    else:
                        messages.info(
                            self.request,
                            'No address available. Please create one')
                        return redirect('products:checkout')
                else:
                    shipping_street_address = form.cleaned_data.get(
                        'shipping_street_address')
                    shipping_apartment_address = form.cleaned_data.get(
                        'shipping_apartment_address')
                    shipping_country = form.cleaned_data.get(
                        'shipping_country')
                    shipping_zip_code = form.cleaned_data.get(
                        'shipping_zip_code')

                    if is_valid_form([
                            shipping_street_address, shipping_country,
                            shipping_zip_code
                    ]):

                        shipping_address = Address(
                            user=self.request.user,
                            street_address=shipping_street_address,
                            apartment_address=shipping_apartment_address,
                            country=shipping_country,
                            zip_code=shipping_zip_code,
                            address_type='S')
                        shipping_address.save()
                        order.shipping_address = shipping_address
                        order.save()

                        set_default_shipping = form.cleaned_data.get(
                            'set_default_shipping')
                        if set_default_shipping:
                            shipping_address.default_address = True
                            shipping_address.save()
                    else:
                        messages.warning(
                            self.request,
                            "Please, enter a valid Shipping address...")
                        return redirect('products:checkout')

                payment_option = form.cleaned_data.get('payment_option')

                if payment_option == 'S':
                    return redirect('products:stripe')
                elif payment_option == 'F':
                    return redirect('products:flutterwave')
                else:
                    messages.warning(self.request, "Invalid payment option")
                    return redirect('products:checkout')
            messages.warning(
                self.request,
                'Failed to checkout, please try again. If the issue persists, please contact customer care.'
            )
            return redirect('products:checkout')
        except ObjectDoesNotExist:
            messages.warning(
                self.request,
                "Your cart is empty. Please add some items to your cart.")
            return redirect("/products")


class StripPaymentView(View):
    def get(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        if order.billing_address:
            context = {'order': order}
            return render(self.request, 'products/stripe-payment.html',
                          context)
        messages.warning(self.request, "You have not added a billing address")
        return redirect('products:checkout')

    def post(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        # token = self.request.POST.get('stripeToken')
        token = "tok_visa"
        amount = int(order.items.get_total() * 100)  # cents
        try:
            charge = stripe.Charge.create(amount=amount,
                                          currency="usd",
                                          source=token)

            payment = Payment()
            payment.stripe_charge_id = charge['id']
            payment.user = self.request.user
            payment.amount = order.items.get_total()
            payment.save()

            # assign payment to order
            order_items = order.items.items.all()
            order_items.update(ordered=True)
            for item in order_items:
                item.save()

            order.items.ordered = True
            order.items.save()
            order.ordered = True
            order.payment = payment
            order.save()

            messages.success(self.request, "Your order was successful.  ")
            return redirect("/products")

        except stripe.error.CardError as e:
            # Since it's a decline, stripe.error.CardError will be caught
            body = e.json_body
            err = body.get('error', {})
            messages.warning(self.request, "%s" % (err.get('message')))
            return redirect("/products")

        except stripe.error.RateLimitError as e:
            # Too many requests made to the API too quickly
            messages.warning(self.request, "Rate limit error")
            return redirect("/products")

        except stripe.error.InvalidRequestError as e:
            # Invalid parameters were supplied to Stripe's API
            messages.warning(self.request, "Invalid parameters")
            return redirect("/products")

        except stripe.error.AuthenticationError as e:
            # Authentication with Stripe's API failed
            # (maybe you changed API keys recently)
            messages.warning(self.request, "Not authenticated")
            return redirect("/products")

        except stripe.error.APIConnectionError as e:
            # Network communication with Stripe failed
            messages.warning(self.request, "Network error")
            return redirect("/products")

        except stripe.error.StripeError as e:
            # Display a very generic error to the user, and maybe send
            # yourself an email
            messages.warning(
                self.request,
                "Something went wrong. Don't worry, you were not charged. Please try again."
            )
            return redirect("/products")

        except Exception as e:
            # Something else happened, completely unrelated to Stripe
            # send email to admin
            messages.warning(self.request,
                             "A serious error occured. We have been notified")
            return redirect("/products")


class FlutterwavePaymentView(View):
    def get(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        if order.billing_address:
            context = {'order': order}
            return render(self.request, 'products/flutterwave-payment.html',
                          context)
        messages.warning(self.request, "You have not added a billing address")
        return redirect('products:checkout')


def add_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    if request.user.is_authenticated:
        cart_item, created = CartItem.objects.get_or_create(item=item,
                                                            user=request.user,
                                                            ordered=False)
        cart_qs = Cart.objects.filter(user=request.user, ordered=False)
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
            cart = Cart.objects.create(user=request.user, ordered=False)
            cart.items.add(cart_item)
            messages.info(request, "Item added to cart")
    else:
        cart_item_id = request.session.get("cart_item_id", None)
        cart_id = request.session.get("cart_id", None)
        cart_item = CartItem.objects.all().filter(id=cart_item_id,
                                                  ordered=False)
        qs = Cart.objects.filter(id=cart_id, ordered=False)
        if qs.exists() and cart_item.exists():
            cart = qs[0]
            cart_item = cart_item[0]
            if cart.items.filter(item__slug=item.slug):
                cart_item.quantity += 1
                cart_item.save()
                messages.info(request, "Quantity updated")
            else:
                cart_item = CartItem.objects.create(item=item, ordered=False)
                cart.items.add(cart_item)
                messages.info(request, "Item added to cart")
        else:
            cart_item = CartItem.objects.create(item=item, ordered=False)
            cart = Cart.objects.create(ordered=False)
            cart.items.add(cart_item)
            messages.info(request, "Item added to cart")
        request.session['cart_item_id'] = cart_item.id
        request.session['cart_id'] = cart.id
    return redirect("products:products-list")


def remove_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    if request.user.is_authenticated:
        cart_qs = Cart.objects.filter(user=request.user, ordered=False)
        if cart_qs.exists():
            cart = cart_qs[0]
            if cart.items.filter(item__slug=item.slug).exists():
                cart_item = CartItem.objects.filter(item=item,
                                                    user=request.user,
                                                    ordered=False)[0]
                cart_item.delete()
                messages.info(request, "Item removed from cart")
                cart_item.save()

                return redirect("products:cart-summary")
            else:
                messages.info(request, "Item not found in cart")
        else:
            messages.info(request, "You do not have an active order")

            return redirect("products:products-list")

    else:
        cart_item_id = request.session.get("cart_item_id", None)
        cart_id = request.session.get("cart_id", None)
        qs = Cart.objects.filter(id=cart_id, ordered=False)
        if qs.exists():
            cart = qs[0]
            if cart.items.filter(item__slug=item.slug):
                cart_item = CartItem.objects.all().filter(id=cart_item_id,
                                                          ordered=False)[0]
                cart_item.delete()
                messages.info(request, "Item removed from cart")
                cart_item.save()
                return redirect("products:cart-summary")
            else:
                messages.info(request, "Item not found in cart")
        else:
            messages.info(request, "You do not have an active order")

            return redirect("products:products-list")


@login_required
def remove_coupon(request):
    cart_qs = Cart.objects.filter(user=request.user, ordered=False)
    if cart_qs.exists():
        cart = cart_qs[0]
        if cart.coupon:
            cart.coupon = None
            cart.save()
            messages.info(request, "Coupon Removed")
            return redirect("products:cart-summary")


def remove_single_item_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    if request.user.is_authenticated:
        cart_qs = Cart.objects.filter(user=request.user, ordered=False)
        if cart_qs.exists():
            cart = cart_qs[0]
            if cart.items.filter(item__slug=item.slug).exists():
                cart_item = CartItem.objects.filter(item=item,
                                                    user=request.user,
                                                    ordered=False)[0]
                if cart_item.quantity > 1:
                    cart_item.quantity -= 1
                    messages.info(request, "Quantity updated")
                else:
                    cart.items.remove(cart_item)
                if cart.coupon:
                    cart.coupon = None
                    cart.save()
                    cart_item.delete()
                    messages.info(request, "Item removed from cart")
                cart_item.save()

                return redirect("products:cart-summary")
            else:
                messages.info(request, "Item not found in cart")
        else:
            messages.info(request, "You do not have an active order")

            return redirect("products:products-list")

    else:
        cart_item_id = request.session.get("cart_item_id", None)
        cart_id = request.session.get("cart_id", None)
        qs = Cart.objects.filter(id=cart_id, ordered=False)
        if qs.exists():
            cart = qs[0]
            if cart.items.filter(item__slug=item.slug):
                cart_item = CartItem.objects.all().filter(id=cart_item_id,
                                                          ordered=False)[0]
                if cart_item.quantity > 1:
                    cart_item.quantity -= 1
                    messages.info(request, "Quantity updated")
                else:
                    cart.items.remove(cart_item)
                    cart_item.delete()
                    messages.info(request, "Item removed from cart")
                cart_item.save()
                return redirect("products:cart-summary")
            else:
                messages.info(request, "Item not found in cart")
        else:
            messages.info(request, "You do not have an active order")

            return redirect("products:products-list")


@login_required
def get_coupon(request, code):
    try:
        coupon = Coupon.objects.get(code=code)
        return coupon
    except ObjectDoesNotExist:
        messages.info(request, "Coupon does not exist")
    except:
        messages.warning(self.request, "Invalid Coupon")
        return redirect("products:cart-summary")


class AddCouponView(LoginRequiredMixin, View):
    def post(self, *args, **kwargs):
        form = CouponForm(self.request.POST or None)
        if form.is_valid():
            try:
                code = form.cleaned_data.get('code')
                cart = Cart.objects.get(user=self.request.user, carted=False)
                cart.coupon = get_coupon(self.request, code)
                cart.save()
                messages.success(self.request, "Coupon added")
                return redirect("products:cart-summary")
            except ObjectDoesNotExist:
                messages.info(self.request, "You do not have an active order")
                return redirect("products:cart-summary")
            except:
                messages.warning(self.request, "Invalid Coupon")
        return redirect("products:cart-summary")
