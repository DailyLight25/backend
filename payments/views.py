from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action, api_view, permission_classes
from django.shortcuts import get_object_or_404 
from django.db import transaction
from django.conf import settings
import stripe 
import logging

from .models import Donation, Subscription
from .serializers import DonationSerializer, CreateDonationSerializer, SubscriptionSerializer, CreateSubscriptionSerializer
from users.models import User # To update premium status

logger = logging.getLogger(__name__)

# Initialize Stripe (move to settings or a config file in production)
stripe.api_key = settings.STRIPE_SECRET_KEY


class PaymentViewSet(viewsets.GenericViewSet):
    # This ViewSet will handle general payment-related actions, not tied to a single model
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'donate':
            return CreateDonationSerializer
        elif self.action == 'subscribe':
            return CreateSubscriptionSerializer
        elif self.action == 'status':
            return SubscriptionSerializer
        return None  # Default case 

    @action(detail=False, methods=['post'], serializer_class=CreateDonationSerializer)
    def donate(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        amount = serializer.validated_data['amount']
        currency = serializer.validated_data['currency']
        payment_method = serializer.validated_data['payment_method']
        notes = serializer.validated_data.get('notes', '')

        user = request.user if request.user.is_authenticated else None

        if payment_method == 'Stripe':
            try:
                # a Stripe PaymentIntent 
                charge = stripe.Charge.create(
                    amount=int(amount * 100), # amount in cents
                    currency=currency,
                    source=request.data.get('stripe_token'), # Assume token from client
                    description=f"Donation for Salt & Light by {user.username if user else 'Anonymous'}",
                    metadata={'user_id': user.id if user else 'anonymous'}
                )
                transaction_id = charge.id
                status_code = 'completed' if charge.status == 'succeeded' else 'failed'
                message = "Donation processed successfully via Stripe."
            except stripe.error.StripeError as e:
                logger.error(f"Stripe error during donation: {e}")
                transaction_id = None
                status_code = 'failed'
                message = f"Stripe payment failed: {str(e)}"
                return Response({'detail': message}, status=status.HTTP_400_BAD_REQUEST)
        elif payment_method == 'M-Pesa':
            phone_number = request.data.get('phone_number')
            if not phone_number:
                return Response({'detail': 'Phone number is required for M-Pesa donation.'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Simulate M-Pesa STK Push
            transaction_id = f"MPESA_SIM_{user.id}_{amount}_{currency}_{phone_number}_{timezone.now().timestamp()}"
            status_code = 'pending'
            message = "M-Pesa STK Push simulated. Awaiting confirmation."
        else:
            return Response({'detail': 'Unsupported payment method.'}, status=status.HTTP_400_BAD_REQUEST)

        donation = Donation.objects.create(
            user=user,
            amount=amount,
            currency=currency,
            payment_method=payment_method,
            transaction_id=transaction_id,
            status=status_code,
            notes=notes
        )
        return Response(DonationSerializer(donation).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], serializer_class=CreateSubscriptionSerializer)
    def subscribe(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        if not user.is_authenticated:
            return Response({'detail': 'Authentication required for subscription.'}, status=status.HTTP_401_UNAUTHORIZED)

        plan_name = serializer.validated_data['plan_name']
        stripe_payment_token = serializer.validated_data.get('stripe_payment_token')
        phone_number = serializer.validated_data.get('phone_number')

        # Prevent duplicate active subscriptions for the same user
        if Subscription.objects.filter(user=user, is_active=True).exists():
            return Response({'detail': 'User already has an active subscription.'}, status=status.HTTP_400_BAD_REQUEST)

        subscription_id = None
        subscription_status = 'pending'
        message = "Subscription initiated."
        
        # Determine price based on plan_name (or fetch from a DB table of plans)
        plan_details = {
            'freemium_monthly': {'price': 1.00, 'currency': 'USD'},
            'freemium_annual': {'price': 10.00, 'currency': 'USD'},
            # Add more plans
        }.get(plan_name.lower())

        if not plan_details:
            return Response({'detail': 'Invalid subscription plan.'}, status=status.HTTP_400_BAD_REQUEST)

        price = plan_details['price']
        currency = plan_details['currency']

        try:
            with transaction.atomic():
                if stripe_payment_token:
                    customer = stripe.Customer.create(
                        email=user.email,
                        source=stripe_payment_token
                    )
                    charge = stripe.Charge.create(
                        amount=int(price * 100),
                        currency=currency,
                        customer=customer.id,
                        description=f"{plan_name} subscription for {user.username}",
                    )
                    subscription_id = f"STRIPE_SUB_{charge.id}"
                    subscription_status = 'active'
                    message = "Stripe subscription activated."
                elif phone_number:
                    subscription_id = f"MPESA_SUB_SIM_{user.id}_{plan_name}_{timezone.now().timestamp()}"
                    subscription_status = 'active'
                    message = "M-Pesa subscription simulated (one-time payment)."
                else:
                    return Response({'detail': 'Payment method (Stripe token or phone number) is required.'}, status=status.HTTP_400_BAD_REQUEST)

                subscription = Subscription.objects.create(
                    user=user,
                    plan_name=plan_name,
                    price=price,
                    currency=currency,
                    stripe_subscription_id=subscription_id,
                    status=subscription_status,
                    is_active=True,
                    last_payment_date=timezone.now(),
                    end_date=timezone.now() + timezone.timedelta(days=30 if 'monthly' in plan_name else 365)
                )
                user.premium_status = True
                user.save()

                return Response(SubscriptionSerializer(subscription).data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Subscription error: {e}", exc_info=True)
            return Response({'detail': f'Subscription failed: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def status(self, request):
        user = request.user
        if not user.is_authenticated:
            return Response({'detail': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            subscription = Subscription.objects.get(user=user, is_active=True)
            serializer = SubscriptionSerializer(subscription)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Subscription.DoesNotExist:
            return Response({'detail': 'No active subscription found.'}, status=status.HTTP_404_NOT_FOUND)

    # Move these OUTSIDE the PaymentViewSet class

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def mpesa_callback(request):
    logger.info(f"M-Pesa Callback Received: {request.data}")
    return Response({"ResultCode": 0, "ResultDesc": "Confirmation Service Success"}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        logger.error(f"Invalid payload: {e}")
        return Response({'detail': 'Invalid payload'}, status=status.HTTP_400_BAD_REQUEST)
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid signature: {e}")
        return Response({'detail': 'Invalid signature'}, status=status.HTTP_400_BAD_REQUEST)

    # Handle event types
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        logger.info(f"Stripe Checkout Session Completed: {session.id}")

    elif event['type'] == 'invoice.payment_succeeded':
        invoice = event['data']['object']
        logger.info(f"Stripe Invoice Payment Succeeded: {invoice.id}")

    return Response({'status': 'success'}, status=status.HTTP_200_OK)
