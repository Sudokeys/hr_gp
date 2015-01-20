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

class hr_gp_recap_paye(osv.osv_memory):
    _name = 'hr_gp.recap_paye'
    _description = 'recap_paye'

    _columns = {
        'etab_ids': fields.many2many('res.partner',string='Établissements', required=True),
        'date_start': fields.date('Date début', required=False),
        'date_end': fields.date('Date fin', required=False),
    }

    _defaults = {
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
        data['model'] = 'hr_gp.recap_paye'
        data['jasper'] = {
            'etab': [x.id for x in wiz.etab_ids],
            'date_debut': wiz.date_start,
            'date_fin': wiz.date_end,
        }

        return {
                'type': 'ir.actions.report.xml',
                'report_name': 'jasper.recap_paye',
                'datas': data,
        }

hr_gp_recap_paye()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
