# Architecture

`content_center_base` owns authenticated knowledge and media.
`content_center_sale` connects published content to sales orders.

Existing `marketing.center.catalog.subject` / `marketing.center.catalog.item` models,
tables and fields are intentionally retained. XML namespaces and addon ownership are
renamed while record IDs remain stable. Marketing attribution, lead lifecycle and
advertising catalog services stay in Marketing Center.

The editor saves directly. There is no publication workflow, AI generation or public
content portal in this version. Access groups, company rules, product and variant
restrictions apply equally to old and new authenticated media URLs.
