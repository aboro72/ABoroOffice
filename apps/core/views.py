"""
Views for the Core app
"""

from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.contrib import messages
from pathlib import Path
from apps.core.forms import ThemeSettingsForm, BrandingSettingsForm, AppTogglesForm
from apps.helpdesk.helpdesk_apps.admin_panel.models import SystemSettings


class HomeView(TemplateView):
    """Home page view"""
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Home - ABoroOffice'
        return context


class DashboardView(LoginRequiredMixin, TemplateView):
    """General dashboard after login."""
    template_name = 'dashboard.html'


class AdminDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Standalone admin dashboard (not Django admin)."""
    template_name = 'admin_dashboard.html'

    def test_func(self):
        return self.request.user.is_superuser or self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        settings_obj = SystemSettings.get_settings()
        context['theme_form'] = ThemeSettingsForm(instance=settings_obj)
        context['branding_form'] = BrandingSettingsForm(instance=settings_obj)
        context['app_toggles_form'] = AppTogglesForm(system_settings=settings_obj)

        # Plugin data
        try:
            from apps.cloude.cloude_apps.plugins.models import Plugin, PluginLog
            context['plugins'] = Plugin.objects.all().order_by('-uploaded_at')
            context['plugin_logs'] = PluginLog.objects.all().order_by('-created_at')[:20]
            context['has_plugins'] = Plugin.objects.exists()
        except Exception:
            context['plugins'] = []
            context['plugin_logs'] = []
            context['has_plugins'] = False

        return context

    def post(self, request, *args, **kwargs):
        if not self.test_func():
            messages.error(request, 'Access denied')
            return redirect('admin_dashboard')

        settings_obj = SystemSettings.get_settings()

        # Theme settings update
        if 'save_theme' in request.POST:
            form = ThemeSettingsForm(request.POST, instance=settings_obj)
            if form.is_valid():
                form.save()
                messages.success(request, 'Theme-Einstellungen gespeichert.')
            else:
                messages.error(request, 'Bitte prüfe die Theme-Felder.')
            return redirect('admin_dashboard')

        # Branding settings update
        if 'save_branding' in request.POST:
            form = BrandingSettingsForm(request.POST, request.FILES, instance=settings_obj)
            if form.is_valid():
                form.save()
                messages.success(request, 'Branding gespeichert.')
            else:
                messages.error(request, 'Bitte prüfe die Branding-Felder.')
            return redirect('admin_dashboard')

        # App toggles update
        if 'save_app_toggles' in request.POST:
            form = AppTogglesForm(request.POST, system_settings=settings_obj)
            if form.is_valid():
                prev = settings_obj.app_toggles or {}
                new_toggles = {
                    'approvals': bool(form.cleaned_data.get('approvals')),
                    'helpdesk': bool(form.cleaned_data.get('helpdesk', True)),
                    'cloudstorage': bool(form.cleaned_data.get('cloudstorage', True)),
                    'classroom': bool(form.cleaned_data.get('classroom', True)),
                }
                settings_obj.app_toggles = new_toggles
                settings_obj.save()

                # Archive approvals if turned off
                if prev.get('approvals', False) and not new_toggles.get('approvals', False):
                    from apps.approvals.models import Approval
                    Approval.objects.update(archived=True)

                messages.success(request, 'App-Toggles gespeichert.')
            else:
                messages.error(request, 'Bitte prüfe die App-Toggles.')
            return redirect('admin_dashboard')

        # Plugin upload
        zip_file = request.FILES.get('zip_file')
        if zip_file:
            try:
                from apps.cloude.cloude_apps.plugins.loader import PluginLoader
                from apps.cloude.cloude_apps.plugins.models import Plugin, PluginLog

                loader = PluginLoader()
                temp_path = Path('/tmp') / zip_file.name
                with open(temp_path, 'wb+') as f:
                    for chunk in zip_file.chunks():
                        f.write(chunk)

                manifest = loader.validate_zip(temp_path)
                plugin = Plugin.objects.create(
                    name=manifest['name'],
                    slug=manifest['slug'],
                    version=manifest['version'],
                    author=manifest.get('author', 'Unknown'),
                    description=manifest.get('description', ''),
                    zip_file=zip_file,
                    manifest=manifest,
                    installed_by=request.user,
                    status='inactive'
                )

                extract_dir = loader.extract_plugin(str(plugin.id), temp_path)
                plugin.extracted_path = str(extract_dir)
                plugin.save()

                PluginLog.objects.create(
                    plugin=plugin,
                    action='uploaded',
                    user=request.user,
                    message=f"Plugin uploaded by {request.user.username}"
                )

                messages.success(request, f'✅ Plugin "{plugin.name}" hochgeladen.')
            except Exception as e:
                messages.error(request, f'❌ Upload fehlgeschlagen: {str(e)}')

            return redirect('admin_dashboard')

        return redirect('admin_dashboard')


class SystemSettingsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Central system settings view."""
    template_name = 'system_settings.html'

    def test_func(self):
        return self.request.user.is_superuser or self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        settings_obj = SystemSettings.get_settings()
        context['theme_form'] = ThemeSettingsForm(instance=settings_obj)
        context['branding_form'] = BrandingSettingsForm(instance=settings_obj)
        context['app_toggles_form'] = AppTogglesForm(system_settings=settings_obj)
        return context

    def post(self, request, *args, **kwargs):
        if not self.test_func():
            messages.error(request, 'Access denied')
            return redirect('system_settings')

        settings_obj = SystemSettings.get_settings()

        if 'save_theme' in request.POST:
            form = ThemeSettingsForm(request.POST, instance=settings_obj)
            if form.is_valid():
                form.save()
                messages.success(request, 'Theme-Einstellungen gespeichert.')
            else:
                messages.error(request, 'Bitte prüfe die Theme-Felder.')
            return redirect('system_settings')

        if 'save_branding' in request.POST:
            form = BrandingSettingsForm(request.POST, request.FILES, instance=settings_obj)
            if form.is_valid():
                form.save()
                messages.success(request, 'Branding gespeichert.')
            else:
                messages.error(request, 'Bitte prüfe die Branding-Felder.')
            return redirect('system_settings')

        if 'save_app_toggles' in request.POST:
            form = AppTogglesForm(request.POST, system_settings=settings_obj)
            if form.is_valid():
                prev = settings_obj.app_toggles or {}
                new_toggles = {
                    'approvals': bool(form.cleaned_data.get('approvals')),
                    'helpdesk': bool(form.cleaned_data.get('helpdesk', True)),
                    'cloudstorage': bool(form.cleaned_data.get('cloudstorage', True)),
                    'classroom': bool(form.cleaned_data.get('classroom', True)),
                }
                settings_obj.app_toggles = new_toggles
                settings_obj.save()

                if prev.get('approvals', False) and not new_toggles.get('approvals', False):
                    from apps.approvals.models import Approval
                    Approval.objects.update(archived=True)

                messages.success(request, 'App-Toggles gespeichert.')
            else:
                messages.error(request, 'Bitte prüfe die App-Toggles.')
            return redirect('system_settings')

        return redirect('system_settings')


class ApiDocsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Unified API documentation landing page."""
    template_name = 'api_docs.html'

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser
