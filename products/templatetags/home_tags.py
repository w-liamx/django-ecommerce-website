from django import template
from products.models import Cart, Category
from django.shortcuts import render
from search.filter import ProductsSearch
from products.models import Item, Review

register = template.Library()


@register.inclusion_tag("tags/colletions.html")
def collections(collections):
    return {'collections': collections}


@register.inclusion_tag("products/search-results.html")
def results(results):
    return {'categorycollection': results}


@register.inclusion_tag("tags/promo_products.html")
def promo_collection(collection, promo_header, show_timer=True):
    return {
        'collection': collection,
        'promo_header': promo_header,
        'show_timer': show_timer
    }


@register.inclusion_tag("tags/home_section_items.html")
def home_section(collection, section_header, show_timer=False):
    return {
        'collection': collection,
        'section_header': section_header,
        'show_timer': show_timer
    }


@register.inclusion_tag("products/includes/category_view.html")
def category_view():
    categories = Category.objects.all()

    return {'categories': categories}


@register.inclusion_tag("tags/aside_top_rated.html")
def top_rated(section_header):
    all_items = Item.objects.all()
    top_rated = []
    for item in all_items:
        rating = item.get_avg_rating()
        if rating > 3:
            top_rated.append(item)
    return {'top_rated': top_rated, 'section_header': section_header}


@register.inclusion_tag("products/includes/search_form.html")
def search_form(request):
    products = ProductsSearch(request.GET or None, queryset=Item.objects.all())

    return {'object_list': products}