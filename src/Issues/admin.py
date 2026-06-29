from django.contrib import admin
from .models import UserProfile, Issue, Verification, Comment
# admin.site.register(UserProfile)
# admin.site.register(Issue)
# admin.site.register(Verification)
# admin.site.register(Comment)

# Register your models here.
@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "category",
        "priority",
        "status",
        "created_at"
    )

    search_fields = (
        "title",
        "description",
        "category"
    )

    list_filter = (
        "status",
        "category",
        "priority"
    )

    ordering = ("-created_at",)
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "email",
        "role",
        "points"
    )

    search_fields = (
        "name",
        "email"
    )

    list_filter = (
        "role",
    )
@admin.register(Verification)
class VerificationAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "issue",
        "vote",
        "verified_at"
    )

    list_filter = (
        "vote",
    )
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "issue",
        "created_at"
    )

    search_fields = (
        "message",
    )