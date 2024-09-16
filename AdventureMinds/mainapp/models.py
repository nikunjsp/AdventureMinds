from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.auth.models import User, AbstractUser
from django.core.exceptions import ValidationError


# Create your models here.
class Place(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=300)
    description = models.TextField(max_length=1000, blank=True)


    def __str__(self):
        return self.name


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=False, blank=True, primary_key=True, default=None)
    phone_number = models.CharField(max_length=12, null=True, blank=True)
    address = models.CharField(max_length=200, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    profile_photo = models.ImageField(upload_to='profile/', null=True, blank=True)
    # interested_places = models.ManyToManyField(Place, null=True, blank=True)
    preferences = models.ForeignKey('UserPreferences', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.user.username

class PreferenceCategory(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class PreferenceChoice(models.Model):
    category = models.ForeignKey(PreferenceCategory, on_delete=models.CASCADE)
    value = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.category.name}: {self.value}"

class TripPreference(models.Model):
    preferences = models.ManyToManyField(PreferenceChoice)

class UserPreferences(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='user_profile', null=True,
                                     blank=True)
    preferences = models.ManyToManyField(PreferenceChoice)

    def __str__(self):
        if self.user_profile:
            return f"Preferences for {self.user_profile.user.username}"
        else:
            return "No associated user profile"

    def get_selected_preferences(self):
        return [preference.value for preference in self.preferences.all()]


class Trip(models.Model):
    uploader = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_trips')
    title = models.CharField(max_length=100, null=True)
    description = models.TextField()
    place = models.ForeignKey(Place, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    max_capacity = models.PositiveIntegerField(default=10)
    cost_per_person = models.DecimalField(max_digits=8, decimal_places=2, default=1000)  # Cost per person for the trip
    meeting_point = models.CharField(max_length=255, blank=True)  # Meeting point for the trip
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    participants = models.ManyToManyField(User, related_name='participating_trips', blank=True)
    is_past = models.BooleanField(default=False)
    is_future = models.BooleanField(default=True)
    preferences = models.ForeignKey(TripPreference, on_delete=models.SET_NULL, null=True, blank=True)
    # Define methods to filter past and future trips
    def get_past_trips(self):
        return Trip.objects.filter(pk=self.pk, is_past=True)

    def get_future_trips(self):
        return Trip.objects.filter(pk=self.pk, is_future=True)

    def _str_(self):
        return self.title

class TripPhoto(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='trip_photos')
    photo = models.ImageField(upload_to='')

    def __str__(self):
        return f"Photo for {self.trip.place}"


class JoinRequest(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='join_requests')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Request to join {self.trip} by {self.user}"


class userchatManager(models.Manager):
    def by_user(self, **kwargs):
        user = kwargs.get('user')
        lookup = models.Q(first_person=user) | models.Q(second_person=user)
        qs = self.get_queryset().filter(lookup).distinct()
        return qs


class ChatGroup(models.Model):
    name = models.CharField(max_length=100)
    members = models.ManyToManyField(UserProfile)

    def __str__(self):
        return self.name


class UserChat(models.Model):
    first_person = models.ForeignKey(UserProfile, on_delete=models.CASCADE, null=True, blank=True,
                                     related_name='userchat_first_person')
    second_person = models.ForeignKey(UserProfile, on_delete=models.CASCADE, null=True, blank=True,
                                      related_name='userchat_second_person')
    group = models.ForeignKey(ChatGroup, on_delete=models.CASCADE, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['first_person', 'second_person', 'group']

    def clean(self):
        if self.first_person == self.second_person:
            raise ValidationError("First person and second person cannot be the same.")

        if self.group:
            if self.second_person is not None:
                raise ValidationError("In a group chat, second person must be null.")

            if UserChat.objects.filter(first_person=self.first_person, group=self.group).exists():
                raise ValidationError("A chat with the same first user and group already exists.")
        else:
            if UserChat.objects.filter(first_person=self.second_person, second_person=self.first_person,
                                       group=None).exists():
                raise ValidationError("Conversation between these users already exists.")

            if UserChat.objects.filter(first_person=self.first_person, second_person=self.second_person).exists():
                raise ValidationError("Conversation between these users already exists.")

            if not self.group and not self.second_person:
                raise ValidationError("Second person or group is required.")

    def __str__(self):
        if self.group:
            return f"Group chat: {self.group.name}"
        else:
            return f"Conversation between {self.first_person} and {self.second_person}"


class ChatMessage(models.Model):
    userchat = models.ForeignKey(UserChat, null=True, blank=True, on_delete=models.CASCADE,
                                 related_name='chatmessage_userchat')
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)


class ContactMessage(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.first_name} {self.last_name} - {self.timestamp}'

class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    trip = models.ForeignKey(Trip, default=1, on_delete=models.CASCADE)
    review = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.first_name


class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    place = models.ForeignKey(Place, on_delete=models.CASCADE)
    RATING_CHOICES = (
        (1, '1 star'),
        (2, '2 star'),
        (3, '3 star'),
        (4, '4 star'),
        (5, '5 star')
    )
    rating = models.PositiveIntegerField(choices=RATING_CHOICES)

    class Meta:
        unique_together = ('user', 'place')

    def __str__(self):
        return f"{self.user}'s {self.rating}-star rating for {self.place}"


class BlogPost(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    place = models.ForeignKey(Place, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='blog_images/', null=True, blank=True)  # Add this line for image upload
    created_at = models.DateTimeField(default=timezone.now)
    display_content = models.TextField()

    def __str__(self):
        return self.title


class Wishlist(models.Model):
    trip_id = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='wishlist_items')
    user_id = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    notes = models.TextField(blank=True, null=True)
    priority = models.IntegerField(default=1)
    date_added = models.DateTimeField(auto_now_add=True)

    def get_place(self):
        return self.trip_id.place

    class Meta:
        unique_together = ('user_id', 'trip_id',)

    def _str_(self):
        return f"{self.user_id.user.username}'s Wishlist Item: (Trip: {self.trip_id.description})"