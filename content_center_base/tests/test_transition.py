"""Fresh-source and metadata-only rename contracts in disposable transactions."""
from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged

from ..transition import CATALOG, MODULES, inverse_transition, prepare_transition


@tagged("post_install", "-at_install")
class TestContentTransition(TransactionCase):
    def test_every_non_retired_legacy_id_has_a_fresh_canonical_target(self):
        for old, new in MODULES.items():
            module = self.env["ir.module.module"].search([("name", "=", new)])
            if module.state != "installed":
                continue
            for name, model in CATALOG[old].items():
                target = self.env.ref(new + "." + name)
                self.assertEqual(target._name, model)
                self.assertTrue(target.exists())

    def _legacy_base(self):
        self.env["ir.config_parameter"].sudo().search(
            [("key", "=like", "content_center.transition.commit.%")]
        ).unlink()
        data = self.env["ir.model.data"]
        module = self.env.ref("base.module_content_center_base")
        for old, new in MODULES.items():
            installed = self.env["ir.module.module"].search([("name", "=", new)])
            if not installed:
                continue
            installed.write(
                {
                    "name": old,
                    "latest_version": "16.0.1.2.0"
                    if new == "content_center_base"
                    else "16.0.1.1.0",
                }
            )
            data.search([("module", "=", new)]).write({"module": old})
            alias = data.search(
                [("module", "=", "base"), ("name", "=", "module_" + new)]
            )
            alias.write({"name": "module_" + old, "noupdate": False})
            self.env["ir.module.module.dependency"].search([("name", "=", new)]).write(
                {"name": old}
            )
        return module

    def test_forward_inverse_preserves_identity_and_original_xmlid_flags(self):
        module = self._legacy_base()
        original = (
            self.env["ir.model.data"]
            .search([("module", "=", "marketing_center_catalog")])
            .read(["module", "name", "model", "res_id", "noupdate"])
        )
        receipt = prepare_transition(self.env)
        self.assertEqual(module.name, "content_center_base")
        self.assertEqual(receipt["modules"][0]["id"], module.id)
        self.assertTrue(
            self.env["ir.model.data"]
            .search(
                [("module", "=", "base"), ("name", "=", "module_content_center_base")]
            )
            .noupdate
        )
        inverse_transition(self.env, receipt)
        self.assertEqual(module.name, "marketing_center_catalog")
        observed = (
            self.env["ir.model.data"]
            .search([("module", "=", "marketing_center_catalog")])
            .read(["module", "name", "model", "res_id", "noupdate"])
        )
        self.assertEqual(observed, original)
        self.assertFalse(
            self.env["ir.model.data"].browse(receipt["created_ids"]).exists()
        )

    def test_unknown_metadata_rejected_before_any_rename(self):
        module = self._legacy_base()
        self.env["ir.model.data"].create(
            {
                "module": "marketing_center_catalog",
                "name": "unexpected_custom_id",
                "model": "ir.module.module",
                "res_id": module.id,
            }
        )
        count = self.env["ir.model.data"].search_count([])
        with self.assertRaises(ValidationError):
            prepare_transition(self.env)
        self.assertEqual(module.name, "marketing_center_catalog")
        self.assertEqual(self.env["ir.model.data"].search_count([]), count)

    def test_inverse_rejects_committed_upgrade_and_pending_state(self):
        module = self._legacy_base()
        receipt = prepare_transition(self.env)
        module.latest_version = "16.0.2.0.0"
        with self.assertRaises(ValidationError):
            inverse_transition(self.env, receipt)
        module.write({"latest_version": "16.0.1.2.0", "state": "to upgrade"})
        with self.assertRaises(ValidationError):
            inverse_transition(self.env, receipt)

    def test_committed_data_checkpoint_forbids_inverse_with_old_versions(self):
        self._legacy_base()
        receipt = prepare_transition(self.env)
        self.env["ir.config_parameter"].sudo().set_param(
            "content_center.transition.commit.content_center_base", "16.0.2.0.0"
        )
        with self.assertRaises(ValidationError):
            inverse_transition(self.env, receipt)

    def test_new_name_and_canonical_collision_leave_original_rows_untouched(self):
        module = self._legacy_base()
        data = self.env["ir.model.data"]
        collision = self.env["ir.module.module"].create({"name": "content_center_base"})
        with self.assertRaises(ValidationError):
            prepare_transition(self.env)
        self.assertEqual(module.name, "marketing_center_catalog")
        collision.unlink()
        old = data.search(
            [("module", "=", "marketing_center_catalog"), ("model", "=", "ir.ui.menu")],
            limit=1,
        )
        data.create(
            {
                "module": "content_center_base",
                "name": old.name,
                "model": "ir.module.module",
                "res_id": module.id,
            }
        )
        count = data.search_count([])
        with self.assertRaises(ValidationError):
            prepare_transition(self.env)
        self.assertEqual(module.name, "marketing_center_catalog")
        self.assertEqual(data.search_count([]), count)

    def test_pending_old_module_cannot_be_prepared(self):
        module = self._legacy_base()
        module.state = "to upgrade"
        with self.assertRaises(ValidationError):
            prepare_transition(self.env)
        self.assertEqual(module.name, "marketing_center_catalog")
