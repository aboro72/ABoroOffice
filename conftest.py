"""
Pytest configuration for ABoroOffice.
Sets up fixtures and test database.
"""

import os
import django
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
os.sys.path.insert(0, str(PROJECT_ROOT))

# Setup Django before importing models
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.licensing.models import LicenseProduct, LicenseKey
from apps.licensing.license_manager import LicenseManager
from datetime import date, timedelta
from decimal import Decimal

User = get_user_model()


@pytest.fixture
def django_db_setup(django_db_blocker):
    """Configure Django test database."""
    with django_db_blocker.unblock():
        pass


@pytest.fixture
def aboro_user(db):
    """Create a test ABoroUser."""
    return User.objects.create_user(
        username='testuser',
        email='testuser@example.com',
        password='testpass123',
        first_name='Test',
        last_name='User',
        role='customer',
        timezone='Europe/Berlin',
    )


@pytest.fixture
def aboro_admin(db):
    """Create a test admin user."""
    return User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='adminpass123',
        first_name='Admin',
        last_name='User',
    )


@pytest.fixture
def aboro_agent(db):
    """Create a test support agent."""
    return User.objects.create_user(
        username='agent',
        email='agent@example.com',
        password='agentpass123',
        first_name='Support',
        last_name='Agent',
        role='support_agent',
        is_agent=True,
        support_level=1,
        department='Support',
    )


@pytest.fixture
def license_basic_product(db):
    """Create ABORO_BASIC license product."""
    return LicenseProduct.objects.create(
        code='ABORO_BASIC',
        name='ABoroOffice Basic',
        tier='basic',
        description='Basic plan for small teams',
        monthly_price=Decimal('399.00'),
        max_staff_users=5,
        max_total_users=20,
        storage_quota_gb=10,
        features={
            'core': True,
            'classroom': True,
            'helpdesk_tickets': False,
        },
        is_active=True,
    )


@pytest.fixture
def license_office_product(db):
    """Create ABORO_OFFICE license product."""
    return LicenseProduct.objects.create(
        code='ABORO_OFFICE',
        name='ABoroOffice Office',
        tier='office',
        description='Full office suite for growing businesses',
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


@pytest.fixture
def license_enterprise_product(db):
    """Create ABORO_ENTERPRISE license product."""
    return LicenseProduct.objects.create(
        code='ABORO_ENTERPRISE',
        name='ABoroOffice Enterprise',
        tier='enterprise',
        description='Unlimited features for enterprises',
        monthly_price=Decimal('2999.00'),
        max_staff_users=-1,  # Unlimited
        max_total_users=-1,   # Unlimited
        storage_quota_gb=-1,  # Unlimited
        features={
            'core': True,
            'classroom': True,
            'helpdesk_tickets': True,
            'helpdesk_knowledge': True,
            'helpdesk_chat': True,
            'helpdesk_ai': True,
            'cloude_storage': True,
            'cloude_sharing': True,
            'approvals': True,
            'api_full': True,
        },
        is_active=True,
    )


@pytest.fixture
def active_license_key(db, license_office_product, aboro_user):
    """Create an active license key."""
    expiry_date = date.today() + timedelta(days=365)
    return LicenseKey.objects.create(
        license_code='ABORO_OFFICE-1-12-20251231-A7F3B2C1D9E8F4A6',
        product=license_office_product,
        customer_name='Test Company',
        customer_email='test@company.com',
        issue_date=date.today(),
        expiry_date=expiry_date,
        status='active',
        instance_count=1,
    )


@pytest.fixture
def expired_license_key(db, license_basic_product):
    """Create an expired license key."""
    expiry_date = date.today() - timedelta(days=30)
    return LicenseKey.objects.create(
        license_code='ABORO_BASIC-1-12-20240101-X8F3B2C1D9E8F4A6',
        product=license_basic_product,
        customer_name='Expired Company',
        customer_email='expired@company.com',
        issue_date=date.today() - timedelta(days=365),
        expiry_date=expiry_date,
        status='expired',
        instance_count=1,
    )


@pytest.fixture
def license_manager_valid_code():
    """Valid license code for testing."""
    return 'ABORO_BASIC-1-12-20251231-' + LicenseManager._generate_signature('ABORO_BASIC|1|12|20251231')


@pytest.fixture
def license_manager_invalid_code():
    """Invalid license code for testing."""
    return 'ABORO_BASIC-1-12-20251231-INVALIDCHECKSUMXXXXXXXXXXXXXXXX'


# Mark all tests in this directory as requiring DB
pytest.mark.django_db(transaction=True)
