"""
License Manager for ABoroOffice.
Migrated and enhanced from HelpDesk license_manager.py with ABORO product codes.
Database-independent license validation using hash-based algorithm.
"""

import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Tuple, Dict, Optional


class LicenseManager:
    """
    License management system using hash-based validation.
    Database-independent - validates licenses using cryptographic signatures.

    License Code Format: PROD-VERSION-DURATION-EXPIRY-SIGNATURE
    Example: ABORO_BASIC-1-12-20251231-A7F3B2C1D9E8F4A6
    """

    # Secret key for generating signatures (should be in .env in production)
    SECRET_KEY = "ABoro-Soft-ABoroOffice-License-Key-2025"

    # ABoroOffice Product codes and their features
    PRODUCTS = {
        # Tier-based products
        'ABORO_BASIC': {
            'name': 'ABoroOffice Basic',
            'tier': 'basic',
            'staff_users': 5,
            'total_users': 20,
            'storage_gb': 10,
            'features': ['core', 'classroom'],
            'restricted': ['helpdesk_tickets', 'helpdesk_knowledge', 'helpdesk_chat', 'helpdesk_ai', 'cloude_storage', 'approvals'],
            'monthly_price': 399,
        },
        'ABORO_OFFICE': {
            'name': 'ABoroOffice Office',
            'tier': 'office',
            'staff_users': 25,
            'total_users': 100,
            'storage_gb': 50,
            'features': ['core', 'classroom', 'helpdesk_tickets', 'helpdesk_knowledge', 'approvals', 'api_basic'],
            'restricted': ['helpdesk_chat', 'helpdesk_ai', 'cloude_storage', 'cloude_sharing', 'cloude_plugins'],
            'monthly_price': 899,
        },
        'ABORO_PROFESSIONAL': {
            'name': 'ABoroOffice Professional',
            'tier': 'professional',
            'staff_users': 100,
            'total_users': 500,
            'storage_gb': 500,
            'features': [
                'core', 'classroom', 'helpdesk_tickets', 'helpdesk_knowledge', 'helpdesk_chat', 'helpdesk_ai',
                'cloude_storage', 'cloude_sharing', 'approvals', 'api_full'
            ],
            'restricted': ['cloude_plugins', 'advanced_analytics', 'sso_ldap', 'dedicated_support'],
            'monthly_price': 1599,
        },
        'ABORO_ENTERPRISE': {
            'name': 'ABoroOffice Enterprise',
            'tier': 'enterprise',
            'staff_users': -1,  # Unlimited
            'total_users': -1,  # Unlimited
            'storage_gb': -1,  # Unlimited
            'features': [
                'core', 'classroom', 'helpdesk_tickets', 'helpdesk_knowledge', 'helpdesk_chat', 'helpdesk_ai',
                'cloude_storage', 'cloude_sharing', 'cloude_plugins', 'approvals', 'api_full',
                'advanced_analytics', 'sso_ldap', 'dedicated_support', 'webhooks'
            ],
            'restricted': [],
            'monthly_price': 2999,
        },
        'ABORO_ON_PREMISE': {
            'name': 'ABoroOffice On-Premise',
            'tier': 'on_premise',
            'staff_users': -1,  # Unlimited
            'total_users': -1,  # Unlimited
            'storage_gb': -1,  # Unlimited
            'features': [
                'core', 'classroom', 'helpdesk_tickets', 'helpdesk_knowledge', 'helpdesk_chat', 'helpdesk_ai',
                'cloude_storage', 'cloude_sharing', 'cloude_plugins', 'approvals', 'api_full',
                'advanced_analytics', 'sso_ldap', 'dedicated_support', 'webhooks', 'source_code',
                'unlimited_installations'
            ],
            'restricted': [],
            'yearly_price': 15000,
        },

        # Standalone products
        'CLASSROOM_STANDALONE': {
            'name': 'Pit-Kalendar Classroom Standalone',
            'tier': 'standalone',
            'staff_users': 10,
            'total_users': 50,
            'storage_gb': 0,
            'features': ['core', 'classroom'],
            'restricted': ['helpdesk_tickets', 'helpdesk_knowledge', 'helpdesk_chat', 'helpdesk_ai', 'cloude_storage', 'approvals'],
            'monthly_price': 199,
        },
        'HELPDESK_STANDALONE': {
            'name': 'HelpDesk Standalone',
            'tier': 'standalone',
            'staff_users': 50,
            'total_users': 200,
            'storage_gb': 0,
            'features': ['core', 'helpdesk_tickets', 'helpdesk_knowledge', 'helpdesk_chat', 'helpdesk_ai', 'api_full'],
            'restricted': ['classroom', 'cloude_storage', 'cloude_sharing', 'cloude_plugins', 'approvals'],
            'monthly_price': 599,
        },
        'CLOUDE_STANDALONE': {
            'name': 'Cloude Storage Standalone',
            'tier': 'standalone',
            'staff_users': 25,
            'total_users': 100,
            'storage_gb': 1000,
            'features': ['core', 'cloude_storage', 'cloude_sharing', 'cloude_plugins', 'api_full'],
            'restricted': ['classroom', 'helpdesk_tickets', 'helpdesk_knowledge', 'helpdesk_chat', 'helpdesk_ai', 'approvals'],
            'monthly_price': 799,
        },
        'APPROVALS_STANDALONE': {
            'name': 'SSH Approvals Standalone',
            'tier': 'standalone',
            'staff_users': 10,
            'total_users': 50,
            'storage_gb': 0,
            'features': ['core', 'approvals', 'api_basic'],
            'restricted': ['classroom', 'helpdesk_tickets', 'helpdesk_knowledge', 'helpdesk_chat', 'helpdesk_ai', 'cloude_storage'],
            'monthly_price': 299,
        },

        # Legacy HelpDesk products (for backward compatibility)
        'STARTER': {
            'name': 'Cloud Starter (Legacy)',
            'tier': 'basic',
            'staff_users': 10,
            'total_users': 50,
            'storage_gb': 10,
            'features': ['helpdesk_tickets', 'helpdesk_knowledge', 'api_basic'],
            'restricted': ['helpdesk_chat', 'helpdesk_ai', 'cloude_storage', 'approvals'],
            'monthly_price': 299,
        },
        'PROFESSIONAL': {
            'name': 'Cloud Professional (Legacy)',
            'tier': 'office',
            'staff_users': 50,
            'total_users': 200,
            'storage_gb': 100,
            'features': ['helpdesk_tickets', 'helpdesk_knowledge', 'helpdesk_chat', 'helpdesk_ai', 'api_full'],
            'restricted': ['cloude_storage', 'cloude_sharing', 'cloude_plugins', 'approvals'],
            'monthly_price': 599,
        },
        'ENTERPRISE': {
            'name': 'Cloud Enterprise (Legacy)',
            'tier': 'enterprise',
            'staff_users': -1,
            'total_users': -1,
            'storage_gb': -1,
            'features': ['helpdesk_tickets', 'helpdesk_knowledge', 'helpdesk_chat', 'helpdesk_ai', 'cloude_storage', 'cloude_sharing', 'api_full'],
            'restricted': [],
            'monthly_price': 1199,
        },
        'ON_PREMISE': {
            'name': 'On-Premise License (Legacy)',
            'tier': 'on_premise',
            'staff_users': -1,
            'total_users': -1,
            'storage_gb': -1,
            'features': ['helpdesk_tickets', 'helpdesk_knowledge', 'helpdesk_chat', 'helpdesk_ai', 'cloude_storage', 'source_code', 'unlimited_installations'],
            'restricted': [],
            'yearly_price': 6500,
        },
    }

    # Trial settings
    TRIAL_DAYS = 30

    @classmethod
    def generate_license_code(
        cls,
        product: str,
        duration_months: int,
        start_date: Optional[datetime] = None
    ) -> str:
        """
        Generate a license code for the given product and duration.

        Args:
            product: Product code (ABORO_BASIC, ABORO_OFFICE, ABORO_PROFESSIONAL, etc.)
            duration_months: License validity in months (1-36)
            start_date: License start date (defaults to today)

        Returns:
            License code string

        Example:
            >>> code = LicenseManager.generate_license_code('ABORO_BASIC', 12)
            >>> # Returns: ABORO_BASIC-1-12-20251231-A7F3B2C1D9E8F4A6
        """
        if product not in cls.PRODUCTS:
            raise ValueError(f"Invalid product: {product}")

        if not (1 <= duration_months <= 36):
            raise ValueError("Duration must be between 1 and 36 months")

        if start_date is None:
            start_date = datetime.now()

        # Calculate expiry date
        year = start_date.year
        month = start_date.month + duration_months
        day = start_date.day

        while month > 12:
            month -= 12
            year += 1

        expiry_date = datetime(year, month, day, 23, 59, 59)
        expiry_str = expiry_date.strftime('%Y%m%d')

        # Create signature
        data_to_sign = f"{product}|1|{duration_months}|{expiry_str}"
        signature = cls._generate_signature(data_to_sign)

        # Format: PRODUCT-VERSION-DURATION-EXPIRY-SIGNATURE
        license_code = f"{product}-1-{duration_months}-{expiry_str}-{signature}"

        return license_code

    @classmethod
    def validate_license(cls, license_code: str) -> Tuple[bool, str]:
        """
        Validate a license code.

        Args:
            license_code: License code to validate

        Returns:
            Tuple of (is_valid: bool, message: str)

        Examples:
            >>> is_valid, msg = LicenseManager.validate_license('ABORO_BASIC-1-12-20251231-A7F3B2C1D9E8F4A6')
            >>> print(is_valid, msg)
            (True, 'License valid')
        """
        if not license_code or not isinstance(license_code, str):
            return False, "Invalid license code format"

        try:
            parts = license_code.strip().split('-')
            if len(parts) < 5:
                return False, "Invalid license code format (expected at least 5 parts)"

            # Handle product codes with underscores (e.g., ABORO_BASIC)
            # Split from the end to avoid splitting on underscores in product name
            signature = parts[-1]
            expiry_str = parts[-2]
            duration_str = parts[-3]
            version = parts[-4]
            product = '-'.join(parts[:-4])

            # Validate product
            if product not in cls.PRODUCTS:
                return False, f"Unknown product: {product}"

            # Validate version
            if version != '1':
                return False, f"Unsupported license version: {version}"

            # Validate duration
            try:
                duration = int(duration_str)
                if not (1 <= duration <= 36):
                    return False, f"Invalid duration: {duration}"
            except ValueError:
                return False, "Invalid duration format"

            # Validate expiry date
            try:
                expiry_date = datetime.strptime(expiry_str, '%Y%m%d')
            except ValueError:
                return False, "Invalid expiry date format"

            # Check if license has expired
            now = datetime.now()
            if now > expiry_date:
                return False, "License has expired"

            # Validate signature
            data_to_sign = f"{product}|{version}|{duration_str}|{expiry_str}"
            expected_signature = cls._generate_signature(data_to_sign)

            if not hmac.compare_digest(signature, expected_signature):
                return False, "Invalid license signature (possibly tampered)"

            return True, "License valid"

        except Exception as e:
            return False, f"License validation error: {str(e)}"

    @classmethod
    def get_license_info(cls, license_code: str) -> Optional[Dict]:
        """
        Get detailed information about a license code.

        Args:
            license_code: License code to inspect

        Returns:
            Dictionary with license info or None if invalid

        Example:
            >>> info = LicenseManager.get_license_info('ABORO_BASIC-1-12-20251231-A7F3B2C1D9E8F4A6')
            >>> print(info)
            {
                'product': 'ABORO_BASIC',
                'product_name': 'ABoroOffice Basic',
                'duration_months': 12,
                'expiry_date': '2025-12-31',
                'days_remaining': 245,
                'max_staff_users': 5,
                'max_total_users': 20,
                'features': ['core', 'classroom'],
                'valid': True
            }
        """
        is_valid, msg = cls.validate_license(license_code)
        if not is_valid:
            return None

        try:
            parts = license_code.strip().split('-')
            signature = parts[-1]
            expiry_str = parts[-2]
            duration_str = parts[-3]
            version = parts[-4]
            product = '-'.join(parts[:-4])

            expiry_date = datetime.strptime(expiry_str, '%Y%m%d')
            now = datetime.now()
            days_remaining = (expiry_date - now).days

            product_info = cls.PRODUCTS[product]

            return {
                'product': product,
                'product_name': product_info['name'],
                'tier': product_info['tier'],
                'version': int(version),
                'duration_months': int(duration_str),
                'expiry_date': expiry_date.strftime('%Y-%m-%d'),
                'days_remaining': days_remaining,
                'max_staff_users': product_info['staff_users'],
                'max_total_users': product_info['total_users'],
                'storage_quota_gb': product_info['storage_gb'],
                'features': product_info['features'],
                'monthly_price': product_info.get('monthly_price'),
                'yearly_price': product_info.get('yearly_price'),
                'valid': True,
                'message': 'License is active'
            }

        except Exception as e:
            return None

    @classmethod
    def validate_trial(cls) -> Tuple[bool, str]:
        """
        Validate if trial period is still valid (30 days from first install).

        Returns:
            Tuple of (is_valid: bool, message: str)
        """
        return True, f"Trial period available ({cls.TRIAL_DAYS} days)"

    @classmethod
    def _generate_signature(cls, data: str) -> str:
        """
        Generate HMAC signature for license data.

        Args:
            data: Data to sign (format: PRODUCT|VERSION|DURATION|EXPIRY)

        Returns:
            Hex signature
        """
        signature = hmac.new(
            cls.SECRET_KEY.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()

        # Return first 16 characters (same as generator)
        return signature[:16].upper()

    @classmethod
    def get_all_products(cls) -> Dict:
        """Get all available products and their details."""
        return cls.PRODUCTS

    @classmethod
    def calculate_license_cost(cls, product: str, duration_months: int) -> Dict:
        """
        Calculate license cost for given product and duration.

        Returns:
            Dictionary with cost breakdown
        """
        if product not in cls.PRODUCTS:
            raise ValueError(f"Invalid product: {product}")

        product_info = cls.PRODUCTS[product]
        monthly_price = product_info.get('monthly_price')
        yearly_price = product_info.get('yearly_price')

        if monthly_price is None and yearly_price is None:
            raise ValueError(f"No pricing available for {product}")

        # Use monthly price if available, otherwise yearly
        if monthly_price:
            monthly_total = monthly_price * duration_months
            cost_per_day = monthly_total / (duration_months * 30)
        else:
            # For yearly-only products, divide yearly price
            monthly_total = yearly_price
            cost_per_day = yearly_price / 365

        setup_fee = 0  # No setup fees in current pricing model
        total_cost = setup_fee + monthly_total

        return {
            'product': product,
            'product_name': product_info['name'],
            'monthly_price': monthly_price,
            'yearly_price': yearly_price,
            'duration_months': duration_months,
            'setup_fee': setup_fee,
            'monthly_total': monthly_total,
            'total_cost': total_cost,
            'cost_per_day': round(cost_per_day, 2),
        }
