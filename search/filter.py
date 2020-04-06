from products.models import *
from .models import SearchTerm
from django.db.models import Q
import django_filters
from django import forms
import re
from functools import reduce
import operator


def search_words(value, queryset):
    search_term = value
    stopwords = ['a', 'is', 'the', 'of']
    search_words = []
    if len(search_term.split()) > 1:
        w = list(
            filter(lambda w: w not in stopwords,
                   re.split(r"\W+", search_term.lower())))
        for word in w:
            search_words.append(word)
        search_words.append(search_term)
    else:
        search_words.append(search_term)
    return queryset.filter(
        reduce(operator.or_,
               (Q(title__icontains=term) | Q(description__icontains=term)
                | Q(brand__title__iexact=term)
                | Q(collections__title__icontains=term)
                | Q(variations__name__icontains=term)
                for term in search_words))).distinct()


class ProductsSearch(django_filters.FilterSet):

    # def __init__(self, q, *args, **kwargs):
    #     super(ProductsSearch, self).__init__(*args, **kwargs)

    query = django_filters.CharFilter(
        method='filter_products',
        widget=forms.TextInput(attrs={
            'class': 'input search-input',
            'placeholder': 'Enter your keyword'
        }))
    category = django_filters.ModelChoiceFilter(
        method='filter_by_category',
        queryset=Category.objects.parent(),
        widget=forms.Select(attrs={
            'class': 'input search-categories',
        }),
        empty_label="All categories")

    class Meta:
        model = Item
        fields = ['query', 'category']

    def filter_by_category(self, queryset, name, value):
        return queryset.filter(category__parent=value).distinct()

    def filter_products(self, queryset, name, value):
        search_words(queryset, value)


class FilterQuery(django_filters.FilterSet):
    brand = django_filters.ModelMultipleChoiceFilter(
        queryset=Brand.objects.all(),
        widget=forms.CheckboxSelectMultiple(
            attrs={'class': 'filter-option'
                   # 'style': 'display:none',
                   }),
    )
    price_min = django_filters.NumberFilter(
        field_name='price',
        lookup_expr='gte',
        widget=forms.NumberInput(attrs={
            'class': 'price_filter_min form-control',
            'placeholder': 'Min',
        }))
    price_max = django_filters.NumberFilter(
        field_name='price',
        lookup_expr='lte',
        widget=forms.NumberInput(attrs={
            'class': 'price_filter_max form-control',
            'placeholder': 'Max',
        }))

    class Meta:
        model = Item
        fields = ['brand', 'price_min', 'price_max']