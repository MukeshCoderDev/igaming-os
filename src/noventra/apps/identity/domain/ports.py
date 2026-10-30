"""Identity domain ports (interfaces)."""

from __future__ import annotations

import abc
import uuid
from typing import Optional

from .aggregates import Role, ServiceIdentity, TenantMembership, User


class UserRepository(abc.ABC):
    @abc.abstractmethod
    def get_by_uuid(self, user_uuid: uuid.UUID) -> Optional[User]: ...

    @abc.abstractmethod
    def get_by_email(self, email: str) -> Optional[User]: ...

    @abc.abstractmethod
    def save(self, user: User) -> None: ...


class TenantMembershipRepository(abc.ABC):
    @abc.abstractmethod
    def get(self, membership_uuid: uuid.UUID) -> Optional[TenantMembership]: ...

    @abc.abstractmethod
    def get_active(self, user_uuid: uuid.UUID, tenant_uuid: uuid.UUID) -> Optional[TenantMembership]: ...

    @abc.abstractmethod
    def list_for_user(self, user_uuid: uuid.UUID) -> list[TenantMembership]: ...

    @abc.abstractmethod
    def save(self, membership: TenantMembership) -> None: ...


class RoleRepository(abc.ABC):
    @abc.abstractmethod
    def get_by_uuid(self, role_uuid: uuid.UUID) -> Optional[Role]: ...

    @abc.abstractmethod
    def get_by_name(self, name: str) -> Optional[Role]: ...

    @abc.abstractmethod
    def permissions_for_role(self, role_uuid: uuid.UUID) -> list[str]: ...


class ServiceIdentityRepository(abc.ABC):
    @abc.abstractmethod
    def get_by_uuid(self, service_uuid: uuid.UUID) -> Optional[ServiceIdentity]: ...

    @abc.abstractmethod
    def save(self, service: ServiceIdentity) -> None: ...
