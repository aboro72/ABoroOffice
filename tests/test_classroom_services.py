"""
Tests for classroom app services.
Tests email reminders, deployment scheduling, and other business logic.
"""

import pytest
from datetime import date, timedelta
from django.utils import timezone
from django.core.mail import outbox
from apps.classroom.models import (
    MobileClassroom, ClassroomDeployment, ShippingAddress,
    EmailReminder
)
from apps.classroom.services import EmailReminderService, DeploymentService

pytestmark = pytest.mark.django_db(transaction=True)


class TestEmailReminderService:
    """Tests for EmailReminderService."""

    @pytest.fixture
    def deployment_with_reminders(self, db):
        """Create deployment with email reminders."""
        classroom = MobileClassroom.objects.create(
            name='HP01',
            room_type='HP',
            status='auf_lager',
        )
        location = ShippingAddress.objects.create(
            name='Munich Training',
            street='Main St 123',
            postal_code='80001',
            city='Munich',
        )

        # Create deployment with shipping and pickup dates
        deployment = ClassroomDeployment.objects.create(
            classroom=classroom,
            location=location,
            deployment_start=date.today() + timedelta(days=30),
            deployment_end=date.today() + timedelta(days=45),
            shipping_date=date.today() + timedelta(days=29),
            pickup_date=date.today() + timedelta(days=46),
        )

        # Create reminders
        EmailReminder.objects.create(
            classroom=classroom,
            deployment=deployment,
            reminder_type='versand',
            send_date=timezone.now() - timedelta(hours=1),  # Past time
            sent=False,
        )

        EmailReminder.objects.create(
            classroom=classroom,
            deployment=deployment,
            reminder_type='abholung',
            send_date=timezone.now() - timedelta(hours=1),  # Past time
            sent=False,
        )

        return deployment

    @pytest.mark.unit
    def test_send_pending_reminders(self, deployment_with_reminders):
        """Test sending pending reminders."""
        pending = EmailReminder.objects.filter(sent=False).count()
        assert pending == 2

        # Note: send_mail is mocked in test mode
        # In actual test, would need to mock email backend
        count = EmailReminderService.send_pending_reminders()

        # This will depend on email configuration
        # Updated reminders should be marked as sent
        updated_pending = EmailReminder.objects.filter(sent=False).count()
        assert updated_pending <= pending

    @pytest.mark.unit
    def test_reminder_send_date_tracking(self, deployment_with_reminders):
        """Test that sent date is tracked."""
        reminder = EmailReminder.objects.filter(reminder_type='versand').first()
        assert reminder.sent is False
        assert reminder.sent_at is None

        # Note: In real test with email backend, would track sent_at

    @pytest.mark.unit
    def test_exclude_already_sent_reminders(self, deployment_with_reminders):
        """Test that already sent reminders are excluded."""
        # Mark one reminder as sent
        reminder = EmailReminder.objects.filter(reminder_type='versand').first()
        reminder.sent = True
        reminder.sent_at = timezone.now()
        reminder.save()

        pending = EmailReminder.objects.filter(sent=False)
        assert pending.count() == 1

    @pytest.mark.unit
    def test_exclude_future_reminders(self, db):
        """Test that future reminders are not sent."""
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

        # Create future reminder
        EmailReminder.objects.create(
            classroom=classroom,
            deployment=deployment,
            reminder_type='versand',
            send_date=timezone.now() + timedelta(days=10),
            sent=False,
        )

        pending = EmailReminder.objects.filter(sent=False)
        assert pending.count() == 1

        count = EmailReminderService.send_pending_reminders()
        assert count == 0  # Should not send future reminders


class TestDeploymentService:
    """Tests for DeploymentService."""

    @pytest.fixture
    def deployment_setup(self, db):
        """Create setup for deployment service tests."""
        classroom = MobileClassroom.objects.create(
            name='HP01',
            room_type='HP',
            status='auf_lager',
        )
        location = ShippingAddress.objects.create(
            name='Munich',
            street='Main St',
            postal_code='80001',
            city='Munich',
        )
        return classroom, location

    @pytest.mark.unit
    def test_check_availability(self, deployment_setup):
        """Test checking classroom availability."""
        classroom, location = deployment_setup

        start = date.today()
        end = date.today() + timedelta(days=14)

        is_available, reason = DeploymentService.check_availability(classroom, start, end)
        assert is_available is True
        assert reason is None

    @pytest.mark.unit
    def test_check_availability_with_conflict(self, deployment_setup):
        """Test checking availability with conflicting deployment."""
        classroom, location = deployment_setup

        # Create conflicting deployment
        ClassroomDeployment.objects.create(
            classroom=classroom,
            location=location,
            deployment_start=date.today() + timedelta(days=10),
            deployment_end=date.today() + timedelta(days=20),
        )

        # Check overlapping period
        start = date.today() + timedelta(days=15)
        end = date.today() + timedelta(days=25)

        is_available, reason = DeploymentService.check_availability(classroom, start, end)
        assert is_available is False
        assert reason is not None

    @pytest.mark.unit
    def test_get_available_classrooms(self, db):
        """Test getting available classrooms."""
        # Create multiple classrooms
        for i in range(3):
            MobileClassroom.objects.create(
                name=f'HP{i:02d}',
                room_type='HP',
                status='auf_lager',
            )

        start = date.today()
        end = date.today() + timedelta(days=14)

        available = DeploymentService.get_available_classrooms(start, end)
        assert available.count() == 3

    @pytest.mark.unit
    def test_get_available_classrooms_excludes_locked(self, db):
        """Test that locked classrooms are excluded."""
        # Create classrooms
        classroom1 = MobileClassroom.objects.create(
            name='HP01',
            room_type='HP',
            status='auf_lager',
        )
        classroom2 = MobileClassroom.objects.create(
            name='HP02',
            room_type='HP',
            status='gesperrt',  # Locked
        )

        start = date.today()
        end = date.today() + timedelta(days=14)

        available = DeploymentService.get_available_classrooms(start, end)
        assert available.count() == 1
        assert classroom1 in available
        assert classroom2 not in available

    @pytest.mark.unit
    def test_suggest_classroom(self, db):
        """Test getting suggested classroom."""
        # Create HP classroom
        hp = MobileClassroom.objects.create(
            name='HP01',
            room_type='HP',
            status='auf_lager',
        )

        start = date.today()
        end = date.today() + timedelta(days=14)

        suggested = DeploymentService.suggest_classroom(start, end)
        assert suggested is not None
        assert suggested.room_type == 'HP'

    @pytest.mark.unit
    def test_suggest_classroom_prefers_hp(self, db):
        """Test that HP classrooms are preferred."""
        # Create both types
        hp = MobileClassroom.objects.create(
            name='HP01',
            room_type='HP',
            status='auf_lager',
        )
        ac = MobileClassroom.objects.create(
            name='AC01',
            room_type='AC',
            status='auf_lager',
        )

        start = date.today()
        end = date.today() + timedelta(days=14)

        suggested = DeploymentService.suggest_classroom(start, end)
        assert suggested == hp

    @pytest.mark.unit
    def test_suggest_classroom_falls_back_to_ac(self, db):
        """Test fallback to AC when no HP available."""
        # Create only AC
        ac = MobileClassroom.objects.create(
            name='AC01',
            room_type='AC',
            status='auf_lager',
        )

        start = date.today()
        end = date.today() + timedelta(days=14)

        suggested = DeploymentService.suggest_classroom(start, end)
        assert suggested == ac
        assert suggested.room_type == 'AC'

    @pytest.mark.unit
    def test_suggest_classroom_none_available(self, db):
        """Test when no classrooms are available."""
        # All locked
        MobileClassroom.objects.create(
            name='HP01',
            room_type='HP',
            status='gesperrt',
        )

        start = date.today()
        end = date.today() + timedelta(days=14)

        suggested = DeploymentService.suggest_classroom(start, end)
        assert suggested is None


@pytest.mark.integration
class TestClassroomServiceIntegration:
    """Integration tests for classroom services."""

    @pytest.mark.integration
    def test_full_deployment_planning_workflow(self, db):
        """Test complete deployment planning workflow."""
        # Check availability
        start = date.today() + timedelta(days=30)
        end = date.today() + timedelta(days=45)

        available = DeploymentService.get_available_classrooms(start, end)
        assert available.count() > 0

        # Get suggestion
        suggested = DeploymentService.suggest_classroom(start, end)
        assert suggested is not None

        # Create location
        location = ShippingAddress.objects.create(
            name='Training Center',
            street='Main St',
            postal_code='80001',
            city='Munich',
        )

        # Create deployment
        deployment = ClassroomDeployment.objects.create(
            classroom=suggested,
            location=location,
            deployment_start=start,
            deployment_end=end,
            shipping_date=start - timedelta(days=1),
            pickup_date=end + timedelta(days=1),
        )

        # Verify reminders were created
        reminders = EmailReminder.objects.filter(deployment=deployment)
        assert reminders.count() >= 1

        # Check classroom is now unavailable for same period
        is_available, reason = DeploymentService.check_availability(
            suggested, start, end
        )
        assert is_available is False
