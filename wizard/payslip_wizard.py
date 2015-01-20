##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, osv
from openerp.tools.translate import _

class gen_accmov_wizard(osv.osv_memory):
    _name = "gen.accmov.wizard"
    _description = "Generate account move"
    _columns = {
                'payslip_ids': fields.many2many('hr_gp.payslip', string='Payslips',readonly=True),
    }
    
    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        res = super(gen_accmov_wizard, self).default_get(cr, uid, fields, context=context)
        res['payslip_ids']=context.get('active_ids')
        return res
    
    def launch(self, cr, uid, ids, context=None):
        self.pool.get('hr_gp.payslip').gen_accmov(cr,uid,context.get('active_ids'),context)
        return True
    
gen_accmov_wizard()

class calc_wizard(osv.osv_memory):
    _name = "calc.wizard"
    _description = "Calculate"
    _columns = {
                'payslip_ids': fields.many2many('hr_gp.payslip', string='Payslips',readonly=True),
    }
    
    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        res = super(calc_wizard, self).default_get(cr, uid, fields, context=context)
        res['payslip_ids']=context.get('active_ids')
        return res
    
    def launch(self, cr, uid, ids, context=None):
        self.pool.get('hr_gp.payslip').calc(cr,uid,context.get('active_ids'),context)
        return True
    
calc_wizard()

class action_validate_wizard(osv.osv_memory):
    _name = "action.validate.wizard"
    _description = "Validate"
    _columns = {
                'payslip_ids': fields.many2many('hr_gp.payslip', string='Payslips',readonly=True),
    }
    
    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        res = super(action_validate_wizard, self).default_get(cr, uid, fields, context=context)
        res['payslip_ids']=context.get('active_ids')
        return res
    
    def launch(self, cr, uid, ids, context=None):
        self.pool.get('hr_gp.payslip').action_validate(cr,uid,context.get('active_ids'),context)
        return True
    
action_validate_wizard()
