from django.core.management.base import BaseCommand
from core.models import Raffle
from django.utils import timezone
import random
from decimal import Decimal

class Command(BaseCommand):
    help = 'Selects a winner for the currently active raffle and starts a new one.'

    def handle(self, *args, **options):
        active_raffle = Raffle.objects.filter(is_active=True).first()
        if not active_raffle:
            self.stdout.write(self.style.WARNING('No active raffle found.'))
            return

        donations = list(active_raffle.donations.all())
        unique_users = list(set([d.user for d in donations]))

        if not unique_users:
            self.stdout.write(self.style.WARNING('No donations in this raffle. Closing without a winner.'))
            active_raffle.is_active = False
            active_raffle.save()
        else:
            winner = random.choice(unique_users)
            # Winner takes exactly 80% of the pool
            winnings = active_raffle.total_pool * Decimal('0.80')
            
            # Award winner
            active_raffle.winner = winner
            active_raffle.amount_won = winnings
            active_raffle.is_active = False
            active_raffle.save()
            
            # Update user profile wallet
            profile = winner.profile
            profile.wallet_balance += winnings
            profile.save()
            
            self.stdout.write(self.style.SUCCESS(f'Winner selected: {winner.username} won NGN {winnings}'))

        # Create tomorrow's raffle
        now = timezone.now()
        next_draw = now.replace(hour=20, minute=0, second=0, microsecond=0)
        if now >= next_draw:
            next_draw += timezone.timedelta(days=1)
        
        new_raffle = Raffle.objects.create(end_date=next_draw)
        self.stdout.write(self.style.SUCCESS(f'Created new raffle ending {next_draw}'))

        # Auto-enter users
        from core.models import UserProfile, Donation
        
        auto_enter_profiles = UserProfile.objects.filter(auto_enter=True, wallet_balance__gte=Decimal('100.00'))
        entered_count = 0
        for profile in auto_enter_profiles:
            profile.wallet_balance -= Decimal('100.00')
            profile.save()
            
            Donation.objects.create(
                user=profile.user,
                raffle=new_raffle,
                amount=Decimal('100.00'),
                paystack_reference='WALLET_PAYMENT_AUTO'
            )
            new_raffle.total_pool += Decimal('100.00')
            entered_count += 1
            
        new_raffle.save()
        if entered_count > 0:
            self.stdout.write(self.style.SUCCESS(f'Auto-entered {entered_count} users into the new raffle.'))
