from django.test import TestCase
from django.contrib.auth.models import User
from decimal import Decimal
from django.core.management import call_command
from .models import Raffle, Donation

class RaffleTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', email='user1@gmail.com', password='password')
        self.user2 = User.objects.create_user(username='user2', email='user2@gmail.com', password='password')
        self.user3 = User.objects.create_user(username='user3', email='user3@gmail.com', password='password')
        
    def test_donation_logic_and_winner_selection(self):
        from django.utils import timezone
        now = timezone.now()
        active_raffle = Raffle.objects.create(end_date=now)

        Donation.objects.create(user=self.user1, raffle=active_raffle, amount=Decimal('100.00'))
        active_raffle.total_pool += Decimal('100.00')
        active_raffle.save()
        
        Donation.objects.create(user=self.user2, raffle=active_raffle, amount=Decimal('100.00'))
        active_raffle.total_pool += Decimal('100.00')
        active_raffle.save()

        Donation.objects.create(user=self.user3, raffle=active_raffle, amount=Decimal('100.00'))
        active_raffle.total_pool += Decimal('100.00')
        active_raffle.save()

        self.assertEqual(active_raffle.total_pool, Decimal('300.00'))

        call_command('select_winner')

        active_raffle.refresh_from_db()
        self.assertFalse(active_raffle.is_active)
        self.assertIsNotNone(active_raffle.winner)
        
        # Winner takes exactly 80%
        self.assertEqual(active_raffle.amount_won, Decimal('240.00'))
        
        winner_profile = active_raffle.winner.profile
        self.assertEqual(winner_profile.wallet_balance, Decimal('240.00'))
        
        new_raffle = Raffle.objects.filter(is_active=True).first()
        self.assertIsNotNone(new_raffle)
