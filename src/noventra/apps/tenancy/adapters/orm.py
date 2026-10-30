"""Tenancy ORM adapter — Django models.

Per ADR-0002 (hexagonal): the ORM adapter implements the domain ports
using Django models. Models are infrastructure; domain logic never
imports them.

Per DEC-0003 (RLS): every tenant-scoped table has a tenant_uuid
column (NOT NULL, UUID) and an RLS policy
`USING (tenant_uuid = app.tenant_uuid()) WITH CHECK (...)`.

Per DEC-0014 (tenant aggregate root): the Tenant model is the
operator/tenant. Brand is a child.
"""

from __future__ import annotations

import uuid

from django.db import models


class TenantManager(models.Manager):
    """Manager for the Tenant model.

    Per DEC-0003, queries are RLS-scoped. The manager does NOT
    bypass RLS. Break-glass access uses the noventra_admin role
    (BYPASSRLS) via a separate connection.
    """


class Tenant(models.Model):
    """Tenant (Operator) — a customer institution.

    Per DEC-0014, this is the aggregate root. Every other tenant-
    scoped table carries a FK to this model's tenant_uuid.

    RLS: this table is itself tenant-scoped (a tenant row is visible
    only to its own tenant context). The RLS policy uses
    `tenant_uuid = app.tenant_uuid()`.
    """

    tenant_uuid = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Tenant UUID (PK). Used by RLS policy.",
    )
    legal_name = models.CharField(max_length=255, help_text="Legal name of the tenant institution.")
    contract_id = models.CharField(max_length=128, help_text="External contract identifier.")
    status = models.CharField(
        max_length=32,
        default="provisioning",
        help_text="Lifecycle status: provisioning, active, suspended, deprovisioned.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    suspended_at = models.DateTimeField(null=True, blank=True)

    objects = TenantManager()

    class Meta:
        db_table = "tenancy_tenant"
        app_label = "tenancy"

    def __str__(self) -> str:
        return f"Tenant({self.legal_name})"


class Brand(models.Model):
    """Brand — a customer-facing brand under a tenant.

    Per DEC-0014, Brand is a child of Tenant. RLS: scoped to the
    tenant via tenant_uuid FK.
    """

    brand_uuid = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Brand UUID (PK).",
    )
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.PROTECT,
        related_name="brands",
        db_column="tenant_uuid",
        to_field="tenant_uuid",
        help_text="Owning tenant.",
    )
    name = models.CharField(max_length=128, help_text="Brand name (machine-readable).")
    display_name = models.CharField(max_length=255, help_text="Brand display name (human-readable).")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "tenancy_brand"
        app_label = "tenancy"
        unique_together = (("tenant", "name"),)

    def __str__(self) -> str:
        return f"Brand({self.name}, tenant={self.tenant_id})"
