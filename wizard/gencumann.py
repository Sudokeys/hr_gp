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
import time
import pooler
from datetime import datetime, timedelta, date
from osv import osv
from osv import fields

class gencumann_wizard(osv.osv_memory):
	_name='hr_gp.wizard.gencumann'
    
	_columns= {
               'name': fields.char('wiz name', size=32),
               'year2cum': fields.integer('year2cum'),
               'state': fields.char('state', size = 8),
	}
	_defaults = {
		'name': 'Clic to begin',
		'year2cum': lambda *a: datetime.now().year,
		'state': 'begin',
	}
	def gen_cumann(self, cr, uid, id, context=None):
		wizard=self.browse(cr, uid, id[0], context=context)
		if wizard.state == "begin":
			curr_year = wizard.year2cum
			cr.execute("select id, name, title, cum_epe, cum_ctt, cum_act, cum_cpy from hr_gp_params_dict where cum_epe = True or cum_ctt = True or cum_act = True or cum_cpy = True")
			param2cum = cr.fetchall()
			compteurs = {}
			cpt = []
			curr_date = date.today()
			curr_year = wizard.year2cum
			for param in param2cum:
				par = param[0]
				cumlev = []
				if param[3]: cumlev.append('epe')
				if param[4]: cumlev.append('ctt')
				if param[5]: cumlev.append('act')
				if param[6]: cumlev.append('cpy') 
				sql_req = """
				SELECT psl.param_name, psl.pay_id, ps.ctt_id, pr.date_begin, pr.date_end, psl.registee, psl.register,
				ctt.employee_id, ctt.activity, act.company 
				FROM hr_gp_payslip_line psl
				LEFT JOIN hr_gp_payslip ps ON (ps.id = psl.pay_id)
				LEFT JOIN hr_gp_payrun pr ON (ps.pay_run = pr.id)
				LEFT JOIN hr_gp_contractframe ctt ON (ps.ctt_id = ctt.id)
				LEFT JOIN hr_gp_activity act ON (ctt.activity = act.id)
				WHERE psl.param_name = %s AND psl.pay_id IS NOT NULL
				""" % (par,)

                                cr.execute(sql_req)
				paysliplines = cr.fetchall()
				for paylig in paysliplines:
					for level in cumlev:
						keylev = ""
						if level == 'ctt': keylev=paylig[2]
						elif level == 'epe': keylev=paylig[7]
						elif level == 'act': keylev=paylig[8]
						elif level == 'cpy': keylev=paylig[9]
						cledict = level + "_" + str(paylig[0]) + "_" + str(keylev)
						ddebpay = datetime.strptime(paylig[3],"%Y-%m-%d")
						m = ddebpay.month
						a = ddebpay.year
						if a == curr_year:
							if compteurs.has_key(cledict) == False:
								compteurs[cledict] = [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00]
							cpt = compteurs[cledict]
							if paylig[5]: reg_e = paylig[5]
							else: reg_e= 0.00
							if paylig[6]: reg_r = paylig[6]
							else: reg_r= 0.00
							cpt[m-1] = cpt[m-1] + reg_e + reg_r
							compteurs[cledict] = cpt
			pool = pooler.get_pool(cr.dbname)
			obj = pool.get('hr_gp.cumann')
			fldkey = {'ctt':'contractframe_key.id','epe':'employee_key.id','act':'activityframe_key.id','cpy':'company_key.id'}
			fldname = {'ctt':'contractframe_key','epe':'employee_key','act':'activityframe_key','cpy':'company_key'}
			for keycpt in compteurs.keys():
				lev = keycpt.split("_")[0]
				parname = keycpt.split("_")[1]
				entitykey = keycpt.split("_")[2]
				crit = [(fldkey[lev],'=',entitykey),('param_name.id','=',parname),('year_cum','=',curr_year)]
				ides = obj.search(cr, uid, crit)
				rec = obj.read(cr, uid, ides, fields=['id',fldname[lev],'param_name'], context=None)
				cum_an = ""
				for m in range(0,12):
					cum_an += "%1.2f;" % (compteurs[keycpt][m])
				fields = {'cum_an':cum_an}
				fields.update({fldname[lev]:entitykey})
				fields.update({'year_cum':curr_year})
				fields.update({'param_name':parname})
				fields.update({'last_update':curr_date})
				if len(rec) > 0:
					obj.write(cr, uid,[rec[0]['id']],fields, context=None)
				else:
					obj.create(cr, uid,fields, context=None)
			self.write(cr, uid, id, {'state':'completed',}, context=context)
				 
		return True

gencumann_wizard()
   
