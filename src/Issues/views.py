from django.shortcuts import render,redirect
from django.contrib import messages
from .models import Issue, Comment, Verification, Notification,AuthorityUpdate
from django.shortcuts import get_object_or_404
from .forms import IssueForm,AuthorityUpdateForm,CommentForm,RegisterForm,LoginForm,ProfileUpdateForm
from django.core.mail import send_mail
from django.http import HttpResponse
from .models import UserProfile
from .gemini_service import analyze_issue
from .models import Comment
from .models import Verification
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .models import Issue, UserProfile
from .forms import IssueForm
import uuid
from django.urls import reverse
import random
from django.db.models import Q


def create_issue(request):
    if "user_id" not in request.session:
        return redirect("login")
    current_user = UserProfile.objects.get(
        id=request.session["user_id"]
    )
    if request.method == "POST":
        form = IssueForm(
            request.POST,
            request.FILES
        )
        if form.is_valid():
            issue = form.save(commit=False)
            issue.reporter = current_user
            try:
                ai_result = analyze_issue(
                    issue.description
                )
                print(ai_result)
                for line in ai_result.split("\n"):
                    line = line.strip()
                    if line.startswith("Category:"):
                        issue.category = (
                            line.replace(
                                "Category:",
                                ""
                            ).strip()
                        )
                    elif line.startswith("Priority:"):
                        issue.priority = (
                            line.replace(
                                "Priority:",
                                ""
                            ).strip().lower()
                        )
                    elif line.startswith("Summary:"):
                        issue.summary = (
                            line.replace(
                                "Summary:",
                                ""
                            ).strip()
                        )
            except Exception as e:
                print("Gemini Error:", e)
            issue.save()
            current_user.points += 10
            current_user.save()
            authority = UserProfile.objects.filter(
                role="authority"
            ).first()
            if authority and authority.email:
                message = f"""
A new civic issue has been reported.
Title:
{issue.title}
Category:
{issue.category}
Priority:
{issue.priority}
Summary:
{issue.summary}
Location:
{issue.location}
Reported By:
{current_user.name}
Please login to Community Hero to review the issue.
"""
                send_mail(
                    "New Civic Issue Reported",
                    message,
                    settings.EMAIL_HOST_USER,
                    [authority.email],
                    fail_silently=False,
                )
            messages.success(
                request,
                "Issue reported successfully!"
            )
            return redirect(
                "issue_detail",
                issue_id=issue.id
            )
    else:
        form = IssueForm()
    return render(
        request,
        "Issues/create_issue.html",
        {
            "form": form,
            "current_user": current_user,
        }
    )

def issue_list(request):
    query = request.GET.get("q")
    status = request.GET.get("status")
    issues = Issue.objects.all().order_by("-created_at")
    if query:
        issues = issues.filter(
            title__icontains=query
        )
    if status:
        issues = issues.filter(
            status=status
        )
    current_user = UserProfile.objects.get(
    id=request.session["user_id"]
)
    return render(
        request,
        "Issues/issue_list.html",
        {
            "issues": issues,
            "current_user": current_user
        }
    )

def issue_detail(request, issue_id):
    issue = get_object_or_404(
        Issue,
        id=issue_id
    )
    current_user = UserProfile.objects.get(
        id=request.session["user_id"]
    )
    if request.method == "POST" and current_user.role == "citizen":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.issue = issue
            comment.user = current_user
            comment.save()
            current_user.points += 2
            current_user.save()
            return redirect(
                "issue_detail",
                issue_id=issue.id
            )
    else:
        form = CommentForm()
    upvotes = issue.verifications.filter(
        vote="upvote"
    ).count()
    downvotes = issue.verifications.filter(
        vote="downvote"
    ).count()
    update_form = AuthorityUpdateForm(
        initial={
            "status": issue.status
        }
    )
    return render(
        request,
        "Issues/issue_detail.html",
        {
            "issue": issue,
            "form": form,
            "update_form": update_form,
            "upvotes": upvotes,
            "downvotes": downvotes,
            "current_user": current_user,
        }
    )

def verify_issue(request, issue_id, vote_type):
    issue = get_object_or_404(
        Issue,
        id=issue_id
    )
    user = UserProfile.objects.get(
        id=request.session["user_id"]
    )
    existing_vote = Verification.objects.filter(
        user=user,
        issue=issue
    ).first()
    if not existing_vote:
        Verification.objects.create(
            user=user,
            issue=issue,
            vote=vote_type
        )
        user.points += 1
        user.save()
    return redirect(
        "issue_detail",
        issue_id=issue.id
    )
     
def add_authority_update(request, issue_id):

    issue = get_object_or_404(
        Issue,
        id=issue_id
    )

    user = UserProfile.objects.get(
        id=request.session["user_id"]
    )

    if user.role not in ["authority", "admin"]:

        messages.error(
            request,
            "Only Authority or Admin users can add authority updates."
        )

        return redirect("issue_list")

    if request.method == "POST":

        form = AuthorityUpdateForm(request.POST)

        if form.is_valid():

            update = form.save(commit=False)

            update.issue = issue
            update.authority = user

            update.save()

            issue.status = form.cleaned_data["status"]
            issue.save()

            # Give authority points
            if issue.status == "verified":
                user.points += 5

            elif issue.status == "in_progress":
                user.points += 5

            elif issue.status == "resolved":
                user.points += 10

            user.save()

            # Citizen notification
            Notification.objects.create(
                user=issue.reporter,
                message=f"Your issue '{issue.title}' has been updated to '{issue.status}'."
            )

            # Authority notification
            Notification.objects.create(
                user=user,
                message=f"You updated '{issue.title}' to '{issue.status}'."
            )

            # Email to citizen
            if issue.reporter.email:

                message = f"""
Hello {issue.reporter.name},

Your reported issue has been updated by the authority.

Issue Details

Title: {issue.title}

Category: {issue.category}

Location: {issue.location}

Current Status: {issue.status}

You can login to Community Hero to view more details.

Thank you for helping improve your community.

Community Hero Team
"""

                send_mail(
                    "Community Hero - Issue Status Updated",
                    message,
                    settings.EMAIL_HOST_USER,
                    [issue.reporter.email],
                    fail_silently=False,
                )

            messages.success(
                request,
                "Issue status updated successfully."
            )

    return redirect(
        "issue_detail",
        issue_id=issue.id
    )

def dashboard(request):
    total_issues = Issue.objects.count()
    pending = Issue.objects.filter(
        status="pending"
    ).count()
    verified = Issue.objects.filter(
        status="verified"
    ).count()
    in_progress = Issue.objects.filter(
        status="in_progress"
    ).count()
    resolved = Issue.objects.filter(
        status="resolved"
    ).count()
    total_comments = Comment.objects.count()
    total_votes = Verification.objects.count()
    return render(
        request,
        "Issues/dashboard.html",
        {
            "total_issues": total_issues,
            "pending": pending,
            "verified": verified,
            "in_progress": in_progress,
            "resolved": resolved,
            "total_comments": total_comments,
            "total_votes": total_votes,
        }
    )

def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            token = str(uuid.uuid4())
            user.verification_token = token
            user.is_verified = False
            user.save()
            verification_link = request.build_absolute_uri(
                reverse(
                    "verify_email",
                    args=[token]
                )
            )
            message = f"""
Hello {user.name},
Welcome to Community Hero!
Please verify your email by clicking the link below:
{verification_link}
If you did not create this account, please ignore this email.
Community Hero Team
"""
            send_mail(
                "Verify Your Community Hero Account",
                message,
                settings.EMAIL_HOST_USER,
                [user.email],
                fail_silently=False,
            )
            return render(
                request,
                "Issues/check_email.html",
                {
                    "email": user.email
                }
            )
    else:
        form = RegisterForm()
    return render(
        request,
        "Issues/register.html",
        {
            "form": form
        }
    )

def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]
            user = UserProfile.objects.filter(
                email=email,
                password=password
            ).first()
            if not user:
                return render(
                    request,
                    "Issues/login.html",
                    {
                        "form": form,
                        "error": "Invalid email or password"
                    }
                )
            if not user.is_verified:
                verification_link = request.build_absolute_uri(
                    reverse(
                        "verify_email",
                        args=[user.verification_token]
                    )
                )
                send_mail(
                    "Verify Your Community Hero Account",
                    f"""
Hello {user.name},
Your email address has not been verified yet.
Click the link below to verify your account:
{verification_link}
Community Hero Team
""",
                    settings.EMAIL_HOST_USER,
                    [user.email],
                    fail_silently=False,
                )
                return render(
                    request,
                    "Issues/login.html",
                    {
                        "form": form,
                        "error": "Your email is not verified. A new verification email has been sent to your inbox."
                    }
                )
            otp = str(random.randint(100000, 999999))
            user.login_otp = otp
            user.otp_verified = False
            user.save()
            send_mail(
                "Community Hero Login OTP",
                f"""
Hello {user.name},
Your login OTP is:
{otp}
This OTP is valid for one login only.
Community Hero Team
""",
                settings.EMAIL_HOST_USER,
                [user.email],
                fail_silently=False,
            )
            request.session["otp_user"] = user.id
            return redirect("verify_login_otp")
    else:
        form = LoginForm()
    return render(
        request,
        "Issues/login.html",
        {
            "form": form
        }
    )

def logout_view(request):
    request.session.flush()
    return render(
        request,
        "Issues/logout_success.html"
    )

def leaderboard(request):

    query = request.GET.get("q", "")

    citizens = UserProfile.objects.filter(
        role="citizen"
    )

    authorities = UserProfile.objects.filter(
        role="authority"
    )

    if query:

        citizens = citizens.filter(
            name__icontains=query
        )

        authorities = authorities.filter(
            name__icontains=query
        )

    citizens = citizens.order_by("-points")
    authorities = authorities.order_by("-points")

    return render(
        request,
        "Issues/leaderboard.html",
        {
            "citizens": citizens,
            "authorities": authorities,
            "query": query,
        }
    )
def profile(request):

    user = get_object_or_404(
        UserProfile,
        id=request.session["user_id"]
    )

    # Calculate rank within the same role
    if user.role == "citizen":

        leaderboard = UserProfile.objects.filter(
            role="citizen"
        ).order_by("-points")

    else:

        leaderboard = UserProfile.objects.filter(
            role="authority"
        ).order_by("-points")

    rank = 1

    for u in leaderboard:

        if u.id == user.id:
            break

        rank += 1


    if user.role == "citizen":

        total_issues = Issue.objects.filter(
            reporter=user
        ).count()

        total_comments = Comment.objects.filter(
            user=user
        ).count()

        my_issues = Issue.objects.filter(
            reporter=user
        ).order_by("-created_at")

        my_comments = Comment.objects.filter(
            user=user
        ).order_by("-created_at")[:5]

        return render(
            request,
            "Issues/profile.html",
            {
                "user": user,
                "rank": rank,
                "total_issues": total_issues,
                "total_comments": total_comments,
                "my_issues": my_issues,
                "my_comments": my_comments,
            }
        )

    

    authority_updates = AuthorityUpdate.objects.filter(
        authority=user
    ).order_by("-created_at")[:5]

    total_updates = AuthorityUpdate.objects.filter(
        authority=user
    ).count()

    pending = Issue.objects.filter(
        status="pending"
    ).count()

    verified = Issue.objects.filter(
        status="verified"
    ).count()

    in_progress = Issue.objects.filter(
        status="in_progress"
    ).count()

    resolved = Issue.objects.filter(
        status="resolved"
    ).count()

    return render(
        request,
        "Issues/profile.html",
        {
            "user": user,
            "rank": rank,
            "total_updates": total_updates,
            "authority_updates": authority_updates,
            "pending": pending,
            "verified": verified,
            "in_progress": in_progress,
            "resolved": resolved,
        }
    )

def authority_dashboard(request):
    user = UserProfile.objects.get(
        id=request.session["user_id"]
    )
    if user.role not in ["authority", "admin"]:
        messages.error(
            request,
            "Only Authority or Admin users can access this page."
        )
        return redirect("issue_list")
    total_issues = Issue.objects.count()
    pending = Issue.objects.filter(
        status="pending"
    ).count()
    verified = Issue.objects.filter(
        status="verified"
    ).count()
    in_progress = Issue.objects.filter(
        status="in_progress"
    ).count()
    resolved = Issue.objects.filter(
        status="resolved"
    ).count()
    recent_issues = Issue.objects.order_by(
        "-created_at"
    )[:5]
    return render(
        request,
        "Issues/authority_dashboard.html",
        {
            "user": user,
            "total_issues": total_issues,
            "pending": pending,
            "verified": verified,
            "in_progress": in_progress,
            "resolved": resolved,
            "recent_issues": recent_issues,
        }
    )

from django.urls import reverse
from django.core.mail import send_mail
from django.conf import settings


def forgot_password(request):
    if request.method == "POST":
        email = request.POST.get("email")

        user = UserProfile.objects.filter(
            email=email
        ).first()

        if not user:
            return render(
                request,
                "Issues/forgot_password.html",
                {
                    "error": "No account found with this email."
                }
            )

        # Create the correct Render URL automatically
        reset_link = request.build_absolute_uri(
            reverse(
                "reset_password",
                args=[user.id]
            )
        )

        message = f"""
Hello {user.name},

We received a request to reset your password.

Click the link below to reset your password:

{reset_link}

If you did not request this, please ignore this email.

Community Hero Team
"""

        send_mail(
            "Community Hero Password Reset",
            message,
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False,
        )

        return render(
            request,
            "Issues/email_sent.html"
        )

    return render(
        request,
        "Issues/forgot_password.html"
    )

def change_password(request):
    user = UserProfile.objects.get(
        id=request.session["user_id"]
    )
    if request.method == "POST":
        current_password = request.POST.get(
            "current_password"
        )
        new_password = request.POST.get(
            "new_password"
        )
        confirm_password = request.POST.get(
            "confirm_password"
        )
        if current_password != user.password:
            return render(
                request,
                "Issues/change_password.html",
                {
                    "error":
                    "Current password is incorrect."
                }
            )
        if new_password != confirm_password:
            return render(
                request,
                "Issues/change_password.html",
                {
                    "error":
                    "Passwords do not match."
                }
            )
        user.password = new_password
        user.save()
        return render(
            request,
            "Issues/change_password_success.html"
        )
    return render(
        request,
        "Issues/change_password.html"
    )

def test_email(request):
    send_mail(
        "Test Email",
        "Email system is working.",
        settings.EMAIL_HOST_USER,
        [settings.EMAIL_HOST_USER],
        fail_silently=False,
    )
    return HttpResponse(
        "Email sent"
    )

def reset_password(request, user_id):
    user = UserProfile.objects.get(
        id=user_id
    )
    if request.method == "POST":
        new_password = request.POST.get(
            "new_password"
        )
        confirm_password = request.POST.get(
            "confirm_password"
        )
        if new_password != confirm_password:
            return render(
                request,
                "Issues/reset_password.html",
                {
                    "error":
                    "Passwords do not match."
                }
            )

        user.password = new_password
        user.save()
        return render(
            request,
            "Issues/password_reset_success.html"
        )
    return render(
        request,
        "Issues/reset_password.html"
    )


def notifications(request):

    user = UserProfile.objects.get(
        id=request.session["user_id"]
    )

    print("Logged in user:", user.name)
    print("Role:", user.role)
    print("User ID:", user.id)

    notifications = Notification.objects.filter(
        user=user
    ).order_by("-created_at")

    notifications.update(is_read=True)

    return render(
        request,
        "Issues/notifications.html",
        {
            "notifications": notifications,
            "unread": 0,
        }
    )

def verify_email(request, token):
    user = UserProfile.objects.filter(
        verification_token=token
    ).first()
    if not user:
        return render(
            request,
            "Issues/verification_failed.html"
        )
    user.is_verified = True
    user.verification_token = ""
    user.save()
    return render(
        request,
        "Issues/register_success.html",
        {
            "user": user
        }
    )

def verify_login_otp(request):
    if "otp_user" not in request.session:
        return redirect("login")
    user = UserProfile.objects.get(
        id=request.session["otp_user"]
    )
    if request.method == "POST":
        entered_otp = request.POST.get("otp")
        if entered_otp == user.login_otp:
            user.otp_verified = True
            user.login_otp = ""
            user.save()
            request.session["user_id"] = user.id
            del request.session["otp_user"]
            if user.role == "authority":
                return redirect("authority_dashboard")
            else:
                return redirect("dashboard")
        else:
            return render(
                request,
                "Issues/verify_login_otp.html",
                {
                    "error": "Invalid OTP"
                }
            )
    return render(
        request,
        "Issues/verify_login_otp.html"
    )

def home(request):
    return render(
        request,
        "Issues/home.html"
    )


def edit_profile(request):

    user = UserProfile.objects.get(
        id=request.session["user_id"]
    )

    if request.method == "POST":

        print("POST received")
        print("FILES:", request.FILES)

        form = ProfileUpdateForm(
            request.POST,
            request.FILES,
            instance=user
        )

        if form.is_valid():

            print("FORM VALID")

            saved_user = form.save()

            print("Saved picture:", saved_user.profile_picture)

            messages.success(
                request,
                "Profile updated successfully."
            )

            return redirect("profile")

        else:

            print(form.errors)

    else:

        form = ProfileUpdateForm(
            instance=user
        )

    return render(
        request,
        "Issues/edit_profile.html",
        {
            "form": form
        }
    )

def remove_profile_picture(request):

    user = UserProfile.objects.get(
        id=request.session["user_id"]
    )

    if user.profile_picture:
        user.profile_picture.delete(save=False)
        user.profile_picture = None
        user.save()

    messages.success(
        request,
        "Profile picture removed successfully."
    )

    return redirect("profile")