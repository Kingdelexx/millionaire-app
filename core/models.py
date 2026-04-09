from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    wallet_balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    auto_enter = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}'s Profile"

class Raffle(models.Model):
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField()
    total_pool = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    is_active = models.BooleanField(default=True)
    winner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='won_raffles')
    amount_won = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"Raffle ending {self.end_date.strftime('%Y-%m-%d')} - Active: {self.is_active}"

class Donation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='donations')
    raffle = models.ForeignKey(Raffle, on_delete=models.CASCADE, related_name='donations')
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('100.00'))
    created_at = models.DateTimeField(auto_now_add=True)
    paystack_reference = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} donated {self.amount} to Raffle #{self.raffle.id}"

class Withdrawal(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Failed', 'Failed'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='withdrawals')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    bank_name = models.CharField(max_length=100)
    account_number = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Withdrawal #{self.id} of {self.amount} by {self.user.username} ({self.status})"
