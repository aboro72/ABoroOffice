"""
Tests for licensing system.
Covers LicenseManager and LicenseKey models.
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.utils import timezone
from apps.licensing.models import LicenseProduct, LicenseKey
from apps.licensing.license_manager import LicenseManager


pytestmark = pytest.mark.django_db(transaction=True)


class TestLicenseManager:
    """Tests for LicenseManager class."""

    @pytest.mark.unit
    def test_generate_license_code_valid_product(self):
        """Test generating license code for valid product."""
        code = LicenseManager.generate_license_code('ABORO_BASIC', 12)
        assert code is not None
        assert code.startswith('ABORO_BASIC-1-12-')
        parts = code.split('-')
        assert len(parts) == 5

    @pytest.mark.unit
    def test_generate_license_code_invalid_product(self):
        """Test that invalid product raises ValueError."""
        with pytest.raises(ValueError, match="Invalid product"):
            LicenseManager.generate_license_code('INVALID_PRODUCT', 12)

    @pytest.mark.unit
    def test_generate_license_code_invalid_duration_too_short(self):
        """Test that duration < 1 month raises ValueError."""
        with pytest.raises(ValueError, match="Duration must be between 1 and 36"):
            LicenseManager.generate_license_code('ABORO_BASIC', 0)

    @pytest.mark.unit
    def test_generate_license_code_invalid_duration_too_long(self):
        """Test that duration > 36 months raises ValueError."""
        with pytest.raises(ValueError, match="Duration must be between 1 and 36"):
            LicenseManager.generate_license_code('ABORO_BASIC', 37)

    @pytest.mark.unit
    def test_validate_license_valid_code(self):
        """Test validating a valid license code."""
        code = LicenseManager.generate_license_code('ABORO_OFFICE', 12)
        is_valid, message = LicenseManager.validate_license(code)
        assert is_valid is True
        assert message == "License valid"

    @pytest.mark.unit
    def test_validate_license_invalid_signature(self):
        """Test that invalid signature is detected."""
        is_valid, message = LicenseManager.validate_license(
            'ABORO_BASIC-1-12-20251231-INVALIDSIGNATURE'
        )
        assert is_valid is False
        assert "Invalid license signature" in message

    @pytest.mark.unit
    def test_validate_license_expired(self):
        """Test that expired license is detected."""
        # Generate code with expired date (90 days ago)
        from datetime import datetime
        expired_date = datetime.now() - timedelta(days=90)
        code = LicenseManager.generate_license_code('ABORO_BASIC', 12, expired_date)

        # This should fail validation due to expired date
        is_valid, message = LicenseManager.validate_license(code)
        assert is_valid is False
        assert "expired" in message.lower()

    @pytest.mark.unit
    def test_validate_license_invalid_format_no_parts(self):
        """Test validation with invalid format."""
        is_valid, message = LicenseManager.validate_license('INVALID')
        assert is_valid is False

    @pytest.mark.unit
    def test_get_license_info_valid(self):
        """Test getting info for valid license."""
        code = LicenseManager.generate_license_code('ABORO_PROFESSIONAL', 24)
        info = LicenseManager.get_license_info(code)

        assert info is not None
        assert info['product'] == 'ABORO_PROFESSIONAL'
        assert info['product_name'] == 'ABoroOffice Professional'
        assert info['tier'] == 'professional'
        assert info['duration_months'] == 24
        assert info['max_staff_users'] == 100
        assert info['valid'] is True
        assert 'classroom' in info['features']

    @pytest.mark.unit
    def test_get_license_info_invalid(self):
        """Test getting info for invalid license."""
        info = LicenseManager.get_license_info('INVALID-CODE-FORMAT')
        assert info is None

    @pytest.mark.unit
    def test_get_all_products(self):
        """Test getting all available products."""
        products = LicenseManager.get_all_products()

        assert 'ABORO_BASIC' in products
        assert 'ABORO_OFFICE' in products
        assert 'ABORO_PROFESSIONAL' in products
        assert 'ABORO_ENTERPRISE' in products
        assert 'ABORO_ON_PREMISE' in products

        # Check Legacy products
        assert 'STARTER' in products
        assert 'PROFESSIONAL' in products

    @pytest.mark.unit
    def test_get_all_products_has_features(self):
        """Test that all products have required fields."""
        products = LicenseManager.get_all_products()

        for code, product in products.items():
            assert 'name' in product
            assert 'features' in product
            assert isinstance(product['features'], list)

    @pytest.mark.unit
    def test_calculate_license_cost_monthly(self):
        """Test calculating cost for monthly license."""
        cost = LicenseManager.calculate_license_cost('ABORO_BASIC', 12)

        assert cost['product'] == 'ABORO_BASIC'
        assert cost['monthly_price'] == 399
        assert cost['duration_months'] == 12
        assert cost['monthly_total'] == 399 * 12
        assert cost['setup_fee'] == 0

    @pytest.mark.unit
    def test_calculate_license_cost_on_premise(self):
        """Test calculating cost for on-premise license."""
        cost = LicenseManager.calculate_license_cost('ABORO_ON_PREMISE', 1)

        assert cost['product'] == 'ABORO_ON_PREMISE'
        assert cost['yearly_price'] == 15000

    @pytest.mark.unit
    def test_validate_trial(self):
        """Test trial validation."""
        is_valid, message = LicenseManager.validate_trial()
        assert is_valid is True
        assert "Trial period" in message


class TestLicenseProduct:
    """Tests for LicenseProduct model."""

    @pytest.mark.unit
    def test_create_license_product(self, license_basic_product):
        """Test creating a license product."""
        assert license_basic_product.code == 'ABORO_BASIC'
        assert license_basic_product.name == 'ABoroOffice Basic'
        assert license_basic_product.tier == 'basic'
        assert license_basic_product.is_active is True

    @pytest.mark.unit
    def test_license_product_str(self, license_office_product):
        """Test string representation of license product."""
        assert str(license_office_product) == 'ABoroOffice Office (ABORO_OFFICE)'

    @pytest.mark.unit
    def test_license_product_with_features(self, license_enterprise_product):
        """Test product with features."""
        assert 'core' in license_enterprise_product.features
        assert license_enterprise_product.features['core'] is True


class TestLicenseKey:
    """Tests for LicenseKey model."""

    @pytest.mark.unit
    def test_create_license_key(self, active_license_key):
        """Test creating a license key."""
        assert active_license_key.product.code == 'ABORO_OFFICE'
        assert active_license_key.customer_name == 'Test Company'
        assert active_license_key.status == 'active'

    @pytest.mark.unit
    def test_license_key_is_valid(self, active_license_key):
        """Test checking if license is valid."""
        assert active_license_key.is_valid() is True

    @pytest.mark.unit
    def test_license_key_is_expired(self, expired_license_key):
        """Test checking if license is expired."""
        assert expired_license_key.is_expired() is True
        assert expired_license_key.is_valid() is False

    @pytest.mark.unit
    def test_license_key_days_until_expiry(self, active_license_key):
        """Test calculating days until expiry."""
        days = active_license_key.days_until_expiry()
        assert days > 0
        assert days <= 365

    @pytest.mark.unit
    def test_license_key_days_until_expiry_negative(self, expired_license_key):
        """Test that expired license shows negative days."""
        days = expired_license_key.days_until_expiry()
        assert days < 0

    @pytest.mark.unit
    def test_license_key_str(self, active_license_key):
        """Test string representation."""
        str_repr = str(active_license_key)
        assert 'ABORO_OFFICE-1-12-202512' in str_repr


class TestLicenseIntegration:
    """Integration tests for licensing system."""

    @pytest.mark.integration
    def test_full_license_workflow(self, license_office_product, aboro_user):
        """Test complete license creation and validation workflow."""
        # Generate license code
        code = LicenseManager.generate_license_code('ABORO_OFFICE', 12)
        assert code is not None

        # Validate the code
        is_valid, message = LicenseManager.validate_license(code)
        assert is_valid is True

        # Get license info
        info = LicenseManager.get_license_info(code)
        assert info is not None
        assert info['product'] == 'ABORO_OFFICE'

        # Create license key in database
        license_key = LicenseKey.objects.create(
            license_code=code,
            product=license_office_product,
            customer_name='Integration Test',
            customer_email=aboro_user.email,
            expiry_date=date.today() + timedelta(days=365),
        )

        # Verify it's valid
        assert license_key.is_valid() is True
        assert license_key.is_expired() is False

    @pytest.mark.integration
    def test_license_backward_compatibility(self):
        """Test that legacy license codes still work."""
        # Legacy STARTER product should still exist
        code = LicenseManager.generate_license_code('STARTER', 12)
        is_valid, message = LicenseManager.validate_license(code)
        assert is_valid is True

        # Should get info
        info = LicenseManager.get_license_info(code)
        assert info is not None
        assert info['product'] == 'STARTER'
