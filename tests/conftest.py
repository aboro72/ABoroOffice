"""
Pytest configuration and fixtures for ABoroOffice tests.
"""

import pytest
from apps.core.models import ABoroUser


@pytest.fixture
def aboro_user(db):
    """Create a regular ABoroUser for testing."""
    return ABoroUser.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123',
        first_name='Test',
        last_name='User',
        role='customer',
        user_timezone='Europe/Berlin',
    )


@pytest.fixture
def aboro_admin(db):
    """Create an admin ABoroUser for testing."""
    return ABoroUser.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='admin123',
        role='admin',
        user_timezone='Europe/Berlin',
    )


@pytest.fixture
def aboro_agent(db):
    """Create a support agent ABoroUser for testing."""
    return ABoroUser.objects.create_user(
        username='agent',
        email='agent@example.com',
        password='agent123',
        first_name='Support',
        last_name='Agent',
        role='support_agent',
        support_level=2,
        is_agent=True,
        user_timezone='Europe/Berlin',
    )
