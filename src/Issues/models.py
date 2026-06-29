from django.db import models
class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('citizen', 'Citizen'),
        ('authority', 'Authority'),
        ('admin', 'Admin'),
    ]

    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    password = models.CharField(max_length=100)
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='citizen'
    )
    profile_picture = models.ImageField(
        upload_to="profile_pictures/",
        blank=True,
        null=True
    )

    points = models.IntegerField(default=0)

    is_verified = models.BooleanField(default=False)

    verification_token = models.CharField(
    max_length=100,
    blank=True,
    null=True
    )

    login_otp = models.CharField(
    max_length=6,
    blank=True,
    null=True
    )

    otp_verified = models.BooleanField(
    default=False
    )

    def __str__(self):
        return self.name
class Issue(models.Model):
    title=models.CharField(max_length=250)
    description = models.TextField()
    category = models.CharField(max_length=100)
    location = models.CharField(max_length=255)
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    reporter = models.ForeignKey(
    UserProfile,
    on_delete=models.CASCADE,
    related_name="reported_issues"
    )
    image = models.ImageField(
    upload_to='issues/images/',
    null=True,
    blank=True
    )

    video = models.FileField(
    upload_to='issues/videos/',
    null=True,
    blank=True
    )

    priority = models.CharField(
    max_length=20,
    default='medium'
    )
    summary = models.TextField(
    null=True,
    blank=True
    )

    latitude = models.FloatField(
    null=True,
    blank=True
    )

    longitude = models.FloatField(
    null=True,
    blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.title

class Verification(models.Model):
    VOTE_CHOICES = [
        ('upvote', 'Upvote'),
        ('downvote', 'Downvote'),
    ]

    user = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='verifications'
    )

    issue = models.ForeignKey(
        Issue,
        on_delete=models.CASCADE,
        related_name='verifications'
    )

    vote = models.CharField(
        max_length=10,
        choices=VOTE_CHOICES
    )

    verified_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.name} - {self.issue.title}"
    
class Comment(models.Model):
    user = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name="comments"
    )

    issue = models.ForeignKey(
        Issue,
        on_delete=models.CASCADE,
        related_name="comments"
    )

    message = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.name} - Comment"
    
class AuthorityUpdate(models.Model):
    authority = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name="authority_updates"
    )

    issue = models.ForeignKey(
        Issue,
        on_delete=models.CASCADE,
        related_name="updates"
    )

    update_message = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.issue.title}"
    
class Notification(models.Model):

    user = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE
    )

    message = models.TextField()

    is_read = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        return self.message


# Create your models here.
