"""
Tests for classroom app license enforcement.
Tests that classroom features are properly restricted by license tier.
"""

import pytest
from datetime import date
from apps.classroom.models import MobileClassroom, ClassroomDeployment, ShippingAddress
from apps.licensing.models import LicenseProduct, LicenseKey
from apps.licensing.decorators import license_required
from apps.licensing.mixins import LicenseRequiredMixin
from decimal import Decimal

pytestmark = pytest.mark.django_db(transaction=True)


class TestClassroomLicenseFeatures:
    """Tests for classroom license features."""

    @pytest.fixture
    def basic_license(self, db):
        """Create ABORO_BASIC license product."""
        return LicenseProduct.objects.create(
            code='ABORO_BASIC',
            name='ABoroOffice Basic',
            tier='basic',
            monthly_price=Decimal('399.00'),
            max_staff_users=5,
            max_total_users=20,
            storage_quota_gb=10,
            features={
                'core': True,
                'classroom': True,
            },
            is_active=True,
        )

    @pytest.fixture
    def office_license(self, db):
        """Create ABORO_OFFICE license product."""
        return LicenseProduct.objects.create(
            code='ABORO_OFFICE',
            name='ABoroOffice Office',
            tier='office',
            monthly_price=Decimal('899.00'),
            max_staff_users=25,
            max_total_users=100,
            storage_quota_gb=50,
            features={
                'core': True,
                'classroom': True,
                'helpdesk_tickets': True,
                'helpdesk_knowledge': True,
                'approvals': True,
            },
            is_active=True,
        )

    @pytest.mark.unit
    def test_classroom_feature_in_basic_license(self, basic_license):
        """Test that classroom feature is in BASIC license."""
        assert 'classroom' in basic_license.features
        assert basic_license.features['classroom'] is True

    @pytest.mark.unit
    def test_classroom_feature_in_office_license(self, office_license):
        """Test that classroom feature is in OFFICE license."""
        assert 'classroom' in office_license.features
        assert office_license.features['classroom'] is True

    @pytest.mark.unit
    def test_get_user_available_features_with_basic_license(self, aboro_user, basic_license):
        """Test getting available features for user with BASIC license."""
        # Create active license
        LicenseKey.objects.create(
            license_code='ABORO_BASIC-1-12-20251231-ABC123DEF456',
            product=basic_license,
            customer_name='Test Company',
            customer_email=aboro_user.email,
            issue_date=date.today(),
            expiry_date=date.today().replace(year=date.today().year + 1),
            status='active',
        )

        # Get available features
        features = aboro_user.get_available_features()

        assert 'core' in features
        assert 'classroom' in features
        assert 'helpdesk_tickets' not in features

    @pytest.mark.unit
    def test_can_access_classroom_feature(self, aboro_user, basic_license):
        """Test can_access_feature method for classroom."""
        LicenseKey.objects.create(
            license_code='ABORO_BASIC-1-12-20251231-ABC123DEF456',
            product=basic_license,
            customer_name='Test Company',
            customer_email=aboro_user.email,
            issue_date=date.today(),
            expiry_date=date.today().replace(year=date.today().year + 1),
            status='active',
        )

        assert aboro_user.can_access_feature('classroom') is True
        assert aboro_user.can_access_feature('helpdesk_tickets') is False

    @pytest.mark.unit
    def test_cannot_access_locked_features(self, aboro_user):
        """Test that user cannot access features without license."""
        # No license created - default behavior
        features = aboro_user.get_available_features()
        assert 'classroom' not in features

        assert aboro_user.can_access_feature('classroom') is False
        assert aboro_user.can_access_feature('helpdesk_tickets') is False

    @pytest.mark.unit
    def test_classroom_accessible_with_office_license(self, aboro_user, office_license):
        """Test classroom is accessible with OFFICE license."""
        LicenseKey.objects.create(
            license_code='ABORO_OFFICE-1-12-20251231-XYZ789GHI012',
            product=office_license,
            customer_name='Large Company',
            customer_email=aboro_user.email,
            issue_date=date.today(),
            expiry_date=date.today().replace(year=date.today().year + 1),
            status='active',
        )

        features = aboro_user.get_available_features()
        assert 'classroom' in features
        assert 'helpdesk_tickets' in features
        assert 'helpdesk_knowledge' in features
        assert 'approvals' in features


@pytest.mark.licensing
class TestLicenseDecorators:
    """Tests for license requirement decorators."""

    @pytest.mark.unit
    def test_license_required_decorator_definition(self):
        """Test that license_required decorator can be created."""
        from apps.licensing.decorators import license_required

        @license_required('classroom')
        def dummy_view(request):
            return "OK"

        assert callable(dummy_view)

    @pytest.mark.unit
    def test_license_required_mixin_definition(self):
        """Test that LicenseRequiredMixin exists."""
        mixin = LicenseRequiredMixin()
        assert hasattr(mixin, 'license_feature')
        assert hasattr(mixin, 'test_func')


@pytest.mark.integration
class TestClassroomLicenseIntegration:
    """Integration tests for classroom license enforcement."""

    @pytest.mark.integration
    def test_classroom_models_accessible_with_license(self, db, aboro_user, basic_license):
        """Test that classroom models are accessible when licensed."""
        # Create active license
        LicenseKey.objects.create(
            license_code='ABORO_BASIC-1-12-20251231-ABC123DEF456',
            product=basic_license,
            customer_name='Test Company',
            customer_email=aboro_user.email,
            issue_date=date.today(),
            expiry_date=date.today().replace(year=date.today().year + 1),
            status='active',
        )

        # User should be able to access classroom
        assert aboro_user.can_access_feature('classroom') is True

        # Should be able to create classroom objects
        classroom = MobileClassroom.objects.create(
            name='HP01',
            room_type='HP',
            status='auf_lager',
        )
        assert classroom.name == 'HP01'

        # Should be able to create deployments
        location = ShippingAddress.objects.create(
            name='Munich',
            street='Main St',
            postal_code='80001',
            city='Munich',
        )

        deployment = ClassroomDeployment.objects.create(
            classroom=classroom,
            location=location,
            deployment_start=date.today(),
            deployment_end=date.today(),
        )
        assert deployment.classroom == classroom

    @pytest.mark.integration
    def test_expired_license_revokes_access(self, db, aboro_user, basic_license):
        """Test that expired license revokes feature access."""
        # Create expired license
        LicenseKey.objects.create(
            license_code='ABORO_BASIC-1-12-20231231-ABC123DEF456',
            product=basic_license,
            customer_name='Test Company',
            customer_email=aboro_user.email,
            issue_date=date.today().replace(year=date.today().year - 2),
            expiry_date=date.today().replace(year=date.today().year - 1),  # Expired
            status='expired',
        )

        # User should not have access (no active license)
        features = aboro_user.get_available_features()
        assert 'classroom' not in features
        assert aboro_user.can_access_feature('classroom') is False
