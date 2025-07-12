from rest_framework import serializers
from .models import Donation, Subscription

class DonationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Donation
        fields = ['id', 'user', 'amount', 'currency', 'payment_method', 'transaction_id', 'status', 'donated_at', 'notes']
        read_only_fields = ['user', 'transaction_id', 'status', 'donated_at'] # Set by view/webhook

class CreateDonationSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency = serializers.CharField(max_length=3, default='KES')
    payment_method = serializers.CharField(max_length=50) # 'M-Pesa', 'Stripe'
    notes = serializers.CharField(max_length=500, required=False, allow_blank=True)

class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ['id', 'user', 'plan_name', 'price', 'currency', 'stripe_subscription_id',
                  'status', 'start_date', 'end_date', 'last_payment_date', 'is_active']
        read_only_fields = ['user', 'stripe_subscription_id', 'status', 'start_date',
                            'end_date', 'last_payment_date', 'is_active']

class CreateSubscriptionSerializer(serializers.Serializer):
    plan_name = serializers.CharField(max_length=50)
    # You might pass a Stripe token or similar for client-side payment initiation
    stripe_payment_token = serializers.CharField(max_length=255, required=False, allow_blank=True)
    # For M-Pesa, you might need phone number
    phone_number = serializers.CharField(max_length=15, required=False, allow_blank=True)