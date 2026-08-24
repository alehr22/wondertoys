# -*- encoding: utf-8 -*-

from odoo import api, fields, models


class ReporteDiario(models.AbstractModel):
    _name = 'report.l10n_gt_extra.reporte_diario'
    _description = 'Libro diario'

    def retornar_saldo_inicial_todos_anios(self, cuenta, fecha_desde):
        dominio = [('account_id', '=', cuenta), ('date', '<', fecha_desde)]
        return self.env['account.move.line']._read_group(dominio, [], ['balance:sum'])[0][0] or 0

    def retornar_saldo_inicial_inicio_anio(self, cuenta, fecha_desde):
        fecha = fields.Date.to_date(fecha_desde)
        dominio = [
            ('account_id', '=', cuenta),
            ('date', '<', fecha_desde),
            ('date', '>=', fecha.replace(month=1, day=1)),
        ]
        return self.env['account.move.line']._read_group(dominio, [], ['balance:sum'])[0][0] or 0

    def agrupar_movimientos(self, cuentas_id, fecha_desde, fecha_hasta, por_dia=False):
        dominio = [
            ('account_id', 'in', list(cuentas_id)),
            ('date', '>=', fecha_desde),
            ('date', '<=', fecha_hasta),
        ]
        agrupar = ['account_id', 'date:day'] if por_dia else ['account_id']
        grupos = self.env['account.move.line']._read_group(dominio, agrupar, ['debit:sum', 'credit:sum'])

        lineas = []
        for grupo in grupos:
            cuenta = grupo[0]
            debe, haber = grupo[-2], grupo[-1]
            linea = {
                'id': cuenta.id,
                'codigo': cuenta.code,
                'cuenta': cuenta.name,
                'saldo_inicial': 0,
                'debe': debe,
                'haber': haber,
                'saldo_final': 0,
                'balance_inicial': cuenta.include_initial_balance,
            }
            if por_dia:
                linea['fecha'] = grupo[1]
            lineas.append(linea)

        if por_dia:
            return sorted(lineas, key=lambda l: (l['fecha'], l['codigo'] or ''))
        return sorted(lineas, key=lambda l: l['codigo'] or '')

    def calcular_saldos(self, lineas, fecha_desde, totales):
        for l in lineas:
            if not l['balance_inicial']:
                l['saldo_inicial'] += self.retornar_saldo_inicial_inicio_anio(l['id'], fecha_desde)
            else:
                l['saldo_inicial'] += self.retornar_saldo_inicial_todos_anios(l['id'], fecha_desde)
            l['saldo_final'] += l['saldo_inicial'] + l['debe'] - l['haber']
            totales['saldo_inicial'] += l['saldo_inicial']
            totales['saldo_final'] += l['saldo_final']

    def lineas(self, datos):
        totales = {'debe': 0, 'haber': 0, 'saldo_inicial': 0, 'saldo_final': 0}

        lineas = self.agrupar_movimientos(datos['cuentas_id'], datos['fecha_desde'], datos['fecha_hasta'], datos['agrupado_por_dia'])
        for l in lineas:
            totales['debe'] += l['debe']
            totales['haber'] += l['haber']

        self.calcular_saldos(lineas, datos['fecha_desde'], totales)

        if datos['agrupado_por_dia']:
            cuentas_agrupadas = {}
            for l in lineas:
                if l['fecha'] not in cuentas_agrupadas:
                    cuentas_agrupadas[l['fecha']] = {'fecha': l['fecha'], 'cuentas': [], 'total_debe': 0, 'total_haber': 0}
                cuentas_agrupadas[l['fecha']]['cuentas'].append(l)

            for la in cuentas_agrupadas.values():
                for l in la['cuentas']:
                    la['total_debe'] += l['debe']
                    la['total_haber'] += l['haber']

            lineas = list(cuentas_agrupadas.values())

        return {'lineas': lineas, 'totales': totales}

    @api.model
    def _get_report_values(self, docids, data=None):
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_ids', []))

        return {
            'doc_ids': self.ids,
            'doc_model': model,
            'data': data['form'],
            'docs': docs,
            'lineas': self.lineas,
            'current_company_id': self.env.company,
        }
