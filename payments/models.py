from django.db import models
from users.models import User

class Donation(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='donations')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='KES') # Kenya Shillings by default
    payment_method = models.CharField(max_length=50) # e.g., 'M-Pesa', 'Stripe'
    transaction_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    status = models.CharField(max_length=20, default='pending') # e.g., 'pending', 'completed', 'failed'
    donated_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-donated_at']

    def __str__(self):
        return f"Donation of {self.amount} {self.currency} by {self.user.username if self.user else 'Anonymous'}"

class Subscription(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    plan_name = models.CharField(max_length=50) # e.g., 'Premium Monthly', 'Annual Supporter'
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    stripe_subscription_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    status = models.CharField(max_length=20, default='active') # e.g., 'active', 'canceled', 'past_due'
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True) # For fixed-term subscriptions or when canceled
    last_payment_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.user.username}'s {self.plan_name} subscription ({self.status})"