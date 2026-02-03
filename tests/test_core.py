"""
Tests for core app.
Covers ABoroUser model and authentication.
"""

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

pytestmark = pytest.mark.django_db(transaction=True)


class TestABoroUser:
    """Tests for ABoroUser model."""

    @pytest.mark.unit
    def test_create_basic_user(self):
        """Test creating a basic customer user."""
        user = User.objects.create_user(
            username='customer',
            email='customer@example.com',
            password='pass123',
            first_name='John',
            last_name='Doe',
        )

        assert user.username == 'customer'
        assert user.email == 'customer@example.com'
        assert user.get_full_name() == 'John Doe'
        assert user.role == 'customer'
        assert user.is_agent is False

    @pytest.mark.unit
    def test_create_agent_user(self):
        """Test creating a support agent user."""
        user = User.objects.create_user(
            username='agent1',
            email='agent1@example.com',
            password='pass123',
            first_name='Support',
            last_name='Agent',
            role='support_agent',
            is_agent=True,
            support_level=2,
            department='Support',
        )

        assert user.role == 'support_agent'
        assert user.is_agent is True
        assert user.support_level == 2
        assert user.department == 'Support'

    @pytest.mark.unit
    def test_create_superuser(self):
        """Test creating a superuser."""
        user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123',
        )

        assert user.is_superuser is True
        assert user.is_staff is True
        assert user.is_active is True

    @pytest.mark.unit
    def test_user_with_cloude_fields(self):
        """Test user with Cloude-specific fields."""
        user = User.objects.create_user(
            username='cloude_user',
            email='cloude@example.com',
            password='pass123',
            two_factor_enabled=True,
            storage_quota_mb=5120,
        )

        assert user.two_factor_enabled is True
        assert user.storage_quota_mb == 5120
        assert user.storage_used_mb == 0

    @pytest.mark.unit
    def test_user_timezone_default(self):
        """Test that timezone defaults to Europe/Berlin."""
        user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='pass123',
        )

        assert user.timezone == 'Europe/Berlin'

    @pytest.mark.unit
    def test_user_custom_timezone(self):
        """Test setting custom timezone."""
        user = User.objects.create_user(
            username='user_tz',
            email='usertz@example.com',
            password='pass123',
            timezone='America/New_York',
        )

        assert user.timezone == 'America/New_York'

    @pytest.mark.unit
    def test_user_with_address_fields(self):
        """Test user with address information."""
        user = User.objects.create_user(
            username='customer_addr',
            email='customer@example.com',
            password='pass123',
            street='123 Main St',
            postal_code='12345',
            city='Berlin',
            country='Deutschland',
        )

        assert user.street == '123 Main St'
        assert user.postal_code == '12345'
        assert user.city == 'Berlin'
        assert user.country == 'Deutschland'

    @pytest.mark.unit
    def test_user_string_representation(self):
        """Test __str__ method."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='pass123',
            first_name='Test',
            last_name='User',
        )

        assert 'Test User' in str(user)
        assert 'test@example.com' in str(user)

    @pytest.mark.unit
    def test_user_authentication(self):
        """Test user can authenticate."""
        user = User.objects.create_user(
            username='authuser',
            email='authuser@example.com',
            password='correctpass',
        )

        # Test correct password
        assert user.check_password('correctpass')

        # Test incorrect password
        assert not user.check_password('wrongpass')

    @pytest.mark.unit
    def test_user_storage_percentage(self, aboro_user):
        """Test calculating storage usage percentage."""
        aboro_user.storage_quota_mb = 1024
        aboro_user.storage_used_mb = 256
        aboro_user.save()

        percentage = aboro_user.get_storage_percentage()
        assert percentage == 25.0

    @pytest.mark.unit
    def test_user_storage_percentage_full(self, aboro_user):
        """Test storage percentage when full."""
        aboro_user.storage_quota_mb = 1024
        aboro_user.storage_used_mb = 1024
        aboro_user.save()

        percentage = aboro_user.get_storage_percentage()
        assert percentage == 100.0

    @pytest.mark.unit
    def test_user_storage_percentage_over_quota(self, aboro_user):
        """Test storage percentage when over quota."""
        aboro_user.storage_quota_mb = 1024
        aboro_user.storage_used_mb = 1536  # Over quota
        aboro_user.save()

        percentage = aboro_user.get_storage_percentage()
        assert percentage == 150.0

    @pytest.mark.unit
    def test_user_update_activity(self, aboro_user):
        """Test updating last activity timestamp."""
        original_activity = aboro_user.last_activity

        # Update activity
        aboro_user.update_activity()

        # Reload from DB
        aboro_user.refresh_from_db()

        # Activity should be updated
        assert aboro_user.last_activity is not None
        if original_activity:
            assert aboro_user.last_activity >= original_activity

    @pytest.mark.unit
    def test_user_force_password_change(self):
        """Test force password change flag."""
        user = User.objects.create_user(
            username='forcechange',
            email='forcechange@example.com',
            password='pass123',
            force_password_change=True,
        )

        assert user.force_password_change is True

    @pytest.mark.unit
    def test_user_email_verified(self):
        """Test email verification flag."""
        user = User.objects.create_user(
            username='verified',
            email='verified@example.com',
            password='pass123',
            email_verified=True,
        )

        assert user.email_verified is True

    @pytest.mark.unit
    def test_user_get_available_features_empty(self, aboro_user):
        """Test getting available features (returns empty by default)."""
        features = aboro_user.get_available_features()
        assert isinstance(features, list)

    @pytest.mark.unit
    def test_user_can_access_feature(self, aboro_user):
        """Test checking feature access."""
        # Should return False by default
        assert aboro_user.can_access_feature('helpdesk') is False

    @pytest.mark.unit
    def test_microsoft_oauth_field(self):
        """Test Microsoft OAuth2 integration field."""
        user = User.objects.create_user(
            username='microsoft_user',
            email='ms@example.com',
            password='pass123',
            microsoft_id='microsoft-unique-id-12345',
        )

        assert user.microsoft_id == 'microsoft-unique-id-12345'

    @pytest.mark.unit
    def test_user_queryset_filtering(self):
        """Test filtering users by various fields."""
        # Create test users
        User.objects.create_user(
            username='admin1',
            email='admin1@example.com',
            password='pass123',
            role='admin',
        )
        User.objects.create_user(
            username='customer1',
            email='customer1@example.com',
            password='pass123',
            role='customer',
        )

        # Filter by role
        admins = User.objects.filter(role='admin')
        customers = User.objects.filter(role='customer')

        assert admins.count() >= 1
        assert customers.count() >= 1

    @pytest.mark.unit
    def test_user_created_at_timestamp(self, aboro_user):
        """Test that created_at is set automatically."""
        assert aboro_user.created_at is not None
        assert isinstance(aboro_user.created_at, type(timezone.now()))

    @pytest.mark.unit
    def test_user_updated_at_timestamp(self, aboro_user):
        """Test that updated_at is set automatically."""
        assert aboro_user.updated_at is not None

        # Update the user
        aboro_user.first_name = 'Updated'
        aboro_user.save()
        aboro_user.refresh_from_db()

        # updated_at should be newer
        assert aboro_user.updated_at >= aboro_user.created_at


class TestUserManager:
    """Tests for ABoroUser manager."""

    @pytest.mark.unit
    def test_create_user_without_email_raises_error(self):
        """Test that creating user without email raises ValueError."""
        with pytest.raises(ValueError):
            User.objects.create_user(
                username='nomail',
                email='',
                password='pass123',
            )

    @pytest.mark.unit
    def test_superuser_is_staff(self):
        """Test that superuser is marked as staff."""
        user = User.objects.create_superuser(
            username='superadmin',
            email='superadmin@example.com',
            password='pass123',
        )

        assert user.is_staff is True
        assert user.is_active is True


class TestUserIndexing:
    """Tests for database indexing on ABoroUser."""

    @pytest.mark.integration
    def test_can_query_by_email_indexed(self):
        """Test that email queries are efficient."""
        user = User.objects.create_user(
            username='indexed',
            email='indexed@example.com',
            password='pass123',
        )

        # Should retrieve from index efficiently
        found = User.objects.filter(email='indexed@example.com').first()
        assert found == user

    @pytest.mark.integration
    def test_can_query_by_role_indexed(self):
        """Test that role queries are efficient."""
        User.objects.create_user(
            username='agent',
            email='agent@example.com',
            password='pass123',
            role='support_agent',
        )

        agents = User.objects.filter(role='support_agent')
        assert agents.count() >= 1
