from odoo import models, api


class L10nMxEdiDocument(models.Model):
    _inherit = "l10n_mx_edi.document"

    def _add_base_lines_cfdi_values(self, cfdi_values, base_lines, percentage_paid=None):
        super()._add_base_lines_cfdi_values(
            cfdi_values,
            base_lines,
            percentage_paid
        )

        is_refund_gi = cfdi_values['receptor']['uso_cfdi'] == 'G02'

        if not is_refund_gi:
            return

        for base_line_values in cfdi_values.get('conceptos_list', []):
            line = base_line_values.get('line',{}).get('record')

            if not line:
                continue

            base_line_values['description'] = (line.name or 'Devoluciones, descuentos o bonificaciones').strip()