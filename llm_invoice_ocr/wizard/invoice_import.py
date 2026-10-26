"""
OCA Invoice Import Wizard Integration — Argentine overrides

Integrates LLM-OCR extraction into OCA account_invoice_import wizard.
Overrides fallback_parse_pdf_invoice() to extract invoice data when
embedded XML parsers (UBL, Factur-X) fail, and adds Argentine/AFIP-specific
pivot-to-invoice conversion (document type/number, percepciones, VAT rate
correction) via OCA's own extension points.
"""

import logging

from odoo import Command, _, api, models
from odoo.exceptions import UserError
from odoo.tools.mimetypes import guess_mimetype

_logger = logging.getLogger(__name__)


class AccountInvoiceImport(models.TransientModel):
    _inherit = "account.invoice.import"

    @api.model
    def default_get(self, field_names):
        """Block the wizard from opening at all when AI import is
        disabled. The "Import Vendor Bills" menu is already hidden while
        disabled (see models/ir_ui_menu.py) - reaching this
        wizard at all means a stale, not-yet-refreshed session, and in
        this deployment every upload through it depends on AI (no XML
        format module like account_invoice_import_ubl is installed), so
        there's nothing it could usefully do anyway.

        This is the sole gate for the disabled case - fallback_parse_pdf_invoice()
        below no longer duplicates the check, since a wizard record can
        only exist here if it was created while enabled. The one narrow
        gap this leaves (AI gets disabled by someone else after this
        wizard was already opened, before the user clicks Import) falls
        through to that method's generic "extraction failed" message
        instead of a disabled-specific one - accepted as not worth the
        extra complexity for how rare that race is.
        """
        if not self.env["account.invoice.import.ocr"]._is_invoice_extraction_enabled():
            raise UserError(
                _(
                    "AI-based invoice import is currently disabled. Go "
                    "to LLM → Configuration → Assistants to re-enable it, or "
                    "use the 'Upload' button on the Vendor Bills list "
                    "instead."
                )
            )
        return super().default_get(field_names)

    @api.model
    def fallback_parse_pdf_invoice(self, file_data, company):
        """Fallback parser using LLM-OCR for PDFs without embedded XML."""
        res = super().fallback_parse_pdf_invoice(file_data, company)
        if res:
            return res

        # OCA's parse_pdf_invoice()/fallback_parse_pdf_invoice() only
        # forward the raw bytes, not the original filename/mimetype
        # (unlike account_move.py's "Process with AI" button, which
        # reads the real ir.attachment mimetype directly) - without
        # sniffing it here, extract_invoice_data() always defaulted to
        # "application/pdf", silently breaking OCR for images (e.g. a
        # WhatsApp photo of an invoice) uploaded through this wizard.
        mimetype = guess_mimetype(file_data, default="application/pdf")
        try:
            return self.env["account.invoice.import.ocr"].extract_invoice_data(
                file_data, company, mimetype
            )
        except Exception:
            _logger.exception("LLM-OCR extraction failed, skipping")
            # Don't let this fall through to OCA's own "nothing parsed"
            # handling (parsed_inv = {}, no chatter_msg at all) - that's
            # the same silent-empty-import problem
            # _convert_llm_data_to_pivot()'s isInvoice check exists for,
            # just triggered by extraction raising instead of classifying
            # the document as non-invoice. Still create the draft (never
            # blocks the import), but with a visible reason on the banner.
            return {
                "type": "in_invoice",
                "chatter_msg": [
                    _(
                        "Automatic data extraction failed for this "
                        "document. Please review the attached file and "
                        "complete the invoice manually."
                    )
                ],
            }

    # AFIP tribute code (account.tax.group.l10n_ar_tribute_afip_code) per
    # otherCharges "type" extracted from the invoice - see
    # account.tax.group in l10n_ar for the full catalog.
    _L10N_AR_TRIBUTE_CODE_BY_CHARGE_TYPE = {
        "vat_perception": "06",
        "iibb_perception": "07",
        "other": "09",
    }

    # Real AR VAT rates are spaced far enough apart (0, 10.5, 21, 27, ...)
    # that a tolerance well under half the smallest gap can't cause
    # ambiguity, while still absorbing rounding noise in the derived amount.
    _L10N_AR_VAT_PERCENT_TOLERANCE = 0.5

    @api.model
    def _prepare_create_invoice_vals(self, parsed_inv, import_config):
        vals = super()._prepare_create_invoice_vals(parsed_inv, import_config)
        self._set_l10n_ar_document(parsed_inv, import_config, vals)
        self._add_l10n_ar_other_charges(parsed_inv, import_config, vals)
        self._fix_l10n_ar_vat_percent(parsed_inv, import_config, vals)
        return vals

    @api.model
    def _prepare_line_vals_nline(self, parsed_inv, import_config, vals, partner):
        """Same as OCA's account_invoice_import, except: when no product is
        matched on a line, try the tax this line's own extraction found
        (line["taxes"]) before falling back to the company's blanket
        default purchase/sale tax - OCA's base implementation does the
        opposite (company default first, line["taxes"] only if that
        default is unset).

        Since our LLM extraction reliably reads the real tax rate straight
        off the document, silently discarding it in favor of "whatever
        this company's default purchase tax happens to be" produces a tax
        that has nothing to do with what's printed on the invoice (e.g. an
        Argentine telecom/utility invoice taxed at 27% IVA getting the
        company's general 21% default instead) - _fix_l10n_ar_vat_percent()
        then has to detect and correct it after the fact from the document
        totals. Trying the extracted tax first avoids that detour and uses
        the company default only as the true last resort (e.g. a line the
        LLM genuinely found no tax info for).
        """
        assert parsed_inv.get("lines")
        bdio = self.env["business.document.import"]
        type_tax_use = (
            "sale"
            if parsed_inv["type"] in ("out_invoice", "out_refund")
            else "purchase"
        )
        for line in parsed_inv["lines"]:
            if line.get("line_note"):
                il_vals = {
                    "product_id": None,
                    "name": line.get("line_note"),
                    "display_type": "line_note",
                }
                vals["invoice_line_ids"].append(Command.create(il_vals))
                continue
            if line.get("sectionheader"):
                il_vals = {
                    "product_id": None,
                    "name": line.get("sectionheader"),
                    "display_type": "line_section",
                }
                vals["invoice_line_ids"].append(Command.create(il_vals))
                continue
            product = False
            if line.get("product"):
                product = bdio._match_product(
                    line["product"],
                    parsed_inv["chatter_msg"],
                    seller=partner,
                    raise_exception=False,
                )
            if not product and import_config.get("product"):
                product = import_config["product"]
            if product:
                product = product.with_company(import_config["company"].id)
                if parsed_inv["type"] in ("out_invoice", "out_refund"):
                    account = product._get_product_accounts()["income"]
                    product_taxes = product.taxes_id
                else:
                    account = product._get_product_accounts()["expense"]
                    product_taxes = product.supplier_taxes_id
                taxes = product_taxes.filtered(
                    lambda tax: tax.company_id == import_config["company"]
                )
            else:
                account = import_config["account"]
                taxes = self.env["account.tax"]
                if line.get("taxes"):
                    taxes = bdio._match_taxes(
                        line["taxes"],
                        parsed_inv["chatter_msg"],
                        company=import_config["company"],
                        type_tax_use=type_tax_use,
                        raise_exception=False,
                    )
                if not taxes:
                    taxes = import_config["taxes"]

            fp = partner and partner.property_account_position_id or False
            if fp:
                account = fp.map_account(account)
                taxes = fp.map_tax(taxes)
            uom = bdio._match_uom(
                line.get("uom"),
                parsed_inv["chatter_msg"],
                product=product,
                raise_exception=False,
            )

            il_vals = {
                "display_type": "product",
                "product_id": product and product.id or False,
                "product_uom_id": uom.id,
                "account_id": account.id,
                "tax_ids": [Command.set(taxes.ids)],
                "quantity": line["qty"],
                "price_unit": line["price_unit"],  # TODO add support for tax incl ?
                "discount": line.get("discount", 0),
            }

            if import_config.get("label"):
                il_vals["name"] = import_config["label"]
            elif line.get("name"):
                il_vals["name"] = line["name"]
            if import_config["start_end_dates_installed"]:
                il_vals["start_date"] = line.get("date_start") or parsed_inv.get(
                    "date_start"
                )
                il_vals["end_date"] = line.get("date_end") or parsed_inv.get("date_end")
            vals["invoice_line_ids"].append(Command.create(il_vals))

    @api.model
    def _set_l10n_ar_document(self, parsed_inv, import_config, vals):
        """Resolve l10n_latam_document_type_id/number from the AR invoice
        letter (A/B/C) detected by OCR, and force "VAT Not Applicable" on
        invoice lines for letters B/C - l10n_ar requires it (see
        account.move._check_argentinean_invoice_taxes() in l10n_ar), since
        those document types never discriminate VAT.

        Best-effort only: any failure to resolve the letter/document
        type/number (module not installed, non-AR company, letter not
        allowed for this journal/partner, unparseable number, no "VAT Not
        Applicable" tax configured) leaves vals untouched. The draft is
        still created for manual review - this never blocks the import.
        """
        letter = parsed_inv.get("l10n_ar_letter")
        if not letter or parsed_inv["type"] not in ("in_invoice", "in_refund"):
            return
        amo = self.env["account.move"]
        if "l10n_latam_document_type_id" not in amo._fields:
            return
        company = import_config["company"]
        if company.account_fiscal_country_id.code != "AR":
            return

        journal = self.env["account.journal"].browse(vals.get("journal_id"))
        partner = self.env["res.partner"].browse(vals.get("partner_id"))
        try:
            allowed_letters = journal._get_journal_letter(counterpart_partner=partner)
        except UserError:
            _logger.warning(
                "Could not compute allowed AR invoice letters for journal "
                "'%s' (company AFIP responsibility likely not configured); "
                "leaving document type/number unset for manual review.",
                journal.display_name,
            )
            return
        if letter not in allowed_letters:
            _logger.warning(
                "OCR-detected invoice letter '%s' is not allowed for "
                "journal '%s' / partner '%s' (allowed: %s); leaving "
                "document type unset for manual review.",
                letter,
                journal.display_name,
                partner.display_name,
                allowed_letters,
            )
            return

        doc_type = self.env["l10n_latam.document.type"].search(
            [
                ("country_id.code", "=", "AR"),
                ("internal_type", "=", "invoice"),
                ("l10n_ar_letter", "=", letter),
            ],
            limit=1,
        )
        if not doc_type:
            return

        number = parsed_inv.get("invoice_number")
        formatted_number = False
        if number:
            try:
                formatted_number = doc_type._format_document_number(number)
            except UserError:
                formatted_number = False
        if not formatted_number:
            _logger.warning(
                "Could not format OCR-detected document number '%s' for "
                "document type '%s'; leaving document type/number unset "
                "for manual review.",
                number,
                doc_type.display_name,
            )
            return

        vals["l10n_latam_document_type_id"] = doc_type.id
        vals["l10n_latam_document_number"] = formatted_number

        if doc_type.purchase_aliquots == "zero":
            self._force_l10n_ar_no_vat_lines(vals, company)

    @api.model
    def _force_l10n_ar_no_vat_lines(self, vals, company):
        """Factura B/C: the vendor doesn't discriminate VAT, so every line
        must carry the "VAT Not Applicable" tax instead of a real VAT
        percentage (l10n_ar_vat_afip_code == '0' on the tax's group) -
        otherwise posting fails l10n_ar's
        account.move._check_argentinean_invoice_taxes()."""
        no_vat_tax = self.env["account.tax"].search(
            [
                ("company_id", "=", company.id),
                ("type_tax_use", "=", "purchase"),
                ("tax_group_id.l10n_ar_vat_afip_code", "=", "0"),
            ],
            limit=1,
        )
        if not no_vat_tax:
            _logger.warning(
                "No 'VAT Not Applicable' purchase tax configured for "
                "company '%s'; leaving invoice line taxes as extracted.",
                company.display_name,
            )
            return
        for command in vals.get("invoice_line_ids", []):
            line_vals = command[2]
            if line_vals.get("display_type") in ("line_note", "line_section"):
                continue
            line_vals["tax_ids"] = [Command.set(no_vat_tax.ids)]

    @api.model
    def _add_l10n_ar_other_charges(self, parsed_inv, import_config, vals):
        """Percepción IIBB/IVA and similar AR document-level charges
        extracted by OCR: apply the matching AFIP tribute tax
        (account.tax.group.l10n_ar_tribute_afip_code) to the existing
        product invoice lines' tax_ids, the same "Impuestos" column IVA
        already goes through, rather than adding a new, separate invoice
        line. Percepciones are computed from the real taxable base already
        on those lines - attaching the resolved tax to a fabricated line
        seeded with the extracted amount would tax that amount again
        (e.g. 3% of an already-computed $649.95 instead of 3% of the real
        base), which is what caused the wrong amounts and stray
        "Adjustment" lines this method used to produce.

        Best-effort: a charge whose tribute tax can't be resolved is still
        added as a plain untaxed line (keeps the total correct, never
        double-taxes) with a chatter/log warning, rather than blocking the
        import.
        """
        charges = parsed_inv.get("l10n_ar_other_charges")
        if not charges or parsed_inv["type"] not in ("in_invoice", "in_refund"):
            return
        company = import_config["company"]
        has_tribute_field = (
            "l10n_ar_tribute_afip_code" in self.env["account.tax.group"]._fields
        )
        product_lines = [
            command[2]
            for command in vals.get("invoice_line_ids", [])
            if command[2].get("display_type") not in ("line_note", "line_section")
        ]
        for charge in charges:
            tax = self.env["account.tax"]
            tribute_code = None
            if has_tribute_field:
                tribute_code = self._L10N_AR_TRIBUTE_CODE_BY_CHARGE_TYPE.get(
                    charge["type"],
                    self._L10N_AR_TRIBUTE_CODE_BY_CHARGE_TYPE["other"],
                )
                tax = self.env["account.tax"].search(
                    [
                        ("company_id", "=", company.id),
                        ("type_tax_use", "=", "purchase"),
                        ("tax_group_id.l10n_ar_tribute_afip_code", "=", tribute_code),
                    ],
                    limit=1,
                )
            if tax and product_lines:
                for line_vals in product_lines:
                    existing_ids = (
                        line_vals["tax_ids"][0][2] if line_vals.get("tax_ids") else []
                    )
                    line_vals["tax_ids"] = [Command.set(list(existing_ids) + tax.ids)]
                continue
            if tribute_code and not tax:
                _logger.warning(
                    "No purchase tax configured for AFIP tribute code "
                    "'%s' (charge type '%s'); adding '%s' as an "
                    "untaxed line.",
                    tribute_code,
                    charge["type"],
                    charge["description"],
                )
            account = import_config.get("account")
            if not account:
                _logger.warning(
                    "No default expense account resolved for company '%s'; "
                    "skipping extracted other-charge line '%s'.",
                    company.display_name,
                    charge["description"],
                )
                continue
            bdio = self.env["business.document.import"]
            # "C62" is uom.product_uom_unit's UNECE code (guaranteed present
            # since base_business_document_import depends on uom_unece).
            # Pointing _match_uom() at it directly resolves to the same
            # 'Unit(s)' fallback an empty uom_dict would produce, but
            # without the "couldn't find any unit of measure" chatter
            # warning - this fallback line never has a real extracted UOM
            # to look up.
            uom = bdio._match_uom(
                {"unece_code": "C62"}, parsed_inv["chatter_msg"], raise_exception=False
            )
            vals["invoice_line_ids"].append(
                Command.create(
                    {
                        "display_type": "product",
                        "product_id": False,
                        "product_uom_id": uom.id,
                        "account_id": account.id,
                        "tax_ids": [],
                        "quantity": 1.0,
                        "price_unit": charge["amount"],
                        "name": charge["description"],
                    }
                )
            )

    @api.model
    def _fix_l10n_ar_vat_percent(self, parsed_inv, import_config, vals):
        """Correct the VAT tax applied to invoice lines using the rate
        implied by the extracted totals, when it disagrees with the
        LLM-extracted taxPercent.

        The LLM's per-line taxPercent reading has proven unreliable on AR
        invoices (observed flipping between 21% and 27% across identical
        re-imports of the same document), while amount_untaxed/amount_total
        have stayed stable across every extraction attempt. Deriving the
        real VAT rate from those two figures instead of trusting the
        labeled percentage sidesteps that unreliability for the common
        case of a single VAT rate applying to the whole invoice.

        Best-effort and non-blocking: skipped entirely if l10n_ar isn't
        installed, if totals are missing, if invoice lines don't already
        agree on a single current VAT-type tax (e.g. a genuinely
        mixed-rate invoice, or a Factura B/C with "VAT Not Applicable"
        lines), or if no configured tax matches the derived rate closely
        enough.
        """
        if parsed_inv["type"] not in ("in_invoice", "in_refund"):
            return
        if "l10n_ar_vat_afip_code" not in self.env["account.tax.group"]._fields:
            return
        amount_untaxed = parsed_inv.get("amount_untaxed")
        amount_total = parsed_inv.get("amount_total")
        if not amount_untaxed or amount_total is None:
            return

        product_lines = [
            command[2]
            for command in vals.get("invoice_line_ids", [])
            if command[2].get("display_type") not in ("line_note", "line_section")
        ]
        if not product_lines:
            return

        company = import_config["company"]
        ato = self.env["account.tax"]
        vat_taxes = ato.search(
            [
                ("company_id", "=", company.id),
                ("type_tax_use", "=", "purchase"),
                ("amount_type", "=", "percent"),
                ("tax_group_id.l10n_ar_vat_afip_code", "not in", [False, "0"]),
            ]
        )
        if not vat_taxes:
            return

        # Identify the single VAT-type tax currently applied across all
        # lines (as opposed to percepción/other taxes, already merged in
        # by _add_l10n_ar_other_charges above). Bail if lines don't agree
        # on exactly one, since the document-level rate derived below
        # wouldn't be meaningful otherwise.
        current_vat_ids = set()
        for line_vals in product_lines:
            line_tax_ids = (
                line_vals["tax_ids"][0][2] if line_vals.get("tax_ids") else []
            )
            line_vat_ids = vat_taxes.filtered(lambda t: t.id in line_tax_ids).ids
            if len(line_vat_ids) > 1:
                return
            current_vat_ids.update(line_vat_ids)
        if len(current_vat_ids) != 1:
            return
        current_vat_tax = ato.browse(next(iter(current_vat_ids)))

        other_charges_total = sum(
            charge["amount"] for charge in parsed_inv.get("l10n_ar_other_charges") or []
        )
        implied_vat_amount = amount_total - amount_untaxed - other_charges_total
        implied_vat_percent = implied_vat_amount / amount_untaxed * 100

        best_tax = min(vat_taxes, key=lambda t: abs(t.amount - implied_vat_percent))
        if (
            abs(best_tax.amount - implied_vat_percent)
            > self._L10N_AR_VAT_PERCENT_TOLERANCE
        ):
            return
        if best_tax.id == current_vat_tax.id:
            return

        for line_vals in product_lines:
            existing_ids = (
                line_vals["tax_ids"][0][2] if line_vals.get("tax_ids") else []
            )
            new_ids = [tid for tid in existing_ids if tid != current_vat_tax.id]
            new_ids.append(best_tax.id)
            line_vals["tax_ids"] = [Command.set(new_ids)]

        parsed_inv["chatter_msg"].append(
            _(
                "The extracted VAT rate (%(old)s) did not match the invoice "
                "totals; it was adjusted to %(new)s based on the reported "
                "total amount."
            )
            % {"old": current_vat_tax.name, "new": best_tax.name}
        )
