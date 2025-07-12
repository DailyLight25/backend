from django.contrib import admin
from .models import Donation, Subscription

@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'currency', 'payment_method', 'status', 'donated_at')
    list_filter = ('payment_method', 'status', 'currency', 'donated_at')
    search_fields = ('user__username', 'transaction_id', 'notes')
    raw_id_fields = ('user',)
    readonly_fields = ('donated_at',)
    fieldsets = (
        (None, {
            'fields': ('user', 'amount', 'currency', 'payment_method', 'transaction_id', 'status')
        }),
        ('Details', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('donated_at',),
            'classes': ('collapse',)
        }),
    )

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan_name', 'price', 'status', 'is_active', 'start_date', 'end_date')
    list_filter = ('plan_name', 'status', 'is_active', 'start_date')
    search_fields = ('user__username', 'stripe_subscription_id')
    raw_id_fields = ('user',)
    readonly_fields = ('start_date', 'last_payment_date', 'stripe_subscription_id')
    fieldsets = (
        (None, {
            'fields': ('user', 'plan_name', 'price', 'currency', 'status', 'is_active')
        }),
        ('Payment Details', {
            'fields': ('stripe_subscription_id',)
        }),
        ('Dates', {
            'fields': ('start_date', 'end_date', 'last_payment_date')
        }),
    )