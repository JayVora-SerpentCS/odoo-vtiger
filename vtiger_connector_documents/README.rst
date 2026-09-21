VTiger Documents Connector
==========================

This module synchronizes VTiger document metadata into Odoo Documents.

Features
--------

* Import VTiger Documents records into Odoo ``documents.document``.
* Store file name, type, size, folder reference, document type, source, and URL.
* Keep VTiger document IDs for reliable updates on later synchronizations.
* Add a manual sync button on the VTiger company configuration page.

The VTiger webservice query returns document metadata. The sync creates Odoo
Documents as URL documents, using the VTiger URL when available and otherwise a
VTiger detail-page URL.
