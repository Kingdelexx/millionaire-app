from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        # Ignore if the social account is already linked
        if sociallogin.is_existing:
            return

        # If the provider gives us an email, let's link it
        user = sociallogin.user
        email = getattr(user, 'email', None)
        
        if not email:
            return

        try:
            # Check if a user with this email already exists
            existing_user = User.objects.get(email=email)
            # Link the social login tightly to this user
            sociallogin.connect(request, existing_user)
        except User.DoesNotExist:
            pass
