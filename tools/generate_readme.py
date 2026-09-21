#!/usr/bin/env python3
# See LICENSE file for full copyright and licensing details.

import ast
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
AGPL_LINK = "https://www.gnu.org/licenses/agpl-3.0.html"
MAINTAINER = (
    '<a href="https://www.serpentcs.com">'
    '<img src="vtiger_connector_base/static/description/images/header-logo.png" '
    'alt="Serpent Consulting Services Pvt. Ltd." height="32"/>'
    "</a>"
)

SUMMARIES = {
    "vtiger_connector_base": (
        "Base configuration and shared utilities for Odoo and vTiger integration."
    ),
    "vtiger_connector_calendar": (
        "Synchronizes calendar events between Odoo and vTiger."
    ),
    "vtiger_connector_crm": "Connects CRM leads between Odoo and vTiger.",
    "vtiger_connector_documents": (
        "Synchronizes document metadata from vTiger into Odoo."
    ),
    "vtiger_connector_helpdesk": (
        "Synchronizes HelpDesk support tickets from vTiger into Odoo."
    ),
    "vtiger_connector_invoice": (
        "Synchronizes customer invoices between Odoo and vTiger."
    ),
    "vtiger_connector_partner": (
        "Synchronizes partners, contacts, and vendors between Odoo and vTiger."
    ),
    "vtiger_connector_products": (
        "Synchronizes products and inventory information between Odoo and vTiger."
    ),
    "vtiger_connector_project": "Connects projects and tasks between Odoo and vTiger.",
    "vtiger_connector_pricebook": (
        "Synchronizes vTiger Price Books into Odoo pricelists."
    ),
    "vtiger_connector_purchase": (
        "Synchronizes purchase and vendor data between Odoo and vTiger."
    ),
    "vtiger_connector_sales": "Synchronizes sales orders between Odoo and vTiger.",
}


def _read_manifest(path):
    return ast.literal_eval(path.read_text(encoding="utf-8"))


def _addons():
    for manifest_path in sorted(ROOT.glob("vtiger_connector_*/__manifest__.py")):
        addon = manifest_path.parent.name
        manifest = _read_manifest(manifest_path)
        yield {
            "addon": addon,
            "version": manifest.get("version", ""),
            "license": manifest.get("license", ""),
            "summary": SUMMARIES.get(
                addon,
                " ".join(str(manifest.get("summary", "")).split()),
            ),
        }


def _table(addons):
    rows = [
        "| addon | version | maintainers | summary |",
        "| --- | --- | --- | --- |",
    ]
    for item in addons:
        rows.append(
            "| [{addon}]({addon}) | {version} | {maintainer} | {summary} |".format(
                addon=item["addon"],
                version=item["version"],
                maintainer=MAINTAINER,
                summary=item["summary"],
            )
        )
    return "\n".join(rows)


def _license(addons):
    licenses = sorted({item["license"] for item in addons if item["license"]})
    if licenses == ["AGPL-3"]:
        return "AGPL-3.0"
    return ", ".join(licenses) or "the license declared by each module"


def main():
    addons = list(_addons())
    license_name = _license(addons)
    content = f"""# odoo-vtiger

Odoo - vTiger Integration

## Available addons

<!-- addon-table-start -->
{_table(addons)}
<!-- addon-table-end -->

This table is generated from module manifests. After changing a module version,
run `python3 tools/generate_readme.py` to refresh it.

## Licenses

This repository's modules declare [{license_name}]({AGPL_LINK}) in their Odoo manifests.

However, each module can have a different license. Consult each module's
`__manifest__.py` file, which contains a `license` key that explains its
license.

Serpent Consulting Services Pvt. Ltd. maintains these modules for Odoo and
vTiger integration.
"""
    README.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
