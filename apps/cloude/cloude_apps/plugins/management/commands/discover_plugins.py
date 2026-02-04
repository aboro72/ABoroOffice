"""
Management command to discover and optionally activate apps.cloude.cloude_apps.plugins.
"""

from django.core.management.base import BaseCommand, CommandError
from apps.cloude.cloude_apps.plugins.loader import PluginLoader
from apps.cloude.cloude_apps.plugins.models import Plugin


class Command(BaseCommand):
    help = 'Discover plugins from the installed folder and optionally activate them'

    def add_arguments(self, parser):
        parser.add_argument(
            '--activate',
            action='store_true',
            help='Automatically activate newly discovered plugins',
        )
        parser.add_argument(
            '--slug',
            type=str,
            help='Only process plugin with this slug',
        )

    def handle(self, *args, **options):
        loader = PluginLoader()

        self.stdout.write('Discovering apps.cloude.cloude_apps.plugins...')
        discovered = loader.discover_plugins()

        if not discovered:
            self.stdout.write(self.style.WARNING('No plugins found.'))
            return

        for item in discovered:
            plugin = item['plugin']
            created = item['created']

            if options['slug'] and plugin.slug != options['slug']:
                continue

            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'  NEW: {plugin.name} v{plugin.version} (slug: {plugin.slug})')
                )
            else:
                self.stdout.write(f'  EXISTS: {plugin.name} v{plugin.version}')

            if options['activate'] and not plugin.enabled:
                try:
                    loader.load_plugin(str(plugin.id))
                    self.stdout.write(
                        self.style.SUCCESS(f'    -> Activated!')
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'    -> Activation failed: {e}')
                    )

        self.stdout.write(self.style.SUCCESS(f'\nTotal: {len(discovered)} plugins discovered.'))
