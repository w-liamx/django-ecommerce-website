from django import template
from products.models import Cart

register = template.Library()

@register.filter
def cart_item_count(user):
    if user.is_authenticated:
        qs = Cart.objects.filter(user=user, ordered=False)
        if qs.exists():
            return qs[0].items.all().filter(ordered=False).count()
        return 0

@register.filter
def anonymous_cart_item_count(session):
    qs = Cart.objects.filter(id=session.get('cart_id'), ordered=False)
    if qs.exists():
        return qs[0].items.all().filter(ordered=False).count()
    return 0

@register.filter
def cart_total(user):
    if user.is_authenticated:
        qs = Cart.objects.filter(user=user, ordered=False)
        if qs.exists():
            return qs[0].get_total()
        return "00.00"

@register.filter
def anonymous_cart_total(session):
    qs = Cart.objects.filter(id=session.get('cart_id'), ordered=False)
    if qs.exists():
        return qs[0].get_total()
    return "00.00"