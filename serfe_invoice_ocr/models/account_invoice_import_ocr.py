"""
Invoice OCR Extraction — Argentina overrides

Extends apx_account_invoice_import_llm's account.invoice.import.ocr abstract
model (left unmodified) with LiteLLM-based OCR (instead of Mistral) and
Argentine/AFIP-specific extraction behavior. _call_llm_for_extraction() and
_parse_llm_response() are generic glue code with no provider- or
country-specific logic, so they are inherited unchanged from the base
module and not overridden here.
"""

import logging

from odoo import _, api, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AccountInvoiceImportOCR(models.AbstractModel):
    _inherit = "account.invoice.import.ocr"

    @api.model
    def extract_invoice_data(self, file_data, company=None, mimetype="application/pdf"):
        """Same orchestration as the base implementation, except the
        company context is threaded through to _render_invoice_extraction_prompt()
        so _get_l10n_ar_vat_rates_note() reads the right company's VAT
        rates rather than silently falling back to self.env.company.
        """
        ocr_text = self._run_ocr_on_file_data(file_data, mimetype)
        if not ocr_text:
            raise UserError(
                _("OCR returned empty text. The document may be unreadable or empty.")
            )

        prepend_messages, assistant = self._render_invoice_extraction_prompt(
            ocr_text, company
        )
        llm_response = self._call_llm_for_extraction(prepend_messages, assistant)
        invoice_data = self._parse_llm_response(llm_response)
        return self._convert_llm_data_to_pivot(invoice_data)

    @api.model
    def _is_invoice_extraction_enabled(self):
        """Non-raising check for callers that just need to know
        whether AI-based invoice import is currently usable,
        without wanting the UserError _get_invoice_extraction_assistant()
        raises when it isn't.
        """
        return bool(
            self.env["llm.assistant"].get_assistant_by_code("invoice_extraction")
        )

    @api.model
    def _get_invoice_extraction_assistant(self):
        """Resolve the invoice_extraction assistant, raising a clear,
        cause-specific UserError when it can't be used.

        Archiving this assistant (its existing toggle_active button) is
        how AI-based invoice import gets turned off - get_assistant_by_code()
        excludes archived records from its search by default, same as any
        other Odoo search, so this distinguishes that intentional-disable
        case from a genuinely missing/misconfigured assistant, which would
        otherwise both surface as the same confusing "not found" message.
        """
        Assistant = self.env["llm.assistant"]
        assistant = Assistant.get_assistant_by_code("invoice_extraction")
        if assistant:
            return assistant

        archived = Assistant.with_context(active_test=False).get_assistant_by_code(
            "invoice_extraction"
        )
        if archived:
            raise UserError(
                _(
                    "AI-based invoice import is currently disabled.\n\n"
                    "Go to LLM → Configuration → Assistants, filter by Archived, "
                    "open 'Invoice Extraction', and re-enable it to turn "
                    "AI import back on."
                )
            )
        raise UserError(
            _(
                "Invoice Extraction Assistant Not Found\n\n"
                "Go to LLM → Configuration → Assistants and create an assistant "
                "with code 'invoice_extraction'."
            )
        )

    @api.model
    def _run_ocr_on_file_data(self, file_data, mimetype="application/pdf"):
        """Run OCR directly on file bytes without creating an attachment.

        Reuses the same provider/model already configured on the
        "invoice_extraction" assistant to transcribe the document, so OCR
        and extraction always go through the same LLM provider (LiteLLM),
        instead of the base module's hardcoded Mistral OCR provider lookup.

        Raises:
            UserError: If the assistant is disabled/missing/has no model,
                or its provider doesn't support OCR
        """
        assistant = self._get_invoice_extraction_assistant()
        if not assistant.model_id:
            raise UserError(
                _(
                    "Invoice Extraction Assistant Has No Model\n\n"
                    "Go to LLM → Configuration → Assistants, open 'Invoice "
                    "Extraction', and configure a model."
                )
            )

        provider = assistant.model_id.provider_id
        if provider.service != "litellm":
            raise UserError(
                _(
                    "OCR is only supported for providers of the 'AI Service' "
                    "type. The Invoice Extraction assistant's model is "
                    "configured on a '%s' provider."
                )
                % provider.service
            )

        return provider.litellm_process_ocr(
            model_name=assistant.model_id.name,
            data=file_data,
            mimetype=mimetype,
        )

    @api.model
    def _render_invoice_extraction_prompt(self, ocr_text, company=None):
        """Render the invoice extraction prompt with OCR text and this
        company's configured Argentine VAT rates.

        Args:
            ocr_text (str): OCR extracted text from invoice
            company (res.company): Company to read configured VAT rates
                from (see _get_l10n_ar_vat_rates_note). Defaults to the
                current user's company.

        Returns:
            tuple: (prepend_messages, assistant) ready for model.chat()
        """
        company = company or self.env.company

        assistant = self._get_invoice_extraction_assistant()
        if not assistant.prompt_id:
            raise UserError(
                _(
                    "Invoice Extraction Assistant Has No Prompt\n\n"
                    "Go to LLM → Configuration → Assistants, open 'Invoice "
                    "Extraction', and configure a prompt."
                )
            )

        context = {
            "ocr_text": ocr_text,
            "vat_rates_note": self._get_l10n_ar_vat_rates_note(company),
            "company_name": company.name,
            "company_vat": company.vat or "",
            "company_currency": company.currency_id.name,
        }

        evaluated_values = assistant.get_evaluated_default_values(context)
        messages = assistant.prompt_id.get_messages(evaluated_values)

        return messages, assistant

    @api.model
    def _get_l10n_ar_vat_rates_note(self, company):
        """Build a prompt addendum listing this company's actually
        configured Argentine VAT rates, read live from account.tax.

        Read live rather than hardcoded in the prompt so it always matches
        this company's chart of accounts, and so the LLM has the real rate
        catalog (e.g. 27% for telecom/gas/electricity non-residential
        invoices) instead of anchoring on commonly-seen European rates
        (21%, 9%) and misreading a different one from the OCR text.

        Returns "" (no addendum) when l10n_ar isn't installed, the company
        isn't Argentine, or no purchase VAT taxes are configured - the
        prompt instructions read fine without it either way.
        """
        atgo = self.env["account.tax.group"]
        if (
            not company
            or company.account_fiscal_country_id.code != "AR"
            or "l10n_ar_vat_afip_code" not in atgo._fields
        ):
            return ""
        taxes = self.env["account.tax"].search(
            [
                ("company_id", "=", company.id),
                ("type_tax_use", "=", "purchase"),
                ("amount_type", "=", "percent"),
                ("tax_group_id.l10n_ar_vat_afip_code", "not in", [False, "0"]),
            ]
        )
        rates = sorted({tax.amount for tax in taxes})
        if not rates:
            return ""
        rates_str = ", ".join(f"{rate:g}%" for rate in rates)
        return (
            "\n\n**Valid Argentine VAT (IVA) rates configured for this "
            f"company: {rates_str}.** Read the percentage character-by-"
            "character from the OCR text - do not default to a commonly "
            "seen rate (e.g. 21%) if the invoice actually shows a "
            "different one from this list (e.g. 27% is common on "
            "telecom/gas/electricity invoices for non-residential use)."
        )

    @api.model
    def _convert_llm_data_to_pivot(self, llm_data):
        """Convert LLM extraction format → Invoice Pivot Format, with
        Argentine-specific fields (invoiceLetter, otherCharges), ARS as the
        default currency (this deployment only imports Argentine vendor
        bills, unlike upstream OCA/Apexive which targets Europe), and a
        UNECE "C62" (unit) fallback UOM on every line, since AR invoices
        never carry a UNECE unit code.
        """
        parsed_inv = {
            "type": "in_invoice",
            "chatter_msg": [],
        }

        # The LLM is asked (see data/invoice_extraction_assistant_data.xml)
        # to self-report whether the document is actually an invoice before
        # extracting anything else - a heuristic on the output shape alone
        # (e.g. "no lines extracted") isn't reliable, since a non-invoice
        # document (a book, a receipt, a contract) can still make the model
        # hallucinate a plausible-looking vendor/line/total instead of
        # returning nothing. The no-vendor-and-no-total fallback below only
        # catches the case where isInvoice is missing entirely (older/
        # non-compliant responses).
        if llm_data.get("isInvoice") is False or (
            not llm_data.get("vendorName") and not llm_data.get("totalAmount")
        ):
            parsed_inv["chatter_msg"].append(
                _(
                    "This document does not appear to be an invoice. "
                    "Please review the attached file and complete the "
                    "invoice manually."
                )
            )

        if llm_data.get("vendorName") or llm_data.get("vat"):
            partner_data = {}
            if llm_data.get("vendorName"):
                partner_data["name"] = llm_data["vendorName"]
            if llm_data.get("vat"):
                vat = llm_data["vat"].replace(" ", "").upper()
                partner_data["vat"] = vat
            parsed_inv["partner"] = partner_data

        currency_code = llm_data.get("currency", "ARS")
        parsed_inv["currency"] = {"iso": currency_code}

        if llm_data.get("invoiceDate"):
            parsed_inv["date"] = llm_data["invoiceDate"]
        if llm_data.get("dueDate"):
            parsed_inv["date_due"] = llm_data["dueDate"]

        if llm_data.get("invoiceNumber"):
            parsed_inv["invoice_number"] = llm_data["invoiceNumber"]

        # Argentine invoice letter (A/B/C), consumed by this module's
        # wizard override to resolve l10n_latam_document_type_id/number.
        # Not part of OCA's standard pivot format - ignored where l10n_ar
        # isn't installed.
        letter = (llm_data.get("invoiceLetter") or "").strip().upper()[:1]
        if letter in ("A", "B", "C"):
            parsed_inv["l10n_ar_letter"] = letter

        # Argentine perceptions/withholdings (Percepción IIBB, Percepción
        # IVA, etc.) shown as extra document-level charges on top of
        # subtotal+IVA. Kept as raw data here; this module's wizard
        # override turns each into its own invoice line, matching an
        # account.tax by AFIP tribute code (account.tax.group.l10n_ar_tribute_afip_code)
        # when l10n_ar is installed. Same non-OCA-standard-pivot rationale
        # as l10n_ar_letter above.
        other_charges = []
        for charge in llm_data.get("otherCharges") or []:
            if charge.get("amount") is None:
                continue
            other_charges.append(
                {
                    "description": charge.get("description") or _("Other Charge"),
                    "amount": float(charge["amount"]),
                    "type": (charge.get("type") or "other").strip().lower(),
                }
            )
        if other_charges:
            parsed_inv["l10n_ar_other_charges"] = other_charges

        if llm_data.get("subtotalAmount") is not None:
            parsed_inv["amount_untaxed"] = float(llm_data["subtotalAmount"])
        if llm_data.get("totalAmount") is not None:
            parsed_inv["amount_total"] = float(llm_data["totalAmount"])

        if llm_data.get("lines"):
            pivot_lines = []
            for llm_line in llm_data["lines"]:
                qty = float(llm_line.get("quantity", 1.0))
                price_unit = float(llm_line.get("unitPrice", 0.0))

                if llm_line.get("lineSubtotal") is not None:
                    price_subtotal = float(llm_line["lineSubtotal"])
                else:
                    price_subtotal = qty * price_unit

                pivot_line = {
                    "name": llm_line.get("description", "Invoice Line"),
                    "qty": qty,
                    "price_unit": price_unit,
                    # OCA needs price_subtotal for adjustment calculations.
                    "price_subtotal": price_subtotal,
                    # Always a list, never None - OCA expects a list here.
                    "taxes": [],
                    # We never ask the LLM for a unit of measure: AR invoices
                    # don't carry a UNECE unit code, so it would always come
                    # back empty. Pointing _match_uom() straight at "C62"
                    # (uom.product_uom_unit's UNECE code, guaranteed present
                    # since base_business_document_import depends on
                    # uom_unece) makes it resolve on the first search instead
                    # of falling through to its "couldn't find any unit of
                    # measure" chatter warning - same fallback UOM, no noise.
                    "uom": {"unece_code": "C62"},
                }

                # Deliberately no "unece_type_code" here: that field is only
                # populated on taxes tagged by account_tax_unece, which
                # never happens for l10n_ar taxes (IVA, percepciones,
                # retenciones). Including it would make _match_tax() find
                # zero candidates for AR companies and silently drop the
                # tax from the line. Matching on amount_type + amount alone
                # still works for AR.
                if llm_line.get("taxPercent") is not None:
                    tax_percent = float(llm_line["taxPercent"])
                    pivot_line["taxes"] = [
                        {
                            "amount_type": "percent",
                            "amount": tax_percent,
                        }
                    ]

                pivot_lines.append(pivot_line)

            parsed_inv["lines"] = pivot_lines
        else:
            _logger.warning("No invoice lines extracted by LLM, creating single line")
            parsed_inv["lines"] = [
                {
                    "name": _("Invoice Line (no details extracted)"),
                    "qty": 1.0,
                    "price_unit": parsed_inv.get("amount_untaxed", 0.0),
                }
            ]

        parsed_inv["chatter_msg"].append(
            _(
                "Invoice data extracted using LLM-OCR technology. "
                "Please verify the extracted information."
            )
        )

        return parsed_inv
