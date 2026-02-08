# Plugin Developer Guide

This guide explains how to build and package plugins for the CloudService module.

## Overview
Plugins can add:
- Dashboard widgets
- File preview providers
- Custom menu items and file actions
- Settings screens

Plugins are discovered from `plugins/installed/` and can also be uploaded as ZIP via the Admin Settings page.

## Minimal Structure
```
my_plugin/
??? __init__.py
??? plugin.json
??? apps.py
??? widget.py              # optional
??? handlers.py            # optional
??? templates/
    ??? my_plugin/
        ??? widget.html
```

## plugin.json
```json
{
  "name": "My Plugin",
  "slug": "my-plugin",
  "version": "1.0.0",
  "author": "Your Name",
  "description": "What the plugin does",
  "django_app": {
    "app_config": "my_plugin.apps.MyPluginConfig"
  },
  "hooks": {
    "ui_dashboard_widget": {
      "handler": "my_plugin.widget.MyWidgetProvider",
      "priority": 10
    }
  },
  "settings": {
    "has_settings": true,
    "schema": {
      "api_key": {
        "type": "password",
        "label": "API Key",
        "required": true
      }
    }
  }
}
```

Required fields:
- `name`, `slug`, `version`
- `django_app.app_config`

## AppConfig & Hooks
```python
from django.apps import AppConfig
from apps.cloude.cloude_apps.plugins.hooks import hook_registry, UI_DASHBOARD_WIDGET
from .widget import MyWidgetProvider

class MyPluginConfig(AppConfig):
    name = 'my_plugin'

    def ready(self):
        hook_registry.register(UI_DASHBOARD_WIDGET, MyWidgetProvider, priority=10)
```

## Widgets
```python
from apps.cloude.cloude_apps.plugins.widgets import DashboardWidgetProvider

class MyWidgetProvider(DashboardWidgetProvider):
    widget_id = "my_widget"
    widget_name = "My Widget"
    widget_icon = "bi-star"
    widget_size = "medium"  # small | medium | large
    widget_order = 50

    def get_context(self, request):
        return {"message": "Hello"}

    def get_template_name(self):
        return "my_plugin/widget.html"
```

## File Preview Providers
Implement a handler that can render previews for custom file types.

## Settings
Use `plugin.settings` to read persisted settings.
```python
from apps.cloude.cloude_apps.plugins.models import Plugin
plugin = Plugin.objects.get(slug='my-plugin')
api_key = plugin.settings.get('api_key', '')
```

## Packaging
ZIP the plugin folder (folder at the root of the ZIP):
```
my_plugin.zip
??? my_plugin/
    ??? __init__.py
    ??? plugin.json
    ??? apps.py
```

## Troubleshooting
- Check server logs for PluginLoader errors
- Verify `plugin.json` is valid JSON
- Ensure `slug` is unique


## Hello World Example
A minimal widget plugin that shows a greeting.

### Folder Structure
```
hello_widget/
??? __init__.py
??? plugin.json
??? apps.py
??? widget.py
??? templates/
    ??? hello_widget/
        ??? widget.html
```

### __init__.py
```python
default_app_config = 'hello_widget.apps.HelloWidgetConfig'
```

### plugin.json
```json
{
  "name": "Hello Widget",
  "slug": "hello-widget",
  "version": "1.0.0",
  "author": "Your Team",
  "description": "Adds a hello widget to the dashboard",
  "django_app": {
    "app_config": "hello_widget.apps.HelloWidgetConfig"
  },
  "hooks": {
    "ui_dashboard_widget": {
      "handler": "hello_widget.widget.HelloWidgetProvider",
      "priority": 20
    }
  }
}
```

### apps.py
```python
from django.apps import AppConfig
from apps.cloude.cloude_apps.plugins.hooks import hook_registry, UI_DASHBOARD_WIDGET
from .widget import HelloWidgetProvider

class HelloWidgetConfig(AppConfig):
    name = 'hello_widget'

    def ready(self):
        hook_registry.register(UI_DASHBOARD_WIDGET, HelloWidgetProvider, priority=20)
```

### widget.py
```python
from apps.cloude.cloude_apps.plugins.widgets import DashboardWidgetProvider

class HelloWidgetProvider(DashboardWidgetProvider):
    widget_id = "hello_widget"
    widget_name = "Hello Widget"
    widget_icon = "bi-emoji-smile"
    widget_size = "medium"
    widget_order = 20

    def get_context(self, request):
        return {"message": f"Hallo {request.user.username}!"}

    def get_template_name(self):
        return "hello_widget/widget.html"
```

### templates/hello_widget/widget.html
```html
<div class="text-center py-3">
  <i class="bi bi-emoji-smile text-primary"></i>
  <h5 class="mt-2">{{ widget_context.message }}</h5>
  <small class="text-muted">Bereitgestellt durch Hello Widget</small>
</div>
```


## Plugin Template Folder
A ready-to-zip template is available at:
- `plugins/templates/hello_widget/`

You can zip the folder and upload it via the Admin Settings page.

## Demo Template Download
A downloadable demo template (ZIP) is available:
- `static/plugin-templates/demo_widget.zip`

This template includes:
- Settings schema example (title + city)
- Widget rendering with settings
