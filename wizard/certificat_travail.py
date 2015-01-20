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


class certificat_travail(osv.osv_memory):
    _name = 'certificat.travail'
    _description = 'Certificat de travail'
    
    _columns = {
        'employee_id':fields.many2one('hr.employee', 'Salarié', required=True),
        'etab': fields.many2one('res.partner',string='Établissement', required=True),
        'solde_heure':fields.integer("Solde d'heures en DIF"),
        'somme':fields.float("Somme"),
        'lieu': fields.char('Fait à',size=128, required=True),
        'date_certificat': fields.date('Le', required=True),
        'type':fields.selection([('nr','Certificat de travail'),('ai','Certificat de travail AI')], 'Type de certificat', required=True)
    }
    _defaults = {   
        'date_certificat': fields.date.context_today,
        'type':lambda self,cr, uid, ctx:ctx.get('type',False)
        }
    
    def onchange_employee(self, cr, uid, ids, employee_id, context=None):
        """Search and return the last salary value and establishment city"""
        if not employee_id:
            return {}
        #
        cr.execute("select distinct hgac.establishment from hr_gp_activity hgac FULL JOIN hr_gp_contractframe hgc ON hgc.activity=hgac.id where hgc.employee_id=%s",(employee_id,) )
        return {'domain': {'etab': [('id','in',cr.fetchall()),('org_cotis2','!=',False)]}}

    def onchange_etab(self, cr, uid, ids, etab_id, context=None):
        """ @return : lieu value """
        if not etab_id:
            return {}
        lieu = self.pool.get('res.partner').browse(cr, uid, [etab_id], context)[0].city
        return {'value': {'lieu': lieu}}
    
    def print_report(self, cr, uid, ids, context=None):
        
        """
        To get the information and print the report
        @return : return jasper report
        """
        current_obj = self.browse(cr, uid, ids, context)[0]
        datas = {'ids': ids, 'model': 'hr.employee'}
        datas['jasper']={
                         'empl_id': current_obj.employee_id.id,
                         'etab': current_obj.etab.id,
                         'solde_heure': current_obj.solde_heure,
                         'somme': current_obj.somme,
                         'lieu': current_obj.lieu,
                         'date_cert':current_obj.date_certificat
                         }
        type = current_obj.type
        return {
            'type': 'ir.actions.report.xml',
            'report_name': (type=='nr') and 'jasper.certificat_travail' or 'jasper.certificat_travail_ai',
            'datas': datas,
       }
certificat_travail()
class certificat_type(osv.osv_memory):
    _name = 'certificat.type'
    _columns = {
            'type':fields.selection([('nr','Certificat de travail'),('ai','Certificat de travail AI')], 'Type de certificat', required=True)
                }
    _defaults = {   
        'type': 'nr'
        }
certificat_type()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

