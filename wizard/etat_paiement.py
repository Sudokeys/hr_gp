# -*- coding: utf-8 -*-
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


class etat_paiement(osv.osv_memory):
    _name = 'etat.paiement'
    _description = 'Etat de paiement'
    
    _columns = {
        'etab_id': fields.many2one('res.partner','Établissement', required=True),
        'pay_run': fields.many2one('hr_gp.payrun','Payrun', required=True),
        'param_model': fields.many2one('hr_gp.param_model','Modèle'),
    }
    
    
    def print_report(self, cr, uid, ids, context=None):
        
        """
        To get the information and print the report
        @return : return jasper report
        """
        current_obj = self.browse(cr, uid, ids, context)[0]
        datas = {'ids': ids, 'model': 'hr_gp.payslip'}
        datas['jasper']={
                         'etab_id': current_obj.etab_id.id,
                         'pay_run': current_obj.pay_run.id,
                         'param_model': (current_obj.param_model and current_obj.param_model.id)  or 0,
                         }
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'jasper.etat_paiement',
            'datas': datas,
       }
        
etat_paiement()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

