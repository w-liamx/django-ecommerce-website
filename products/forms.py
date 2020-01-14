from django import forms
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget

PAYMENT_CHOICES = (
    ('S', 'Stripe'),
    ('P', 'PayPal')
)

class CheckoutForm(forms.Form):
    street_address = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'input',
        'placeholder': 'Address'
    }))
    apartment_address = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'input',
        'placeholder': 'Apartment'
    }))
    country = CountryField(blank_label='--- Select country ---').formfield(widget=CountrySelectWidget(attrs={
        'class': 'input'
    }))
    zip_code = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'input',
        'placeholder': 'ZIP Code'
    }))
    same_billing_address = forms.BooleanField(required=False, widget=forms.CheckboxInput())
    save_info = forms.BooleanField(required=False, widget=forms.CheckboxInput())
    payment_option = forms.ChoiceField(widget=forms.RadioSelect, choices=PAYMENT_CHOICES)
    
class CouponForm(forms.Form):
    code = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'input',
        'style': 'background-color:#fff',
        'placeholder': 'Coupon code',
        'aria-label': 'Coupon code',
        'aria-describedby': 'button-addon1'
    }))

class ReviewForm(forms.Form):
    user_name = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'input',
        'placeholder': 'Your Name'
    }))
    customer_email = forms.EmailField(widget=forms.TextInput(attrs={
        'class': 'input',
        'placeholder': 'Email Address'
    }))
    comment = forms.CharField(widget=forms.Textarea(attrs={
        'class': 'input',
        'placeholder': 'Comment'
    }))
    rating = forms.IntegerField(max_value=5)