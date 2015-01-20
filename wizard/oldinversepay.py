# -*- coding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Enterprise Management Solution
#    Copyright (C) 2004-2010 OpenERP s.a. (<http://openerp.com>).
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
import pooler
from osv import osv
from osv import fields

class inversepay_wizard(osv.osv_memory):
	def _getnetline(self, cr, uid, context=None):
		lstlines = []
		payslip_obj = self.pool.get('hr_gp.payslip')
        	for payslip in payslip_obj.browse(cr, uid, context.get('active_ids'), context=None):
			print "payid: ", payslip.payid
			for payslipline in payslip.payslip_lines:
				lstlines.append((payslipline.id, payslipline.param_name.title))
		return lstlines
		
	def _getgrossline(self, cr, uid, context=None):
		lstlines = []
		payslip_obj = self.pool.get('hr_gp.payslip')
        	for payslip in payslip_obj.browse(cr, uid, context.get('active_ids'), context=None):
			for payslipline in payslip.payslip_lines:
				if payslipline.category != 'r':
					lstlines.append((payslipline.id, payslipline.param_name.title))
		return lstlines		
	
	
	_name='hr_gp.inversepay.wizard'
    
	_columns= {
               'name': fields.char('name',size=12),
               'net_line':fields.selection(_getnetline,'net line target'),
               'gross_line': fields.selection(_getgrossline,'gross line to net'),
               'net_target': fields.float('net target',digits=(9,2)),
               'payid': fields.integer('payid')
	}
	
	def payinverse(self, cr, uid, id, context=None):
		wizard=self.browse(cr, uid, id[0], context=context)
        	payslip_obj = self.pool.get('hr_gp.payslip')
#        	for payslip in payslip_obj.browse(cr, uid, context.get('active_ids'), context=None):
#			print "payid: ", payslip.payid
		payslipline_obj = self.pool.get('hr_gp.payslip_line')
		for payslipline in payslipline_obj.browse(cr, uid, [wizard.net_line], context=None):
				oldnet = payslipline.val_e
		diff = wizard.net_target - oldnet
		while abs(diff) > 0.005 :
			for payslipline in payslipline_obj.browse(cr, uid, [wizard.gross_line], context=None):
				oldgross = payslipline.val_e
			factor = wizard.net_target/oldnet
			newgross = factor * oldgross
			payslipline_obj.write(cr, uid, wizard.gross_line, {'val_sim_e':newgross}, context=None)
			payslip_obj.calc(cr, uid,context.get('active_ids'))
			for payslipline in payslipline_obj.browse(cr, uid, [wizard.net_line], context=None):
				oldnet = payslipline.val_e
			diff = wizard.net_target - oldnet
			print "net target: %9.2f net achieved: %9.2f diff: %5.2f gross achieved: %9.2f" % (wizard.net_target,oldnet,diff,newgross)
		return True

inversepay_wizard()
   
