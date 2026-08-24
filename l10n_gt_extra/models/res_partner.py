# -*- encoding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = "res.partner"

    cui = fields.Char(string="CUI")
    no_validar_nit = fields.Boolean(string="No validar NIT")
    pequenio_contribuyente = fields.Boolean(string="Pequeño Contribuyente")

    @api.constrains('vat')
    def _validar_nit(self):
        for p in self:
            if p.vat in ('CF', 'C/F') or not p.vat:
                continue

            if p.country_id and p.country_id.code != 'GT':
                continue

            if p.no_validar_nit:
                continue

            # No validar NIT si el partner fue creado desde un sitio web, para evitar errores
            if 'website_id' in p.env.context:
                continue

            nit = p.vat.replace('-', '')
            verificador = nit[-1]
            if verificador == 'K':
                verificador = '10'
            secuencia = nit[:-1]

            total = 0
            i = 2
            for c in secuencia[::-1]:
                if not c.isdigit():
                    raise ValidationError("El NIT " + p.vat + " no es correcto (según lineamientos de la SAT)")
                total += int(c) * i
                i += 1

            resultante = (11 - (total % 11)) % 11

            if str(resultante) != verificador:
                raise ValidationError("El NIT " + p.vat + " no es correcto (según lineamientos de la SAT)")

    @api.constrains('vat')
    def _validar_duplicado(self):
        for p in self:
            # No validar NIT si el partner fue creado desde un sitio web, para evitar errores
            if 'website_id' in p.env.context:
                continue

            if not p.parent_id and p.vat and p.vat not in ('CF', 'C/F') and not p.no_validar_nit:
                repetidos = self.search([('vat', '=', p.vat), ('id', '!=', p.id), ('parent_id', '=', False)])
                if repetidos:
                    raise ValidationError("El NIT " + p.vat + " ya existe")
