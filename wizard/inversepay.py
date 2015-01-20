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
		if not context.get('active_ids', False) :
			return False
		lstlines = []
		payslip_obj = self.pool.get('hr_gp.payslip')
        	for payslip in payslip_obj.browse(cr, uid, context.get('active_ids'), context=None):
				for payslipline in payslip.payslip_lines:
					lstlines.append((payslipline.id, payslipline.param_name.title))
		return lstlines
		
	def _getgrossline(self, cr, uid, context=None):
		if not context.get('active_ids', False) :
			return False
		lstlines = []
		payslip_obj = self.pool.get('hr_gp.payslip')
        	for payslip in payslip_obj.browse(cr, uid, context.get('active_ids'), context=None):
				for payslipline in payslip.payslip_lines:
					if payslipline.category != 'r':
						lstlines.append((payslipline.id, payslipline.param_name.title))
		return lstlines		
	
	def _get_states(self, cr, uid, context=None):
		return [('to_comp','to compute'),('computed','computed'),('restored','restored')]
	
	_name='hr_gp.inversepay.wizard'
    
	_columns= {
               'name': fields.char('Name',size=12),
               'net_line':fields.selection(_getnetline,'Net line target'),
               'gross_line': fields.selection(_getgrossline,'Line of gross reference'),
               'line2adjust': fields.selection(_getgrossline,'Gross line to adjust'),
               'net_target': fields.float('Net target',digits=(9,2)),
               'payid': fields.integer('Payid'),
               'nbstep': fields.integer('Nb step'),
               'gross_result': fields.float('Gross result', digits=(9,2)),
               'log': fields.boolean('Log'),
               'state': fields.selection(_get_states,'State'),
	}
	_defaults = {
		'state':'to_comp',
		'log':False,
	}
	
	def payinverse(self, cr, uid, id, context=None):
		if not context :
			return False
		wizard=self.browse(cr, uid, id[0], context=context)
		if wizard.state == "to_comp":
			payslip_obj = self.pool.get('hr_gp.payslip')
			payslip_obj.calc(cr, uid,context.get('active_ids'))
			payslipline_obj = self.pool.get('hr_gp.payslip_line')
			for payslipline1 in payslipline_obj.browse(cr, uid, [int(wizard.net_line)], context=None):
				oldnet = payslipline1.val_e
			for payslipline in payslipline_obj.browse(cr, uid, [int(wizard.gross_line)], context=None):
				oldgross = payslipline.val_e
			for payslipline in payslipline_obj.browse(cr, uid, [int(wizard.line2adjust)], context=None):
				val2adjust = payslipline.val_e
			newdiff = oldnet - float(wizard.net_target)
			if wizard.gross_line == wizard.line2adjust: oldgross = 0.00
			if float(wizard.net_target) > oldnet: sens = 1
			else: sens = -1
			coef_gross_net = oldnet / (oldgross + val2adjust)
			newval= val2adjust
			hstep = abs(round((float(wizard.net_target)/coef_gross_net)-(oldgross + newval),3)) * sens
			if wizard.log: print "diff initiale: ",newdiff," hstep initial = ",hstep," oldnet= ",oldnet," oldgross= ",oldgross, "val2adj= ",val2adjust
			nbstep = 0
			while abs(newdiff) > 0.005:
				nbstep += 1
				olddiff = newdiff
				newval += hstep
				payslipline_obj.write(cr, uid, int(wizard.line2adjust), {'val_sim_e':newval}, context=None)
				payslip_obj.calc(cr, uid,context.get('active_ids'))
				for payslipline in payslipline_obj.browse(cr, uid, [int(wizard.net_line)], context=None):
					newnet = payslipline.val_e
				newdiff = newnet - float(wizard.net_target)
				if (sens == 1 and newnet > float(wizard.net_target)) or (sens == -1 and newnet < float(wizard.net_target)):
					if float(wizard.net_target) > newnet: sens = 1
					else: sens = -1
					coef_gross_net = newnet/(oldgross + newval)
					hstep = abs(round((float(wizard.net_target)/coef_gross_net)-(oldgross + newval),3)) * sens
				else:
					if abs(newdiff) > abs(olddiff): 
						print "    Alert newdiff = ", newdiff," olddiff = ", olddiff
                                if nbstep > 30:
					raise osv.except_osv(u"Alert",u"Impossible to approach net - Please verify your parameters")
				if wizard.log: print "%2d achvd:%9.4f diff:%9.4f h:%7.6f newval:%9.4f sens:%d" % (nbstep,newnet,newdiff,hstep,newval,sens)
                                if abs(hstep)< 0.005: break
			self.write(cr, uid, id, {'gross_result':newval,'nbstep':nbstep,'state':'computed',}, context=context)
			
		return True
		
	def erase_res(self, cr, uid, id, context=None):
		if not context :
			return False
		wizard=self.browse(cr, uid, id[0], context=context)
		if wizard.state == "computed":
			payslip_obj = self.pool.get('hr_gp.payslip')
			payslipline_obj = self.pool.get('hr_gp.payslip_line')
			payslipline_obj.write(cr, uid, int(wizard.line2adjust), {'val_sim_e':''}, context=None)
			payslip_obj.calc(cr, uid,context.get('active_ids'))
			self.write(cr, uid, id, {'state':'restored',}, context=context)
		return True
			
inversepay_wizard()
   
