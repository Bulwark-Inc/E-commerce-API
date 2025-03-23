from django.urls import path
from .views import InitiatePaymentView, VerifyPaymentView, paystack_webhook

urlpatterns = [
    path('initiate/<int:order_id>/', InitiatePaymentView.as_view(), name='initiate-payment'),
    path('verify/<str:reference>/', VerifyPaymentView.as_view(), name='verify-payment'),
    path('webhook/', paystack_webhook, name='paystack-webhook'),
]
