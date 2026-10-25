# Upgrade from Marketing Center Catalog

> Historical procedure from 2026-10-05. The Contact Center bridge was retired in
> `content_center_base` 16.0.2.0.1. The current transition helper supports only base and
> base with Sale. The three-addon profiles and recovery table below describe the
> original release and must not be applied with the current helper.

Supported origins: `marketing_center_catalog` 16.0.1.2.0 and its optional bridges
16.0.1.1.0. New modules are 16.0.2.0.0. Supported profiles: base only, base with one
bridge, all three. Fresh installations do not need this transition.

1. Validate the declared legacy XMLID/schema map, supported versions, stable installed
   states, dependency owners and absence of new-name collisions.
2. Load `content_center_base/transition.py` with `runpy.run_path` in an **old
   registry**. `prepare_transition(env)` validates before writing and never commits.
   Dry-run preparation and `inverse_transition(env, receipt)`, compare relevant
   metadata/data and roll back.
3. Under the deploy mutex, drain jobs and stop the application. Take a fresh
   preservation projection. Prepare the rename, durably persist its private receipt on
   root-private, non-volatile storage, fsyncing the file and directory **before
   committing** the ORM transaction. It renames module rows in place and adds canonical
   XMLIDs; IDs, records and schema ownership remain.
4. Remove the three old addon providers, enable the fixed Content Center root, and
   upgrade only the three installed new addon names. Old aliases are frozen; canonical
   aliases retain the original noupdate policy. Both native `base.module_*` aliases are
   frozen to survive an upgrade of native base.
5. Compare catalog/file/security/schema/business projections, installed versions and
   English/Portuguese branding. Check the running service, both old/new authenticated
   media URLs, static assets and its configured startup log.

Never uninstall/reinstall to rename the addons. Never run a broad upgrade, global
translation overwrite or SQL mutation. Module hooks only change explicitly listed
branding fields; customized unrelated translations remain untouched.

## Recovery boundaries

Before **every** plain registry load or restart, read module flags through an
independent read-only SQL connection. Any `to install`, `to upgrade`, `to remove` state
forbids that load/restart; a plain Odoo startup can implicitly upgrade.

The native Odoo loader commits schema/data before writing `latest_version`. Each
post-migration therefore records `content_center.transition.commit.<new_module>` with
value `16.0.2.0.0` in that same native transaction. **Old versions do not prove absence
of a commit.** Preparation and inverse require all three keys to be absent. Read module
state and checkpoint keys independently before loading a registry. Operational SQL
examples belong in the deployment's private runbook.

Also inspect the global pending module states and prepared XMLID/schema identities. The
two tested partial states, with all modules stably installed, are:

| Failed bridge  | Stored versions Base / Contact / Sale | Committed checkpoints   |
| -------------- | ------------------------------------- | ----------------------- |
| Contact Center | original / original / original        | Base only               |
| Sale           | 2.0 / original / original             | Base and Contact Center |

Only these shapes permit automatic availability recovery after full compatibility proof.
Both remain failed deliveries requiring repair. A late failure with all three
checkpoints and a stale Sale version stays stopped. Inspect the evidence, validate
source and metadata, and finish a reviewed scoped upgrade under both locks; never erase
checkpoints or reset states/versions to force an inverse.

The reviewed applicator allows at most two scoped upgrade attempts. If neither committed
an addon upgrade, all checkpoints are absent, and all original stored versions,
installed states, prepared alias identities and original preservation projections match,
the ORM inverse may use the durable receipt. It deletes only XMLIDs created by this
helper, restores original module metadata/names/translations/dependency names, and never
deletes catalog records, attachments, schema or module rows. Restore old code/config
only **after** inverse committed and independent SQL proves old names; compare the old
registry before restarting.

If base or a bridge upgrade committed, inverse is forbidden. A known partial version
combination can restore availability only after compatibility proof with the new source
and stable installed flags. This remains a **failed delivery pending repair**. Unknown
metadata, pending flags or failed compatibility keeps the service stopped. Do not reset
to old source or reset module flags manually.

Repair under the same locks: inspect preserved evidence, fix and review the new source,
require exact-SHA CI, converge fixed new providers, and finish the same scoped upgrade.
Preserve business/schema/security identities and prove registry, API and HTTP health
before restarting. Do not resend fiscal documents.

## Future removal of canonical data

Frozen legacy aliases can protect records from native uninstall/deletion. Before
deliberately removing a canonical record in a future version, call
`retire_legacy_aliases(env, new_module, names)` in that version's migration, then remove
the declared canonical source record. Add the retired names to the versioned `RETIRED`
contract and adjust the fresh-source contract. Never remove aliases blindly. Uninstall
hooks retire the uninstalling addon's legacy aliases; production uninstall is outside
this extraction procedure.

Technical models/tables and old JS action tags/media URLs stay supported. No content
approval workflow, public portal, tracking or sending policy changes.
