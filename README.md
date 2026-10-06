# Content Center — Odoo 16

Company and product knowledge, FAQs and files for sales and support.
Direct editing, saving and archiving; authenticated access.

| Addon | Role | Requires |
| --- | --- | --- |
| `content_center_base` | Library, subjects, text/FAQ/files, product references, browser | Native product/mail/web/web_editor |
| `content_center_sale` | Consult materials from quotations and sales orders | Base + native sale |
| `content_center_contact_center` | Search and add materials to conversation drafts | Base + contact_center_ui |

Base installs without CRM or Marketing Center. Bridges are optional and never
install automatically. Adding content prepares a draft; the agent chooses when
to send. Materials stay private and obey catalog permissions and company rules.

Official branch: **16.0**, AGPL-3. Extracted from
[Marketing Center](https://github.com/soloztech/marketing-center), retaining
technical model names and original authors. See [source provenance](SOURCE-PROVENANCE.json),
[architecture](ARCHITECTURE.md), [migration](MIGRATION.md), and
[the original MVP plan](catalog-plan.md).

Install the new names on a fresh database. For an existing catalog installation,
use the reviewed migration procedure before enabling the new provider; never
uninstall/reinstall the library to rename it.
