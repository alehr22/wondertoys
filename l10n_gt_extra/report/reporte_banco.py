# -*- encoding: utf-8 -*-

from odoo import api, models


class ReporteBanco(models.AbstractModel):
    _name = 'report.l10n_gt_extra.reporte_banco'
    _description = 'Libro de banco'

    def lineas(self, datos):
        cuenta = self.env['account.account'].browse(datos['cuenta_bancaria_id'][0])

        lineas = []
        for linea in self.env['account.move.line'].search([('account_id', '=', cuenta.id), ('parent_state', '=', 'posted'), ('date', '>=', datos['fecha_desde']), ('date', '<=', datos['fecha_hasta'])], order='date'):
            detalle = {
                'fecha': linea.date,
                'documento': linea.move_id.name if linea.move_id else '',
                'nombre': linea.partner_id.name or '',
                'concepto': (linea.ref if linea.ref else '') + (linea.name if linea.name else ''),
                'debito': linea.debit,
                'credito': linea.credit,
                'balance': 0,
                'tipo': '',
                'moneda': linea.company_id.currency_id,
            }

            if linea.amount_currency:
                detalle['moneda'] = linea.currency_id
                if linea.amount_currency > 0:
                    detalle['debito'] = linea.amount_currency
                else:
                    detalle['credito'] = -1 * linea.amount_currency

            # Si la cuenta no tiene moneda o la moneda de la cuenta es la misma de la compañía
            if not cuenta.currency_id or (cuenta.currency_id.id == linea.company_id.currency_id.id):

                # Se agregan lineas que no tiene moneda o tienen la misma moneda que la compañía
                if not linea.currency_id or linea.currency_id.id == linea.company_id.currency_id.id:
                    lineas.append(detalle)

            # Sino, si la cuenta si tienen moneda y la moneda de la cuenta es diferente que la de la compañía
            else:

                # Se agregan lineas que tienen la moneda de la cuenta
                if linea.currency_id.id == cuenta.currency_id.id:
                    lineas.append(detalle)

        balance_inicial = self.balance_inicial(datos)
        if balance_inicial['balance_moneda']:
            balance = balance_inicial['balance_moneda']
        elif balance_inicial['balance']:
            balance = balance_inicial['balance']
        else:
            balance = 0

        for linea in lineas:
            balance = balance + linea['debito'] - linea['credito']
            linea['balance'] = balance

        return lineas

    def balance_inicial(self, datos):
        dominio = [
            ('account_id', '=', datos['cuenta_bancaria_id'][0]),
            ('parent_state', '=', 'posted'),
            ('date', '<', datos['fecha_desde']),
        ]
        balance, moneda = self.env['account.move.line']._read_group(dominio, [], ['balance:sum', 'amount_currency:sum'])[0]
        return {'balance': balance or 0, 'balance_moneda': moneda or 0}

    @api.model
    def _get_report_values(self, docids, data=None):
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_ids', []))

        return {
            'doc_ids': self.ids,
            'doc_model': model,
            'data': data['form'],
            'docs': docs,
            'moneda': docs[0].cuenta_bancaria_id.currency_id or self.env.company.currency_id,
            'lineas': self.lineas,
            'balance_inicial': self.balance_inicial(data['form']),
            'current_company_id': self.env.company,
        }
