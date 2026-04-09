from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.conf import settings
from django.urls import reverse
from django.contrib import messages
import uuid
import requests
from decimal import Decimal
from .models import Raffle, Donation, Withdrawal

def index_view(request):
    past_raffles = Raffle.objects.filter(is_active=False, winner__isnull=False).order_by('-end_date')[:3]
    return render(request, 'index.html', {'past_raffles': past_raffles})

@login_required
def dashboard_view(request):
    active_raffle = Raffle.objects.filter(is_active=True).first()
    if not active_raffle:
        now = timezone.now()
        next_draw = now.replace(hour=19, minute=0, second=0, microsecond=0)
        if now >= next_draw:
            next_draw += timezone.timedelta(days=1)
        active_raffle = Raffle.objects.create(end_date=next_draw)
        
    user_donated = request.user.donations.filter(raffle=active_raffle).exists()
    
    past_raffle = Raffle.objects.filter(is_active=False, winner__isnull=False).order_by('-end_date').first()
    
    user_donations = request.user.donations.select_related('raffle').order_by('-created_at')
    
    return render(request, 'dashboard.html', {
        'active_raffle': active_raffle,
        'past_raffle': past_raffle,
        'user_donated': user_donated,
        'wallet_balance': request.user.profile.wallet_balance,
        'user_donations': user_donations
    })

@login_required
def donate_view(request):
    if request.method == 'POST':
        active_raffle = Raffle.objects.filter(is_active=True).first()
        if not active_raffle:
            messages.error(request, "No active raffle available.")
            return redirect('dashboard')
            
        if request.user.donations.filter(raffle=active_raffle).exists():
            messages.info(request, "You have already donated for this week's raffle!")
            return redirect('dashboard')

        amount_needed = Decimal('100.00')
        profile = request.user.profile
        if profile.wallet_balance >= amount_needed:
            # Deduct from wallet and enter raffle
            profile.wallet_balance -= amount_needed
            profile.save()
            
            Donation.objects.create(
                user=request.user,
                raffle=active_raffle,
                amount=amount_needed,
                paystack_reference='WALLET_PAYMENT'
            )
            active_raffle.total_pool += amount_needed
            active_raffle.save()
            messages.success(request, "You've successfully entered the draw using your wallet balance!")
        else:
            messages.error(request, "Insufficient wallet balance. Please deposit funds first.")
            
    return redirect('dashboard')

@login_required
def deposit_view(request):
    if request.method == 'POST':
        amount_ngn = request.POST.get('amount')
        try:
            amount_kobo = int(float(amount_ngn) * 100)
            if amount_kobo <= 0:
                raise ValueError
        except (TypeError, ValueError):
            messages.error(request, "Invalid deposit amount.")
            return redirect('dashboard')

        reference = str(uuid.uuid4())
        
        headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "email": request.user.email,
            "amount": amount_kobo,
            "reference": reference,
            "callback_url": request.build_absolute_uri(reverse('paystack_callback'))
        }
        
        response = requests.post("https://api.paystack.co/transaction/initialize", json=data, headers=headers)
        if response.status_code == 200:
            response_data = response.json()
            return redirect(response_data['data']['authorization_url'])
        else:
            messages.error(request, "Error connecting to payment gateway.")
            return redirect('dashboard')
            
    return redirect('dashboard')

@login_required
def paystack_callback(request):
    reference = request.GET.get('reference')
    if not reference:
        return redirect('dashboard')
        
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
    }
    response = requests.get(f"https://api.paystack.co/transaction/verify/{reference}", headers=headers)
    
    if response.status_code == 200:
        response_data = response.json()
        if response_data['data']['status'] == 'success':
            amount_kobo = response_data['data']['amount']
            amount_deposited = Decimal(str(amount_kobo)) / Decimal('100')
            profile = request.user.profile
            profile.wallet_balance += amount_deposited
            profile.save()
            messages.success(request, f"Successfully deposited ₦{amount_deposited:.2f} into your wallet!")
        else:
            messages.error(request, "Payment failed.")
    return redirect('dashboard')

@login_required
def withdraw_view(request):
    if request.method == 'POST':
        amount_str = request.POST.get('amount')
        bank_name = request.POST.get('bank_name')
        account_number = request.POST.get('account_number')
        
        try:
            amount = Decimal(amount_str)
            if amount <= Decimal('0.00'):
                raise ValueError
        except (TypeError, ValueError):
            messages.error(request, "Invalid withdrawal amount.")
            return redirect('dashboard')
            
        profile = request.user.profile
        if profile.wallet_balance >= amount:
            profile.wallet_balance -= amount
            profile.save()
            
            Withdrawal.objects.create(
                user=request.user,
                amount=amount,
                bank_name=bank_name,
                account_number=account_number
            )
            messages.success(request, f"Withdrawal request of ₦{amount:.2f} submitted successfully! It is currently pending.")
        else:
            messages.error(request, "Insufficient wallet balance.")
            
    return redirect('dashboard')

@login_required
def toggle_auto_enter(request):
    if request.method == 'POST':
        profile = request.user.profile
        profile.auto_enter = request.POST.get('auto_enter') == 'on'
        profile.save()
        if profile.auto_enter:
            messages.success(request, "Daily auto-enter has been enabled.")
        else:
            messages.success(request, "Daily auto-enter has been disabled.")
    return redirect('dashboard')
