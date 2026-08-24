# -*- encoding: utf-8 -*-

from odoo import models
from odoo.tools import convert_file

ARCHIVO_IMPUESTOS = 'data/l10n_gt_extra_base.xml'


class IrModuleModule(models.Model):
    _inherit = 'ir.module.module'

    def _register_hook(self):
        res = super()._register_hook()
        datos = self.env['ir.model.data']
        if datos.search_count([('module', '=', 'l10n_gt_extra'), ('model', '=', 'account.tax')], limit=1):
            return res
        if self.env['ir.module.module'].search_count([('name', '=', 'l10n_gt_extra'), ('state', '=', 'installed')], limit=1):
            convert_file(self.env, 'l10n_gt_extra', ARCHIVO_IMPUESTOS, None, noupdate=True)
        return res
