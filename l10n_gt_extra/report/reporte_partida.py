# -*- encoding: utf-8 -*-

from odoo import api, models


class ReportePartida(models.AbstractModel):
    _name = 'report.l10n_gt_extra.reporte_partida'
    _description = 'Partida contable'

    def analitica(self, linea):
        if not linea.analytic_distribution:
            return ''
        ids = [int(x) for llave in linea.analytic_distribution for x in llave.split(',')]
        return ', '.join(self.env['account.analytic.account'].browse(ids).exists().mapped('name'))

    @api.model
    def _get_report_values(self, docids, data=None):
        model = 'account.move'
        docs = self.env[model].browse(docids)

        return {
            'doc_ids': docids,
            'doc_model': model,
            'docs': docs,
            'analitica': self.analitica,
            'current_company_id': self.env.company,
        }
