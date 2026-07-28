"""Registry: create/read/update/delete for master data (leverandører, kontaktpersoner).

Pure core — takes a Session, imports no UI (hard rule #1). Every write appends an audit row
(hard rule #7). This is the persistence layer behind the "Leverandør A–Z" tool.
"""
from core.registry.leverandor import (
    RegistryError,
    add_contact,
    create_supplier,
    delete_contact,
    get_supplier,
    list_contacts,
    list_suppliers,
    restore_supplier,
    soft_delete_supplier,
    update_contact,
    update_supplier,
)

__all__ = [
    "RegistryError",
    "list_suppliers", "get_supplier", "create_supplier", "update_supplier",
    "soft_delete_supplier", "restore_supplier",
    "list_contacts", "add_contact", "update_contact", "delete_contact",
]
