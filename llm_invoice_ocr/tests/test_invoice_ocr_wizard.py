"""End-to-end test of the OCA import wizard's LLM-OCR fallback path.

Exercises the real wizard button (account.invoice.import.import_invoices)
through the full production code path (fallback_parse_pdf_invoice ->
account.invoice.import.ocr -> litellm_process_ocr -> llm.model.chat ->
llm.provider litellm_chat -> LiteLLMClient) down to creating the
account.move record, without touching the network: only the HTTP transport
(requests.Session.request) is mocked, at its narrowest external-dependency
seam, so both the OCR and the extraction call go through the real
LiteLLMClient/litellm_provider code end to end, and no LLM tokens are
consumed.

Relocated from serfe_account_invoice_import_llm/tests/test_import_wizard_litellm.py
as part of extracting the Argentina-specific invoice OCR behavior out of that
(now pristine, unmodified) third-party module.
"""

import base64
import json
from unittest.mock import MagicMock, patch

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

MOCK_OCR_TEXT = (
    "Invoice from Acme Corp. Total: 121.00 EUR (100.00 + 21% VAT = 21.00). "
    "Invoice number INV-2024-001, date 2024-01-15."
)
MOCK_LLM_JSON = json.dumps(
    {
        "vendorName": "Acme Corp",
        # Matches the partner created in setUpClass, so _match_partner()
        # resolves a real partner_id (with a real property_payment_term_id)
        # instead of leaving the invoice partner-less.
        "vat": "BE0123456789",
        "invoiceNumber": "INV-2024-001",
        "invoiceDate": "2024-01-15",
        # Deliberately no "dueDate": account_invoice_import.py sets
        # invoice_date_due AND clears invoice_payment_term_id whenever
        # date_due is present, overriding the partner's payment term above
        # regardless. Leaving it out lets Odoo compute the due date from
        # the matched partner's property_payment_term_id instead, the
        # standard path that reliably produces a valid payment_term line.
        "subtotalAmount": 100.0,
        "taxAmount": 21.0,
        "totalAmount": 121.0,
        "currency": "EUR",
        "lines": [
            {
                "description": "Consulting services",
                "quantity": 1.0,
                "unitPrice": 100.0,
                "lineSubtotal": 100.0,
                "taxPercent": 21.0,
            }
        ],
    }
)


def _fake_responses_sse(text):
    """Build a fake requests.Response mimicking the real LiteLLM /responses
    SSE stream shape (captured live against litellm.example.test): the final
    aggregated object carries no output, only the response.output_text.done
    event does - see LiteLLMClient._aggregate_response_text.
    """
    lines = [
        b'data: {"type": "response.created"}',
        b'data: {"type": "response.in_progress"}',
        (
            'data: {"type": "response.output_text.done", "text": %s}' % json.dumps(text)
        ).encode(),
        b'data: {"type": "response.completed", "response": {"output": []}}',
        b"data: [DONE]",
    ]
    fake_response = MagicMock()
    fake_response.iter_lines.return_value = lines
    fake_response.raise_for_status.return_value = None
    return fake_response


# Needs a chart of accounts and journals, see test_llm_ocr_enabled.py.
@tagged("post_install", "-at_install")
class TestInvoiceImportLiteLLM(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.provider = cls.env["llm.provider"].create(
            {
                "name": "Test LiteLLM",
                "service": "litellm",
                "api_base": "https://litellm.example.test",
                "api_key": "sk-test",
            }
        )
        cls.model = cls.env["llm.model"].create(
            {
                "name": "chatgpt-gpt-5.4",
                "provider_id": cls.provider.id,
                "model_use": "chat",
                "model_info": {"mode": "responses"},
            }
        )
        cls.assistant = cls.env["llm.assistant"].search(
            [("code", "=", "invoice_extraction")], limit=1
        )
        cls.assistant.model_id = cls.model.id

        # OCA's _prepare_create_invoice_journal() requires a Purchase
        # journal to exist on the company, and (since our mock extraction
        # never matches an existing Odoo product - realistic for LLM-OCR'd
        # vendor bills) _last_update_import_config() falls back to the
        # journal's default_account_id for invoice lines. In a fresh test
        # DB both only get set once l10n_generic_coa loads, which can
        # happen after llm_invoice_ocr in the module graph - so neither
        # is reliably present yet at this point. Create them explicitly,
        # matching account_invoice_import's own test suite convention of
        # setting up exactly the accounting fixtures a test needs rather
        # than relying on chart-of-accounts install order.
        purchase_journal = cls.env["account.journal"].search(
            [("type", "=", "purchase"), ("company_id", "=", cls.env.company.id)],
            limit=1,
        )
        if not purchase_journal:
            expense_account = cls.env["account.account"].create(
                {
                    "code": "TESTEXP",
                    "name": "Test Expense Account",
                    "account_type": "expense",
                    "company_id": cls.env.company.id,
                }
            )
            purchase_journal = cls.env["account.journal"].create(
                {
                    "name": "Test Vendor Bills",
                    "code": "TVB",
                    "type": "purchase",
                    "company_id": cls.env.company.id,
                    "default_account_id": expense_account.id,
                }
            )
        elif not purchase_journal.default_account_id:
            expense_account = cls.env["account.account"].create(
                {
                    "code": "TESTEXP",
                    "name": "Test Expense Account",
                    "account_type": "expense",
                    "company_id": cls.env.company.id,
                }
            )
            purchase_journal.default_account_id = expense_account.id

        # Match the vendor by VAT (see MOCK_LLM_JSON) so the invoice gets a
        # real partner_id with a payment term Odoo can use to build the
        # payable line's payment_term display line - without a matched
        # partner, OCA's own code leaves the invoice partner-less (flags it
        # for manual resolution instead, a separate real behavior, not
        # something this test needs to also exercise), and with no partner
        # there's no property_payment_term_id for Odoo to fall back on.
        payment_term = cls.env["account.payment.term"].search([], limit=1)
        if not payment_term:
            payment_term = cls.env["account.payment.term"].create(
                {
                    "name": "Test Immediate Payment",
                    "line_ids": [(0, 0, {"value": "balance", "nb_days": 0})],
                }
            )
        # _check_payable_receivable requires the invoice's auto-generated
        # control line to sit on an account_type="liability_payable"
        # account. A fresh test DB with no chart of accounts loaded yet has
        # no such account at all, so create one explicitly and assign it as
        # this partner's payable account - the actual missing piece behind
        # every previous attempt at this constraint, regardless of due
        # date/payment term.
        payable_account = cls.env["account.account"].create(
            {
                "code": "TESTPAY",
                "name": "Test Accounts Payable",
                "account_type": "liability_payable",
                "reconcile": True,
                "company_id": cls.env.company.id,
            }
        )
        # no_vat_validation: this test only needs _match_partner() to find
        # a partner by VAT, not a real, checksum-valid one - country-aware
        # environments (e.g. l10n_ar installed) enforce structural VAT
        # validation on create() otherwise.
        cls.partner = (
            cls.env["res.partner"]
            .with_context(no_vat_validation=True)
            .create(
                {
                    "name": "Acme Corp",
                    "vat": "BE0123456789",
                    "supplier_rank": 1,
                    "property_payment_term_id": payment_term.id,
                    "property_account_payable_id": payable_account.id,
                }
            )
        )

    @staticmethod
    def _minimal_pdf_bytes():
        # No embedded XML, so pdf_helper.pdf_get_xml_files() finds nothing
        # and the wizard falls through to fallback_parse_pdf_invoice().
        return (
            b"%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF"
        )

    @patch("requests.Session.request")
    def test_import_invoice_via_litellm_responses_mode(self, mock_request):
        # First call is the OCR transcription (litellm_process_ocr), second
        # is the structured extraction (_litellm_chat_responses_mode) - both
        # go through LiteLLMClient.create_response -> POST /responses.
        mock_request.side_effect = [
            _fake_responses_sse(MOCK_OCR_TEXT),
            _fake_responses_sse(MOCK_LLM_JSON),
        ]

        attachment = self.env["ir.attachment"].create(
            {
                "name": "invoice.pdf",
                "datas": base64.b64encode(self._minimal_pdf_bytes()),
            }
        )
        wizard = self.env["account.invoice.import"].create(
            {"invoice_attachment_ids": [(6, 0, attachment.ids)]}
        )

        action = wizard.import_invoices()

        # No real HTTP call: only our mocked transport, hit exactly twice
        # (OCR, then extraction), both against /responses.
        self.assertEqual(mock_request.call_count, 2)
        for call in mock_request.call_args_list:
            self.assertIn("/responses", call.kwargs["url"])

        invoice_id = action["params"]["next"]["res_id"]
        invoice = self.env["account.move"].browse(invoice_id)
        self.assertEqual(invoice.move_type, "in_invoice")
        self.assertEqual(invoice.ref, "INV-2024-001")
        # amount_untaxed is not asserted: it depends on this database having
        # a 21% VAT account.tax configured to match against, which is an
        # OCA/chart-of-accounts concern unrelated to the LLM extraction path
        # this test exercises.
        self.assertEqual(invoice.amount_total, 121.0)
        self.assertEqual(len(invoice.invoice_line_ids), 1)
        self.assertEqual(invoice.invoice_line_ids[0].name, "Consulting services")

        # The source file is set as the move's main attachment, so the vendor
        # bill form's PDF preview renders without a manual page reload
        # (llm_invoice_ocr.models.business_document_import).
        self.assertTrue(invoice.message_main_attachment_id)
        self.assertEqual(invoice.message_main_attachment_id.res_model, "account.move")
        self.assertEqual(invoice.message_main_attachment_id.res_id, invoice.id)
        self.assertEqual(invoice.message_main_attachment_id.mimetype, "application/pdf")

    @patch("requests.Session.request")
    def test_extraction_failure_creates_invoice_with_warning(self, mock_request):
        """fallback_parse_pdf_invoice()'s except block must not silently
        swallow an extraction failure into a blank, unexplained invoice
        (parsed_inv = {}, no chatter_msg) - same "no importar vacío
        silenciosamente" requirement as the non-invoice-document case,
        just triggered by a raised exception instead of an isInvoice=false
        classification. See Ticket 0140997.
        """
        # Fails on the very first call (OCR transcription), simulating a
        # network/API failure rather than a malformed response.
        mock_request.side_effect = Exception("Simulated network failure")

        attachment = self.env["ir.attachment"].create(
            {
                "name": "invoice.pdf",
                "datas": base64.b64encode(self._minimal_pdf_bytes()),
            }
        )
        wizard = self.env["account.invoice.import"].create(
            {"invoice_attachment_ids": [(6, 0, attachment.ids)]}
        )

        action = wizard.import_invoices()

        invoice_id = action["params"]["next"]["res_id"]
        invoice = self.env["account.move"].browse(invoice_id)

        # Still created, never silently.
        self.assertEqual(invoice.move_type, "in_invoice")
        self.assertEqual(invoice.state, "draft")
        self.assertTrue(invoice.import_warnings)
        self.assertIn("extraction failed", invoice.import_warnings)

        # Original file still preserved as an attachment (ticket:
        # "conservar el archivo original") - confirmed to still hold on
        # this failure path too.
        attachments = self.env["ir.attachment"].search(
            [("res_model", "=", "account.move"), ("res_id", "=", invoice.id)]
        )
        self.assertIn("invoice.pdf", attachments.mapped("name"))

    def test_upload_button_opens_wizard_for_vendor_bills(self):
        """account.journal.create_document_from_attachment() is the method
        behind the "Upload" button. For a vendor bill/refund context (the
        "default_move_type" the real Vendor Bills action and journal
        dashboard widget both set), OCA's own implementation creates the
        account.invoice.import wizard and immediately calls
        import_invoices() on it, creating the invoice with no review step.
        Overridden here to stop before that call and open the wizard
        instead - see Ticket 0141016.
        """
        attachment = self.env["ir.attachment"].create(
            {
                "name": "invoice.pdf",
                "datas": base64.b64encode(self._minimal_pdf_bytes()),
            }
        )
        move_count_before = self.env["account.move"].search_count([])

        action = (
            self.env["account.journal"]
            .with_context(default_move_type="in_invoice")
            .create_document_from_attachment(attachment.ids)
        )

        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["res_model"], "account.invoice.import")
        self.assertEqual(action["view_mode"], "form")
        self.assertEqual(action["target"], "new")

        wizard = self.env["account.invoice.import"].browse(action["res_id"])
        self.assertIn(attachment, wizard.invoice_attachment_ids)

        # No invoice created yet - creation only happens once the user
        # reviews the wizard and clicks its own "Import" button.
        self.assertEqual(self.env["account.move"].search_count([]), move_count_before)

    def test_upload_button_does_not_open_wizard_for_customer_invoices(self):
        """Clicking Upload on a non-vendor-bill list (e.g. Customer
        Invoices, "default_move_type": "out_invoice") must not route
        through the vendor-bill OCR wizard at all - see Ticket 0141016.
        """
        attachment = self.env["ir.attachment"].create(
            {
                "name": "invoice.pdf",
                "datas": base64.b64encode(self._minimal_pdf_bytes()),
            }
        )
        wizard_count_before = self.env["account.invoice.import"].search_count([])

        action = (
            self.env["account.journal"]
            .with_context(default_move_type="out_invoice")
            .create_document_from_attachment(attachment.ids)
        )

        self.assertEqual(action["res_model"], "account.move")
        self.assertEqual(
            self.env["account.invoice.import"].search_count([]),
            wizard_count_before,
        )
