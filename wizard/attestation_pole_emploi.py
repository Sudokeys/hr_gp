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

class hr_gp_attestation_pole_emploi(osv.osv_memory):
    _name = 'hr_gp.attestation_pole_emploi'
    _description = 'attestation_pole_emploi'

    _columns = {
        'hr_gp_contractframe_id': fields.many2one('hr_gp.contractframe',string='Contract',required=True),
    }

    _defaults = {
        
    }

    def launch(self, cr, uid, ids, context=None):
        """
        Launch the report, and pass each value in the form as parameters
        """
        wiz = self.browse(cr, uid, ids, context=context)[0]
        data = {}
        data['ids'] = ids
        data['model'] = 'hr_gp.attestation_pole_emploi'
        data['jasper'] = {
           'hr_gp_contract_frame_id': wiz.hr_gp_contractframe_id and wiz.hr_gp_contractframe_id.id or 0,
        }
        return {
                'type': 'ir.actions.report.xml',
                'report_name': 'jasper.attestation_pole_emploi',
                'datas': data,
        }

hr_gp_attestation_pole_emploi()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
