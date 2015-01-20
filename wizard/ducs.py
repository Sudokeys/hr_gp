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

class hr_gp_etat_ducs(osv.osv_memory):
    _name = 'hr_gp.etat_ducs'
    _description = 'ducs'

    _columns = {
        'etab_de': fields.many2one('res.partner',string='etab_de'),
        'etab_a': fields.many2one('res.partner',string='etab_a'),
        'org_cotis_de': fields.many2one('hr_gp.org_cotis',string='org_cotis_de'),
        'org_cotis_a': fields.many2one('hr_gp.org_cotis',string='org_cotis_a'),
        'date_start': fields.date('Date début', required=False),
        'date_end': fields.date('Date fin', required=False),
    }

    _defaults = {
        'etab_de': lambda self,cr,uid,c: self.pool.get('res.partner').search(cr, uid, [('org_cotis2','!=',False)],order='name', context=c) and self.pool.get('res.partner').search(cr, uid, [('org_cotis2','!=',False)],order='name', context=c)[0] or False,
        'etab_a': lambda self,cr,uid,c: self.pool.get('res.partner').search(cr, uid, [('org_cotis2','!=',False)],order='name', context=c) and self.pool.get('res.partner').search(cr, uid, [('org_cotis2','!=',False)],order='name', context=c)[-1] or False,
        'org_cotis_de': lambda self,cr,uid,c: self.pool.get('hr_gp.org_cotis').search(cr, uid, [],order='id', context=c) and self.pool.get('hr_gp.org_cotis').search(cr, uid, [],order='id', context=c)[0] or False,
        'org_cotis_a': lambda self,cr,uid,c: self.pool.get('hr_gp.org_cotis').search(cr, uid, [],order='id', context=c) and self.pool.get('hr_gp.org_cotis').search(cr, uid, [],order='id', context=c)[-1] or False,
        'date_start': lambda *a: time.strftime('%Y-%m-01'),
        'date_end': lambda *a: (datetime.strptime(time.strftime('%Y-%m-01'),'%Y-%m-%d') + relativedelta(months=1) - relativedelta(days=1)).strftime('%Y-%m-%d'),
    }

    def launch(self, cr, uid, ids, context=None):
        """
        Launch the report, and pass each value in the form as parameters
        """
        wiz = self.browse(cr, uid, ids, context=context)[0]
        data = {}
        data['ids'] = ids
        data['model'] = 'hr_gp.etat_ducs'
        data['jasper'] = {
            'etab_de': wiz.etab_de.id,
            'etab_a': wiz.etab_a.id,
            'org_cotis_de': wiz.org_cotis_de.id,
            'org_cotis_a': wiz.org_cotis_a.id,
            'date_debut': wiz.date_start,
            'date_fin': wiz.date_end,
        }

        return {
                'type': 'ir.actions.report.xml',
                'report_name': 'jasper.ducs',
                'datas': data,
        }

hr_gp_etat_ducs()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
