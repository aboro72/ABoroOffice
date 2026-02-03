"""
Tests for classroom app models.
Tests deployment scheduling, availability checking, and model logic.
"""

import pytest
from datetime import date, timedelta, datetime
from django.utils import timezone
from apps.classroom.models import (
    MobileClassroom, ClassroomDeployment, ShippingAddress, Warehouse,
    DeploymentHistory, EmailReminder, ChecklistTemplate, ChecklistCompletion
)
from apps.core.models import ABoroUser

pytestmark = pytest.mark.django_db(transaction=True)


class TestMobileClassroom:
    """Tests for MobileClassroom model."""

    @pytest.fixture
    def classroom_hp(self, db):
        """Create a HP classroom."""
        return MobileClassroom.objects.create(
            name='HP01',
            room_type='HP',
            status='auf_lager',
        )

    @pytest.fixture
    def classroom_ac(self, db):
        """Create an AC classroom."""
        return MobileClassroom.objects.create(
            name='AC02',
            room_type='AC',
            status='auf_lager',
        )

    @pytest.fixture
    def location(self, db):
        """Create a shipping address."""
        return ShippingAddress.objects.create(
            name='Training Center Munich',
            location_type='training',
            street='Main Street 123',
            postal_code='80001',
            city='Munich',
        )

    @pytest.mark.unit
    def test_classroom_creation(self, classroom_hp):
        """Test creating a classroom."""
        assert classroom_hp.name == 'HP01'
        assert classroom_hp.room_type == 'HP'
        assert classroom_hp.status == 'auf_lager'

    @pytest.mark.unit
    def test_classroom_string_representation(self, classroom_ac):
        """Test __str__ method."""
        assert str(classroom_ac) == 'AC02'

    @pytest.mark.unit
    def test_is_in_stock(self, classroom_hp):
        """Test is_in_stock method."""
        assert classroom_hp.is_in_stock() is True
        classroom_hp.status = 'versand_geplant'
        assert classroom_hp.is_in_stock() is False

    @pytest.mark.unit
    def test_can_ship(self, classroom_hp):
        """Test can_ship method."""
        assert classroom_hp.can_ship() is False
        classroom_hp.status = 'versandfertig'
        assert classroom_hp.can_ship() is True

    @pytest.mark.unit
    def test_availability_with_no_deployments(self, classroom_hp):
        """Test availability check when no deployments exist."""
        start = date.today()
        end = date.today() + timedelta(days=14)
        is_available, reason = classroom_hp.is_available_for_deployment(start, end)
        assert is_available is True
        assert reason is None

    @pytest.mark.unit
    def test_availability_with_overlapping_deployment(self, classroom_hp, location):
        """Test availability check with overlapping deployment."""
        # Create a deployment for next month
        deployment = ClassroomDeployment.objects.create(
            classroom=classroom_hp,
            location=location,
            deployment_start=date.today() + timedelta(days=30),
            deployment_end=date.today() + timedelta(days=45),
        )

        # Test non-overlapping dates
        start = date.today()
        end = date.today() + timedelta(days=14)
        is_available, reason = classroom_hp.is_available_for_deployment(start, end)
        assert is_available is True

        # Test overlapping dates
        start = date.today() + timedelta(days=35)
        end = date.today() + timedelta(days=50)
        is_available, reason = classroom_hp.is_available_for_deployment(start, end)
        assert is_available is False
        assert "überschneidet sich" in reason.lower()

    @pytest.mark.unit
    def test_get_available_classrooms(self, classroom_hp, classroom_ac, location):
        """Test getting available classrooms."""
        start = date.today()
        end = date.today() + timedelta(days=14)

        available = MobileClassroom.get_available_classrooms(start, end)
        assert available.count() == 2
        assert classroom_hp in available
        assert classroom_ac in available

    @pytest.mark.unit
    def test_get_available_classrooms_excludes_locked(self, classroom_hp, classroom_ac):
        """Test that locked classrooms are excluded."""
        classroom_hp.status = 'gesperrt'
        classroom_hp.save()

        start = date.today()
        end = date.today() + timedelta(days=14)

        available = MobileClassroom.get_available_classrooms(start, end)
        assert available.count() == 1
        assert classroom_ac in available
        assert classroom_hp not in available

    @pytest.mark.unit
    def test_get_suggested_classroom_prefers_hp(self, classroom_hp, classroom_ac):
        """Test that HP classrooms are preferred."""
        start = date.today()
        end = date.today() + timedelta(days=14)

        suggested = MobileClassroom.get_suggested_classroom(start, end)
        assert suggested is not None
        assert suggested.room_type == 'HP'

    @pytest.mark.unit
    def test_get_suggested_classroom_falls_back_to_ac(self, classroom_ac, location):
        """Test that AC classrooms are suggested if no HP available."""
        # Lock all HP classrooms
        hp_rooms = MobileClassroom.objects.filter(room_type='HP')
        for room in hp_rooms:
            room.status = 'gesperrt'
            room.save()

        start = date.today()
        end = date.today() + timedelta(days=14)

        suggested = MobileClassroom.get_suggested_classroom(start, end)
        assert suggested is not None
        assert suggested.room_type == 'AC'


class TestClassroomDeployment:
    """Tests for ClassroomDeployment model."""

    @pytest.fixture
    def deployment_setup(self, db):
        """Create setup for deployment tests."""
        classroom = MobileClassroom.objects.create(
            name='HP01',
            room_type='HP',
            status='auf_lager',
        )
        location = ShippingAddress.objects.create(
            name='Munich Training Center',
            location_type='training',
            street='Main St 123',
            postal_code='80001',
            city='Munich',
        )
        return classroom, location

    @pytest.mark.unit
    def test_deployment_creation(self, deployment_setup):
        """Test creating a deployment."""
        classroom, location = deployment_setup
        deployment = ClassroomDeployment.objects.create(
            classroom=classroom,
            location=location,
            deployment_start=date.today() + timedelta(days=30),
            deployment_end=date.today() + timedelta(days=45),
        )
        assert deployment.classroom == classroom
        assert deployment.location == location

    @pytest.mark.unit
    def test_is_in_deployment(self, deployment_setup):
        """Test is_in_deployment method."""
        classroom, location = deployment_setup
        today = date.today()

        # Not in deployment (future)
        deployment = ClassroomDeployment.objects.create(
            classroom=classroom,
            location=location,
            deployment_start=today + timedelta(days=30),
            deployment_end=today + timedelta(days=45),
        )
        assert deployment.is_in_deployment() is False

        # In deployment (today within range)
        deployment2 = ClassroomDeployment.objects.create(
            classroom=classroom,
            location=location,
            deployment_start=today - timedelta(days=5),
            deployment_end=today + timedelta(days=10),
        )
        assert deployment2.is_in_deployment() is True

    @pytest.mark.unit
    def test_deployment_string_representation(self, deployment_setup):
        """Test __str__ method."""
        classroom, location = deployment_setup
        deployment = ClassroomDeployment.objects.create(
            classroom=classroom,
            location=location,
            deployment_start=date.today() + timedelta(days=30),
            deployment_end=date.today() + timedelta(days=45),
        )
        assert 'HP01' in str(deployment)
        assert 'Munich' in str(deployment)


class TestDeploymentHistory:
    """Tests for DeploymentHistory model."""

    @pytest.fixture
    def deployment_with_history(self, db, aboro_admin):
        """Create deployment with history."""
        classroom = MobileClassroom.objects.create(
            name='HP01',
            room_type='HP',
        )
        location = ShippingAddress.objects.create(
            name='Munich',
            street='Main St',
            postal_code='80001',
            city='Munich',
        )
        deployment = ClassroomDeployment.objects.create(
            classroom=classroom,
            location=location,
            deployment_start=date.today() + timedelta(days=30),
            deployment_end=date.today() + timedelta(days=45),
        )
        return deployment, aboro_admin

    @pytest.mark.unit
    def test_deployment_history_creation(self, deployment_with_history):
        """Test creating deployment history."""
        deployment, user = deployment_with_history
        history = DeploymentHistory.objects.create(
            deployment=deployment,
            event_type='versand_geplant',
            event_date=timezone.now(),
            user=user,
            notes='Shipping planned'
        )
        assert history.deployment == deployment
        assert history.event_type == 'versand_geplant'
        assert history.user == user


class TestChecklistTemplate:
    """Tests for ChecklistTemplate model."""

    @pytest.mark.unit
    def test_create_checklist_template(self, db):
        """Test creating a checklist template."""
        template = ChecklistTemplate.objects.create(
            name='Technical Inspection AC',
            room_type='AC',
            description='Technical inspection for AC classrooms',
        )
        assert template.name == 'Technical Inspection AC'
        assert template.room_type == 'AC'
        assert template.is_active is True

    @pytest.mark.unit
    def test_checklist_template_string(self, db):
        """Test __str__ method."""
        template = ChecklistTemplate.objects.create(
            name='Technical Inspection AC',
            room_type='AC',
        )
        assert str(template) == 'Technical Inspection AC'


@pytest.mark.integration
class TestClassroomIntegration:
    """Integration tests for classroom functionality."""

    @pytest.mark.integration
    def test_full_deployment_workflow(self, db, aboro_user, aboro_admin):
        """Test complete deployment workflow."""
        # Create classroom
        classroom = MobileClassroom.objects.create(
            name='HP01',
            room_type='HP',
            status='auf_lager',
        )

        # Create location
        location = ShippingAddress.objects.create(
            name='Munich Training',
            street='Main St 123',
            postal_code='80001',
            city='Munich',
        )

        # Create deployment
        deployment = ClassroomDeployment.objects.create(
            classroom=classroom,
            location=location,
            deployment_start=date.today() + timedelta(days=30),
            deployment_end=date.today() + timedelta(days=45),
            shipping_date=date.today() + timedelta(days=29),
            pickup_date=date.today() + timedelta(days=46),
        )

        # Check classroom is unavailable during deployment
        is_available, _ = classroom.is_available_for_deployment(
            date.today() + timedelta(days=35),
            date.today() + timedelta(days=40),
        )
        assert is_available is False

        # Create history
        DeploymentHistory.objects.create(
            deployment=deployment,
            event_type='versendet',
            event_date=timezone.now(),
            user=aboro_admin,
        )

        # Verify history exists
        assert deployment.history_entries.count() == 1
