"""Storage helpers for built-in system authentication users."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from src.db.models import SystemUserModel
from src.db.storage.base import BaseStorage


class UserAuthStorage(BaseStorage):
    """Persistence layer for built-in email/password users."""

    @staticmethod
    def _commit_and_detach(session, user: SystemUserModel) -> SystemUserModel:
        """Persist a user and return a detached instance with loaded scalar fields."""
        session.flush()
        session.refresh(user)
        session.expunge(user)
        session.commit()
        return user

    def get_by_email(self, email: str) -> Optional[SystemUserModel]:
        normalized_email = email.strip().lower()
        with self.managed_session(commit_on_success=False) as session:
            return session.query(SystemUserModel).filter(
                SystemUserModel.email == normalized_email
            ).first()

    def get_by_id(self, user_id: int) -> Optional[SystemUserModel]:
        with self.managed_session(commit_on_success=False) as session:
            return session.query(SystemUserModel).filter(
                SystemUserModel.id == user_id
            ).first()

    def create_user(
        self,
        email: str,
        password_hash: str,
        display_name: str | None = None,
        is_superuser: bool = False,
    ) -> SystemUserModel:
        normalized_email = email.strip().lower()
        normalized_name = (display_name or "").strip() or None
        with self.managed_session(commit_on_success=False) as session:
            user = SystemUserModel(
                email=normalized_email,
                password_hash=password_hash,
                display_name=normalized_name,
                is_superuser=is_superuser,
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            session.add(user)
            return self._commit_and_detach(session, user)

    def update_last_login(self, user_id: int) -> None:
        with self.managed_session() as session:
            user = session.query(SystemUserModel).filter(SystemUserModel.id == user_id).first()
            if user is None:
                return
            user.last_login_at = datetime.utcnow()
            user.updated_at = datetime.utcnow()

    def count_users(self) -> int:
        with self.managed_session(commit_on_success=False) as session:
            return session.query(SystemUserModel).count()

    def list_users(self) -> list[SystemUserModel]:
        with self.managed_session(commit_on_success=False) as session:
            return session.query(SystemUserModel).order_by(SystemUserModel.created_at.asc()).all()

    def set_active(self, user_id: int, is_active: bool) -> Optional[SystemUserModel]:
        with self.managed_session(commit_on_success=False) as session:
            user = session.query(SystemUserModel).filter(SystemUserModel.id == user_id).first()
            if user is None:
                return None
            user.is_active = is_active
            user.updated_at = datetime.utcnow()
            return self._commit_and_detach(session, user)

    def update_password_hash(self, user_id: int, password_hash: str) -> Optional[SystemUserModel]:
        with self.managed_session(commit_on_success=False) as session:
            user = session.query(SystemUserModel).filter(SystemUserModel.id == user_id).first()
            if user is None:
                return None
            user.password_hash = password_hash
            user.updated_at = datetime.utcnow()
            return self._commit_and_detach(session, user)
