from django import forms
from multiupload.fields import MultiFileField
from titlecase import titlecase
from .models import *
from django.contrib.auth.models import User


class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(label='First Name', required=False)
    last_name = forms.CharField(label='Last Name', required=False)

    class Meta:
        model = UserProfile
        fields = ['phone_number', 'address', 'date_of_birth', 'profile_photo']

        labels = {
            'phone_number': 'Phone Number',
            'address': 'Address',
            'date_of_birth': 'Date of Birth',
            'profile_photo': 'Profile Photo'
        }
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'profile_photo': forms.ClearableFileInput(attrs={'class': 'form-control-file'})
        }

    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        if self.instance.user:
            self.fields['username'] = forms.CharField(label='Username', initial=self.instance.user.username, disabled=True)
            self.fields['email'] = forms.EmailField(label='Email', initial=self.instance.user.email, disabled=True, required=False)

            # Set initial values for first_name and last_name
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name

    def clean_email(self):
        return self.instance.user.email

    def save(self, commit=True):
        # Update first_name and last_name of the associated User object
        self.instance.user.first_name = self.cleaned_data['first_name']
        self.instance.user.last_name = self.cleaned_data['last_name']
        self.instance.user.save()  # Save the User object
        return super(UserProfileForm, self).save(commit)


class UserPreferencesForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        initial_data = kwargs.pop('initial', {})
        super(UserPreferencesForm, self).__init__(*args, **kwargs)

        categories = PreferenceCategory.objects.all()
        for category in categories:
            choices = category.preferencechoice_set.all()
            field_name = category.name
            self.fields[field_name] = forms.ModelMultipleChoiceField(
                queryset=choices,
                widget=forms.CheckboxSelectMultiple,
                required=False  # Make fields not required
            )
            self.fields[field_name].label_from_instance = lambda obj: obj.value

            initial_values = initial_data.get(field_name, [])
            self.initial[field_name] = initial_values  # Use choice objects directly

    class Meta:
        model = UserPreferences
        fields = []  # No need to specify fields as they are dynamically generated


class AddTripForm(forms.ModelForm):
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label='Start Date'
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label='End Date'
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        label='Description'
    )
    meeting_point = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='Meeting Point',
        required=False
    )
    max_capacity = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label='Max Capacity'
    )
    cost_per_person = forms.DecimalField(
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label='Cost Per Person'
    )
    photos = MultiFileField(
        min_num=1,
        max_num=10,
        max_file_size=1024*1024*5,
        label='Upload Photos'
    )

    class Meta:
        model = Trip
        fields = ['title', 'place', 'start_date', 'end_date', 'description', 'meeting_point', 'max_capacity', 'cost_per_person', 'photos']
        labels = {
            'title': 'Title',
            'place': 'Place',
        }
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'place': forms.Select(attrs={'class': 'form-select form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)


    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date and end_date < start_date:
            raise forms.ValidationError("End date must be greater than or equal to start date.")

        return cleaned_data

    def save(self, commit=True):
        trip = super().save(commit=False)
        trip.uploader = self.user
        if commit:
            trip.save()
            self.save_m2m()  # Save many-to-many fields after the trip is saved
        return trip


class TripPreferenceForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        categories = PreferenceCategory.objects.all()
        for category in categories:
            label = titlecase(category.name.replace('_', ' '))
            choices = PreferenceChoice.objects.filter(category=category)
            choices_list = [(choice.pk, choice.value) for choice in choices]
            self.fields[f'{category.name}'] = forms.MultipleChoiceField(
                choices=choices_list,
                widget=forms.CheckboxSelectMultiple,
                label=label,
            required = False
            )

    class Meta:
        model = TripPreference
        fields = []


class TripSearchForm(forms.Form):
    query = forms.CharField(label='Search', max_length=100)


class SignupForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'password']
        labels = {
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'username': 'Username',
            'email': 'Email',
            'password': 'Password'
        }
        widgets = {
            'password': forms.PasswordInput()
        }

    phone_number = forms.CharField(label='Phone Number')
    address = forms.CharField(label='Address')
    date_of_birth = forms.DateField(label='Date of Birth', widget=forms.DateInput(attrs={'type': 'date'}))


class LoginForm(forms.Form):
    username = forms.CharField(label='Username')
    password = forms.CharField(widget=forms.PasswordInput, label='Password')


class ForgotPasswordForm(forms.Form):
    username = forms.CharField(label='Username')
    email = forms.EmailField(label='Email')
    last_three_digits_of_phone_number = forms.CharField(label='Last Three Digits of Phone Number')
    date_of_birth = forms.DateField(label='Date of Birth', widget=forms.DateInput(attrs={'type': 'date'}))
    new_password = forms.CharField(widget=forms.PasswordInput, label='New Password')
    confirm_password = forms.CharField(widget=forms.PasswordInput, label='Confirm Password')


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['first_name', 'last_name', 'email', 'message']


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['review']


class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ['rating']


class BlogPostForm(forms.ModelForm):
    class Meta:
        model = BlogPost
        fields = ['title', 'display_content', 'content', 'place', 'image']