# -*- encoding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = "account.move"

    tipo_gasto = fields.Selection([("mixto", "Mixto"), ("compra", "Compra/Bien"), ("servicio", "Servicio"), ("importacion", "Importación/Exportación"), ("combustible", "Combustible")], string="Tipo de Gasto", default="mixto")
    serie_rango = fields.Char(string="Serie Rango")
    inicial_rango = fields.Integer(string="Inicial Rango")
    final_rango = fields.Integer(string="Final Rango")
    diario_facturas_por_rangos = fields.Boolean(string="Las facturas se ingresan por rango", help="Cada factura realmente es un rango de factura y el rango se ingresa en Referencia/Descripción", related="journal_id.facturas_por_rangos")
    nota_debito = fields.Boolean(string="Nota de debito")

    @api.constrains('inicial_rango', 'final_rango')
    def _validar_rango(self):
        for factura in self:
            if not factura.diario_facturas_por_rangos:
                continue

            if int(factura.final_rango) < int(factura.inicial_rango):
                raise ValidationError('El número inicial del rango es mayor que el final.')

            dominios = [
                [('inicial_rango', '<=', factura.inicial_rango), ('final_rango', '>=', factura.inicial_rango)],
                [('inicial_rango', '<=', factura.final_rango), ('final_rango', '>=', factura.final_rango)],
                [('inicial_rango', '>=', factura.inicial_rango), ('inicial_rango', '<=', factura.final_rango)],
            ]
            for dominio in dominios:
                cruzados = self.search([('serie_rango', '=', factura.serie_rango), ('id', '!=', factura.id)] + dominio)
                if cruzados:
                    raise ValidationError('Ya existe otra factura con esta serie y en el mismo rango')

            factura.name = "{}-{} al {}-{}".format(factura.serie_rango, factura.inicial_rango, factura.serie_rango, factura.final_rango)


class AccountPayment(models.Model):
    _inherit = "account.payment"

    descripcion = fields.Char(string="Descripción")
    numero_viejo = fields.Char(string="Numero Viejo")
    nombre_impreso = fields.Char(string="Nombre Impreso")
    no_negociable = fields.Boolean(string="No Negociable", default=True)
    anulado = fields.Boolean('Anulado')
    fecha_anulacion = fields.Date('Fecha anulación')

    def action_cancel(self):
        for rec in self:
            rec.numero_viejo = rec.name
        return super().action_cancel()

    def anular(self):
        for rec in self:
            move = rec.move_id
            if not move:
                continue

            move.button_draft()
            move.line_ids.remove_move_reconcile()
            move.line_ids.write({'balance': 0, 'amount_currency': 0})
            move.action_post()

            rec.anulado = True
            rec.fecha_anulacion = fields.Date.context_today(rec)


class AccountJournal(models.Model):
    _inherit = "account.journal"

    direccion = fields.Many2one('res.partner', string='Dirección')
    codigo_establecimiento = fields.Integer(string='Código de establecimiento')
    facturas_por_rangos = fields.Boolean(string='Las facturas se ingresan por rango', help='Cada factura realmente es un rango de factura y el rango se ingresa en Referencia/Descripción')
    usar_referencia = fields.Boolean(string='Usar referencia para libro de ventas', help='El número de la factua se ingresa en Referencia/Descripción')
