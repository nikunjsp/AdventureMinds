from django.contrib import admin
from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q
from .models import *


# Register your models here.
admin.site.register(UserProfile)
admin.site.register(Place)
admin.site.register(ChatMessage)
admin.site.register(UserPreferences)
admin.site.register(PreferenceChoice)
admin.site.register(PreferenceCategory)
admin.site.register(ChatGroup)
admin.site.register(Trip)
admin.site.register(TripPhoto)
admin.site.register(TripPreference)
admin.site.register(JoinRequest)
admin.site.register(Rating)
admin.site.register(Review)
admin.site.register(BlogPost)
admin.site.register(Wishlist)


class ChatMessage(admin.TabularInline):
    model = ChatMessage


class userchatForm(forms.ModelForm):
    def clean(self):
        """
        This is the function that can be used to
        validate your model data from admin
        """
        super(userchatForm, self).clean()
        first_person = self.cleaned_data.get('first_person')
        second_person = self.cleaned_data.get('second_person')

        lookup1 = Q(first_person=first_person) & Q(second_person=second_person)
        lookup2 = Q(first_person=second_person) & Q(second_person=first_person)
        lookup = Q(lookup1 | lookup2)
        qs = UserChat.objects.filter(lookup)
        if qs.exists():
            raise ValidationError(f'Chat between {first_person} and {second_person} already exists.')


class UserChatAdmin(admin.ModelAdmin):
    inlines = [ChatMessage]

    class Meta:
        model = UserChat


admin.site.register(UserChat, UserChatAdmin)
