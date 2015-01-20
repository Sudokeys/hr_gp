# -*- coding: utf-8 -*-
##############################################################################
#
#    jasper_server_wizard_sample module for OpenERP, Sample to show haw to launch report from wizard
#    Copyright (C) 2011 SYLEAM (<http://www.syleam.fr/>)
#              Christophe CHAUVET <christophe.chauvet@syleam.fr>
#
#    This file is a part of jasper_server_wizard_sample
#
#    jasper_server_wizard_sample is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    jasper_server_wizard_sample is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import osv
from osv import fields
import time
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta 

class hr_gp_livre_paie(osv.osv_memory):
    _name = 'hr_gp.livre_paie'
    _description = 'livre_paie'

 #   def _get_employee_ids(self, cr, uid, ):
    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        if context is None:context = {}
        res = super(hr_gp_livre_paie, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar,submenu=False)
        fields = ['etab','date_start','date_end','activity_id']
        defualt_res = self.default_get(cr, uid, fields, context)
        self._get_domain(cr, uid, defualt_res, context)
        for field in res['fields']:
            if field=='employee_ids':
                res['fields'][field]['domain']=self._get_domain(cr, uid, defualt_res, context)
        return res
    
    def _get_domain(self, cr, uid, fields, context=None):
        values=()
        where=""
        query="select distinct employee_id from hr_gp_contractframe "
        etab = fields['etab']
        date_start = fields['date_start']
        date_end = fields['date_end']
        activity = fields.get('activity_id', False)
        if etab and not activity:
            where = "where activity in (select id from hr_gp_activity where establishment=%s) and date_begin<=%s and date_end>=%s"
            values = (etab,date_end,date_start)
        elif etab and activity:
            where = "where activity=%s and date_begin<=%s and date_end>=%s"
            values = (activity,date_end,date_start)
        cr.execute(query+where,values)
        return [('id','in',[r[0] for r in cr.fetchall()])]
    
    _columns = {
        'etab': fields.many2one('res.partner',string='Établissement', required=True),
        'activity_id': fields.many2one('hr_gp.activity',string='Activité'),
        'employee_ids': fields.many2many('hr.employee',string='Salariés'),
        'date_start': fields.date('Date début', required=False),
        'date_end': fields.date('Date fin', required=False),
        'param_model': fields.many2one('hr_gp.param_model',string='Modèle'),
    }

    _defaults = {
        'etab': lambda self,cr,uid,c: self.pool.get('res.partner').search(cr, uid, [('org_cotis2','!=',False)],order='name', context=c) and self.pool.get('res.partner').search(cr, uid, [('org_cotis2','!=',False)],order='name', context=c)[0] or False,
        'date_start': lambda *a: time.strftime('%Y-%m-01'),
        'date_end': lambda *a: (datetime.strptime(time.strftime('%Y-%m-01'),'%Y-%m-%d') + relativedelta(months=1) - relativedelta(days=1)).strftime('%Y-%m-%d'),
    }
    def onchange_fields(self, cr, uid, ids,etab,activity_id,date_start,date_end, context=None):
        fields = {'etab':etab,'activity_id':activity_id,'date_start':date_start, 'date_end':date_end}
        res={'employee_ids':self._get_domain(cr, uid, fields, context)}
        return {'domain':res}
    
    def launch(self, cr, uid, ids, context=None):
        """
        Launch the report, and pass each value in the form as parameters
        """
        wiz = self.browse(cr, uid, ids, context=context)[0]
        data = {}
        data['ids'] = ids
        data['model'] = 'hr_gp.livre_paie'
        data['jasper'] = {
            'employee_ids': [x.id for x in wiz.employee_ids],
            'date_debut': wiz.date_start,
            'date_fin': wiz.date_end,
            'etab':wiz.etab.name,
            'param_model': wiz.param_model and wiz.param_model.id or 0,
        }

        return {
                'type': 'ir.actions.report.xml',
                'report_name': 'jasper.livre_paie',
                'datas': data,
        }

hr_gp_livre_paie()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
