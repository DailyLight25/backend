from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import PaymentViewSet, mpesa_callback, stripe_webhook # Import the standalone webhook views

router = DefaultRouter()
router.register(r'payments', PaymentViewSet, basename='payment') # basename is required for GenericViewSet

urlpatterns = [
    path('', include(router.urls)),
    path('payments/mpesa-callback/', mpesa_callback, name='mpesa_callback'),
    path('payments/stripe-webhook/', stripe_webhook, name='stripe_webhook'),
]