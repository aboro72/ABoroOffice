"""
ABoro-Soft Helpdesk License Feature Checker
============================================

Provides feature checking functionality based on license restrictions.
Used throughout the application to enforce license limitations.
"""
from typing import Optional, Dict, Any
from .license_manager import LicenseManager


class LicenseFeatureChecker:
    """
    Checks if features are enabled based on the current license.
    Used to enforce license restrictions throughout the application.
    """
    
    _current_license_info: Optional[Dict] = None
    
    @classmethod
    def set_license(cls, license_code: str) -> bool:
        """
        Set the current license for feature checking.
        
        Args:
            license_code: License code to validate and use
            
        Returns:
            True if license is valid, False otherwise
        """
        license_info = LicenseManager.get_license_info(license_code)
        if license_info and license_info.get('valid'):
            cls._current_license_info = license_info
            return True
        else:
            cls._current_license_info = None
            return False
    
    @classmethod
    def get_current_license(cls) -> Optional[Dict]:
        """Get current license information."""
        return cls._current_license_info
    
    @classmethod
    def has_feature(cls, feature_name: str) -> bool:
        """
        Check if a feature is enabled in the current license.
        
        Args:
            feature_name: Feature to check
            
        Returns:
            True if feature is available, False if restricted or no license
        """
        if not cls._current_license_info:
            # No license set - only basic features available
            basic_features = ['tickets', 'email']
            return feature_name in basic_features
        
        # Check if feature is explicitly allowed
        allowed_features = cls._current_license_info.get('features', [])
        if feature_name in allowed_features:
            return True
        
        # Check if feature is explicitly restricted
        product = cls._current_license_info.get('product', '')
        product_info = LicenseManager.PRODUCTS.get(product, {})
        restricted_features = product_info.get('restricted', [])
        
        return feature_name not in restricted_features
    
    @classmethod
    def get_max_agents(cls) -> int:
        """
        Get maximum number of support agents allowed.
        
        Returns:
            Maximum agents (default: 1 for unlicensed)
        """
        if not cls._current_license_info:
            return 1  # Unlicensed = 1 agent only
        
        return cls._current_license_info.get('max_agents', 1)
    
    @classmethod
    def check_agent_limit(cls, current_agent_count: int) -> bool:
        """
        Check if current agent count exceeds license limit.
        
        Args:
            current_agent_count: Number of active agents
            
        Returns:
            True if within limit, False if exceeded
        """
        max_agents = cls.get_max_agents()
        return current_agent_count <= max_agents
    
    @classmethod
    def get_feature_restrictions(cls) -> Dict[str, Any]:
        """
        Get all feature restrictions for the current license.
        
        Returns:
            Dictionary with feature availability and restrictions
        """
        if not cls._current_license_info:
            return {
                'license_active': False,
                'product': 'UNLICENSED',
                'max_agents': 1,
                'features': {
                    'tickets': True,
                    'email': True,
                    'web_form': False,
                    'knowledge_base': False,
                    'mobile_ready': False,
                    'live_chat': False,
                    'ai_automation': False,
                    'advanced_reporting': False,
                    'custom_branding': False,
                    'api_access': False,
                    'api_full': False,
                    'webhooks': False,
                    'sso_ldap': False,
                    'sla': False,
                    'dedicated_support': False,
                    'unlimited_installations': False,
                    'source_code': False,
                },
                'restrictions': [
                    'Only basic ticket management available',
                    'Maximum 1 support agent',
                    'No AI automation',
                    'No API access',
                    'No live chat support'
                ]
            }
        
        product = cls._current_license_info.get('product', '')
        product_info = LicenseManager.PRODUCTS.get(product, {})
        allowed_features = cls._current_license_info.get('features', [])
        restricted_features = product_info.get('restricted', [])
        
        # All possible features
        all_features = [
            'tickets', 'email', 'web_form', 'knowledge_base', 'mobile_ready',
            'live_chat', 'ai_automation', 'advanced_reporting', 'custom_branding',
            'api_access', 'api_full', 'webhooks', 'sso_ldap', 'sla',
            'dedicated_support', 'unlimited_installations', 'source_code'
        ]
        
        feature_status = {}
        for feature in all_features:
            feature_status[feature] = cls.has_feature(feature)
        
        return {
            'license_active': True,
            'product': product,
            'product_name': cls._current_license_info.get('product_name', ''),
            'max_agents': cls._current_license_info.get('max_agents', 1),
            'expiry_date': cls._current_license_info.get('expiry_date', ''),
            'days_remaining': cls._current_license_info.get('days_remaining', 0),
            'features': feature_status,
            'restricted_features': restricted_features,
        }
    
    @classmethod
    def get_upgrade_suggestions(cls) -> Dict[str, Any]:
        """
        Get suggestions for license upgrades based on current license.
        
        Returns:
            Dictionary with upgrade suggestions
        """
        if not cls._current_license_info:
            return {
                'current': 'UNLICENSED',
                'suggestions': [
                    {
                        'product': 'STARTER',
                        'name': 'Cloud Starter',
                        'price': '€299/month',
                        'benefits': ['10 support agents', 'Knowledge base', 'Web forms', 'Mobile ready']
                    },
                    {
                        'product': 'PROFESSIONAL', 
                        'name': 'Cloud Professional',
                        'price': '€599/month',
                        'benefits': ['50 support agents', 'AI automation', 'Live chat', 'API access', 'Custom branding']
                    }
                ]
            }
        
        current_product = cls._current_license_info.get('product', '')
        suggestions = []
        
        if current_product == 'STARTER':
            suggestions = [
                {
                    'product': 'PROFESSIONAL',
                    'name': 'Cloud Professional', 
                    'price': '€599/month',
                    'benefits': ['Increase to 50 agents', 'AI automation', 'Live chat', 'API access']
                },
                {
                    'product': 'ENTERPRISE',
                    'name': 'Cloud Enterprise',
                    'price': '€1199/month', 
                    'benefits': ['Unlimited agents', 'Full API access', 'SSO/LDAP', 'SLA management']
                }
            ]
        elif current_product == 'PROFESSIONAL':
            suggestions = [
                {
                    'product': 'ENTERPRISE',
                    'name': 'Cloud Enterprise',
                    'price': '€1199/month',
                    'benefits': ['Unlimited agents', 'Full API & webhooks', 'SSO/LDAP', 'SLA management']
                },
                {
                    'product': 'ON_PREMISE',
                    'name': 'On-Premise License',
                    'price': '€6500/year',
                    'benefits': ['Complete control', 'Source code access', 'Unlimited installations']
                }
            ]
        elif current_product == 'ENTERPRISE':
            suggestions = [
                {
                    'product': 'ON_PREMISE',
                    'name': 'On-Premise License', 
                    'price': '€6500/year',
                    'benefits': ['Complete control', 'Source code access', 'Unlimited installations', 'No monthly fees']
                }
            ]
        
        return {
            'current': current_product,
            'current_name': cls._current_license_info.get('product_name', ''),
            'suggestions': suggestions
        }


def require_feature(feature_name: str):
    """
    Decorator to require a specific feature for a view or function.
    
    Usage:
        @require_feature('ai_automation')
        def ai_chat_view(request):
            # This view requires AI automation feature
            pass
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not LicenseFeatureChecker.has_feature(feature_name):
                # Import here to avoid circular imports
                from django.http import JsonResponse
                from django.shortcuts import render
                
                # Check if this is an API request
                request = args[0] if args else None
                if request and hasattr(request, 'META'):
                    if request.META.get('HTTP_ACCEPT', '').startswith('application/json'):
                        return JsonResponse({
                            'error': f'Feature "{feature_name}" not available in current license',
                            'required_license': 'PROFESSIONAL or higher',
                            'upgrade_url': '/admin/license/'
                        }, status=403)
                
                # Render feature not available page
                return render(request, 'license/feature_not_available.html', {
                    'feature_name': feature_name,
                    'current_license': LicenseFeatureChecker.get_current_license(),
                    'upgrade_suggestions': LicenseFeatureChecker.get_upgrade_suggestions()
                })
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def require_agent_limit_check():
    """
    Decorator to check agent limits before allowing actions.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # This would typically check current agent count from database
            # For now, just pass through
            return func(*args, **kwargs)
        return wrapper
    return decorator