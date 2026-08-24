# -*- encoding: utf-8 -*-

from odoo import api, models


class ReporteMayor(models.AbstractModel):
    _name = 'report.l10n_gt_extra.reporte_mayor'
    _description = 'Libro mayor'

    def base(self):
        return self.env['report.l10n_gt_extra.reporte_diario']

    def retornar_saldo_inicial_todos_anios(self, cuenta, fecha_desde):
        return self.base().retornar_saldo_inicial_todos_anios(cuenta, fecha_desde)

    def retornar_saldo_inicial_inicio_anio(self, cuenta, fecha_desde):
        return self.base().retornar_saldo_inicial_inicio_anio(cuenta, fecha_desde)

    def lineas(self, datos):
        totales = {'debe': 0, 'haber': 0, 'saldo_inicial': 0, 'saldo_final': 0}

        lineas = self.base().agrupar_movimientos(datos['cuentas_id'], datos['fecha_desde'], datos['fecha_hasta'], datos['agrupado_por_dia'])
        for l in lineas:
            totales['debe'] += l['debe']
            totales['haber'] += l['haber']

        if datos['agrupado_por_dia']:
            cuentas_agrupadas = {}
            for l in lineas:
                llave = l['codigo']
                if llave not in cuentas_agrupadas:
                    cuentas_agrupadas[llave] = {
                        'codigo': llave,
                        'cuenta': l['cuenta'],
                        'saldo_inicial': 0,
                        'saldo_final': 0,
                        'fechas': [],
                        'total_debe': 0,
                        'total_haber': 0,
                    }

                    if not l['balance_inicial']:
                        cuentas_agrupadas[llave]['saldo_inicial'] = self.retornar_saldo_inicial_inicio_anio(l['id'], datos['fecha_desde'])
                    else:
                        cuentas_agrupadas[llave]['saldo_inicial'] = self.retornar_saldo_inicial_todos_anios(l['id'], datos['fecha_desde'])
                cuentas_agrupadas[llave]['fechas'].append(l)

            for cuenta in cuentas_agrupadas.values():
                for fecha in cuenta['fechas']:
                    cuenta['total_debe'] += fecha['debe']
                    cuenta['total_haber'] += fecha['haber']
                cuenta['saldo_final'] += cuenta['saldo_inicial'] + cuenta['total_debe'] - cuenta['total_haber']

            lineas = list(cuentas_agrupadas.values())
        else:
            self.base().calcular_saldos(lineas, datos['fecha_desde'], totales)

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
