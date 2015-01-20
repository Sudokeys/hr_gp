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

class stc_salary(osv.osv_memory):
    _name='stc.salary'
    _columns = {
            'name': fields.char('Desciption', required=True),
            'amount':fields.float('Salaire(€)'),
            'stc_id': fields.many2one('stc','Solde de tout compte')
            }
stc_salary()

class stc(osv.osv_memory):
    _name = 'stc'
    _description = 'Solde de tout compte'
    
    _columns = {
        'employee_id':fields.many2one('hr.employee', 'Salarié', required=True),
        'contract_id': fields.many2one('hr_gp.contractframe', 'Référence contrat', required=True),
        'employee_name': fields.char('Je soussigné(e)', size=256, readonly=True),
        'amount': fields.float('reconnais reçu de mon employeur la somme de', required=True),
        'amount_desc': fields.char('',size=512, required=True),
        'payment_method': fields.char('',size=512, required=True),
        'stc_salary_ids': fields.one2many('stc.salary','stc_id',''),
        'comment': fields.text(''),
        'place': fields.char('Fait à', required=True),
        'date': fields.date(',le', required=True)
    }
    _defaults = {   
        'date': fields.date.context_today,
        }
    
    def onchange_contract(self, cr, uid, ids, contract_id, context=None):
        """Search and return the last salary value and establishment city"""
        if not contract_id:
            return {}
        #
        cr.execute("select registee from hr_gp_payslip_line where param_name=(select id from hr_gp_params_dict where name='R_NETAPAYER' limit 1) and pay_id=(select id from hr_gp_payslip where date_end=(select max(date_end) from hr_gp_payslip limit 1) and ctt_id=%s limit 1)  ",(contract_id,) )
        res_amount = cr.fetchone()
        cr.execute("select res_partner.city from res_partner where id=(select hr_gp_activity.establishment from hr_gp_activity, hr_gp_contractframe where hr_gp_activity.id=hr_gp_contractframe.activity and hr_gp_contractframe.id=%s)",(contract_id,))
        res_place = cr.fetchone()
        return {'value': {'amount': (res_amount and res_amount[0]) or False, 'place': (res_place and res_place[0]) or False}}

    def onchange_employee(self, cr, uid, ids, employee_id, context=None):
        """ @return : employee name """
        if not employee_id:
            return {}
        employe_name = self.pool.get('hr.employee').browse(cr, uid, [employee_id], context)[0].name_related
        return {'value': {'employee_name': employe_name}}
    
    def print_report(self, cr, uid, ids, context=None):
        
        """
        To get the information and print the report
        @return : return jasper report
        """
        current_obj = self.browse(cr, uid, ids, context)[0]
        datas = {'ids': ids, 'model': 'hr.employee'}
        datas['jasper']={
                         'empl_id': current_obj.employee_id.id,
                         'contrat_id': current_obj.contract_id.id,
                         'somme': current_obj.amount,
                         'somme_lettre': current_obj.amount_desc,
                         'methode_paye': current_obj.payment_method,
                         'lieu_signature': current_obj.place,
                         'date': str(current_obj.date)
                         }
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'jasper.solde_tout_compte',
            'datas': datas,
       }
stc()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

