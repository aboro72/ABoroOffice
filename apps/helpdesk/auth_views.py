"""
Authentication and account views for HelpDesk integration.
Uses ABoroUser as AUTH_USER_MODEL.
"""

from django import forms
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model, login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.shortcuts import redirect, render, get_object_or_404

User = get_user_model()


class HelpdeskLoginView(DjangoLoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['app_title'] = 'Helpdesk'
        return context


class RegistrationForm(forms.Form):
    first_name = forms.CharField(max_length=100)
    last_name = forms.CharField(max_length=100)
    email = forms.EmailField()
    phone = forms.CharField(max_length=20)
    username = forms.CharField(max_length=150)
    department = forms.CharField(max_length=100, required=False)
    location = forms.CharField(max_length=100, required=False)
    password = forms.CharField(min_length=8)
    password_confirm = forms.CharField(min_length=8)


def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            if data['password'] != data['password_confirm']:
                messages.error(request, _("Passwörter stimmen nicht überein."))
            elif User.objects.filter(username=data['username']).exists():
                messages.error(request, _("Benutzername ist bereits vergeben."))
            elif User.objects.filter(email=data['email']).exists():
                messages.error(request, _("E-Mail ist bereits registriert."))
            else:
                user = User.objects.create_user(
                    username=data['username'],
                    email=data['email'],
                    password=data['password'],
                    first_name=data['first_name'],
                    last_name=data['last_name'],
                )
                user.phone = data['phone']
                user.department = data.get('department') or ''
                user.location = data.get('location') or ''
                user.role = 'customer'
                user.save()

                messages.success(request, _("Konto erstellt. Bitte anmelden."))
                return redirect('helpdesk_accounts:login')
        else:
            messages.error(request, _("Bitte prüfen Sie Ihre Eingaben."))
    else:
        form = RegistrationForm()

    return render(request, 'accounts/register.html', {'form': form, 'app_title': 'Helpdesk'})


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'department', 'location']


@login_required
def profile_edit(request):
    profile_form = ProfileForm(instance=request.user)
    password_form = PasswordChangeForm(user=request.user)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'profile':
            profile_form = ProfileForm(request.POST, instance=request.user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, _("Profil aktualisiert."))
                return redirect('helpdesk_accounts:profile_edit')
            messages.error(request, _("Profil konnte nicht gespeichert werden."))
        elif action == 'password':
            password_form = PasswordChangeForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, _("Passwort aktualisiert."))
                return redirect('helpdesk_accounts:profile_edit')
            messages.error(request, _("Passwort konnte nicht geändert werden."))

    return render(
        request,
        'accounts/profile_edit.html',
        {
            'profile_form': profile_form,
            'password_form': password_form,
            'app_title': 'Helpdesk',
        }
    )


@login_required
def user_detail(request, user_id):
    target_user = get_object_or_404(User, id=user_id)
    can_edit = request.user.is_superuser or request.user.is_staff
    return render(
        request,
        'accounts/user_management/user_detail.html',
        {
            'target_user': target_user,
            'can_edit': can_edit,
            'app_title': 'Helpdesk',
        }
    )
