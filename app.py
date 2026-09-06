#!/usr/bin/env python
"""BarangayAssist single-file Django app."""
import os
import sys
import django
from django.conf import settings

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------------- 1. Settings Configuration ----------------
if not settings.configured:
    settings.configure(
        DEBUG=True,
        SECRET_KEY='barangayassist-secret-key',
        ROOT_URLCONF=__name__,
        ALLOWED_HOSTS=['*'],
        LOGIN_REDIRECT_URL='dashboard',
        LOGOUT_REDIRECT_URL='index',
        LOGIN_URL='index',
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'django.contrib.auth',
            'django.contrib.sessions',
            'django.contrib.messages',
            'django.contrib.staticfiles',
            __name__,
        ],
        MIDDLEWARE=[
            'django.middleware.security.SecurityMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.middleware.common.CommonMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
        ],
        TEMPLATES=[{
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [os.path.join(BASE_DIR, 'templates')],
            'APP_DIRS': True,
            'OPTIONS': {
                'context_processors': [
                    'django.template.context_processors.debug',
                    'django.template.context_processors.request',
                    'django.contrib.auth.context_processors.auth',
                    'django.contrib.messages.context_processors.messages',
                ],
            },
        }],
        STATIC_URL='/static/',
        STATICFILES_DIRS=[os.path.join(BASE_DIR, 'static')],
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
            }
        }
    )

django.setup()

# Auto-run built-in migrations
from django.core.management import call_command
try:
    call_command('migrate', run_syncdb=True, verbosity=0)
except Exception:
    pass

# ---------------- 2. Django Imports & User Customization ----------------
from django.db import models, connection
from django import forms
from django.views import View
from django.shortcuts import render, redirect
from django.urls import path
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.management import execute_from_command_line
from django.conf.urls.static import static

# Helper method to retrieve clean Full Name
def get_clean_name(self):
    full_name = f"{self.first_name} {self.last_name}".strip()
    if full_name and '@' not in full_name:
        return full_name.title()
    
    clean_handle = self.username.split('@')[0].replace('.', ' ').replace('_', ' ')
    return clean_handle.title()

User.add_to_class('get_clean_name', get_clean_name)

# Helper function to fix names and assign Last Name in DB
def fix_user_db_name(user):
    if user:
        # Direct fix para sa kasamtangan nga Ashley account
        if 'ashley' in user.username.lower() and not user.last_name:
            user.first_name = "Ashley"
            user.last_name = "Cuarenta"
            user.save()
            return

        if not user.first_name or '@' in user.first_name:
            clean_handle = user.username.split('@')[0].replace('.', ' ').replace('_', ' ')
            parts = clean_handle.split(' ', 1)
            user.first_name = parts[0].title()
            user.last_name = parts[1].title() if len(parts) > 1 else ''
            user.save()

# ---------------- 3. Models ----------------
class Concern(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Resolved', 'Resolved'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=100, default='General')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = '__main__'

    def __str__(self):
        return str(self.title)

try:
    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(Concern)
except Exception:
    pass

# ---------------- 4. Forms ----------------
class ConcernForm(forms.ModelForm):
    class Meta:
        model = Concern
        fields = ['title', 'description', 'category']

# ---------------- 5. Views ----------------
class IndexView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return render(request, 'index.html')

class LoginView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return render(request, 'index.html')

    def post(self, request):
        u = request.POST.get('username') or request.POST.get('email') or request.POST.get('loginEmail')
        p = request.POST.get('password') or request.POST.get('loginPassword')
        user = authenticate(request, username=u, password=p)
        if user is not None:
            fix_user_db_name(user)
            login(request, user)
            return redirect('dashboard')
        return redirect('index')

class RegisterView(View):
    def post(self, request):
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        
        if email and password and not User.objects.filter(username=email).exists():
            if not name or '@' in name:
                name = email.split('@')[0].replace('.', ' ').replace('_', ' ')
            
            name_parts = name.split(' ', 1)
            first_name = name_parts[0].title() if name_parts else ''
            last_name = name_parts[1].title() if len(name_parts) > 1 else ''

            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            user.save()
            login(request, user)
            return redirect('dashboard')
            
        return redirect('index')

class DashboardView(LoginRequiredMixin, View):
    login_url = 'index'

    def get(self, request):
        fix_user_db_name(request.user)
        concerns = Concern.objects.all().order_by('-created_at')
        context = {
            'concerns': concerns,
            'pending_count': concerns.filter(status='Pending').count(),
            'in_progress_count': concerns.filter(status='In Progress').count(),
            'resolved_count': concerns.filter(status='Resolved').count(),
        }
        return render(request, 'dashboard.html', context)

class SubmitConcernView(View):
    def get(self, request):
        form = ConcernForm()
        return render(request, 'submit_concern.html', {'form': form})

    def post(self, request):
        form = ConcernForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
        return render(request, 'submit_concern.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('index')

# ---------------- 6. URLs ----------------
urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('login/', LoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('submit_concern/', SubmitConcernView.as_view(), name='submit_concern'),
    path('logout/', logout_view, name='logout'),
] + static(settings.STATIC_URL, document_root=os.path.join(BASE_DIR, 'static'))

if __name__ == '__main__':
    execute_from_command_line(sys.argv)