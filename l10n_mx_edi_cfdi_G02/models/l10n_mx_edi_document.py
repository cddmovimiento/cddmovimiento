from odoo import models, api


class L10nMxEdiDocument(models.Model):
    _inherit = "l10n_mx_edi.document"

    def _add_base_lines_cfdi_values(self, cfdi_values, base_lines, percentage_paid=None):
        super()._add_base_lines_cfdi_values(
            cfdi_values,
            base_lines,
            percentage_paid
        )
        
        is_refound_gi = cfdi_values['receptor']['uso_cfdi'] == 'G02'
        base_lines_map = {line['record']: line for line in base_lines}
        
        if not is_refound_gi:
            return
        
        for base_line_values in cfdi_values('conceptos_list', []):
                line = base_line_values.get('line',{}).get('record')
                base_line = base_lines_map.get(line)
                
                if base_line.get('name') == "":
                    description = "Devoluciones, descuentos o bonificaciones"
                else:
                    description = base_line.get('name')
                
                base_line_values['description'] = description.get('name')