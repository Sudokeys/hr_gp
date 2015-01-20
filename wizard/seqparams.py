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

class seqparams_wizard(osv.osv_memory):
	_name='hr_gp.seqparams.wizard'
    
	_columns= {
               'name': fields.char('Name', size=16),
               'state': fields.char('State', size=32),
	}
	_defaults = {
		'state': 'begin'
	}
	def seq_allparams(self, cr, uid, id, context=None):
	   	def getAntecId(params, id):
			res = []
			dictres = {}
			dictres['id'] = params.id
			param_codeid = False
			param_title = False
			param_entity_type = False
			if params.category == "f":
				for op in ('a_', 'b_', 'c_', 'd_', 'e_', 'f_'):
					if op == "a_" : 
						param_codeid = params.a_.id
						param_entity_type = params.a_.entity_type
						param_title = params.a_.title
					elif op == "b_" : 
						param_codeid = params.b_.id
						param_entity_type = params.b_.entity_type
						param_title = params.b_.title
					elif op == "c_" : 
						param_codeid = params.c_.id
						param_entity_type = params.c_.entity_type
						param_title = params.c_.title
					elif op == "d_" : 
						param_codeid = params.d_.id
						param_entity_type = params.d_.entity_type
						param_title = params.d_.title
					elif op == "e_" : 
						param_codeid = params.e_.id
						param_entity_type = params.e_.entity_type
						param_title = params.e_.title
					elif op == "f_" : 
						param_codeid = params.f_.id
						param_entity_type = params.f_.entity_type
						param_title = params.f_.title
					if param_codeid: dictres[op] = param_codeid
			numcounter = 0
			for counter in params.epe_counter_add:
				numcounter += 1
				key = "rege_"+str(numcounter)
				if counter.id: dictres[key] = counter.id
			for counter in params.epr_counter_add:
				numcounter += 1
				key = "regr_"+str(numcounter)
				if counter.id: dictres[key] = counter.id
			res.append(dictres)
			return res
			
		def find_cycle(NODES, EDGES, READY):
			todo = set(NODES())
			while todo:
				node = todo.pop()
				stack = [node]
				while stack:
					top = stack[-1]
					for node in EDGES(top):
						if node in stack:
							return stack[stack.index(node):]
						if node in todo:
							stack.append(node)
							todo.remove(node)
							break
					else:
						node = stack.pop()
						READY(node)
			return []
		def nodes():
			return x.keys()
		def edges(node):
			return y[node]
		def ready(node):
			return
		def newnode(n):
			if n not in nod:
				nod.append(n)
				x[n]=[]
			if not(y.has_key(n)):
				y[n]=[]			
			return
		def newedge(n, d):
			if not(x.has_key(n)):
				x[n]=[]
			x[n].append(d)
			if not(y.has_key(d)):
				y[d]=[]
			y[d].append(n)
			return
######## deb de seq-allparams() ###########################################
		wizard=self.browse(cr, uid, id, context=context)
		self.write(cr, uid, id, {'state':'begin',}, context=context)
		x = {}
		y = {}
		nod = []
		pool = pooler.get_pool(cr.dbname)
		par_obj = pool.get('hr_gp.params_dict')
		lstids = par_obj.search(cr, uid, [('category',"in",('v','f','r'))])
		for params in par_obj.browse(cr, uid, lstids, context=None):
			if params.id:
				newnode(params.id)	
			anteced = getAntecId(params, [params.id])[0]
			for fields in anteced.keys():
				if fields[0:3] == 'reg':
					newnode(anteced[fields])
					newedge(params.id,anteced[fields])
				if fields[0:2] in ('a_','b_','c_','d_','e_','f_'):
					newedge(anteced[fields],params.id)
		res = find_cycle(nodes, edges, ready)
		if len(res) > 0:
			raise osv.except_osv(u'Avertissement ', u'Les lignes suivantes sont dans une boucle \n' + str(res))
		seq={}
		niv = -1
		while (len(seq) < len(x)) and (niv < 20):
			niv += 1
			for elx in x:
				if len(x[elx]) == 0: 
					if not seq.has_key(elx): 
						seq.update({elx:niv})
				else:
					nivmax =0
					for ant in x[elx]:
						if not seq.has_key(ant):
							if seq.has_key(elx):						
								del seq[elx]
						else:
							if seq[ant] > nivmax: nivmax = seq[ant]
					if nivmax < niv:
						if not seq.has_key(elx):							
							seq.update({elx:niv})
						else:
							if seq[elx] <= nivmax:
								seq[elx]= nivmax + 1
					else:
						if seq.has_key(elx):					
							del seq[elx] 
		for params in par_obj.browse(cr, uid, lstids, context=None):
			newseq = seq[params.id]*10
			par_obj.write(cr, uid, params.id,{'seq':newseq})
		self.write(cr, uid, id, {'state':'completed',}, context=context)
		return True

seqparams_wizard()
   
