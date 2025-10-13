from dataclasses import dataclass
from enum import Enum
from src.app.common.nav.encode import encode_id
from typing import Any


class GlobalRole(Enum):
    SUPER_ADMIN = 'super_admin'
    PARTICIPANT = 'participant'
    SUPPORT_TECHNICIAN = 'support_technician'


class GroupRole(Enum):
    MANAGER = 'manager'
    MEMBER = 'member'


class GroupVisibility(Enum):
    PUBLIC = 'public'
    PRIVATE = 'private'


class GroupStatus(Enum):
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    PENDING = 'pending'


@dataclass
class User:
    id: Any = None
    first_name: Any = None
    last_name: Any = None
    gender: Any = None
    age: Any = None
    age_group: Any = None
    town: Any = None
    email: Any = None
    password_hash: Any = None
    global_role: Any = None
    status: Any = None

    @property
    def encoded_user_id(self):
        return encode_id(self.id) if self.id is not None else None

    @property
    def resource_id(self):
        """
        Returns the resource ID for this user based on their role.
        For route guarding and authorization purposes.
        """
        return self.id

    @property
    def is_super_admin(self) -> bool:
        return self.global_role == GlobalRole.SUPER_ADMIN

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


@dataclass
class CommunityGroup:
    id: Any = None
    name: Any = None
    description: Any = None
    town: Any = None
    visibility: Any = None
    status: Any = None
    created_by: Any = None

    @property
    def encoded_group_id(self):
        return encode_id(self.id) if self.id is not None else None

    @property
    def is_public(self) -> bool:
        return self.visibility == GroupVisibility.PUBLIC


@dataclass
class GroupMembership:
    group_id: Any = None
    user_id: Any = None
    group_role: Any = None
    member_status: Any = None

    # Additional fields for joined data
    group_name: Any = None
    user_name: Any = None

    @property
    def is_manager(self) -> bool:
        return self.group_role == GroupRole.MANAGER

    @property
    def is_active(self) -> bool:
        return self.member_status == 'active'


@dataclass
class GroupApplication:
    id: Any = None
    applicant_id: Any = None
    proposed_name: Any = None
    proposed_description: Any = None
    proposed_town: Any = None
    visibility: Any = None
    status: Any = None
    decision_by: Any = None

    # Additional fields for joined data
    applicant_name: Any = None
    decision_maker_name: Any = None

    @property
    def is_pending(self) -> bool:
        return self.status == 'pending'

    @property
    def is_approved(self) -> bool:
        return self.status == 'approved'

    @property
    def is_rejected(self) -> bool:
        return self.status == 'rejected'


# Legacy Role enum for backward compatibility during migration
class Role(Enum):
    ADMIN = 'super_admin'
    PARTICIPANT = 'participant'
    GROUP_MANAGER = 'group_manager'
