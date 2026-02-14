"""
REST API Views for CloudService.
Django REST Framework with comprehensive CRUD operations.
"""

from rest_framework import viewsets, status, generics, filters, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.db.models import Q, Count, Sum
from django.http import FileResponse
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.contrib.auth import get_user_model

from apps.cloude.cloude_apps.core.models import StorageFile, StorageFolder, FileVersion, ActivityLog, Notification
from apps.cloude.cloude_apps.accounts.models import UserProfile
from apps.cloude.cloude_apps.sharing.models import UserShare, PublicLink, SharePermission
from apps.cloude.cloude_apps.storage.models import StorageStats
from apps.cloude.cloude_apps.api.serializers import (
    StorageFileSerializer, StorageFileDetailSerializer, StorageFolderSerializer,
    FileVersionSerializer, UserShareSerializer, PublicLinkSerializer,
    ActivityLogSerializer, NotificationSerializer, UserSerializer,
    StorageStatsSerializer, FileUploadSerializer, BulkDeleteSerializer,
    SearchResultSerializer, StorageQuotaSerializer,
    RestoreFileVersionRequestSerializer, RestoreFileVersionResponseSerializer,
    MessageResponseSerializer, UpdateSharePermissionRequestSerializer,
    SetPublicLinkPasswordRequestSerializer
)
from apps.cloude.cloude_apps.api.permissions import IsFileOwnerOrShared, IsPublicLinkValid
from drf_spectacular.utils import extend_schema, OpenApiTypes, OpenApiExample
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class StandardResultsSetPagination(PageNumberPagination):
    """Custom pagination for API"""
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 100


class StorageFileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for file operations.
    Supports CRUD operations with permissions.
    """
    serializer_class = StorageFileSerializer
    queryset = StorageFile.objects.all()
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'updated_at', 'size', 'name']
    ordering = ['-created_at']

    def get_queryset(self):
        """Get files for current user"""
        user = self.request.user
        # Get IDs of files shared with this user via UserShare (which uses GenericForeignKey)
        from django.contrib.contenttypes.models import ContentType
        file_content_type = ContentType.objects.get_for_model(StorageFile)
        shared_file_ids = UserShare.objects.filter(
            shared_with=user,
            content_type=file_content_type,
            is_active=True
        ).values_list('object_id', flat=True)

        return StorageFile.objects.filter(
            Q(owner=user) | Q(id__in=shared_file_ids)
        ).distinct()

    def get_serializer_class(self):
        """Use detailed serializer for retrieve"""
        if self.action == 'retrieve':
            return StorageFileDetailSerializer
        return StorageFileSerializer

    def perform_create(self, serializer):
        """Create file with current user as owner"""
        serializer.save(owner=self.request.user)
        # Log activity
        ActivityLog.objects.create(
            user=self.request.user,
            activity_type='upload',
            file=serializer.instance,
            description=f"Uploaded file: {serializer.instance.name}",
            ip_address=self.get_client_ip()
        )

    def perform_update(self, serializer):
        """Update file"""
        serializer.save()
        ActivityLog.objects.create(
            user=self.request.user,
            activity_type='rename',
            file=serializer.instance,
            description=f"Updated file: {serializer.instance.name}",
            ip_address=self.get_client_ip()
        )

    def perform_destroy(self, instance):
        """Delete file"""
        ActivityLog.objects.create(
            user=self.request.user,
            activity_type='delete',
            file=instance,
            description=f"Deleted file: {instance.name}",
            ip_address=self.get_client_ip()
        )
        instance.delete()

    @action(detail=True, methods=['post'])
    def download(self, request, pk=None):
        """Download file"""
        file_obj = self.get_object()

        # Check permissions
        if file_obj.owner != request.user:
            share = UserShare.objects.filter(
                shared_with=request.user,
                object_id=file_obj.id,
                content_type__model='storagefile',
                is_active=True
            ).first()
            if not share or not share.can_download():
                raise PermissionDenied("You don't have permission to download this file")

        file_obj.increment_download_count()
        ActivityLog.objects.create(
            user=request.user,
            activity_type='download',
            file=file_obj,
            description=f"Downloaded: {file_obj.name}",
            ip_address=self.get_client_ip()
        )

        response = FileResponse(file_obj.file.open('rb'), as_attachment=True)
        response['Content-Disposition'] = f'attachment; filename="{file_obj.name}"'
        return response

    @action(detail=True, methods=['post'])
    def star(self, request, pk=None):
        """Star/unstar file"""
        file_obj = self.get_object()
        file_obj.is_starred = not file_obj.is_starred
        file_obj.save()
        return Response({
            'is_starred': file_obj.is_starred
        })

    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """Create duplicate of file"""
        original = self.get_object()

        # Create new file instance
        import shutil
        import os

        duplicate = StorageFile.objects.create(
            owner=request.user,
            folder=original.folder,
            name=f"{original.name} (copy)",
            size=original.size
        )

        # Copy file content
        duplicate.file.save(
            os.path.basename(original.file.name),
            original.file.open('rb'),
            save=True
        )

        serializer = self.get_serializer(duplicate)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def get_client_ip(self):
        """Get client IP address"""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip


class StorageFolderViewSet(viewsets.ModelViewSet):
    """ViewSet for folder operations"""
    serializer_class = StorageFolderSerializer
    queryset = StorageFolder.objects.all()
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering = ['-created_at']

    def get_queryset(self):
        """Get folders for current user"""
        return StorageFolder.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        """Create folder with current user as owner"""
        serializer.save(owner=self.request.user)
        ActivityLog.objects.create(
            user=self.request.user,
            activity_type='create_folder',
            folder=serializer.instance,
            description=f"Created folder: {serializer.instance.name}"
        )

    @action(detail=True, methods=['get'])
    def contents(self, request, pk=None):
        """Get folder contents"""
        folder = self.get_object()

        subfolders = folder.subfolders.all()
        files = folder.files.all()

        folder_serializer = StorageFolderSerializer(subfolders, many=True)
        file_serializer = StorageFileSerializer(files, many=True)

        return Response({
            'folders': folder_serializer.data,
            'files': file_serializer.data
        })


class FileVersionsView(generics.ListAPIView):
    """Get file versions"""
    serializer_class = FileVersionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        """Get versions for specific file"""
        file_id = self.kwargs.get('file_id')
        return FileVersion.objects.filter(file_id=file_id).order_by('-version_number')


class RestoreFileVersionView(generics.GenericAPIView):
    """Restore file to previous version"""
    permission_classes = [IsAuthenticated]
    serializer_class = RestoreFileVersionRequestSerializer

    @extend_schema(
        request=RestoreFileVersionRequestSerializer,
        responses=RestoreFileVersionResponseSerializer,
        examples=[
            OpenApiExample(
                'Restore Version',
                value={'version_id': 3},
                request_only=True
            ),
            OpenApiExample(
                'Restore OK',
                value={'message': 'File restored successfully', 'version_number': 4},
                response_only=True
            )
        ],
    )
    def post(self, request, file_id):
        """Restore file version"""
        file_obj = get_object_or_404(StorageFile, id=file_id, owner=request.user)
        version_id = request.data.get('version_id')

        version = get_object_or_404(FileVersion, id=version_id, file=file_obj)

        # Create new version with restored content
        new_version_number = file_obj.version_count + 1

        FileVersion.objects.create(
            file=file_obj,
            version_number=new_version_number,
            file_data=version.file_data,
            file_hash=version.file_hash,
            size=version.size,
            change_description=f"Restored from version {version.version_number}",
            is_current=True
        )

        # Update current file
        file_obj.version_count = new_version_number
        file_obj.save()

        return Response({
            'message': 'File restored successfully',
            'version_number': new_version_number
        })


class UserShareViewSet(viewsets.ModelViewSet):
    """ViewSet for user shares"""
    serializer_class = UserShareSerializer
    queryset = UserShare.objects.all()
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        """Get shares for current user"""
        user = self.request.user
        return UserShare.objects.filter(
            Q(owner=user) | Q(shared_with=user)
        ).distinct()

    def perform_create(self, serializer):
        """Create share with current user as owner"""
        serializer.save(owner=self.request.user)

        # Send notification to shared user
        Notification.create_notification(
            user=serializer.instance.shared_with,
            notification_type='share',
            title='File Shared',
            message=f"{self.request.user.username} shared a file with you",
            expires_hours=72
        )

    @action(detail=True, methods=['post'])
    def update_permission(self, request, pk=None):
        """Update share permission"""
        share = self.get_object()
        if share.owner != request.user:
            raise PermissionDenied("You don't have permission to update this share")

        permission = request.data.get('permission')
        share.permission = permission
        share.save()

        return Response(UserShareSerializer(share).data)


class PublicLinkViewSet(viewsets.ModelViewSet):
    """ViewSet for public links"""
    serializer_class = PublicLinkSerializer
    queryset = PublicLink.objects.all()
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    lookup_field = 'token'

    def get_queryset(self):
        """Get public links for current user"""
        return PublicLink.objects.filter(owner=self.request.user)

    @action(detail=True, methods=['post'])
    def set_password(self, request, token=None):
        """Set password for public link"""
        link = self.get_object()
        password = request.data.get('password')

        if password:
            link.set_password(password)
            link.save()

        return Response({'message': 'Password updated'})

    @action(detail=True, methods=['post'])
    def disable(self, request, token=None):
        """Disable public link"""
        link = self.get_object()
        link.is_active = False
        link.save()
        return Response({'message': 'Link disabled'})


class ActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for activity logs"""
    serializer_class = ActivityLogSerializer
    queryset = ActivityLog.objects.all()
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering = ['-created_at']
    search_fields = ['description', 'activity_type']

    def get_queryset(self):
        """Get activities for current user"""
        return ActivityLog.objects.filter(user=self.request.user)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for users"""
    serializer_class = UserSerializer
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        """Get users (limited view for privacy)"""
        # Only return current user
        return self.request.user.__class__.objects.filter(id=self.request.user.id)


class StorageStatsView(generics.RetrieveAPIView):
    """Get storage statistics"""
    serializer_class = StorageStatsSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """Get or create storage stats for current user"""
        stats, _ = StorageStats.objects.get_or_create(user=self.request.user)
        return stats


class StorageQuotaView(generics.GenericAPIView):
    """Get storage quota information"""
    permission_classes = [IsAuthenticated]
    serializer_class = StorageQuotaSerializer

    @extend_schema(
        responses=StorageQuotaSerializer,
        examples=[
            OpenApiExample(
                'Quota Example',
                value={
                    'quota': 5368709120,
                    'used': 123456789,
                    'remaining': 5245252331,
                    'percentage_used': 2.3,
                    'is_full': False,
                    'is_warning': False
                },
                response_only=True
            )
        ],
    )
    def get(self, request):
        """Get quota details"""
        profile = request.user.profile

        return Response({
            'quota': profile.storage_quota,
            'used': profile.get_storage_used(),
            'remaining': profile.get_storage_remaining(),
            'percentage_used': profile.get_storage_used_percentage(),
            'is_full': profile.is_storage_full(),
            'is_warning': profile.is_storage_warning()
        })


class FileDownloadAPIView(generics.GenericAPIView):
    """Download file via API"""
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.Serializer

    @extend_schema(responses={200: OpenApiTypes.BINARY})
    def get(self, request, file_id):
        """Download file"""
        file_obj = get_object_or_404(StorageFile, id=file_id)

        if file_obj.owner != request.user:
            raise PermissionDenied("You don't have permission to download this file")

        file_obj.increment_download_count()

        response = FileResponse(file_obj.file.open('rb'), as_attachment=True)
        response['Content-Disposition'] = f'attachment; filename="{file_obj.name}"'
        return response


class FileUploadAPIView(generics.CreateAPIView):
    """
    Upload file via API (JWT authenticated).
    Used by Desktop Sync App.
    """
    serializer_class = StorageFileSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def create(self, request, *args, **kwargs):
        """Handle file upload"""
        uploaded_file = request.FILES.get('file')

        if not uploaded_file:
            return Response({
                'success': False,
                'error': 'Keine Datei bereitgestellt'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Get or create root folder for user
            root_folder, _ = StorageFolder.objects.get_or_create(
                owner=request.user,
                parent=None,
                defaults={'name': 'Root', 'description': 'Root folder'}
            )

            # Get optional folder_id from request
            folder_id = request.data.get('folder_id')
            if folder_id:
                folder = get_object_or_404(StorageFolder, id=folder_id, owner=request.user)
            else:
                folder = root_folder

            # Create file object
            storage_file = StorageFile(
                owner=request.user,
                folder=folder,
                file=uploaded_file,
                name=request.data.get('name', uploaded_file.name),
                size=uploaded_file.size,
                mime_type=uploaded_file.content_type or 'application/octet-stream'
            )
            storage_file.save()

            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                activity_type='upload',
                file=storage_file,
                description=f"Uploaded via API: {storage_file.name}",
                ip_address=self.get_client_ip(request)
            )

            logger.info(f"API Upload: {storage_file.name} by {request.user.username}")

            return Response({
                'success': True,
                'file_id': storage_file.id,
                'file_name': storage_file.name,
                'file_size': storage_file.size,
                'message': f'Datei {storage_file.name} erfolgreich hochgeladen'
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"API Upload error: {str(e)}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SearchAPIView(generics.GenericAPIView):
    """Search files and folders"""
    permission_classes = [IsAuthenticated]
    serializer_class = SearchResultSerializer
    pagination_class = StandardResultsSetPagination

    @extend_schema(
        examples=[
            OpenApiExample(
                'Search Example',
                value={'q': 'report'},
                request_only=True
            ),
            OpenApiExample(
                'Search Result',
                value=[{'type': 'file', 'id': 12, 'name': 'report.pdf'}],
                response_only=True
            )
        ]
    )
    def get(self, request):
        """Search"""
        query = request.query_params.get('q', '')

        if not query:
            return Response([])

        files = StorageFile.objects.filter(
            owner=request.user,
            name__icontains=query
        )[:10]

        folders = StorageFolder.objects.filter(
            owner=request.user,
            name__icontains=query
        )[:10]

        results = []
        for file in files:
            results.append({
                'type': 'file',
                'id': file.id,
                'name': file.name
            })

        for folder in folders:
            results.append({
                'type': 'folder',
                'id': folder.id,
                'name': folder.name
            })

        return Response(results)


class NotificationListView(generics.ListAPIView):
    """Get notifications"""
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        """Get notifications for current user"""
        return Notification.objects.filter(user=self.request.user)


class MarkNotificationReadView(generics.GenericAPIView):
    """Mark notification as read"""
    permission_classes = [IsAuthenticated]
    serializer_class = MessageResponseSerializer

    @extend_schema(
        responses=MessageResponseSerializer,
        examples=[OpenApiExample('Read OK', value={'message': 'Marked as read'}, response_only=True)]
    )
    def post(self, request, notification_id):
        """Mark as read"""
        notification = get_object_or_404(Notification, id=notification_id, user=request.user)
        notification.is_read = True
        notification.save()

        return Response({'message': 'Marked as read'})


class UpdateSharePermissionView(generics.GenericAPIView):
    """Update share permission"""
    permission_classes = [IsAuthenticated]
    serializer_class = UpdateSharePermissionRequestSerializer

    @extend_schema(
        request=UpdateSharePermissionRequestSerializer,
        responses=UserShareSerializer,
        examples=[
            OpenApiExample('Update Permission', value={'permission': 'edit'}, request_only=True)
        ],
    )
    def post(self, request, share_id):
        """Update permission"""
        share = get_object_or_404(UserShare, id=share_id, owner=request.user)
        permission = request.data.get('permission')

        share.permission = permission
        share.save()

        return Response(UserShareSerializer(share).data)


class SetPublicLinkPasswordView(generics.GenericAPIView):
    """Set password for public link"""
    permission_classes = [IsAuthenticated]
    serializer_class = SetPublicLinkPasswordRequestSerializer

    @extend_schema(
        request=SetPublicLinkPasswordRequestSerializer,
        responses=MessageResponseSerializer,
        examples=[
            OpenApiExample('Set Password', value={'password': 'secret123'}, request_only=True)
        ],
    )
    def post(self, request, link_id):
        """Set password"""
        link = get_object_or_404(PublicLink, id=link_id, owner=request.user)
        password = request.data.get('password')

        if password:
            link.set_password(password)
            link.save()

        return Response({'message': 'Password updated'})


# Plugin Management Views
@extend_schema(exclude=True)
class PluginActivateView(APIView):
    """Activate a plugin"""
    permission_classes = [IsAdminUser]

    def post(self, request, plugin_id):
        """Activate plugin"""
        try:
            from apps.cloude.cloude_apps.plugins.models import Plugin
            from apps.cloude.cloude_apps.plugins.loader import PluginLoader
            from django.contrib import messages

            plugin = get_object_or_404(Plugin, id=plugin_id)
            loader = PluginLoader()
            loader.load_plugin(str(plugin_id))

            # Redirect back with success message
            from django.shortcuts import redirect
            messages.success(request, _("✅ Plugin \"%(name)s\" aktiviert.") % {"name": plugin.name})
            return redirect('core:settings')

        except Exception as e:
            from django.shortcuts import redirect
            from django.contrib import messages
            messages.error(request, _("❌ Aktivierung fehlgeschlagen: %(error)s") % {"error": str(e)})
            return redirect('core:settings')


@extend_schema(exclude=True)
class PluginDeactivateView(APIView):
    """Deactivate a plugin"""
    permission_classes = [IsAdminUser]

    def post(self, request, plugin_id):
        """Deactivate plugin"""
        try:
            from apps.cloude.cloude_apps.plugins.models import Plugin
            from apps.cloude.cloude_apps.plugins.loader import PluginLoader
            from django.contrib import messages

            plugin = get_object_or_404(Plugin, id=plugin_id)
            loader = PluginLoader()
            loader.unload_plugin(str(plugin_id))

            # Redirect back with success message
            from django.shortcuts import redirect
            messages.success(request, _("✅ Plugin \"%(name)s\" deaktiviert.") % {"name": plugin.name})
            return redirect('core:settings')

        except Exception as e:
            from django.shortcuts import redirect
            from django.contrib import messages
            messages.error(request, _("❌ Deaktivierung fehlgeschlagen: %(error)s") % {"error": str(e)})
            return redirect('core:settings')


@extend_schema(exclude=True)
class PluginDiscoverView(APIView):
    """Discover plugins from filesystem"""
    permission_classes = [IsAdminUser]

    def post(self, request):
        """Scan plugins directory and register new plugins"""
        try:
            from apps.cloude.cloude_apps.plugins.loader import PluginLoader
            from django.contrib import messages
            from django.shortcuts import redirect

            loader = PluginLoader()
            discovered = loader.discover_plugins()

            new_count = sum(1 for d in discovered if d['created'])

            if new_count > 0:
                messages.success(request, _("✅ %(count)s neue Plugin(s) entdeckt!") % {"count": new_count})
            else:
                messages.info(request, _("Keine neuen Plugins gefunden."))

            return redirect('core:settings')

        except Exception as e:
            from django.shortcuts import redirect
            from django.contrib import messages
            messages.error(request, _("❌ Fehler: %(error)s") % {"error": str(e)})
            return redirect('core:settings')


@extend_schema(exclude=True)
class PluginSettingsView(APIView):
    """View and update plugin settings"""
    permission_classes = [IsAdminUser]

    def get(self, request, plugin_id):
        """Show plugin settings form"""
        from django.shortcuts import render
        from apps.cloude.cloude_apps.plugins.models import Plugin

        plugin = get_object_or_404(Plugin, id=plugin_id)

        # Prepare fields with current values
        fields = []
        for key, field_def in plugin.settings_schema.items():
            field = {
                'key': key,
                'value': plugin.settings.get(key, field_def.get('default', '')),
                **field_def
            }
            fields.append(field)

        return render(request, 'plugins/settings.html', {
            'plugin': plugin,
            'fields': fields,
        })

    def post(self, request, plugin_id):
        """Save plugin settings"""
        from django.shortcuts import redirect
        from django.contrib import messages
        from apps.cloude.cloude_apps.plugins.models import Plugin

        plugin = get_object_or_404(Plugin, id=plugin_id)

        try:
            # Get settings from form
            new_settings = {}
            for key, field_def in plugin.settings_schema.items():
                value = request.POST.get(key, '')

                # Type conversion based on schema
                field_type = field_def.get('type', 'text')
                if field_type == 'number':
                    value = float(value) if value else 0
                elif field_type == 'boolean':
                    value = key in request.POST
                elif field_type == 'integer':
                    value = int(value) if value else 0

                new_settings[key] = value

            # Save settings
            plugin.settings = new_settings
            plugin.save()

            messages.success(request, _("✅ Einstellungen für \"%(name)s\" gespeichert!") % {"name": plugin.name})

        except Exception as e:
            messages.error(request, _("❌ Fehler beim Speichern: %(error)s") % {"error": str(e)})

        return redirect('cloude_api:plugin_settings', plugin_id=plugin_id)