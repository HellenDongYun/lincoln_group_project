from dataclasses import dataclass
from enum import Enum
from typing import Optional

from src.app.common.nav.encode import encode_id


class GlobalRole(Enum):
    SUPER_ADMIN = 'super_admin'
    PARTICIPANT = 'participant'


class GroupRole(Enum):
    MANAGER = 'manager'
    MEMBER = 'member'


class GroupVisibility(Enum):
    PUBLIC = 'public'
    PRIVATE = 'private'


class GroupJoinType(Enum):
    OPEN = 'open'
    CLOSED = 'closed'


class GroupStatus(Enum):
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    PENDING = 'pending'


@dataclass
class User:
    id: int = None
    first_name: str = None
    last_name: str = None
    town: str = None
    email: str = None
    password_hash: str = None
    global_role: GlobalRole = None
    status: str = None

    @property
    def encoded_user_id(self) -> str:
        return encode_id(self.id)

    @property
    def resource_id(self) -> int:
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
    id: int = None
    name: str = None
    description: str = None
    town: str = None
    visibility: GroupVisibility = None
    join_type: GroupJoinType = None
    status: GroupStatus = None
    created_by: int = None

    @property
    def encoded_group_id(self) -> str:
        return encode_id(self.id)

    @property
    def is_public(self) -> bool:
        return self.visibility == GroupVisibility.PUBLIC

    @property
    def is_open_join(self) -> bool:
        return self.join_type == GroupJoinType.OPEN


@dataclass
class GroupMembership:
    group_id: int = None
    user_id: int = None
    group_role: GroupRole = None
    member_status: str = None
    
    # Additional fields for joined data
    group_name: str = None
    user_name: str = None

    @property
    def is_manager(self) -> bool:
        return self.group_role == GroupRole.MANAGER

    @property
    def is_active(self) -> bool:
        return self.member_status == 'active'


@dataclass
class GroupApplication:
    id: int = None
    applicant_id: int = None
    proposed_name: str = None
    proposed_description: str = None
    proposed_town: str = None
    visibility: GroupVisibility = None
    join_type: GroupJoinType = None
    status: str = None
    decision_by: Optional[int] = None
    
    # Additional fields for joined data
    applicant_name: str = None
    decision_maker_name: str = None

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
