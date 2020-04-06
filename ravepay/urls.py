from django.urls import path
from . import settings, views
from django.views.decorators.csrf import csrf_exempt

app_name="ravepay"
urlpatterns = [
    path(
        "verify-payment/<order>/",
        views.verify_payment,
        name="verify_payment",
    ),
    path(
        "failed-verification/<order_id>/",
        views.FailedView.as_view(),
        name="failed_verification",
    ),
    path(
        "successful-verification/<order_id>/",
        views.SuccessView.as_view(),
        name="successful_verification",
    ),
    path(
        "failed-page/",
        views.TemplateView.as_view(template_name="ravepay/failed-page.html"),
        name="failed_page",
    ),
    path(
        "success-page/",
        views.TemplateView.as_view(template_name="ravepay/success-page.html"),
        name="success_page",
    ),
    path("webhook/", csrf_exempt(views.webhook_view), name="webhook"),
]
