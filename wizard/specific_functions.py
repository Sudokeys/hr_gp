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
from osv import osv
from osv import fields
from datetime import datetime, timedelta, date

class functions_gp(osv.osv_memory): 
	_name='hr_gp.functions_gp'    
	_columns= {
		'func_name': fields.char('Func name', size=32),
		'description': fields.char('Description', size=32),
		'param_chain': fields.char('Param_chain', size=128),
		'payid': fields.char('pay id', size=9),
	}

	def compute(self, cr, uid, id, context=None):

		def ppbel(payid, args):
			res = 0.00
#			Cette fonction nécessite:
#			- les paramètres suivants:BE_IPPEXEMPT,REV_CJT, BE_PLAFONDREVCJT, IPP_REDUCTIONS, NB_ENF_ACHARGE,  
#			- les tables suivantes: IPP_FraisProf, IPP_BE_Base, IPP_RedEnfACharge 
			revannbrut = float(args[0])* 12
			ddeb= payid.date_begin
			dfin= payid.date_end
			employee = payid.employee_name
			pool = pooler.get_pool(cr.dbname)
			tab_obj = pool.get('hr_gp.table')
#           calcul des frais professionnels déductibles
			crit = [('name','=','IPP_FraisProf'),('date_begin','<=',ddeb),('date_end','>=',dfin)]
			tab_id = tab_obj.search(cr, uid, crit)
			if len(tab_id) == 1:
				x = tab_obj.lookup(cr, uid, tab_id,[0,revannbrut,"*","ge"])
				fpbas = float(x[1])
				fppct = float(x[2])
				fptr = float(x[3])
				fp = fpbas + (fppct * (revannbrut - fptr))
			else:
				return u'ERR table frais professionnels non trouvée'
#           calcul du net imposable
			revannnetimpos = revannbrut - fp
#           calcul impot de base
			legframe = payid.legal_frame_name
			par_obj = pool.get('hr_gp.params_val')
			crit = [('param_name.name','=','BE_IPPEXEMPT'),('legalframe_key','=',legframe),('date_begin','<=',ddeb),('date_end2','>=',dfin)]
			par_id = par_obj.search(cr, uid, crit)
			if len(par_id) == 1:
				ex = par_obj.read(cr, uid, par_id ,['res_n'])
				exempt = ex[0]['res_n']
			else:
				return u"ERR param BE_IPPEXEMPT non trouvé"
			crit = [('name','=','IPP_BE_Base'),('date_begin','<=',ddeb),('date_end','>=',dfin)]
			tab_id = tab_obj.search(cr, uid, crit )
			if len(tab_id) != 1:
				return u"ERR table IPP_BE_Base non trouvée"
			ipprevcjt = 0.00
			crit = [('param_name.name','=','REV_CJT'),('employee_key','=',employee),('date_begin','<=',ddeb),('date_end2','>=',dfin)]
			par_id = par_obj.search(cr, uid, crit)
			if len(par_id) == 1:
				rcj = par_obj.read(cr, uid, par_id ,['res_n'])
				revcjt = rcj[0]['res_n']
			else:
				return u"ERR param REV_CJT non trouvé"
			if revcjt == 0:
				crit = [('param_name.name','=','BE_PLAFONDREVCJT'),('legalframe_key','=',legframe),('date_begin','<=',ddeb),('date_end2','>=',dfin)]
				par_id = par_obj.search(cr, uid, crit)
				if len(par_id) == 1:
					ex = par_obj.read(cr, uid, par_id ,['res_n'])
					plafrevcjt = ex[0]['res_n']
				else:
					return u"ERR param BE_PLAFONDREVCJT non trouvé"
#				Calcul de l'impôt sur le revenu attribué au conjoint	
				if plafrevcjt > 0.30 * revannnetimpos: revcjt = 0.30 * revannnetimpos
				else: revcjt = plafrevcjt
				x = tab_obj.lookup(cr, uid, tab_id,[0,revcjt,"*","ge"])
				pctipprevcjt = float(x[2])
				ippbasrevcjt = float(x[1])
				trbasrevcjt = float(x[3])
				ipprevcjt = round(ippbasrevcjt + (pctipprevcjt* (revcjt - trbasrevcjt)),2)
#				Calcul de l'impôt sur la différence entre le rev annuel net et le revenu attribué au conjoint					
				revdiff = revannnetimpos - revcjt
				x = tab_obj.lookup(cr, uid, tab_id,[0,revdiff,"*","ge"])
				pctippdiff = float(x[2])
				ippbasdiff = float(x[1])
				trbasdiff = float(x[3])
				ippdiff = round(ippbasdiff + (pctippdiff* (revdiff - trbasdiff)),2)
				ippbase = ipprevcjt + ippdiff - (2 * exempt)
			else:
				x = tab_obj.lookup(cr, uid, tab_id,[0,revannnetimpos,"*","ge"])
				pctipptr = float(x[2])
				ippbastr = float(x[1])
				trbas = float(x[3])
				ippbase = round(ippbastr + (pctipptr * (revannnetimpos - trbas)) - exempt, 2)
#			calcul des réductions isolé et enfants à charge
			redenf = 0.00
			reduc = 0.00
			nbenf = 0
			crit = [('param_name.name','=','IPP_REDUCTIONS'),('employee_key','=',employee),('date_begin','<=',ddeb),('date_end2','>=',dfin)]
			par_id = par_obj.search(cr, uid, crit)
			if len(par_id) == 1:
				red = par_obj.read(cr, uid, par_id ,['res_n'])
				reduc = red[0]['res_n']
			else:
				return u"ERR param IPP_REDUCTIONS non trouvé"
			crit = [('param_name.name','=','NB_ENF_ACHARGE'),('employee_key','=',employee),('date_begin','<=',ddeb),('date_end2','>=',dfin)]
			par_id = par_obj.search(cr, uid, crit)
			if len(par_id) == 1:
				ex = par_obj.read(cr, uid, par_id ,['res_n'])
				nbenf = ex[0]['res_n']
			else:
				return u"ERR param NB_ENF_ACHARGE non trouvé"
			crit =[('name','=','IPP_RedEnfACharge'),('date_begin','<=',ddeb),('date_end','>=',dfin)]
			tab_id = tab_obj.search(cr, uid, crit)
			if len(tab_id) == 1:
				x = tab_obj.lookup(cr, uid, tab_id,[0,nbenf,"*","ge"])
				redbase = float(x[1])
				redenf = redbase
				if nbenf > 8:
					x = tab_obj.lookup(cr, uid, tab_id,[0,8,"*","ge"])
					base8 = float(x[1])
					redenf = base8 + ((nbenf - 8) * redbase)
			else:
				return u'ERR table IPP_RedEnfACharge non trouvée'
			res = round((ippbase - redenf - reduc)/12, 2)
			return res

		def cotsss_bel(payid,args):
			res = 0.00
			brut = args[0]
			sitfam = args[1]
			ddeb= payid.date_begin
			dfin= payid.date_end
			pool = pooler.get_pool(cr.dbname)
			tab_obj = pool.get('hr_gp.table')
			crit = [('name','=','ONSS_TAUXCOTSSS'),('date_begin','<=',ddeb),('date_end','>=',dfin)]
			tab_id = tab_obj.search(cr, uid, crit)
			if len(tab_id) == 1:
				x = tab_obj.lookup(cr, uid, tab_id,[0,brut,"*","ge"])
				bas = float(x[1])
				pct2rv = float(x[2])
				pctiso = float(x[3])
				fft2rv = float(x[4])
				fftiso = float(x[5])
				min2rv = float(x[6])
				miniso = float(x[7])
				max2rv = float(x[8])
				maxiso = float(x[9])
				if sitfam == 1:
					res = min(max(fft2rv + (pct2rv * (float(brut) - bas)),min2rv),max2rv)
				else:
					res = min(max(fftiso + (pctiso * (float(brut) - bas)),miniso),maxiso)
			else:
				return u'ERR table ONSS_TAUXCOTSSS non trouvee'
			return res
		def essai(args):
			res = (float(args[0]) + float(args[1]))/2
			return res
			
########compute ###################################################   
		rec = self.browse(cr, uid,id,context=None)
		desc = rec.description
		args = rec.param_chain.split(";")
		func = rec.func_name
		payid = rec.payid
		res = False
##      Insérer ci-dessous l'appel aux nouvelles fonctions
		if func == "essai": res= essai(args)
		elif func == "pp_bel": res= ppbel(payid, args)
		elif func == "cotsss_bel": res= cotsss_bel(payid, args)
		return res    

functions_gp()



