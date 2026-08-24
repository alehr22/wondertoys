# -*- encoding: utf-8 -*-

import datetime

from odoo import api, models


class ReporteInventario(models.AbstractModel):
    _name = 'report.l10n_gt_extra.reporte_inventario'
    _description = 'Libro de inventario'

    GRUPOS = {'asset': 'activo', 'liability': 'pasivo', 'equity': 'capital'}

    def base(self):
        return self.env['report.l10n_gt_extra.reporte_diario']

    def retornar_saldo_inicial_todos_anios(self, cuenta, fecha_desde):
        return self.base().retornar_saldo_inicial_todos_anios(cuenta, fecha_desde)

    def retornar_saldo_inicial_inicio_anio(self, cuenta, fecha_desde):
        return self.base().retornar_saldo_inicial_inicio_anio(cuenta, fecha_desde)

    def lineas(self, datos):
        totales = {'debe': 0, 'haber': 0, 'saldo_inicial': 0, 'saldo_final': 0}
        lineas = {'activo': [], 'total_activo': 0, 'pasivo': [], 'total_pasivo': 0, 'capital': [], 'total_capital': 0}

        fecha_desde = self.fecha_desde()
        cuentas = self.env['account.account'].browse(list(datos['cuentas_id'])).exists()
        grupo_por_cuenta = {c.id: self.GRUPOS.get(c.internal_group) for c in cuentas}

        for linea in self.base().agrupar_movimientos(cuentas.ids, fecha_desde, datos['fecha_hasta']):
            totales['debe'] += linea['debe']
            totales['haber'] += linea['haber']
            grupo = grupo_por_cuenta.get(linea['id'])
            if grupo:
                lineas[grupo].append(linea)

        for grupo in ('activo', 'pasivo', 'capital'):
            self.base().calcular_saldos(lineas[grupo], fecha_desde, totales)
            lineas['total_' + grupo] = sum(l['saldo_final'] for l in lineas[grupo])

        return {'lineas': lineas, 'totales': totales}

    def fecha_desde(self):
        return datetime.date.today().replace(month=1, day=1).strftime('%Y-%m-%d')

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
            'fecha_desde': self.fecha_desde,
            'current_company_id': self.env.company,
        }
