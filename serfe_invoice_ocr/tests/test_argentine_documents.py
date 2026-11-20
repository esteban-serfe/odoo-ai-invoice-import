from odoo import Command
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestArgentineDocuments(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        country = cls.env.ref("base.ar")
        responsibility = cls.env["l10n_ar.afip.responsibility.type"].search(
            [("code", "=", "1")], limit=1
        )
        cls.company = cls.env["res.company"].create(
            {
                "name": "Argentina OCR Tests",
                "country_id": country.id,
                "account_fiscal_country_id": country.id,
                "l10n_ar_afip_responsibility_type_id": responsibility.id,
            }
        )
        cls.journal = cls.env["account.journal"].with_company(cls.company).create(
            {"name": "Purchases AR", "code": "OARP", "type": "purchase"}
        )
        cls.wizard = cls.env["account.invoice.import"].with_company(cls.company)
        cls.ocr = cls.env["account.invoice.import.ocr"].with_company(cls.company)
        no_vat_group = cls.env["account.tax.group"].search(
            [("l10n_ar_vat_afip_code", "=", "0")], limit=1
        )
        cls.no_vat = cls.env["account.tax"].with_company(cls.company).create(
            {
                "name": "VAT not applicable test",
                "amount": 0,
                "type_tax_use": "purchase",
                "tax_group_id": no_vat_group.id,
            }
        )

    def test_latam_document_number_and_vat_for_letters_a_b_c(self):
        for letter, afip_code in (("A", "1"), ("B", "6"), ("C", "11")):
            with self.subTest(letter=letter):
                parsed = self.ocr._convert_llm_data_to_pivot(
                    {
                        "isInvoice": True,
                        "vendorName": "Proveedor de prueba",
                        "vat": "30-12345678-9",
                        "invoiceNumber": "0003-00000456",
                        "invoiceLetter": letter,
                        "invoiceDate": "2026-11-19",
                        "subtotalAmount": 100,
                        "totalAmount": 127,
                        "lines": [
                            {
                                "description": "Service",
                                "unitPrice": 100,
                                "taxPercent": 27,
                                "taxPercentEvidence": "IVA 27%",
                            }
                        ],
                    }
                )
                self.assertEqual(parsed["partner"]["vat"], "30-12345678-9")
                self.assertEqual(parsed["date"], "2026-11-19")
                vals = {
                    "journal_id": self.journal.id,
                    "invoice_line_ids": [Command.create({"price_unit": 100})],
                }
                self.wizard._set_l10n_ar_document(parsed, {"company": self.company}, vals)
                document_type = self.env["l10n_latam.document.type"].browse(
                    vals["l10n_latam_document_type_id"]
                )
                self.assertEqual(document_type.code, afip_code)
                self.assertEqual(vals["l10n_latam_document_number"], "00003-00000456")
                if letter in ("B", "C"):
                    self.assertEqual(
                        vals["invoice_line_ids"][0][2]["tax_ids"],
                        [Command.set(self.no_vat.ids)],
                    )
                else:
                    self.assertNotIn("tax_ids", vals["invoice_line_ids"][0][2])
