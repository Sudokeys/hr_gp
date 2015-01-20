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

class hr_gp_accline_validation(osv.osv_memory):
    _name = 'hr_gp.accline.validation'
    _description = 'accline validation'

    _columns = {
        'month':fields.selection([('01','January'), ('02','February'), ('03','March'), ('04','April'), ('05','May'), ('06','June'),
                                  ('07','July'), ('08','August'), ('09','September'), ('10','October'), ('11','November'), ('12','December')],'Month',readonly=False),
        'year': fields.char('Year', size=4, readonly=False),
        'accline_ids': fields.many2many('hr_gp.accline',string='Account lines',readonly=True),
        'journal_id': fields.many2one('account.journal', 'Journal'),
        'ref': fields.char('Reference', size=64),
        'date': fields.date('Date'),
    }

    _defaults = {
        'month': lambda *a: time.strftime('%m'),
        'year': lambda *a: time.strftime('%Y'),
    }
  
    
    def next(self, cr, uid, ids, context=None):
        for item in self.browse(cr,uid,ids,context):
            sql="""SELECT hgac.id
                    FROM hr_gp_accline hgac
                    JOIN hr_gp_payslip hgp ON hgp.id=hgac.pay_id
                    JOIN hr_gp_payrun hgpr ON hgp.pay_run=hgpr.id
                    LEFT JOIN account_account aa ON hgac.acc_id=aa.id
                    WHERE ((EXTRACT(MONTH FROM hgpr.date_begin)>=%s AND EXTRACT(YEAR FROM hgpr.date_begin)>=%s)
                    AND (EXTRACT(MONTH FROM hgpr.date_begin)<=%s AND EXTRACT(YEAR FROM hgpr.date_begin)<=%s))
                    AND acc_id IS NOT NULL AND hgac.name!='Total' AND hgac.moved is Null
                    ORDER BY aa.code""" % (item.month, item.year, item.month, item.year)
            cr.execute(sql)
            records = map(lambda x:x[0], cr.fetchall())
            self.write(cr,uid,item.id,{'accline_ids':[(6,0,records)]})
        
        mod_obj = self.pool.get('ir.model.data')
        res = mod_obj.get_object_reference(cr, uid, 'hr_gp', 'accline_validation_view2')
        res_id = res and res[1] or False
        return {
                'res_id': ids[0],
                'view_id': [res_id],
                'view_type': 'form',
                "view_mode": 'form',
                'res_model': 'hr_gp.accline.validation',
                'type': 'ir.actions.act_window',
                'target':'new',
                'context': {'accline_ids':[(6,0,records)]}
        }
        
    def launch(self, cr, uid, ids, context=None):
        move_obj = self.pool.get('account.move')
        for item in self.browse(cr,uid,ids,context):
            move = move_obj.account_move_prepare(cr, uid, item.journal_id.id, item.date, item.ref, company_id=False, context=None)
            move_id = move_obj.create(cr,uid,move,context)
            for accline in item.accline_ids:
                self.pool.get('hr_gp.accline').write(cr,uid,accline.id,{'moved':True})
                move_line = {
                    'journal_id': move['journal_id'],
                    'period_id': move['period_id'],
                    'name': move['ref'],
                    'account_id': accline.acc_id.id,
                    'move_id': move_id,
                    'credit': accline.amount_c,
                    'debit': accline.amount_d,
                    'date': move['date']
                }
                self.pool.get('account.move.line').create(cr,uid,move_line,context)
            
        return True

hr_gp_accline_validation()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
