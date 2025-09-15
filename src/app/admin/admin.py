from dataclasses import dataclass

from src.app.common.nav.encode import encode_id
from src.app.user.user import User


@dataclass
class Admin(User):
    pass

    @property
    def encoded_admin_id(self) -> str:
        return encode_id(self.user_id)
