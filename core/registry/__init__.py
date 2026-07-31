"""Registry: create/read/update/delete for master data (leverandører, kontaktpersoner,
tjenester/produkter, kvalifikasjoner, kategorier, avtaler/prislister).

Pure core — takes a Session, imports no UI (hard rule #1). Every write appends an audit row
(hard rule #7). This is the persistence layer behind the "Leverandør" and "Kontrakt" tools.
"""
from core.registry.faktura import (
    intake_invoice,
    latest_decision,
    record_decision,
)
from core.registry.forpliktelse import (
    assess_gyldighet,
    create_commitment,
    create_commitments_for_suppliers,
    get_commitment,
    list_commitments,
    resolve_contract_id,
    restore_commitment,
    soft_delete_commitment,
    update_commitment,
)
from core.registry.kontrakt import (
    _clause_label,
    add_line,
    change_clause_of,
    create_contract,
    delete_line,
    get_contract,
    list_contracts,
    list_lines,
    restore_contract,
    soft_delete_contract,
    update_contract,
    update_line,
)
from core.registry.leverandor import (
    SUPPLIER_STATUSES,
    RegistryError,
    add_category,
    add_contact,
    add_qualification,
    add_service,
    create_supplier,
    delete_contact,
    delete_qualification,
    delete_service,
    get_supplier,
    list_categories,
    list_contacts,
    list_qualifications,
    list_services,
    list_suppliers,
    remove_category,
    restore_supplier,
    soft_delete_supplier,
    update_contact,
    update_qualification,
    update_service,
    update_supplier,
)

__all__ = [
    "RegistryError", "SUPPLIER_STATUSES",
    "list_suppliers", "get_supplier", "create_supplier", "update_supplier",
    "soft_delete_supplier", "restore_supplier",
    "list_contacts", "add_contact", "update_contact", "delete_contact",
    "list_categories", "add_category", "remove_category",
    "list_services", "add_service", "update_service", "delete_service",
    "list_qualifications", "add_qualification", "update_qualification", "delete_qualification",
    # Kontrakt + prisliste
    "list_contracts", "get_contract", "create_contract", "update_contract",
    "soft_delete_contract", "restore_contract",
    "list_lines", "add_line", "update_line", "delete_line",
    "change_clause_of", "_clause_label",
    # Faktura intake + decision
    "intake_invoice", "record_decision", "latest_decision",
    # Forpliktelse (commitment) CRUD
    "list_commitments", "get_commitment", "create_commitment",
    "create_commitments_for_suppliers", "update_commitment",
    "soft_delete_commitment", "restore_commitment",
    "assess_gyldighet", "resolve_contract_id",
]
