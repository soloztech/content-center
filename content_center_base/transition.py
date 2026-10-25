"""Metadata-only module rename. Caller owns persistence and commit/rollback.

This file is also loaded with runpy from an OLD registry. It deliberately imports
no addon model, so importing it never starts the new application.
"""
import json
from pathlib import Path

from odoo.exceptions import ValidationError

MODULES = {
    "marketing_center_catalog": "content_center_base",
    "marketing_center_catalog_sale": "content_center_sale",
}
VERSIONS = {
    "marketing_center_catalog": "16.0.1.2.0",
    "marketing_center_catalog_sale": "16.0.1.1.0",
}
INFO_FIELDS = (
    "category_id",
    "shortdesc",
    "summary",
    "description",
    "author",
    "maintainer",
    "contributors",
    "website",
    "license",
    "sequence",
    "application",
    "auto_install",
    "icon",
    "url",
    "to_buy",
)
TRANSLATED_FIELDS = ("shortdesc", "summary", "description")
CATALOG = json.loads((Path(__file__).parent / "data/legacy_xmlids.json").read_text())
SCHEMA_NAMES = json.loads(
    (Path(__file__).parent / "data/schema_names.json").read_text()
)
RETIRED = {old: () for old in MODULES}
CHECKPOINT_PREFIX = "content_center.transition.commit."
CHECKPOINT_VERSION = "16.0.2.0.0"


def upgrade_checkpoint(env, module):
    """Native loader commits data BEFORE it persists latest_version.

    This marker shares the native data transaction; never commit it separately.
    Its presence forbids inverse even if native stored versions remain old.
    """
    if module not in MODULES.values():
        _fail("Unknown content upgrade checkpoint.")
    env["ir.config_parameter"].sudo().set_param(
        CHECKPOINT_PREFIX + module, CHECKPOINT_VERSION
    )


def clear_upgrade_checkpoint(env, module):
    if module not in MODULES.values():
        _fail("Unknown content upgrade checkpoint.")
    env["ir.config_parameter"].sudo().search(
        [("key", "=", CHECKPOINT_PREFIX + module)]
    ).unlink()


def _require_no_checkpoint(env):
    if (
        env["ir.config_parameter"]
        .sudo()
        .search_count([("key", "=like", CHECKPOINT_PREFIX + "%")])
    ):
        _fail("An addon data upgrade committed or an unknown checkpoint exists.")


def _fail(message):
    # Operational messages describe metadata; no customer content is interpolated.
    raise ValidationError(message)


def _ids_value(value):
    return value[0] if isinstance(value, (tuple, list)) else value


def _row(data):
    return {
        "id": data.id,
        "module": data.module,
        "name": data.name,
        "model": data.model,
        "res_id": data.res_id,
        "noupdate": data.noupdate,
    }


def _target_exists(env, data):
    return data.model in env and bool(
        env[data.model].sudo().browse(data.res_id).exists()
    )


def _lookup(env, module, name):
    return (
        env["ir.model.data"]
        .sudo()
        .search([("module", "=", module), ("name", "=", name)], limit=1)
    )


def _info(record):
    values = record.with_context(lang=None).read(list(INFO_FIELDS))[0]
    values.pop("id")
    values["category_id"] = _ids_value(values["category_id"])
    return values


def _translations(env, record):
    codes = {code for code, _label in env["res.lang"].get_installed()} | {"en_US"}
    return {
        code: {
            field: record.with_context(lang=code)[field] for field in TRANSLATED_FIELDS
        }
        for code in sorted(codes)
    }


def _schema(env, ids):
    return {
        model: [
            {"id": row.id, "name": row.name, "module_id": row.module.id}
            for row in env[model].sudo().search([("module", "in", ids)], order="id")
        ]
        for model in ("ir.model.constraint", "ir.model.relation")
    }


def guard_parallel_install(env, new_module):
    old = next(old for old, new in MODULES.items() if new == new_module)
    if (
        env["ir.module.module"]
        .sudo()
        .search_count([("name", "=", old), ("state", "=", "installed")])
    ):
        _fail("Prepare the catalog module rename before installing the new addon.")


def validate_prepared(env, names=None):
    """Accept migrated namespaces only if every alias is live and canonical."""
    env = env(context=dict(env.context, lang=None))
    names = names or tuple(MODULES)
    rows = env["ir.model.data"].sudo().search([("module", "in", names)])
    for row in rows:
        if CATALOG[row.module].get(row.name) != row.model:
            _fail("Unsupported legacy catalog metadata.")
        canonical = _lookup(env, MODULES[row.module], row.name)
        if (
            not row.noupdate
            or not canonical
            or (canonical.model, canonical.res_id) != (row.model, row.res_id)
            or not _target_exists(env, row)
        ):
            _fail("Catalog alias adoption is incomplete or inconsistent.")
    return len(rows)


def prepare_transition(env):  # noqa: C901
    """Validate everything first; return a serialisable reversible receipt."""
    env = env(context=dict(env.context, lang=None))
    Module = env["ir.module.module"].sudo()
    Data = env["ir.model.data"].sudo()
    existing = Module.search([("name", "in", tuple(MODULES))])
    if any(
        row.state not in ("installed", "uninstalled", "uninstallable")
        for row in existing
    ):
        _fail("A legacy catalog module has a pending operation.")
    old_rows = existing.filtered(lambda row: row.state == "installed")
    if not old_rows:
        validate_prepared(env)
        return {"already_prepared": True, "modules": [], "created_ids": []}
    installed = {row.name: row for row in old_rows}
    _require_no_checkpoint(env)
    for old, row in installed.items():
        if row.latest_version != VERSIONS[old]:
            _fail("Unsupported stored catalog version.")
        if Module.search_count([("name", "=", MODULES[old])]):
            _fail("New catalog module name already exists.")
        alias = _lookup(env, "base", "module_" + old)
        if not alias or alias.model != "ir.module.module" or alias.res_id != row.id:
            _fail("Original module XMLID does not identify the installed module.")
        newer = _lookup(env, "base", "module_" + MODULES[old])
        if newer and (newer.model, newer.res_id) != ("ir.module.module", row.id):
            _fail("New module XMLID collides with another record.")
    rows = Data.search([("module", "in", tuple(installed))], order="module,name")
    for old in installed:
        if {row.name: row.model for row in rows if row.module == old} != CATALOG[old]:
            _fail("The declared catalog metadata set is incomplete.")
    schema = _schema(env, old_rows.ids)
    for model, records in schema.items():
        if sorted(row["name"] for row in records) != SCHEMA_NAMES[model]:
            _fail("Unsupported catalog schema ownership.")
    for row in rows:
        if CATALOG[row.module].get(row.name) != row.model or not _target_exists(
            env, row
        ):
            _fail("Unsupported or dangling legacy catalog metadata.")
        canonical = _lookup(env, MODULES[row.module], row.name)
        if canonical and (canonical.model, canonical.res_id, canonical.noupdate) != (
            row.model,
            row.res_id,
            row.noupdate,
        ):
            _fail("Canonical catalog metadata collides with the original.")
    links = []
    for model in ("ir.module.module.dependency", "ir.module.module.exclusion"):
        for row in (
            env[model].sudo().search([("name", "in", tuple(installed))], order="id")
        ):
            if row.module_id.name not in MODULES:
                _fail("A foreign module still declares a legacy catalog dependency.")
            links.append(
                {
                    "model": model,
                    "id": row.id,
                    "old_name": row.name,
                    "new_name": MODULES[row.name],
                }
            )
    receipt = {
        "format": 1,
        "already_prepared": False,
        "modules": [
            {
                "id": row.id,
                "old": old,
                "new": MODULES[old],
                "state": row.state,
                "latest_version": row.latest_version,
                "info": _info(row),
                "translations": _translations(env, row),
            }
            for old, row in sorted(installed.items())
        ],
        "old_xmlids": [_row(row) for row in rows],
        "base_xmlids": [],
        "created_ids": [],
        "links": links,
        "schema": _schema(env, old_rows.ids),
    }
    # Nothing above this line mutates a record.
    for row in rows:
        canonical = _lookup(env, MODULES[row.module], row.name)
        if not canonical:
            canonical = Data.create(
                {
                    "module": MODULES[row.module],
                    "name": row.name,
                    "model": row.model,
                    "res_id": row.res_id,
                    "noupdate": row.noupdate,
                }
            )
            receipt["created_ids"].append(canonical.id)
        row.write({"noupdate": True})
    for old, module in installed.items():
        for name in ("module_" + old, "module_" + MODULES[old]):
            row = _lookup(env, "base", name)
            if row:
                receipt["base_xmlids"].append(_row(row))
                row.write({"noupdate": True})
            else:
                row = Data.create(
                    {
                        "module": "base",
                        "name": name,
                        "model": "ir.module.module",
                        "res_id": module.id,
                        "noupdate": True,
                    }
                )
                receipt["created_ids"].append(row.id)
        module.write({"name": MODULES[old]})
    for row in links:
        env[row["model"]].sudo().browse(row["id"]).write({"name": row["new_name"]})
    receipt["created_xmlids"] = [
        _row(row) for row in Data.browse(receipt["created_ids"])
    ]
    return receipt


def inverse_transition(env, receipt):  # noqa: C901
    """Reverse ONLY a prepared rename with no committed addon upgrade.

    The controller additionally proves business projections before calling this.
    No catalog record, field, schema object, attachment or module row is unlinked.
    """
    env = env(context=dict(env.context, lang=None))
    if receipt.get("format") != 1 or receipt.get("already_prepared"):
        _fail("A complete original transition receipt is required.")
    Module = env["ir.module.module"].sudo()
    Data = env["ir.model.data"].sudo()
    modules = receipt["modules"]
    _require_no_checkpoint(env)
    for item in modules:
        row = Module.browse(item["id"]).exists()
        if (
            not row
            or (row.name, row.state, row.latest_version)
            != (item["new"], "installed", item["latest_version"])
            or Module.search_count([("name", "=", item["old"])])
        ):
            _fail("An addon upgrade committed or module identity/state changed.")
    validate_prepared(env, [item["old"] for item in modules])
    if _schema(env, [item["id"] for item in modules]) != receipt["schema"]:
        _fail("Catalog schema ownership changed after preparation.")
    for item in receipt["created_xmlids"]:
        row = Data.browse(item["id"]).exists()
        if not row or _row(row) != item:
            _fail("A helper-created XMLID changed after preparation.")
    for item in receipt["old_xmlids"]:
        row = Data.browse(item["id"]).exists()
        expected = dict(item, noupdate=True)
        if not row or _row(row) != expected:
            _fail("Original alias identity changed after preparation.")
    for item in receipt["base_xmlids"]:
        row = Data.browse(item["id"]).exists()
        if not row or _row(row) != dict(item, noupdate=True):
            _fail("Original base module XMLID changed after preparation.")
    for item in receipt["links"]:
        row = env[item["model"]].sudo().browse(item["id"]).exists()
        if not row or row.name != item["new_name"]:
            _fail("A dependency changed after preparation.")
    # All preconditions passed; only the declared metadata delta is reversed.
    Data.browse(receipt["created_ids"]).unlink()
    for item in receipt["old_xmlids"] + receipt["base_xmlids"]:
        Data.browse(item["id"]).write({"noupdate": item["noupdate"]})
    for item in modules:
        row = Module.browse(item["id"])
        current = _info(row)
        changes = {
            field: value
            for field, value in item["info"].items()
            if current[field] != value
        }
        row.write(dict(changes, name=item["old"]))
        codes = sorted(set(item["translations"]) - {"en_US"}) + ["en_US"]
        for code in codes:
            translated = row.with_context(lang=code)
            changes = {
                field: value
                for field, value in item["translations"][code].items()
                if translated[field] != value
            }
            if changes:
                translated.write(changes)
    for item in receipt["links"]:
        env[item["model"]].sudo().browse(item["id"]).write({"name": item["old_name"]})
    return {"reversed": True, "modules": len(modules)}


def retire_legacy_aliases(env, new_module, names):
    """Future removals must retire frozen aliases before dropping canonical data."""
    old = next(old for old, new in MODULES.items() if new == new_module)
    names = tuple(names)
    if any(name not in CATALOG[old] for name in names):
        _fail("Only declared legacy aliases may be retired.")
    rows = (
        env["ir.model.data"]
        .sudo()
        .search([("module", "=", old), ("name", "in", names)])
    )
    for row in rows:
        canonical = _lookup(env, new_module, row.name)
        if canonical and (canonical.model, canonical.res_id) != (row.model, row.res_id):
            _fail("Cannot retire an alias owned by a different record.")
    rows.unlink()
    return len(rows)
