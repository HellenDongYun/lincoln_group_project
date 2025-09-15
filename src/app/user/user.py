from dataclasses import dataclass
from enum import Enum

from src.app.common.nav.encode import encode_id


class Role(Enum):
    ADMIN = 'admin'
    PARTICIPANT = 'participant'
    VOLUNTEER = 'volunteer'

@dataclass
class User:
    id: int = None
    first_name: str = None
    last_name: str = None
    town: str = None
    email: str = None
    password_hash: str = None
    role: Role = None
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
        # In this implementation, all roles use the same user ID as their resource ID
        return self.id
