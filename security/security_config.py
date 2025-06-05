"""Security configuration for Bangladesh Student Data Analytics.

This module provides security configurations and utilities for:
- Data encryption
- Access control
- Authentication
- Audit logging
"""

import logging
from typing import Dict, Optional


class SecurityConfig:
    """Central security configuration for the application."""

    def __init__(self):
        """Initialize SecurityConfig with access levels, sensitive fields, and retention periods."""
        self.logger = logging.getLogger(__name__)

        # Access Control Levels
        self.ACCESS_LEVELS = {
            "ADMIN": 100,
            "ANALYST": 75,
            "RESEARCHER": 50,
            "VIEWER": 25,
        }

        # Sensitive Data Fields
        self.SENSITIVE_FIELDS = [
            "student_id",
            "name",
            "date_of_birth",
            "address",
            "guardian_info",
            "contact_number",
        ]

        # Data Retention Periods (in days)
        self.RETENTION_PERIODS = {
            "raw_data": 365,
            "processed_data": 730,
            "audit_logs": 1825,
            "user_activity": 180,
        }

    def get_required_access_level(self, operation: str) -> int:
        """Determine required access level for an operation.

        Args:
            operation: The operation being performed

        Returns:
            Required access level for the operation
        """
        access_mapping = {
            "view_basic": self.ACCESS_LEVELS["VIEWER"],
            "view_sensitive": self.ACCESS_LEVELS["RESEARCHER"],
            "modify_data": self.ACCESS_LEVELS["ANALYST"],
            "manage_users": self.ACCESS_LEVELS["ADMIN"],
        }
        return access_mapping.get(operation, self.ACCESS_LEVELS["ADMIN"])

    def should_encrypt_field(self, field_name: str) -> bool:
        """Determine if a field should be encrypted.

        Args:
            field_name: Name of the data field

        Returns:
            Boolean indicating if field should be encrypted
        """
        return field_name in self.SENSITIVE_FIELDS

    def get_retention_period(self, data_type: str) -> Optional[int]:
        """Get retention period for a type of data.

        Args:
            data_type: Type of data

        Returns:
            Number of days to retain the data
        """
        return self.RETENTION_PERIODS.get(data_type)

    def get_audit_config(self) -> Dict:
        """Get audit logging configuration.

        Returns:
            Dictionary of audit logging settings
        """
        return {
            "enabled": True,
            "log_level": logging.INFO,
            "include_user_id": True,
            "include_timestamp": True,
            "include_ip_address": True,
            "retention_days": self.RETENTION_PERIODS["audit_logs"],
        }

    def get_security_headers(self) -> Dict[str, str]:
        """Get security headers for HTTP responses.

        Returns:
            Dictionary of security headers
        """
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'",
            "Referrer-Policy": "strict-origin-when-cross-origin",
        }


class DataPrivacyConfig:
    """Configuration for data privacy and protection."""

    def __init__(self):
        """Initialize DataPrivacyConfig with privacy rules and anonymization levels."""
        self.privacy_rules = {
            "student_data": {
                "mask_fields": ["name", "address"],
                "encrypt_fields": ["student_id", "contact_number"],
                "aggregate_only": ["income_level", "family_size"],
            },
            "academic_data": {
                "mask_fields": [],
                "encrypt_fields": ["exam_id"],
                "aggregate_only": ["grades", "attendance"],
            },
        }

        self.anonymization_levels = {
            "research": "partial",  # Some identifying info retained
            "public": "full",  # All identifying info removed
            "internal": "minimal",  # Minimal anonymization
        }

    def get_privacy_rules(self, data_type: str) -> Dict:
        """Get privacy rules for a specific type of data."""
        return self.privacy_rules.get(data_type, {})

    def get_anonymization_level(self, usage: str) -> str:
        """Get required anonymization level for a usage type."""
        return self.anonymization_levels.get(usage, "full")


# Example usage
if __name__ == "__main__":
    security_config = SecurityConfig()
    privacy_config = DataPrivacyConfig()

    # Example security check
    required_level = security_config.get_required_access_level("view_sensitive")
    print(f"Required access level: {required_level}")

    # Example privacy rules
    student_privacy = privacy_config.get_privacy_rules("student_data")
    print(f"Student data privacy rules: {student_privacy}")
