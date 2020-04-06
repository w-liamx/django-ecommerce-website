from django import forms
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget

PAYMENT_CHOICES = (('S', 'Stripe'), ('F', 'Flutterwave'))


class CheckoutForm(forms.Form):
    shipping_street_address = forms.CharField(required=False)
    shipping_apartment_address = forms.CharField(required=False)
    shipping_country = CountryField(
        blank_label='--- Select country ---').formfield(
            required=False,
            widget=CountrySelectWidget(attrs={'class': 'input'}))
    shipping_zip_code = forms.CharField(required=False)

    billing_street_address = forms.CharField(required=False)
    billing_apartment_address = forms.CharField(required=False)
    billing_country = CountryField(
        blank_label='--- Select country ---').formfield(
            required=False,
            widget=CountrySelectWidget(attrs={'class': 'input'}))
    billing_zip_code = forms.CharField(required=False)

    same_billing_address = forms.BooleanField(required=False)
    set_default_shipping = forms.BooleanField(required=False)
    use_default_shipping = forms.BooleanField(required=False)
    set_default_billing = forms.BooleanField(required=False)
    use_default_billing = forms.BooleanField(required=False)

    payment_option = forms.ChoiceField(widget=forms.RadioSelect,
                                       choices=PAYMENT_CHOICES)


class CouponForm(forms.Form):
    code = forms.CharField(widget=forms.TextInput(
        attrs={
            'class': 'input',
            'style': 'background-color:#fff',
            'placeholder': 'Coupon code',
            'aria-label': 'Coupon code',
            'aria-describedby': 'button-addon1'
        }))


class ReviewForm(forms.Form):
    user_name = forms.CharField(widget=forms.TextInput(
        attrs={
            'class': 'input',
            'placeholder': 'Your Name'
        }))
    customer_email = forms.EmailField(widget=forms.TextInput(
        attrs={
            'class': 'input',
            'placeholder': 'Email Address'
        }))
    comment = forms.CharField(widget=forms.Textarea(attrs={
        'class': 'input',
        'placeholder': 'Comment'
    }))
    rating = forms.IntegerField(max_value=5)