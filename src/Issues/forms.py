from django import forms
from .models import Issue,Comment,AuthorityUpdate,UserProfile




class IssueForm(forms.ModelForm):
    class Meta:
        model = Issue
        fields = [
            "title",
            "description",
            "image",
            "video",
            "location",
            "latitude",
            "longitude",
        ]



class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment

        fields = ["message"]

        widgets = {
            "message": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Write your comment..."
                }
            )
        }

class AuthorityUpdateForm(forms.ModelForm):

    status = forms.ChoiceField(
        choices=Issue.STATUS_CHOICES
    )

    class Meta:

        model = AuthorityUpdate

        fields = [
            "update_message",
            "status"
        ]


class RegisterForm(forms.ModelForm):

    class Meta:
        model = UserProfile

        fields = [
            "name",
            "email",
            "phone",
            "password",
            "role",
            "profile_picture"
        ]

        widgets = {
            "password": forms.PasswordInput()
        }

class LoginForm(forms.Form):

    email = forms.EmailField()

    password = forms.CharField(
        widget=forms.PasswordInput()
    )

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            "name",
            "phone",
            "profile_picture",
        ]