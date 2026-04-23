from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from .models import CustomUser, ConsentText, UserReferrals

class UserReferralsInline(admin.TabularInline):
    model = UserReferrals
    fk_name = 'referrer'
    extra = 0
    readonly_fields = ('referral_code', 'invitee', 'created_at', 'stop_at', 'used_at', 'referral_type', 'status')
    can_delete = False


@admin.register(ConsentText)
class ConsentTextAdmin(admin.ModelAdmin):
    list_display = ('version', 'created_at', 'text')
    ordering = ('-created_at',)


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    add_form = UserCreationForm
    form = UserChangeForm
    model = CustomUser

    list_display = ["username", "email", "consent_given", "country", "region", "city"]

    fieldsets = UserAdmin.fieldsets + (
        ("Мешкання", {
            "fields": ("country", "region", "city", "country_public", "region_public", "city_public"),
        }),
        ("Юридична згода", {
            "fields": ("consent_given", "consent_date", "consent_version"),
        }),
    )
    readonly_fields = ("consent_date", "consent_version")

    # Keep add_fieldsets minimal to avoid conflicts with custom city/region API logic
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                "username",
                "password1",
                "password2",
                "display_name",
                "email",
                "consent_given",
            ),
        }),
    )
    inlines = [UserReferralsInline]