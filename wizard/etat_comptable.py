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
MONTHS = [('01','January'), ('02','February'), ('03','March'), ('04','April'), ('05','May'), ('06','June'), ('07','July'), ('08','August'), ('09','September'), ('10','October'), ('11','November'), ('12','December')]
class hr_gp_etat_comptable(osv.osv_memory):
    _name = 'hr_gp.etat_comptable'
    _description = 'etat comptable'

    _columns = {
        'month':fields.selection(MONTHS,'Month',readonly=False),
        'year': fields.char('Year', size=4, readonly=False),
    }

    _defaults = {
        'month': lambda *a: time.strftime('%m'),
        'year': lambda *a: time.strftime('%Y'),
    }

    def launch(self, cr, uid, ids, context=None):
        """
        Launch the report, and pass each value in the form as parameters
        """
        wiz = self.browse(cr, uid, ids, context=context)[0]
        data = {}
        data['ids'] = ids
        data['model'] = 'hr_gp.etat_comptable'
        month_nb = wiz.month
        month_string = ''
        if month_nb:
            for mn in MONTHS:
                if mn[0]==month_nb:
                    month_string = mn[1]
        data['jasper'] = {
            'month': month_nb,
            'month_str': month_string,
            'year': wiz.year,
        }

        return {
                'type': 'ir.actions.report.xml',
                'report_name': 'jasper.etat_comptable',
                'datas': data,
        }

hr_gp_etat_comptable()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
