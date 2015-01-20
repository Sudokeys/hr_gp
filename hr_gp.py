# -*- coding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Enterprise Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://openerp.com>).
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
###################################################################
import time
import pooler
from datetime import datetime, timedelta, date
from osv import osv
from osv import fields
from bisect import bisect_left, bisect_right
from tools.translate import _
from tools.translate import translate
import openerp
from openerp import tools,addons
import logging
_logger = logging.getLogger(__name__)


buffer_val ={}

class hr_gp_param_model(osv.osv):
    def _get_entity_types(self, cr, uid, context=None):
            return[('leg','leg'),('cny','cny'),('emp','emp'),('act','act'),('ctt','ctt'),('pay','pay')]
    
    _name = 'hr_gp.param_model'
    _description = 'Params model'
    _columns = {
        'name': fields.char('Model name', size=128),
        'entity_type': fields.selection(_get_entity_types,'Entity'),
        'descr': fields.text('Description'),
        'date_effet': fields.date("Date d'effet"),
        'params': fields.one2many('hr_gp.param_model_item','model_id'),
        'active': fields.boolean('active'),
    }
    _defaults = {
        'active': 'True',
        'date_effet' : lambda *a: time.strftime("%Y-%m-%d"),
    } 
hr_gp_param_model()

class hr_gp_company(osv.osv):
    _name = 'hr_gp.company'
    _description = 'Company'
#   _inherits = 'res.company'
    _columns = {
        'name': fields.char('Cny Name', size=32),
        'description': fields.text('Description'),
        'params': fields.one2many('hr_gp.params_val','company_key'),
        'active': fields.boolean('Active'),
        'cumuls': fields.one2many('hr_gp.cumann','company_key'),
    }
    _defaults = {
            'active': 'True',
    }
hr_gp_company() 

class hr_gp_legal_frame(osv.osv):
    _name = 'hr_gp.legal_frame'
    _description = 'Legal frame'
    _columns = {
        'name': fields.char('Name', size=32),
        'description': fields.char('Description', size=40),
        'params': fields.one2many('hr_gp.params_val','legalframe_key'),
        'active': fields.boolean('Active'),
    }
    _defaults = {
            'active': 'True',
    }
hr_gp_legal_frame()


class hr_gp_activity(osv.osv):
    _name = 'hr_gp.activity'
    _description = 'Activity frame'

    def create(self, cr, uid, vals, context=None):
        if context is None: context = {}
        if context.get('type') : vals['type'] = context.get('type') 
        result = super(hr_gp_activity, self).create(cr, uid, vals, context)
        return result
    
    _columns = {
        'name': fields.char('Name', size=32),
        'description': fields.text('Description'),
        'legal_frame': fields.many2one('hr_gp.legal_frame', 'Legal frame'),
        'company': fields.many2one('hr_gp.company','Company'),
        'establishment': fields.many2one('res.partner','Establishment'),
        'params': fields.one2many('hr_gp.params_val','activityframe_key'),
        'active': fields.boolean('Active'),
        'cumuls': fields.one2many('hr_gp.cumann','activityframe_key'),
        'type'  : fields.selection([('activity', 'activity'),('collective', 'Collective convention'),('establishment', 'establishment')], 'grouping'),
    }
    _defaults = {
            'active': 'True',
            'type': 'activity',
    } 
hr_gp_activity()


class hr_employee(osv.osv):
    _name = "hr.employee"
    _description = "Employee"
    _inherit = "hr.employee"

    def _get_latest_contract(self, cr, uid, ids, field_name, args, context=None):
        res = {}
        obj_contract = self.pool.get('hr_gp.contractframe')
        for emp in self.browse(cr, uid, ids, context=context):
            contract_ids = obj_contract.search(cr, uid, [('employee_id','=',emp.id),], order='date_start', context=context)
            if contract_ids:
                res[emp.id] = contract_ids[-1:][0]
            else:
                res[emp.id] = False
        return res
    
    def _address(self, cr, uid, ids, name, args, context=None):
        res = {}
        for employee in self.browse(cr, uid, ids, context=context):
            res[employee.id] = {
                'street': employee.address_home_id.street,
                'street2': employee.address_home_id.street2,
                'zip': employee.address_home_id.zip,
                'city': employee.address_home_id.city,
            }
        return res

    def _get_address(self, cr, uid, ids, context=None):
        res = {}
        for partner in self.pool.get('res.partner').browse(cr, uid, ids, context=context):
            employee = self.pool.get('hr.employee').search(cr,uid,[('address_home_id','=',partner.id)])
            for e in employee:
                if e:
                  res[e] = True
        return res.keys()
    

    _columns = {
        'prenom': fields.char('Prénom', size=64,required=False),
        'place_of_birth': fields.char('Place of Birth', size=30),
        'contract_ids': fields.one2many('hr_gp.contractframe', 'employee_id', 'Contracts'),
        'params': fields.one2many('hr_gp.params_val','employee_key'),
        'cumuls': fields.one2many('hr_gp.cumann','employee_key'),
                'matricule': fields.char('Matricule', size=30),
        'street': fields.function(_address,string='street', type='char',
            store = {
                'hr.employee': (lambda self,cr,uid,ids,c=None: ids, ['address_home_id'], 10),
                'res.partner': (_get_address, ['street'], 10),
            },
            multi='address'),
        'street2': fields.function(_address,string='street2', type='char',
            store = {
                'hr.employee': (lambda self,cr,uid,ids,c=None: ids, ['address_home_id'], 10),
                'res.partner': (_get_address, ['street2'], 10),
            },
            multi='address'),
        'zip': fields.function(_address,string='zip', type='char',
            store = {
                'hr.employee': (lambda self,cr,uid,ids,c=None: ids, ['address_home_id'], 10),
                'res.partner': (_get_address, ['zip'], 10),
            },
            multi='address'),
        'city': fields.function(_address,string='city', type='char',
            store = {
                'hr.employee': (lambda self,cr,uid,ids,c=None: ids, ['address_home_id'], 10),
                'res.partner': (_get_address, ['city'], 10),
            },
            multi='address'),
        'mode_reglement_p': fields.many2one('hr_gp.mode.paiement', 'Mode de règlement'),
    }
    
hr_employee()

class hr_gp_mode_paiement(osv.osv):
    _name = 'hr_gp.mode.paiement'
    _description = 'Mode de paiement'
    
    _columns = {
        'name':fields.char('Libellé')
    }
    
hr_gp_mode_paiement()


class hr_gp_contractframe(osv.osv):
    _name = 'hr_gp.contractframe'
    _description = 'Contract frame'
    _columns = {
        'name': fields.char('Contract Reference', size=32),
        'employee_id': fields.many2one('hr.employee', "Employee_id"),
        'date_begin': fields.date('Start Date', required=True),
        'date_end': fields.date('End Date'),
        'payslip_model': fields.many2one('hr_gp.param_model', 'Payslip model'),
        'notes': fields.text('Notes'),
        'analytic_acc_split': fields.one2many('hr_gp.analytic_split','contract_frame'),
        'activity': fields.many2one('hr_gp.activity','Activity', required=True),
        'convention': fields.many2one('hr_gp.activity','Convention'),
        'establishment': fields.many2one('hr_gp.activity','Establishment'),
        'params': fields.one2many('hr_gp.params_val','contractframe_key'),
        'cumuls': fields.one2many('hr_gp.cumann','contractframe_key'),
    }
    _defaults = {
        'date_end': lambda *a: "2099-12-31"
    }

    def _check_dates(self, cr, uid, ids, context=None):
        for contract in self.browse(cr, uid, ids, context=None):
            if contract['date_begin'] and contract['date_end'] and contract['date_begin'] > contract['date_end']:
                return False
        return True
        
    def _check_analytic_split(self, cr, uid, ids, context=None):
        for contract in self.browse(cr, uid, ids, context=None):
            dictper = {}
            for splitacc in contract.analytic_acc_split:
                keysplit = str(splitacc.date_begin)+"_"+ str(splitacc.date_end)
                if dictper.has_key(keysplit) == False:
                    dictper[keysplit]=[]
                dictper[keysplit].append(splitacc.split_percent)
            for eachkey in dictper.keys():
                sumpct = 0.00
                for eachsplit in dictper[eachkey]:
                    sumpct += eachsplit
                if sumpct != 1.00: return False
        return True
        
    _constraints = [
        (_check_dates, 'Error! contract begin-date must be lower then contract end-date.', ['date_begin', 'date_end']),
        (_check_analytic_split,'Error! Total split percentages not = 100%',['analytic_acc']),
        ]
hr_gp_contractframe()           

class account_analytic_account(osv.osv):
    _name = 'account.analytic.account'
    _description = 'Analytic Account'
    _inherit = 'account.analytic.account'
    _columns = {
        'hr_contract_split': fields.one2many('hr_gp.analytic_split','contract_frame'),
        }

account_analytic_account()
    

class hr_gp_analytic_split(osv.osv):
    _name = 'hr_gp.analytic_split'
    _description = 'Contract analytic split'
    _columns = {
        'name':fields.char('Split name', size =16, ),
        'contract_frame':fields.many2one('hr_gp.contractframe','ctt name'),
        'analytic_acc': fields.many2one('account.analytic.account','acc name'),
        'split_percent': fields.float('Split %', digits = (5,4)),
        'date_begin': fields.date('Validity begin', required=True),
        'date_end': fields.date('Validity end'),
    }
    _defaults = {
        'date_end': lambda *a: "2099-12-31"
    }
hr_gp_analytic_split()

    
class hr_gp_params_dict(osv.osv):
    _name = 'hr_gp.params_dict'
    _description = "Params Dictionary"
    
    def _get_entity_types(self, cr, uid, context=None):
        return[('leg','legal'),('cny','company'),('emp','employee'),('act','activity'),('ctt','contract'),('pay','pay')]
    
    def _get_states(self, cr, uid, context=None):
        return[('draft','draft'),('comp','computed'),('val','validated'),('del','deleted')]
    
    def _get_dc(self, cr, uid, context=None):
        return[('D','Debit'),('C','Credit')]

    def _get_formats(self, cr, uid, context=None):
        return[('n','numeric'),('t','text'),('d','date')]

    def _get_categories(self, cr, uid, context=None):
        return[('f','formula'),('r','register'),('v','value')]
    
    def _get_group (self, cr, uid, context=None):
        return [('JH','Jour / Heure'),('BRUT','Brut'),('COT','Cotisations'),('NET','Net'),('CUM','Cumuls')]
    
    def _get_group_view (self, cr, uid, context=None):
        return [('input_1','Groupe 1'),('input_2','Groupe 2'),('input_3','Groupe 3')]
    
    def _formule_check(self, cr, uid, ids, context=None):
            res= True
            for rec in self.browse(cr, uid, ids, context=None):
                if rec.category == "f":
                    if rec.base_formula == False and rec.rate_formula == False:
                        res = False
                    for exp in (rec.base_formula, rec.qtye_formula, rec.rate_formula, rec.qtyr_formula, rec.ratr_formula):
                        if exp:
                            if exp.count('(') != exp.count(')'): res = False
            return res
        
    def _validexpr(self, cr, uid, ids, context=None):
        res = True
        for rec in self.browse(cr, uid, ids, context=None):
            if rec.category == 'v':
                expr = rec.validexp
                if expr:
                    expaev = expr.replace("$x","x")
                    if rec.format == "n": 
                        x = 5
                    elif rec.format == "t":
                        x = "a"
                    else: x = date.today()
                    try:
                        res1 = eval(expaev)
                    except: 
                        res = False
        return res
        
    def _cum_regist_check(self, cr, uid, ids, context=None):
            res = True
            for rec in self.browse(cr, uid, ids, context=None):
                if rec.cum_epe == True or rec.cum_ctt == True or rec.cum_act == True or rec.cum_cpy == True:
                    if rec.entity_type == "pay" and rec.category == 'r' and rec.format == 'n':
                        res = True
                    else: 
                        res = False
            return res
    
    def _compute_ducs(self, cr, uid, ids, name, args, context=None):
        result = {}
        return result
    
    _columns = {
        'name': fields.char('Code', size = 20, select=True),
        'title': fields.char('Title', size = 40),
        'desc': fields.text('Description'),
        'origin': fields.char('Origin', size = 16),
        'entity_type': fields.selection(_get_entity_types, 'Type', select=True),
        'format': fields.selection(_get_formats, 'Format'),
        'category': fields.selection(_get_categories, 'Category'),
        'creation_date': fields.date('Creation date'),
        'update_date': fields.date('Update date'),
        'a_': fields.many2one('hr_gp.params_dict','Op a_', select=True),
        'b_': fields.many2one('hr_gp.params_dict','Op b_', select=True),
        'c_': fields.many2one('hr_gp.params_dict','Op c_', select=True),
        'd_': fields.many2one('hr_gp.params_dict','Op d_', select=True),
        'e_': fields.many2one('hr_gp.params_dict','Op e_', select=True),
        'f_': fields.many2one('hr_gp.params_dict','Op f_', select=True),
        'base_formula': fields.text('Base formula',help='Formula using operands a_, b_, c_, d_, e_ or f_ referring to params \n Result always = base * rate *qty'),
        'rate_formula': fields.text('Rate employee formula',help='Formula using operands a_, b_, c_, d_, e_ or f_ referring to params \n Result always = base * rate *qty'),
        'qtye_formula': fields.text('Qty employee formula',help='Formula using operands a_, b_, c_, d_, e_ or f_ referring to params \n Result always = base * rate *qty'),
        'ratr_formula': fields.text('Rate employer formula',help='Formula using operands a_, b_, c_, d_, e_ or f_ referring to params \n Result always = base * rate *qty'),
        'qtyr_formula': fields.text('Qty employer formula',help='Formula using operands a_, b_, c_, d_, e_ or f_ referring to params \n Result always = base * rate *qty'),
        'epe_counter_add': fields.many2many('hr_gp.params_dict','hr_gp_params_dict_employee_related', 'line', 'registre'),
        'epr_counter_add': fields.many2many('hr_gp.params_dict','hr_gp_params_dict_employer_related', 'line', 'registre'),
        'active': fields.boolean('Active'),
        'account_e_d': fields.many2one('account.account','Acc debit employee'),
        'account_e_c': fields.many2one('account.account','Acc credit employee'),
        'account_r_d': fields.many2one('account.account','Acc debit employer'),
        'account_r_c': fields.many2one('account.account','Acc credit employer'),
        'cum_epe': fields.boolean('Cum employee'),
        'cum_ctt': fields.boolean('Cum contrat'),
        'cum_act': fields.boolean('Cum activity'),
        'cum_cpy': fields.boolean('Cum company'), 
        'validexp':fields.char('Validation expression',size=128, help="Expression logique Python en utilisant $x pour l'input à tester"),
        'seq': fields.integer('Seq'), 
        'group' : fields.selection(_get_group, 'Group'),
        'group_view' : fields.selection(_get_group_view, 'Groupe de saisie'),
        'optional': fields.boolean('Optional'),
        'defwhenopt': fields.char('Default value when optional',size=16, help="Defaut value when parameter optional"),
        'org_cotis': fields.many2one('hr_gp.org_cotis_group','Organisme de cotisations'),
        'ducs': fields.many2one('hr_gp.ducs','Code DUCS'),
        'org_cotis_ducs': fields.function(_compute_ducs, relation='hr_gp.ducs', type="many2many", string='DUCS'),
        }
    _defaults = {
        'active': 'True',
        'entity_type': 'pay',
        'format': 'n',
        'rate_formula':"1",
        'ratr_formula':"0",
        'qtye_formula':"1",
        'qtyr_formula':"0",
        'cum_epe': False,
        'cum_ctt': False,
        'cum_act': False,
        'cum_cpy': False,  
        'optional': False,
        'creation_date': lambda *a: time.strftime("%Y-%m-%d"),
        }
    _sql_constraints = [
        ('name_unique', 'unique(name)', 'Name must be unique.'),
        ]
    _constraints = [
        (_formule_check,"Formula not defined or incorrect ",['base_formula','rate_formula','ratr_formula']),
        (_validexpr,"Incorrect validation expression ",['validexp']),
        (_cum_regist_check,"Cum only on param of type register",['cum_epe','cum_ctt','cum_act','cum_cpy'])
        ]
        
hr_gp_params_dict()

class hr_gp_params_val(osv.osv):
    def _get_entity_types(self, cr, uid, context=None):
        return[('leg','legal'),('cny','company'),('emp','employee'),('act','activity'),('ctt','contract')]
    
    def _calcres(self, cr, uid, ids, name, args, context=None):
        res = {}
        for rec in self.browse(cr, uid, ids, context=None):
            res[rec.id]={'res_n':0.00,'res_d':'','res_t2':''}
            if rec.format == 'n':
                if rec.inp == False:
                    resN = 0.00
                else:
                    resN = float(str(rec.inp).replace(",",".")) 
                res[rec.id]={'res_n':resN,'res_d':'','res_t2':''}
            elif rec.format == 'd':
                if rec.inp <> False:
                    resD=''
                    try:
                        strttime = datetime.strptime(rec.inp,"%d/%m/%Y")
                    except:
                        oldinp = rec.inp
                        rec.inp = "Invalid date: " + oldinp
                        res[rec.id]={'res_n':0.00,'res_d':'','res_t2':rec.inp}
                        return res
                    resD = strttime.isoformat()[0:10]
                else:
                    strttime = datetime.strptime("31/12/2099","%d/%m/%Y")
                    resD = strttime.isoformat()[0:10]
                res[rec.id]={'res_n':0.00,'res_d':resD,'res_t2':''}
            elif rec.format == 't':
                if rec.inp <> False:
                    resT = rec.inp
                else: 
                    resT = ""
                res[rec.id]={'res_n':0.00,'res_d':'','res_t2':resT}
            else: 
                raise osv.except_osv(u'Alert', u"Invalid format: " + rec.format)
            
        return res
            
    def _validexpr(self, cr, uid, ids, context=None):
        res = False
        for rec in self.browse(cr, uid, ids, context=None):
            if rec.param_name.category == 'v':
                expr = rec.param_name.validexp
                if expr and rec.inp:
                    if rec.param_name.format == 'n':
                        expaev = expr.replace("$x",rec.inp)
                    elif rec.param_name.format == 't':
                        expaev = expr.replace("$x","'"+rec.inp+"'")
                    try:
                        res = eval(expaev)
                    except: raise osv.except_osv(u'Alert', u"Incorrect validation expression in params dict: " + expr)
                elif rec.param_name.format == 'd':
                    try:
                        strttime = datetime.strptime(rec.inp,"%d/%m/%Y")
                    except:
                        raise osv.except_osv(u'Alert', u"Invalid format date " + rec.inp)
                    res=True
                else:
                    res =True
            else:
                res=True
        return res
        
        
    def _get_cur_par_id(self, cr, uid,ids,context=None):
        res = {}
        for rec in self.browse(cr, uid, ids, context=None):
            crit = [('param_name',"=",rec.param_name.id)]
            crit.append(('activityframe_key','=',rec.activityframe_key.id))
            crit.append(('legalframe_key','=',rec.legalframe_key.id))
            crit.append(('contractframe_key','=',rec.contractframe_key.id))
            crit.append(('employee_key','=',rec.employee_key.id))
            idsearch = self.search(cr, uid, crit)
            res = idsearch
        return res
        
    def _defaultdatdeb():
            return time.strftime("%Y-%m-%d")
            
    def _datefinval(self, cr, uid, ids, name, args, context=None):
        res = {}    
        for rec in self.browse(cr, uid, ids, context=None):         
            crit = [('param_name',"=",rec.param_name.id)]
            crit.append(('activityframe_key','=',rec.activityframe_key.id))
            crit.append(('legalframe_key','=',rec.legalframe_key.id))
            crit.append(('contractframe_key','=',rec.contractframe_key.id))
            crit.append(('employee_key','=',rec.employee_key.id))
            crit.append(('date_begin','>',rec.date_begin))
            idsearch = self.search(cr, uid, crit)
            rec1 = []
            datemin = datetime.strptime("2099-12-31","%Y-%m-%d")
            if len(idsearch)>0:
                rec1 = self.read(cr, uid, idsearch,fields=['id','param_name','activityframe_key','entity_type','date_begin'], context=None)
            if len(rec1) > 0:
                for rec3 in rec1:
                    datebeg = datetime.strptime(rec3['date_begin'],"%Y-%m-%d")
                    if datebeg < datemin: 
                        datemin = datebeg
            dateprec = datemin -timedelta(days=1)
            new_end = dateprec.isoformat()[0:10]
            res[rec.id]= new_end
        return res
        
    _name = 'hr_gp.params_val'
    _description = 'Params values for entities'
    _columns = {
        'name': fields.char('Name bidon',size= 12),
        'param_name': fields.many2one('hr_gp.params_dict','name', ondelete='restrict', select=True),
        'legalframe_key': fields.many2one('hr_gp.legal_frame','legalframe_id', ondelete='restrict', select=True),
        'activityframe_key': fields.many2one('hr_gp.activity','activityframe_id', ondelete='restrict', select=True),
        'contractframe_key': fields.many2one('hr_gp.contractframe','contractframe_id', ondelete='restrict', select=True),
        'employee_key': fields.many2one('hr.employee','employee_id', ondelete='restrict', select=True),
        'company_key': fields.many2one('hr_gp.company','company_id', ondelete='restrict', select=True),
        'title': fields.related('param_name','title',type='char', string='title', readonly=True),
        'entity_type': fields.related('param_name','entity_type',type='char', string='Type', readonly=True),
        'format': fields.related('param_name','format',type='char', string='format', readonly=True),
        'inp': fields.char('Input', size = 64),
        'res_n': fields.function(_calcres, type='float', digits = (12,5), string = 'Value Num', method=True, multi='res'),
        'res_d': fields.function(_calcres, type='date', string = 'Value Date', method=True, multi='res'),
        'res_t2': fields.function(_calcres, type='char', string= 'Value Text', size = 64, method=True, multi='res'),
        'date_begin': fields.date('Validity begin', select=True),
        'date_end': fields.date('Validity end old', select=True),
        'date_end2': fields.function(_datefinval, type='date', string = 'Validity end', method=True, store={'hr_gp.params_val':(_get_cur_par_id,['date_begin'],10)}, select=True)
        }
    _defaults = {
        'date_begin': _defaultdatdeb(),
    }
    _constraints = [
       (_validexpr,"Incorrect value referring to params dict validation expression ",['inp'])
        ]
    _order = "date_end2 desc"
        
hr_gp_params_val()

class hr_gp_table(osv.osv):
    def _get_cur_tab_id(self, cr, uid,ids,context=None):
        res = {}
        for rec in self.browse(cr, uid, ids, context=None):
            crit = [('name',"=",rec.name)]
            idsearch = self.search(cr, uid, crit)
            res = idsearch
        return res

    def _datefinval(self, cr, uid, ids, name, args, context=None):
        res = {}
        for rec in self.browse(cr, uid, ids, context=None):
            crit = [('name',"=",rec.name)]
            crit.append(('date_begin','>',rec.date_begin))
            idsearch = self.search(cr, uid, crit)
            rec1 = []
            datemin = datetime.strptime("2099-12-31","%Y-%m-%d")
            if len(idsearch)>0:
                rec1 = self.read(cr, uid, idsearch,fields=['id','name','date_begin'], context=None)
            if len(rec1) > 0:
                for rec3 in rec1:
                    datebeg = datetime.strptime(rec3['date_begin'],"%Y-%m-%d")
                    if datebeg < datemin: datemin = datebeg
            dateprec = datemin -timedelta(days=1)
            new_end = dateprec.isoformat()[0:10]
            res[rec.id]= new_end
        return res

    def _formatable(self, cr, uid, ids, name,args, context=None):
        res = {}
        for tab in self.browse(cr, uid, ids, context=None):
            rest = "\n.."
            table= tab.textable.encode('ascii')
            a = table.splitlines()
            b = []
            for lines in a:
                tabcol = lines.split(";")
                newlig = "\n"
                for col in tabcol:
                    y = col.replace(",",".")
                    x = self.tonumeric(y)
                    if type(x) == type(0.00): fmt = "%09.2f"
                    elif type(x) == type(0): fmt = "  %07d"
                    else: fmt = "%07s"
                    newlig = newlig + (fmt % x).rjust(13)
                rest = rest + newlig
            res[tab.id]= rest
        return res

    _name = 'hr_gp.tablle'
    _description = 'Rates tables'
    _columns = {
        'name': fields.char('Name', size=32),
        'description': fields.text('Description'),
        'textable': fields.text('TextContent'),
        'test_formule': fields.text('Formule test'),
        'formated_tab': fields.function(_formatable,type='text',string='Formatted table',method=True),
        'res_test': fields.text('Résultat'),
        'date_begin': fields.date('Validity date begin', required=True),
        'date_end': fields.function(_datefinval, type='date', string = 'Validity end', method=True,
            store={'hr_gp.tablle':(_get_cur_tab_id,['date_begin'],10)}),
        'active': fields.boolean('Active'),
    }
    _defaults = {
            'active': 'True',
    }

    def tonumeric(self, str):
        try:
            return int(str)
        except ValueError:
            pass
        try:
            return float(str)
        except ValueError:
            return str

    def lookup(self, cr, uid, ids, args):
        res = {}
        for tab in self.browse(cr, uid, ids, context=None):
            table= tab.textable.encode('ascii')
            colkey = args[0]
            valkey = self.tonumeric(args[1])
            colres = args[2]
            oper = args[3]
            a = table.splitlines()
            b = []
            for lines in a:
                x = lines.replace(",",".")
                b.append(x.split(";"))
            b.sort(key=lambda r:self.tonumeric(r[colkey]))
            c = []
            idl = 0
            nbcol = 0
            for lines in b:
                idv = 0
                for val in lines:
                    if idl == 0: c.append([])
                    c[idv].append(self.tonumeric(val))
                    idv += 1
                    if nbcol < idv: nbcol = idv
                idl += 1
            l = bisect_left(c[colkey],valkey)
            r = bisect_right(c[colkey],valkey)
            if colres == '*': res = b
            else: res = c[colres]
            if oper == "eq":
                if (l != len(c[colkey])) and (c[colkey][l] == valkey): return res[l]
                else: return False
            if oper == "lt":
                if l: return res[l-1]
                else: return False
            if oper == "le":
                if r: return res[r-1]
                else: return False
            if oper == "gt":
                if r != len(c[colkey]): return res[r]
                else: return False
            if oper == "ge":
                if l != len(c[colkey]): return res[l]
                else: return False
        return False

    def testformule(self, cr, uid, ids, context={}):
        res = {}
        for rec in self.browse(cr, uid, ids, context={}):
            oper = rec.test_formule
            if oper[0:7] == "$lookup":
                st1 = oper[7:len(oper)-1]
                st2 = st1.split(";")
                valkey = self.tonumeric(st2[2])
                if st2[3] == "*": colres = st2[3]
                else: colres = int(st2[3])
                res['res_test'] = rec.lookup([int(st2[1]),valkey,colres,st2[4]])
            else: res['res_test'] = str(0)
            if res['res_test']:
                self.write(cr, uid, ids, res, context=None)
            else: raise osv.except_osv(u'Alert', u"Value not found in table")
        return True

hr_gp_table()

class hr_gp_payrun(osv.osv):
    def _get_states(self, cr, uid, context=None):
            return[('draft','draft'),('calc','calculated'),('acc','accountable'),('accted','accounted'),('val','validated'),('clo','closed')]
            
    _name = 'hr_gp.payrun'
    _description = 'Pay run for several'
    _columns = {
        'name': fields.char('Run name', size = 32),
        'company': fields.many2one('hr_gp.company','company_id'),
        'date_begin': fields.date('Date begin'),
        'date_end': fields.date('Date end'),
        'date_compute': fields.date('Date computation'),
        'date_pay': fields.date('Date payment'),
        'descr': fields.text('Description'),
        'selection': fields.text('Selection'),
        'payslips': fields.one2many('hr_gp.payslip','pay_run'),
        'state': fields.selection(_get_states,'state'),
        'activity': fields.many2one('hr_gp.activity','Activity', required=False)
    }
    _defaults = {
        'state':'draft'
    }
    def genpayslipdef(self, cr, uid, ids, context=None):
        for rec in self.browse(cr, uid, ids, context=None):
            sql_rec = """
            SELECT ctt.id, ctt.name, ctt.payslip_model, ctt.activity 
            FROM hr_gp_contractframe ctt 
            LEFT JOIN hr_gp_activity act on (ctt.activity = act.id) 
            WHERE act.company = %s and ctt.date_begin <= %s and ctt.date_end >= %s"""
            cr.execute(sql_rec,(rec.company.id,rec.date_begin,rec.date_end,))
            ctt2pay = cr.fetchall()
            pool = pooler.get_pool(cr.dbname)
            
            model_obj = pool.get('hr_gp.param_model')
            payslip_obj = pool.get('hr_gp.payslip')
            payslip_line_obj = pool.get('hr_gp.payslip_line')
            for ctt in ctt2pay:
                if rec.activity:
                    if ctt[3]==rec.activity.id:    
                        model = model_obj.browse(cr, uid, ctt[2])
                        payslip_id = payslip_obj.create(cr, uid,
                                    { 'pay_run': rec.id,
                                      'name' : ctt[1] + " de " +str(rec.date_begin) +" a "+ str(rec.date_end),
                                      'ctt_id' : ctt[0],
                                      'origin' : model.name,
                                                      'date_begin' : rec.date_begin,
                                                      'date_end' : rec.date_end,
                                     })
                        payslip_line_ids =[]
                        if model.params:
                            for item in model.params:
                                payslip_line_obj.create(cr, uid,
                                            { 'sequence': item.sequence,
                                              'param_name' : item.params.id,
                                              'printable' : item.printable,
                                              'pay_id' : payslip_id,
                                             })
                else:
                    model = model_obj.browse(cr, uid, ctt[2])
                    payslip_id = payslip_obj.create(cr, uid,
                                { 'pay_run': rec.id,
                                  'name' : ctt[1] + " de " +str(rec.date_begin) +" a "+ str(rec.date_end),
                                  'ctt_id' : ctt[0],
                                  'origin' : model.name,
                                                  'date_begin' : rec.date_begin,
                                                  'date_end' : rec.date_end,
                                 })
                    payslip_line_ids =[]
                    if model.params:
                        for item in model.params:
                            payslip_line_obj.create(cr, uid,
                                        { 'sequence': item.sequence,
                                          'param_name' : item.params.id,
                                          'printable' : item.printable,
                                          'pay_id' : payslip_id,
                                         })
        
        return True
        
    def genaccmove(self, cr, uid, ids, context=None):
        for run in self.browse(cr, uid, ids, context=None):
            for payslip in run.payslips:
                if payslip.state in ('calc','val'):
                    res = payslip.gen_accmov()
            payrunstate = "acc"
            for payslip in run.payslips:
                if payslip.state != "acc": payrunstate = "calc"
            if payrunstate == "acc":
                self.write(cr, uid, run.id,{'state':'acc'})
        return True
hr_gp_payrun()

calculate=0
nbr=0
def timing(f):
    def wrap(*args):
        global calculate,nbr
        time1 = time.time()
        ret = f(*args)
        time2 = time.time()
        _logger.info('%s function took %0.3f ms',f.func_name, (time2-time1)*1000.0)
        if f.func_name=='calculate':
            calculate+=(time2-time1)*1000.0
            nbr+=1
        if nbr!=0:    
            _logger.info('%0.3f ms, nbr = %s, moyenne = %0.3f ms',calculate,nbr,calculate/nbr)
        return ret
    return wrap


class hr_gp_payslip(osv.osv):
    def _getId(self, cr, uid, ids, name, args, context=None):
        res = {}
        for rec in self.browse(cr, uid, ids, context=None):
            res[rec.id]=rec.id
        return res
        
    def _get_states(self, cr, uid, context=None):
        return [('draft','draft'),('calc','calculated'),('val','validated'),('acc','accountable'),('accted','accounted'),('clo','closed')]
        
    def cycle_detect(self, cr, uid, ids, context=None):
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
        x = {}
        y = {}
        nod = []
        line_obj = self.pool.get('hr_gp.payslip_line')
        for payslip in self.browse(cr, uid, ids, context=None):
            for payslipline in payslip.payslip_lines:
                if payslipline.id:
                    newnode(payslipline.id) 
                anteced = line_obj.getAntecId(cr, uid, payslipline)[0]
                for fields in anteced.keys():
                    if fields[0:3] == 'reg':
                        newnode(anteced[fields])
                        newedge(anteced[fields],payslipline.id)
                    if fields[0:2] in ('a_','b_','c_','d_','e_','f_'):
                        newedge(payslipline.id, anteced[fields])
                                
        res = find_cycle(nodes, edges, ready)
        if len(res) > 0:
            raise osv.except_osv(u'Avertissement ', u'Les lignes suivantes sont dans une boucle \n' + str(res))
        else:
            raise osv.except_osv(u'OK', u"Il n'y a pas de boucles dans les lignes de cette paie")
        return res
    
    #~ @timing
    def seqcalc_gen (self, cr, uid, ids, buffer_lines, context=None):
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
        x = {}
        y = {}
        nod = []
        line_obj = self.pool.get('hr_gp.payslip_line')
        
        for payslip in self.browse(cr, uid, ids, context=None):
            for payslipline in payslip.payslip_lines:
                if payslipline.id:
                    newnode(payslipline.id) 
                anteced = line_obj.getAntecId(cr, uid, payslipline, lines=buffer_lines)[0]
                for fields in anteced.keys():
                    if fields[0:3] == 'reg':
                        newnode(anteced[fields])
                        newedge(anteced[fields],payslipline.id)
                    if fields in ('a_','b_','c_','d_','e_','f_'):
                        newedge(payslipline.id, anteced[fields])
        
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
        
        payslip_line_obj1 = self.pool.get('hr_gp.payslip_line')
        for payslip1 in self.browse(cr, uid, ids, context=None):
            for payslipline1 in payslip1.payslip_lines:
                payslip_line_obj1.write(cr, uid, [payslipline1.id], {'seqcalc':seq[payslipline1.id]*100}, context=None)
        
        return True                 
        
        
    _name = 'hr_gp.payslip'
    _description = 'Pay slip'
    _columns = {
        'payid': fields.function(_getId, type='integer', string='PayId',method=True),
        'name': fields.char('Description', size=60),
        'origin': fields.char('Origine', size=128),
        'pay_run': fields.many2one('hr_gp.payrun','Payrun_id',ondelete='cascade'),
        'ctt_id': fields.many2one('hr_gp.contractframe','Contrat', ondelete='restrict'),
        'employee_name': fields.related('ctt_id','employee_id','name', type='char', string='Employee name', readonly=True),
        'legal_frame_name': fields.related('ctt_id','activity','legal_frame','name', type = 'char',string='legalframe'),
        'date_begin': fields.date('Date begin'),
        'date_end': fields.date('Date end'),
        'payslip_lines': fields.one2many('hr_gp.payslip_line','pay_id'),
        'viewline' : fields.selection([('all','Toutes les lignes de paye'),('all_take','Lignes à saisir'), ('input_1','Saisie groupe 1'), ('input_2','Saisie groupe 2'), ('input_3','Saisie groupe 3'), ('print', 'Lignes imprimées')], 'Afficher', store=False),
        'date_compute': fields.date('Date compute'),
        'state': fields.selection(_get_states,'state'),
        'log': fields.boolean('Log'),
        'logrec': fields.one2many('hr_gp.logpay','pay_id'),
        'ligacc': fields.one2many('hr_gp.accline','pay_id'),
    }
    _defaults = {
        'state': 'draft',
        'log': False,
        'viewline' : 'all',
    }

    def write(self, cr, uid, ids, vals, context=None):
      if vals.has_key('viewline') : vals['viewline']='all'
      return super(hr_gp_payslip, self).write(cr, uid, ids, vals, context)
    

    def onchange_viewline(self, cr, uid, ids, type_viewline, context={}):
        line_ids =[]
        if type_viewline == 'all' :
            line_ids = self.pool.get('hr_gp.payslip_line').search(cr, uid, [('pay_id', 'in', ids)])
        elif type_viewline == 'all_take' :
            line_ids = self.pool.get('hr_gp.payslip_line').search(cr, uid, [('pay_id', 'in', ids), ('category', '=', 'v')])
        elif type_viewline == 'print' :
            line_ids = self.pool.get('hr_gp.payslip_line').search(cr, uid, [('pay_id', 'in', ids), ('printable', '=', True)], order='group ASC, sequence ASC')
        else :
            line_ids = self.pool.get('hr_gp.payslip_line').search(cr, uid, [('pay_id', 'in', ids), ('group_view', '=', type_viewline)])
        return {'value': {'payslip_lines': line_ids}}

    #~ @timing
    def calc(self, cr, uid, ids, context=None):
        buffer_val.clear()
        payslip_line_obj = self.pool.get('hr_gp.payslip_line')
        curr_date = date.today()
        for payslip in self.browse(cr, uid, ids, context=None):
            buffer_lines = {}
            debut = time.time()
            registre_ids =[]
            value_ids =[]
            for payslipline in payslip.payslip_lines :
              buffer_lines[payslipline.id]= [payslip.id, payslipline.param_name.id]
              if payslipline.category == 'r' : 
                  registre_ids.append(payslipline.id)  
              if (payslipline.category == 'v') and not payslipline.inp : 
                  value_ids.append(payslipline.id)
            payslip_line_obj.write(cr, uid, registre_ids, {'registee' : 0.00, 'register' : 0.00}, context=None)
            payslip_line_obj.write(cr, uid, value_ids, {'inp' : 0.0, }, context=None)

            if payslip.state in('draft', 'calc'): payslip.seqcalc_gen(buffer_lines=buffer_lines)
            
            payslip_line_ids = payslip_line_obj.search(cr, uid, [('pay_id', '=', payslip.id),], order='seqcalc, id ASC')
            for line in payslip_line_obj.browse(cr, uid, payslip_line_ids):
                payslip_line_obj.calculate(cr, uid, [line.id], line, buffer_lines=buffer_lines)
            self.write(cr, uid, ids, {'state':'calc','date_compute':curr_date})
            cr.commit()
            
        buffer_val.clear()
        return True
        
    def gen_accmov(self, cr, uid, ids, context=None):
        for payslip in self.browse(cr, uid, ids, context=None):
            if payslip.state in ("val","calc","acc"):
                curr_date = date.today()
                sql_req = """
                SELECT ps.id, 
                ps.name,
                pd.account_e_d, 
                pd.account_e_c, 
                pd.account_r_d, 
                pd.account_r_c, 
                coalesce(psl.res_ne, 0.00) + coalesce(psl.registee,0.00) AS val_e, 
                coalesce(psl.res_nr,0.00) + coalesce(psl.register,0.00) AS val_r, 
                pd.name
                FROM hr_gp_payslip_line psl
                LEFT JOIN hr_gp_payslip ps ON (ps.id = psl.pay_id)
                LEFT JOIN hr_gp_payrun pr ON (ps.pay_run = pr.id)
                LEFT JOIN hr_gp_params_dict pd ON (psl.param_name = pd.id)
                WHERE ps.id = %s AND psl.pay_id IS NOT NULL
                """ % (payslip.id)
                cr.execute(sql_req)
                paysliplines = cr.fetchall()
                cledict = []
                cum = {}
                for paylig in paysliplines:
                    pd_id = paylig[0]
                    ps_name = paylig[1]
                    cledict = []
                    for acc in range(2,6):
                        if str(paylig[acc]) != "None": cledict.append(str(paylig[acc]) + '_' + str(acc))
                    for cles in cledict:
                        clecum = cles[0:len(cles)-2]
                        if cles[-1:] in ('2','4'): cod_dc = "D"
                        else: cod_dc = "C"
                        if cles[-1:] in ('2','3'): cod_er = "E"
                        else: cod_er = "R"
                        if cum.has_key(clecum) == False: 
                            cum[clecum] = [0.00,0.00]
                        if cod_dc == "D" :
                            if cod_er == "E": 
                                if paylig[6] > 0.00: cum[clecum][0] += round(paylig[6],2)
                                else: cum[clecum][1] -= round(paylig[6],2)
                            else: 
#Modif Aurore !!!
#                                if paylig[7] > 0.00: cum[clecum][0] += round(paylig[7],2)
#                                else: cum[clecum][1] -= round(paylig[7],2)
                                 cum[clecum][0] += round(paylig[7],2)
                        if cod_dc == "C" :
                            if cod_er == "E": 
                                if paylig[6] > 0.00: cum[clecum][1] += round(paylig[6],2)
                                else: cum[clecum][0] -= round(paylig[6],2)
                            else: 
#Modif Aurore !!!
#                                if paylig[7] > 0.00: cum[clecum][1] += round(paylig[7],2)
#                                else: cum[clecum][0] -= round(paylig[7],2)
                                cum[clecum][1] += round(paylig[7],2)


                ligacc_obj = self.pool.get('hr_gp.accline')
                lig_ids = []
                if payslip.ligacc:
                    ligacc2del = []
                    ligacc2del = payslip.ligacc
                    for ligacc in ligacc2del:
                        lig_ids.append((3,ligacc),)
                    for ligacc in ligacc2del:
                        ligacc_obj.unlink(cr, uid, [ligacc.id])
                rep = {}
                
                if payslip.ctt_id.analytic_acc_split:
                    totrep = 0.00
                    for analacc in payslip.ctt_id.analytic_acc_split:
                        if (analacc.date_begin <= payslip.date_begin) and (analacc.date_end >= payslip.date_end):
                            rep.update({analacc.analytic_acc.id:analacc.split_percent})
                            totrep += analacc.split_percent
                else:
                    rep = {False:1.00}
                    totrep = 1.00
                if totrep != 1.00:
                    rep = {False:1.00}
                lig_ids = []
                acc_obj = self.pool.get('account.account')
                tot_deb = 0.00
                tot_cre = 0.00
                for cumkeys in cum.keys():
                    acc_rec = acc_obj.read(cr, 1, [cumkeys],['code','name']) #uid : Access denied (Document type: Account, Operation: read)
                    acc_code = acc_rec[0]['code']           
                    if acc_code[0] in ('6','7'): 
                        rep2 = rep
                    else: rep2 = {False:1.00}
                    sol_d = round(cum[cumkeys][0],2)
                    sol_c = round(cum[cumkeys][1],2)
                    for keyrep in rep2.keys():
                        recacc = {'name':cumkeys,
                            'acc_id':cumkeys,
                            'anal_acc_id':keyrep,
                            'pay_id':payslip.id,
                            'amount_d':round(cum[cumkeys][0]*rep2[keyrep],2),
                            'amount_c':round(cum[cumkeys][1]*rep2[keyrep],2)}
                        sol_d -= recacc['amount_d']
                        sol_c -= recacc['amount_c']
                        if keyrep == rep.keys()[-1]:
                            recacc['amount_d'] += sol_d
                            recacc['amount_c'] += sol_c
                        lig_id = ligacc_obj.create(cr, uid,recacc)
                        lig_ids.append((4,lig_id),)
                        tot_deb += recacc['amount_d']
                        tot_cre += recacc['amount_c']
                lig_id = ligacc_obj.create(cr, uid,{'name':'Total',
                                    'pay_id':payslip.id,
                                    'amount_d':tot_deb,
                                    'amount_c':tot_cre})
                lig_ids.append((4,lig_id),)
                self.write(cr, uid, payslip.id, {'ligacc':lig_ids,})
                if round(tot_deb - tot_cre,2) == 0.00:
                    self.write(cr, uid, payslip.id, {'state':'acc',})
                     
        return True

    def action_wait(self, cr, uid, ids, *args):
        for o in self.browse(cr, uid, ids):
                self.write(cr, uid, [o.id], {'state': 'draft'})
        return True
    def action_validate(self, cr, uid, ids, *args):
        for o in self.browse(cr, uid, ids):
                self.write(cr, uid, [o.id], {'state': 'val'})
        return True
    def action_unvalidate(self, cr, uid, ids, *args):
        for o in self.browse(cr, uid, ids):
                self.write(cr, uid, [o.id], {'state': 'draft'})
        return True
    def action_close(self, cr, uid, ids, *args):
        for o in self.browse(cr, uid, ids):
                self.write(cr, uid, [o.id], {'state': 'clo'})
        return True
        
    def _check_dates(self, cr, uid, ids, context=None):
        res = False
        for rec in self.browse(cr, uid, ids, context=None):
                        if rec.pay_run:
                                if rec.date_begin == False or rec.date_end == False :
                                        self.write(cr, uid, rec.id, {'date_begin':rec.pay_run.date_begin,'date_end':rec.pay_run.date_end})
                                        return True
                                elif rec.date_begin < rec.pay_run.date_begin or rec.date_end > rec.pay_run.date_end :
                                        return False
                                else:
                                        return True
                        else:
                                return True
            
        _constraints = [
        (_check_dates,"Dates must comply with the interval of the pay run",['Date'])
        ]
        
hr_gp_payslip()



class hr_gp_payslip_line(osv.osv):
    def _get_states(self, cr, uid, context=None):
        return[('draft','draft'),('calc','calculated'),('val','validated'),('clo','closed')]
        
    def _getkey(self, cr, uid, ids, name, args, context=None):
        res = {}
        for par in self.browse(cr, uid, ids, context=None):
            pool = pooler.get_pool(cr.dbname)
            modobj = pool.get('hr_gp.params_val')
            ides = modobj.search(cr, uid, [('title','=',u'Taux salarié CSG déductible')])
            rec = modobj.read(cr, uid, ides, fields=['title'], context=None)
            res[par.id] = rec[0]['title']
        return res
    
    def _calcval_e(self, cr, uid, ids, name, args, context=None):
        res = {}
        for rec in self.browse(cr, uid, ids, context=None): 
            res[rec.id]=rec.res_ne + rec.registee
        return res
    def _calcval_r(self, cr, uid, ids, name, args, context=None):
        res = {}
        for rec in self.browse(cr, uid, ids, context=None): 
            res[rec.id]=rec.res_nr + rec.register
        return res 
    def _validexpr(self, cr, uid, ids, context=None):
        res = False
        for rec in self.browse(cr, uid, ids, context=None):
            if rec.param_name.category == 'v':
                expr = rec.param_name.validexp
                if expr and rec.inp:
                    if rec.param_name.format == 'n':
                        expaev = expr.replace("$x",rec.inp)
                    elif rec.param_name.format == 't':
                        expaev = expr.replace("$x","'"+rec.inp+"'")
                    try:
                        res = eval(expaev)
                    except: raise osv.except_osv(u'Alert', u"Incorrect validation expression in params dict" + expr)
                else:
                    res =True
            else:
                res=True
        return res
                    
    
    _name = 'hr_gp.payslip_line'
    _description = "Payslip line"
    _columns = {
        'pay_id': fields.many2one('hr_gp.payslip','payslip_id', ondelete='cascade', select=True),
        'payslip_id': fields.related('pay_id', type='integer', string='Pay slip Id', readonly=True, select=True),
        'cttframe_name': fields.related('pay_id','ctt_id','name', type='char', string='Contract frame', readonly=True),
        'actframe_name': fields.related('pay_id','ctt_id','activity','name', type='char', string='Activity frame', readonly=True),
        'employee_name': fields.related('pay_id','ctt_id','employee_id','name', type='char', string='Employee name', readonly=True),
        'legframe_name': fields.related('pay_id','ctt_id','activity','legal_frame','name', type='char', string='Legal frame', readonly=True),
        'company_name': fields.related('pay_id','ctt_id','activity','company','name', type='char', string='Company', readonly=True),
        'sequence':fields.integer('Seq'),
        'param_name': fields.many2one('hr_gp.params_dict', 'Parameter name', ondelete='restrict', select=True),
        'title': fields.related('param_name','title', type='char', size= 32, string='Title', readonly=True),
        'entity_type': fields.related('param_name','entity_type',type='char', string='Type', readonly=True),
        'format': fields.related('param_name','format',type='char', string='Format', readonly=True),
        'category': fields.related('param_name','category',type='char', string='Category', readonly=True,),
        'base_formula': fields.related('param_name','base_formula',type='char', string='base formula', size = 48, readonly=True),
        'rate_formula': fields.related('param_name','rate_formula',type='char', string='rate formula', readonly=True),
        'qtye_formula': fields.related('param_name','qtye_formula',type='char', string='qtye formula', readonly=True),
        'ratr_formula': fields.related('param_name','ratr_formula',type='char', string='ratr formula', readonly=True),
        'qtyr_formula': fields.related('param_name','qtyr_formula',type='char', string='qtyr formula', readonly=True),
        'group_view': fields.related('param_name','group_view',type='char', string='', readonly=True),
        'inp': fields.char('Input', size = 64),
        'res_d': fields.date('ResultDe'),
        'res_t': fields.char('ResultTe', size = 64),
        'res_ne': fields.float('ResultNe', digits = (9,4)),
        'res_nr': fields.float('ResultNr', digits = (9,4)),
        'a_': fields.char('a_', size = 16),
        'b_': fields.char('b_', size = 16),
        'c_': fields.char('c_', size = 16),
        'd_': fields.char('d_', size = 16),
        'e_': fields.char('e_', size = 16),
        'f_': fields.char('f_', size = 16),
        'base': fields.float('Base', digits = (9,2)),
        'rate': fields.float('Rate employee', digits = (12,5)),
        'qtye': fields.float('Qty employee', digits = (9,2)),
        'basr': fields.float('Base employer', digits = (9,2)),
        'ratr': fields.float('Rate employer', digits = (12,5)),
        'qtyr': fields.float('Qty employer', digits = (9,2)),
        'registee': fields.float('Registee', digits = (9,2)),
        'register': fields.float('Register', digits = (9,2)),
        'val_e': fields.function(_calcval_e, type='float', digits = (9,2), string = 'Value num_e', method=True),
        'val_r': fields.function(_calcval_r, type='float', digits = (9,2), string = 'Value num_r', method=True),
        'val_sim_e': fields.float('Val simul', digits = (9,2)),
        'printable': fields.boolean('Print?'),
        'cumul': fields.boolean('Cum?'),
        'ddeb': fields.date('Date debut'),
        'dfin': fields.date('Date fin'),
        'baseprint': fields.char('Base print', size=28),
        'seqcalc': fields.integer('Seq calc'),
        'state': fields.selection(_get_states, 'State'),
        'group' : fields.related('param_name', 'group', type='selection', selection=[('JH','Jour / Heure'),('BRUT','Brut'),('COT','Cotisations'),('NET','Net'),('CUM','Cumuls')], string='Group', readonly=True),
        }
    _defaults = {
        'cumul': 'True',
        'state': 'draft',
    }
    _order = 'sequence'
    _constraints = [
        (_validexpr,"Incorrect value referring to params dict validation expression ",['inp'])
        ]

    def onchange_paramdict(self, cr, uid, ids, param_dict, context=None):
        paramdict = self.pool.get('hr_gp.params_dict').browse(cr, uid, [param_dict], context=None)[0]
        res={}
        res['title']= paramdict.title
        res['group']= paramdict.group
        res['category']= paramdict.category
        res['format']= paramdict.format
        res['entity_type']= paramdict.entity_type
        return {'value': res}
    
    def getAntecId(self, cr, uid, payline, lines=None, context={}):
        def makedictres(dictres, paylineid, paramcodeid, key, title):
            if lines :
                for cle, value in lines.items() :
                    if value == [paylineid, paramcodeid] :
                         dictres[key] = cle
            else :    
                crit = [('param_name.id',"=",paramcodeid)]
                crit.append(('pay_id','=',paylineid))
                idsearch = self.search(cr, uid, crit)
                rec1 = []
                if len(idsearch)>0:
                    rec1 = self.read(cr, uid, idsearch,fields=['id'],context=None)
                if len(rec1) > 0:
                    dictres[key] = rec1[0]['id']
            return dictres
        
        res = []
        dictres = {}
        dictres['id'] = payline.id
        param_codeid = False
        param_title = False
        param_entity_type = False
        if payline.param_name.category == "f":
            for op in ('a_', 'b_', 'c_', 'd_', 'e_', 'f_'):
                if op == "a_" : 
                        param_codeid = payline.param_name.a_.id
                        param_entity_type = payline.param_name.a_.entity_type
                        param_title = payline.param_name.a_.title
                elif op == "b_" : 
                        param_codeid = payline.param_name.b_.id
                        param_entity_type = payline.param_name.b_.entity_type
                        param_title = payline.param_name.b_.title
                elif op == "c_" : 
                        param_codeid = payline.param_name.c_.id
                        param_entity_type = payline.param_name.c_.entity_type
                        param_title = payline.param_name.c_.title
                elif op == "d_" : 
                        param_codeid = payline.param_name.d_.id
                        param_entity_type = payline.param_name.d_.entity_type
                        param_title = payline.param_name.d_.title
                elif op == "e_" : 
                        param_codeid = payline.param_name.e_.id
                        param_entity_type = payline.param_name.e_.entity_type
                        param_title = payline.param_name.e_.title
                elif op == "f_" : 
                        param_codeid = payline.param_name.f_.id
                        param_entity_type = payline.param_name.f_.entity_type
                        param_title = payline.param_name.f_.title
                if param_entity_type == 'pay':
                        dictres = makedictres(dictres, payline.pay_id.id, param_codeid, op, param_title)
                        
        numcounter = 0
        for counter in payline.param_name.epe_counter_add:
            if counter.entity_type == 'pay':
                numcounter += 1
                dictres = makedictres(dictres, payline.pay_id.id, counter.id, "rege_"+str(numcounter),counter.title)
        for counter in payline.param_name.epr_counter_add:
            if counter.entity_type == 'pay':
                numcounter += 1
                dictres = makedictres(dictres, payline.pay_id.id, counter.id, "regr_"+str(numcounter), counter.title)
        res.append(dictres)
        
        return res
            
    def diff_date_cal(self, cr, uid, ids, context={}):
        res = {}
        for rec in self.browse(cr, uid, ids, context=None):
            fldres = {}
            nbdays = datetime.strptime(rec.dfin,"%Y-%m-%d") - datetime.strptime(rec.ddeb,"%Y-%m-%d")
            fldres['inp'] = str(nbdays).split(" ")[0]
            res = self.write(cr, uid, ids, fldres, context=None)
        return True
        
    def diff_date_ouv(self, cr, uid, ids, context={}):
        res = {}
        (MON, TUE, WED, THU, FRI, SAT, SUN) = range(7)
        whichdays=(MON,TUE,WED,THU,FRI)
        for rec in self.browse(cr, uid, ids, context=None):
            fldres = {}
            start_date = datetime.strptime(rec.ddeb,"%Y-%m-%d")
            end_date = datetime.strptime(rec.dfin,"%Y-%m-%d")       
            delta_days = (end_date -start_date ).days + 1
            full_weeks, extra_days = divmod(delta_days, 7)
            # num_workdays = how many days/week you work * total # of weeks
            num_workdays = (full_weeks + 1) * len(whichdays)
            # subtract out any working days that fall in the 'shortened week'
            for d in range(1, 8 - extra_days):
                if (end_date + timedelta(d)).weekday() in whichdays:
                    num_workdays -= 1
            fldres['inp'] = str(num_workdays)               
            res = self.write(cr, uid, ids, fldres, context=None)
        return True
    
    def getvalfromcalendar(self, cr, uid, ids, context={}):
        res = {}
        for rec in self.browse(cr, uid, ids, context=None):
            sumcal = 0.00
            pool = pooler.get_pool(cr.dbname)
            cal_obj = pool.get('hr_gp.calendar')
            ddebpay = rec.pay_id.date_begin
            dfinpay = rec.pay_id.date_end
            crit = [('code','=',rec.param_name.id),('contractframe','=',rec.cttframe_name),('dat','>=',ddebpay),('dat','<=',dfinpay)]
            calid = cal_obj.search(cr, uid, crit)
            for cal in calid:
                recal = cal_obj.read(cr, uid, cal, fields=['qty'], context=None)
                sumcal += recal['qty']
            self.write(cr, uid, [rec.id],{'inp':sumcal}, context=None)
        return True
    

    
    #~ @timing        
    def calculate(self, cr, uid, ids, rec, buffer_lines=None, context={}):
        def tonumeric(str):
            try:
                return int(str)
            except ValueError:
                pass
            try:
                return float(str)
            except ValueError:
                return str
        def lookup(tablename, colkey, valkey, colres, oper, ddebpay, dfinpay):
            res = ""
            pool = pooler.get_pool(cr.dbname)
            tab_obj = pool.get('hr_gp.tablle')
            crit = [('name','=',tablename),('date_end','>=',ddebpay),]
            tabid = tab_obj.search(cr, uid, crit)
            if len(tabid) == 1: 
                res = tab_obj.lookup(cr, uid, tabid,[colkey,valkey,colres,oper])
            else : 
                if len(tabid) == 0:
                    raise osv.except_osv(u'Avertissement ', u'Impossible de trouver la table ' + tablename)
                else: 
                    raise osv.except_osv(u'Avertissement ', u'Plusieurs occurences applicables pour ' + tablename)

            return res
            
        def get_cum(param,entity_type,entity_id,year,monthfrom,monthto):
            res = 0.00
            pool = pooler.get_pool(cr.dbname)
            cum_obj = pool.get('hr_gp.cumann')
            crit = [('param_name',"=",param)]
            if entity_type == "ctt": crit.append(('contractframe_key','=',entity_id))
            elif entity_type == "act": crit.append(('activityframe_key','=',entity_id))
            elif entity_type == "emp": crit.append(('employee_key','=',entity_id))
            elif entity_type == "cny": crit.append(('company_key','=',entity_id))
            crit.append(('year_cum','=',year))
            reccum = cum_obj.read(cr, uid, cum_obj.search(cr, uid, crit),fields=['cum_an'],context=None)
            if reccum:
                tabcum = reccum[0]['cum_an'].split(";")
                for m in range(int(monthfrom) - 1, int(monthto)):
                    res += float(tabcum[m])
            return res
                
        def findendfunc(formul,idld):
            exp = formul[idld:len(formul)]
 
            fp = exp.find("(")
            func = exp[0:fp]
            if fp >= 0:
                z = exp[fp:len(exp)]
                nbparin = z.count("(")
                nbparout = z.count(")")
                p = 1
                i = 1
                while (p > 0) and (i < len(z)):
                    if z[i] == "(": p += 1
                    elif z[i] == ")": p -= 1
                    i +=1
                return i + fp - 1
            return -1
            
        def parse_formule (formule, a_, b_, c_, d_, e_, f_, pay_id, ddebpay, dfinpay, rectitle, cttkey, empkey, actkey, cnykey):
            dat_pay = datetime.strptime(ddebpay,"%Y-%m-%d")
            curr_year = dat_pay.year
            curr_month = dat_pay.month
            ddp_ = ddebpay
            dfp_ = dfinpay
            an_ = curr_year
            mo_ = curr_month
            nbf = 0
            for op in ("$lookup(","$func(","$get_cum(","$diffdat("):
                nbf += formule.count(op)
            if nbf > 0:
                idx = 0
                idl = [-1,-1,-1,-1]
                formulook = formule
                res= []
                lgf = len(formulook)
                while idx < lgf:
                    idl[0] = formulook.find("$lookup(",idx,lgf)
                    idl[1] = formulook.find("$func(",idx,lgf)
                    idl[2] = formulook.find("$get_cum(",idx,lgf)
                    idl[3] = formulook.find("$diffdat(",idx,lgf)
                    if min(idl) > -1: idld = min(idl)
                    else: idld = max(idl)
                    if idld > -1:
                        if idld > idx:
                            res.append(formulook[idx:idld])
                        idlf = findendfunc(formulook,idld)
                        if idlf > -1:
                            res.append(formulook[idld:idld+idlf+1])
                            idx = idld + idlf + 1
                    else:
                        res.append(formulook[idx:lgf])
                        idx = lgf
                        
                formul = ""
                for oper in res:
                    if oper[0:7] == "$lookup":
                        st1 = oper[8:len(oper)-1]
                        st2 = st1.split(";")
                        tabparam = []
                        for par in st2:
                            nbop = 0
                            for op in ("a_","b_","c_","d_","e_","f_","mo_","an_"):
                                nbop += par.count(op)
                            if nbop > 0:
                                try:
                                    pareval = eval(par)
                                except:
                                    raise osv.except_osv(u'Alert','Fail to evaluate table name '+par)
                            else:
                                pareval = par.strip()
                            tabparam.append(str(pareval))
                        z = lookup(str(tabparam[0]),int(str(tabparam[1])),str(tabparam[2]),int(str(tabparam[3])),str(tabparam[4]).strip(), ddebpay, dfinpay)
                        if not z: raise osv.except_osv(u'Alert', 'Value not found in table %s key %s ' % (tbname,valkey))
                        formul = formul + str(z)
                    elif oper[0:8] == "$get_cum":
                        st1 = oper[9:len(oper)-1]
                        st2 = st1.split(";")
                        tabparam = []
                        for par in st2:
                            nbop = 0
                            for op in ("a_","b_","c_","d_","e_","f_"):
                                nbop += par.count(op)
                            if nbop > 0: tabparam.append(str(eval(par)))
                            elif "an_" in par:
                                x = par.replace("an_",str(curr_year))
                                tabparam.append(str(eval(x)))
                            elif "mo_" in par:
                                x = par.replace("mo_",str(curr_month))
                                mo = eval(x)
                                if mo < 1: mo = 0
                                tabparam.append(str(mo))
                            else: tabparam.append(par)
                        if tabparam[1] == 'ctt': entitykey = cttkey
                        elif tabparam[1] == 'emp': entitykey = empkey
                        elif tabparam[1] == 'act': entitykey = actkey
                        elif tabparam[1] == 'cny': entitykey = cnykey
                        else: raise osv.except_osv(u'Alert',u'Incorrect parameter for get_cum' + tabparam[1])
                        z = get_cum(tabparam[0],tabparam[1],entitykey,tabparam[2],tabparam[3],tabparam[4])
                        formul = formul + str(z)
                    elif oper[0:8] == "$diffdat":
                        st1 = oper[9:len(oper)-1]
                        st2 = st1.split(";")
                        tabparam = []
                        for par in st2:
                            nbop = 0
                            for op in ("a_","b_","c_","d_","e_","f_"):
                                nbop += par.count(op)
                            if nbop > 0: tabparam.append(str(eval(par)))
                            elif "ddp_"in par:
                                x = par.replace("ddp_",str(ddp_))
                                tabparam.append(str(ddp_))
                            elif "dfp_"in par:
                                x = par.replace("dfp_",str(dfp_))
                                tabparam.append(str(dfp_))
                            else: tabparam.append(par)
                        nbdays = datetime.strptime(tabparam[1],"%Y-%m-%d") - datetime.strptime(tabparam[0],"%Y-%m-%d")
                        formul = formul + str(int(nbdays.days))
                    elif oper[0:5] == "$func":
                        st1 = oper[6:len(oper)-1]
                        st2 = st1.split(";")
                        funcname = st2[0]
                        del st2[0]
                        paramchain = ""
                        for par in st2:
                            nbop = 0
                            for op in ("a_","b_","c_","d_","e_","f_"):
                                nbop += par.count(op)
                            if nbop > 0: paramchain = paramchain + str(eval(par)) + ";"
                            else: paramchain = paramchain + par + ";"
                        funct = self.pool.get('hr_gp.functions_gp')
                        funct_id = funct.create(cr, uid,
                                {  'func_name': funcname,
                                   'description': 'Desc',
                                   'param_chain': paramchain,
                                   'payid': pay_id
                                 })
                        res_f = funct.compute(cr, uid, funct_id, context=None)
                        if unicode(res_f).count("ERR") > 0:
                            raise osv.except_osv(u'Avertissement', unicode(res_f))
                        else:
                            formul = formul + str(res_f)
                        funct.unlink(cr, uid,[funct_id], context=None)
                    else:
                        formul = formul + oper
                formule = formul.encode('ascii')
            try:    
                z = eval(formule)
                return z
            except :
                pass
            try :
                tmp = str(formule).replace('  ', '\t')
                tmp1 = str(tmp).replace('>>','\t')
                exec(tmp1) in locals()
                return resultat
            except :
                raise osv.except_osv(u'Avertissement ', u'Formule inexecutable \n' + formule + "\n" + rectitle)
                pass
            
             
        def calcres(rec, ddebpay, dfinpay):
            def is_number(s):
                if str(s).isdigit() and str(s)[0]=="0": return False
                try:
                    float(s)
                    return True
                except ValueError:
                    return False
            tmp ='0'
            res = {}
            if rec.a_ == False:
                a_ = 0.00
            else:
                if is_number(rec.a_): a_ = float(str(rec.a_).replace(",","."))
                else: a_ = str(rec.a_)
            if rec.b_ == False:
                b_ = 0.00
            else:
                if is_number(rec.b_): b_ = float(str(rec.b_).replace(",","."))
                else: b_ = str(rec.b_)
            if rec.c_ == False:
                c_ = 0.00
            else:
                if is_number(rec.c_): c_ = float(str(rec.c_).replace(",","."))
                else: c_ = str(rec.c_)
            if rec.d_ == False:
                d_ = 0.00
            else:
                if is_number(rec.d_): d_ = float(str(rec.d_).replace(",","."))
                else: d_ = str(rec.d_)
            if rec.e_ == False:
                e_ = 0.00
            else:
                if is_number(rec.e_): e_ = float(str(rec.e_).replace(",","."))
                else: e_ = str(rec.e_)
            if rec.f_ == False:
                f_ = 0.00
            else:
                if is_number(rec.f_): f_ = float(str(rec.f_).replace(",","."))
                else: f_ = str(rec.f_)
            if rec.registee == False:
                registee = 0.00
            else:
                registee = rec.registee
            if rec.register == False:
                register = 0.00
            else:
                register = rec.register 

            if rec.base_formula == False:
                res_base = 1.00
            else:
                res_base = parse_formule(rec.base_formula, a_, b_, c_, d_, e_, f_, rec.pay_id, ddebpay, dfinpay, rec.title, rec.cttframe_name, rec.employee_name, rec.actframe_name, rec.company_name)
            if rec.rate_formula == False:
                res_rate = 0.00
            else:
                res_rate = parse_formule(rec.rate_formula, a_, b_, c_, d_, e_, f_, rec.pay_id, ddebpay, dfinpay, rec.title, rec.cttframe_name, rec.employee_name, rec.actframe_name, rec.company_name)

            if rec.qtye_formula == False:
                res_qtye = 0.00
            else:
                res_qtye = parse_formule(rec.qtye_formula, a_, b_, c_, d_, e_, f_, rec.pay_id, ddebpay, dfinpay, rec.title, rec.cttframe_name, rec.employee_name, rec.actframe_name, rec.company_name)
            
            if rec.ratr_formula == False:
                res_ratr = 0.00
            else:
                res_ratr = parse_formule(rec.ratr_formula, a_, b_, c_, d_, e_, f_, rec.pay_id, ddebpay, dfinpay, rec.title, rec.cttframe_name, rec.employee_name, rec.actframe_name, rec.company_name)
            
            if rec.qtyr_formula == False:
                res_qtyr = 0.00
            else:
                res_qtyr = parse_formule(rec.qtyr_formula, a_, b_, c_, d_, e_, f_, rec.pay_id, ddebpay, dfinpay, rec.title, rec.cttframe_name, rec.employee_name, rec.actframe_name, rec.company_name)
                
            res_ne = 0.00
            res_nr = 0.00
            if rec.format =='n' :
                res_ne = round(res_base * res_rate * res_qtye,4)
                res_nr = round(res_base * res_ratr * res_qtyr,4)
                res['baseprint'] = "%10.2f" % (res_base)
            elif rec.format == 'd' :
                res['res_d'] = res_base
                res['baseprint'] = res_base
                res_base = 0 
            elif rec.format == 't':
                res['res_t'] = res_base
                res['baseprint'] = res_base
                res_base = 0
            res['res_ne'] = res_ne
            res['res_nr'] = res_nr
            res['base'] = res_base
            res['rate'] = res_rate
            res['qtye'] = res_qtye
            res['ratr'] = res_ratr
            res['qtyr'] = res_qtyr
            res['a_'] = a_
            res['b_'] = b_
            res['c_'] = c_
            res['d_'] = d_
            res['e_'] = e_
            res['f_'] = f_          
            return res
                 
        def getvalue(rec, name, ddeb, dfin):
            res = 0.00
            rec_codeid = 0
            if rec.param_name.category == "f":
                rec_entity_type = ""
                if name == "a_" and rec.param_name.a_.id:
                    rec_codeid = rec.param_name.a_.id
                    rec_entity_type = rec.param_name.a_.entity_type
                    rec_category = rec.param_name.a_.category
                    rec_format = rec.param_name.a_.format
                    rec_optional = rec.param_name.a_.optional
                    rec_defwhenopt = rec.param_name.a_.defwhenopt
                    par_name = rec.param_name.a_.name
                elif name == "b_" and rec.param_name.b_.id:
                    rec_codeid = rec.param_name.b_.id
                    rec_entity_type = rec.param_name.b_.entity_type
                    rec_category = rec.param_name.b_.category
                    rec_format = rec.param_name.b_.format
                    rec_optional = rec.param_name.b_.optional
                    rec_defwhenopt = rec.param_name.b_.defwhenopt
                    par_name = rec.param_name.b_.name
                elif name == "c_" and rec.param_name.c_.id:
                    rec_codeid = rec.param_name.c_.id
                    rec_entity_type = rec.param_name.c_.entity_type
                    rec_category = rec.param_name.c_.category
                    rec_format = rec.param_name.c_.format
                    rec_optional = rec.param_name.c_.optional
                    rec_defwhenopt = rec.param_name.c_.defwhenopt
                    par_name = rec.param_name.c_.name
                elif name == "d_" and rec.param_name.d_.id:
                    rec_codeid = rec.param_name.d_.id
                    rec_entity_type = rec.param_name.d_.entity_type
                    rec_category = rec.param_name.d_.category
                    rec_optional = rec.param_name.d_.optional
                    rec_defwhenopt = rec.param_name.d_.defwhenopt
                    rec_format = rec.param_name.d_.format
                    par_name = rec.param_name.d_.name
                elif name == "e_" and rec.param_name.e_.id:
                    rec_codeid = rec.param_name.e_.id
                    rec_entity_type = rec.param_name.e_.entity_type
                    rec_category = rec.param_name.e_.category
                    rec_format = rec.param_name.e_.format
                    rec_optional = rec.param_name.e_.optional
                    rec_defwhenopt = rec.param_name.e_.defwhenopt
                    par_name = rec.param_name.e_.name
                elif name == "f_" and rec.param_name.f_.id:
                    rec_codeid = rec.param_name.f_.id
                    rec_entity_type = rec.param_name.f_.entity_type
                    rec_category = rec.param_name.f_.category
                    rec_format = rec.param_name.f_.format
                    rec_optional = rec.param_name.f_.optional
                    rec_defwhenopt = rec.param_name.f_.defwhenopt
                    par_name = rec.param_name.f_.name
                else:
                    return res
                
            rec1=""
            if rec_entity_type == "pay" :
                if buffer_lines :
                    idsearch = []
                    for cle, value in buffer_lines.items() :
                        if value == [rec.pay_id.id, rec_codeid] :
                            idsearch.append(cle)
                else :
                    crit = [('param_name.id',"=",rec_codeid)]
                    crit.append(('pay_id.id','=',rec.pay_id.id))
                    idsearch = self.search(cr, uid, crit)
                
                if len(idsearch) == 1:
                    if rec_category == 'r' :
                        rec1 = self.read(cr, uid, idsearch,fields=['registee','register'],context=None)
                        res=rec1[0]['registee'] + rec1[0]['register']
                    else :  
                        rec1 = self.read(cr, uid, idsearch,fields=['res_ne','res_nr','res_d','res_t'],context=None)
                        
                        if rec_format == 'n':
                            if name in ('a_','b_','c_') : res=rec1[0]['res_ne']
                            elif name in ('d_','e_','f_') : res=rec1[0]['res_nr']
                            else: osv.except_osv('Avertissement ', 'Parametre name incorrect: ' + str(par_name))
                        elif rec_format == 't':
                            res=rec1[0]['res_t']
                        elif rec_format == 'd':
                            res=rec1[0]['res_d']
                        else: osv.except_osv(u'Avertissement ', u'Format incorrect: ' + str(par_name))
                else : 
                    if len(idsearch) == 0:
                        if rec_optional:
                            if rec_format == "n":res = float(rec_defwhenopt)
                            else: res = rec_defwhenopt
                        else:
                            raise osv.except_osv(u'Avertissement ', u'Impossible de determiner la valeur de ' + str(par_name) + 'dans la paie courante')
                    else:
                        raise osv.except_osv(u'Avertissement ', u'Plusieurs valeurs de ' + str(par_name) + 'dans la paie courante')
                    
            elif rec_entity_type in ["leg","ctt","emp","act","cny"] :
                pool = pooler.get_pool(cr.dbname)
                obj = pool.get('hr_gp.params_val')
                crit = ['&', ('param_name.id',"=",rec_codeid)]
                crit.append(('date_begin','<=',ddeb))
                crit.append(('date_end2','>=',dfin))
                if rec_entity_type == "leg": crit.append(('legalframe_key','=',rec.legframe_name))
                elif rec_entity_type == "ctt": crit.append(('contractframe_key','=',rec.cttframe_name))
                elif rec_entity_type == "act": 
                    crit.append('|')
                    crit.append('|')
                    crit.append(('activityframe_key','=',rec.pay_id.ctt_id.activity.id))
                    crit.append(('activityframe_key','=',rec.pay_id.ctt_id.convention.id))
                    crit.append(('activityframe_key','=',rec.pay_id.ctt_id.establishment.id))
                elif rec_entity_type == "emp": crit.append(('employee_key','=',rec.employee_name))
                elif rec_entity_type == "cny": crit.append(('company_key','=',rec.company_name))
                
                val_ids=obj.search(cr, uid, crit)
                if val_ids[0] in buffer_val.keys() :
                    rec1 = buffer_val[val_ids[0]]
                else :
                    rec1 = obj.read(cr, uid, val_ids,fields=['res_n','res_d','res_t2'],context=None)
                    buffer_val[val_ids[0]] = rec1

                if len(rec1) == 1:
                    if rec_format == 'n': res=rec1[0]['res_n']
                    elif rec_format == 'd': res=rec1[0]['res_d']
                    elif rec_format == 't': res=str(rec1[0]['res_t2'])
                    else: raise osv.except_osv('Avertissement ', u'Format parametre incorrect: ' + str(par_name))
                else : 
                    if len(rec1) == 0:
                        if rec_optional:
                            if rec_format == "n": res = float(rec_defwhenopt)
                            else: res =  rec_defwhenopt
                        else:
                            raise osv.except_osv(u'Avertissement ', u'Impossible de determiner la valeur du parametre ' + str(par_name) + ' pour periode ' + ddeb + ' > ' + dfin)
                    else:
                        raise osv.except_osv(u'Avertissement ',u'Plusieurs valeurs du parametre ' + str(par_name) + u' pour periode ' + ddeb + ' > ' + dfin)
                
            else:
                if rec_codeid > 0 : raise osv.except_osv(u'Avertissement ', u'Parametre incorrect: ' + str(par_name))
                res = 0.00
            return res
        

###################### Debut fonction calculate #################################################               
        
        res={}
        if rec.category == 'r':
            rec = self.browse(cr, uid, ids)[0]

        for i_test_onsenfout in [1] :
            ddebpay = rec.pay_id.date_begin
            dfinpay = rec.pay_id.date_end
            fldres = {}
            simul = False
            if rec.val_sim_e:
                if rec.val_sim_e != 0.00:
                    simul = True
            if simul:
                fldres['res_ne'] = rec.val_sim_e
                rec.res_ne =  fldres['res_ne']
                res = self.write(cr, uid, ids, fldres, context=None)
            else:
                if rec.category == 'v':
                    fldres['res_ne'] = ""
                    if rec.inp:
                        if rec.format == 'n': 
                            fldres['res_ne'] = round(float(str(rec.inp).replace(",",".")),2)
                            if rec.ddeb:
                                dd = datetime.strftime(datetime.strptime(rec.ddeb,"%Y-%m-%d"),"%d/%m/%Y")
                                df = datetime.strftime(datetime.strptime(rec.dfin,"%Y-%m-%d"),"%d/%m/%Y")
                                fldres['baseprint'] = "du %s au %s" % (dd,df)
                            else:
                                fldres['baseprint'] = "%5.2f" % (fldres['res_ne'])
                        elif rec.format == 't':
                            fldres['res_t'] = str(rec.inp)
                            rec.res_t = fldres['res_t']
                            fldres['baseprint'] = fldres['res_t']
                        elif rec.format == 'd':
                            fldres['res_d'] = datetime.strptime(str(rec.inp),"%d/%m/%Y")
                            rec.res_d = fldres['res_d']
                            fldres['baseprint'] = datetime.strftime(fldres['res_d'],"%d/%m/%Y")
                        rec.baseprint = fldres['baseprint']
                    else :
                        fldres['res_ne'] = 0.0  
                    rec.res_ne =  fldres['res_ne']
                    res = self.write(cr, uid, ids, fldres, context=None)    
                    
                    
                elif rec.category == 'f':
                    
                    fldres = {}
                    for fields in ('a_', 'b_', 'c_','d_','e_','f_'):
                        fldres[fields] = getvalue(rec, fields, ddebpay, dfinpay)
                    
                    rec.a_ = fldres['a_']
                    rec.b_ = fldres['b_']
                    rec.c_ = fldres['c_']
                    rec.d_ = fldres['d_']
                    rec.e_ = fldres['e_']
                    rec.f_ = fldres['f_']
                    resultats = {}
                    resultats = calcres(rec, ddebpay, dfinpay)
                    rec.res_ne =  resultats['res_ne']  
                    rec.res_nr =  resultats['res_nr']
                    res = self.write(cr, uid, ids, resultats, context=None)
                    
                    
            for counter in rec.param_name.epe_counter_add :
                if counter.entity_type == "pay":
                    add = rec.res_ne + rec.registee
                    if add != 0 : 
                        cr.execute('UPDATE hr_gp_payslip_line SET registee=(registee + %s) WHERE pay_id=%s AND param_name=%s' %(add, rec.pay_id.id, counter.id))
                    """crit = [('pay_id.id',"=",rec.pay_id.id),('param_name.id','=',counter.id)]
                    listIdsCrit = self.search(cr, uid, crit)
                    if not listIdsCrit: raise osv.except_osv(u'Alert', u"Missing register " + counter.name)
                    for line in self.browse(cr, uid, listIdsCrit, context=None):
                        line.registee = line.registee + rec.res_ne + rec.registee
                        self.write(cr, uid, [line.id], {'registee' : line.registee}, context=None)"""
            
            for counter in rec.param_name.epr_counter_add :
                if counter.entity_type == "pay":
                    add = rec.res_nr + rec.register
                    if add != 0 :
                        cr.execute('UPDATE hr_gp_payslip_line SET register=(register + %s) WHERE pay_id=%s AND param_name=%s' %(add, rec.pay_id.id, counter.id))
                    """crit = [('pay_id.id',"=",rec.pay_id.id),('param_name.id','=',counter.id)]
                    listIdsCrit = self.search(cr, uid, crit)
                    if not listIdsCrit: raise osv.except_osv(u'Alert', u"Missing register " + counter.name)
                    for line in self.browse(cr, uid, listIdsCrit, context=None):
                        line.register = line.register + rec.res_nr + rec.register
                        self.write(cr, uid, [line.id], {'register' : line.register}, context=None)"""
             
        return True
    
hr_gp_payslip_line() 
    
class hr_gp_param_model_item(osv.osv):
    _name = 'hr_gp.param_model_item'
    _description = 'Params model items'
    _columns = {
        'model_id': fields.many2one('hr_gp.param_model'),
        'sequence': fields.integer('Sequence'),
        'params': fields.many2one('hr_gp.params_dict','name'),
        'name': fields.related('params','name', type='char', string='Dictionnary', readonly=True),
        'category': fields.related('params','category', type='char', string='Category', store=False, readonly=True),
        'printable': fields.boolean('Printable'),
        'input' : fields.char('Input', size = 64),
    }
    _order = 'sequence ASC'
hr_gp_param_model_item()



class hr_gp_cumann(osv.osv):
    def _monthcum(self, cr, uid, ids, name, args, context=None):
        res = {}
        for cum in self.browse(cr, uid, ids, context=None):
            tabcum = cum.cum_an.split(";")
            res[cum.id]={}
            totyear = 0.00
            for month in range(0,12):
                res[cum.id].update({'mo'+str(month+1):float(tabcum[month])})
                totyear += float(tabcum[month])
            res[cum.id].update({'moan':totyear})
        return res
    _name = 'hr_gp.cumann'
    _description = 'Register annual cumuls for entities'
    _columns = {
        'name': fields.char('Name bidon',size= 12),
        'year_cum': fields.integer('year'),
        'param_name': fields.many2one('hr_gp.params_dict','Param name'),
        'activityframe_key': fields.many2one('hr_gp.activity','Activityframe_id'),
        'contractframe_key': fields.many2one('hr_gp.contractframe','Contractframe_id'),
        'employee_key': fields.many2one('hr.employee','Employee_id'),
        'company_key': fields.many2one('hr_gp.company','Company_id'),
        'title': fields.related('param_name','title',type='char', string='Title', readonly=True),
        'cum_an': fields.char('Cumuls',size=150),
        'last_update': fields.date('Last update'),
        'mo1': fields.function(_monthcum, type='float',digits = (9,2), string = '01', method=True, multi='mo'),
        'mo2': fields.function(_monthcum, type='float',digits = (9,2), string = '02', method=True, multi='mo'),
        'mo3': fields.function(_monthcum, type='float',digits = (9,2), string = '03', method=True, multi='mo'),
        'mo4': fields.function(_monthcum, type='float',digits = (9,2), string = '04', method=True, multi='mo'),
        'mo5': fields.function(_monthcum, type='float',digits = (9,2), string = '05', method=True, multi='mo'),
        'mo6': fields.function(_monthcum, type='float',digits = (9,2), string = '06', method=True, multi='mo'),
        'mo7': fields.function(_monthcum, type='float',digits = (9,2), string = '07', method=True, multi='mo'),
        'mo8': fields.function(_monthcum, type='float',digits = (9,2), string = '08', method=True, multi='mo'),
        'mo9': fields.function(_monthcum, type='float',digits = (9,2), string = '09', method=True, multi='mo'),
        'mo10': fields.function(_monthcum, type='float',digits = (9,2), string = '10', method=True, multi='mo'),
        'mo11': fields.function(_monthcum, type='float',digits = (9,2), string = '11', method=True, multi='mo'),
        'mo12': fields.function(_monthcum, type='float',digits = (9,2), string = '12', method=True, multi='mo'),
        'moan': fields.function(_monthcum, type='float',digits = (9,2), string = 'Tot. year', method=True, multi='mo'),
    }
        
hr_gp_cumann()  

class hr_gp_calendar(osv.osv):
    _name = 'hr_gp.calendar'
    _description = 'Calendar for contract'
    _columns = {
        'name': fields.char('Description',size=16),
        'dat': fields.date('Date'),
        'contractframe': fields.many2one('hr_gp.contractframe','Contractframe Id'),
        'employee_name': fields.related('contractframe','employee_id','name', string='Employee name', type="char"),
        'code': fields.many2one('hr_gp.params_dict','Param code'),
        'qty': fields.float('Qty',digits=(4,2)),
    }
    _defaults = {
        'qty': 8.0
    }
    
hr_gp_calendar()

class hr_gp_accline(osv.osv):
    _name = 'hr_gp.accline'
    _description = 'Account move line for payslip'
    _columns = {
        'name': fields.char('Description',size=16),
        'acc_id': fields.many2one('account.account','Account'),
        'anal_acc_id': fields.many2one('account.analytic.account','Analytic acc'),
        'acc_cod': fields.related('acc_id','code',string='Account code', type="char"),
        'pay_id': fields.many2one('hr_gp.payslip','Ref payslip'),
        'amount_d': fields.float('Debit',digits=(9,2)),
        'amount_c': fields.float('Credit',digits=(9,2)),
        'state': fields.char('State',size=15),
        'moved': fields.boolean('Moved')
    }
    
hr_gp_accline()


class hr_gp_logpay(osv.osv):
    _name = 'hr_gp.logpay'
    _description = 'Logging calc payslip'
    _columns = {
        'name': fields.char('Description',size=16),
        'dat': fields.datetime('Date'),
        'pay_id': fields.many2one('hr_gp.payslip','Ref payslip'),
        'log': fields.text('Log')
    }
    
hr_gp_logpay()

class res_partner(osv.osv):
    _name = "res.partner"
    _inherit = "res.partner"

    _columns = {
        'siret_p': fields.char('SIRET', size=50),
        'naf': fields.char('NAF', size=50),
        'org_cotis': fields.many2many('hr_gp.org_cotis',string='Organisme de cotisation'),
        'org_cotis2': fields.many2one('hr_gp.org_cotis',string='Organisme de cotisation'),
        'n_affil': fields.char('N° d\'affiliation', size=50),
        'conv_coll': fields.char('Convention collective', size=50),
    }
    
res_partner()

class hr_gp_org_cotis_group(osv.osv):
    _name="hr_gp.org_cotis_group"
    
    _columns = {
        'name': fields.char('Intitulé',size=100),
        'code': fields.char('Code',size=10),
        'org_cotis_ids': fields.one2many('hr_gp.org_cotis','groupe',string='Organismes de cotisation'),
    }
hr_gp_org_cotis_group()

class hr_gp_org_cotis(osv.osv):
    _name="hr_gp.org_cotis"
    _description="Organismes"
    _columns = {
        'name': fields.char('Intitulé',size=16),
        'name_long': fields.char('Intitulé complet',size=250),
        'sous_titre': fields.char('Sous-titre',size=250),
        'code': fields.char('Code',size=10),
        'code_org': fields.char('Code organisme',size=10),
        'groupe': fields.many2one('hr_gp.org_cotis_group','Groupe'),
        'ducs': fields.many2many('hr_gp.ducs',string='Ducs'),
        'n_affil':fields.char('N° d\'affiliation', size=50),
        'siret': fields.char('SIRET', size=50),
        'contact': fields.char('Contact', size=128),
        'street': fields.char('Adresse', size=128),
        'street2': fields.char('Adresse (suite)', size=128),
        'zip': fields.char('Code postal', change_default=True, size=24),
        'city': fields.char('Commune', size=128),
        'email': fields.char('E-Mail', size=240),
        'phone': fields.char('Téléphone', size=64),
        'fax': fields.char('Fax', size=64),
        'mobile': fields.char('Téléphone portable', size=64),
        'exi_date': fields.selection([('debut','Début de mois'),('fin','Fin de mois'),('suivant','Mois suivant'),('non','Non imprimable')],'Date exigibilité'),
        'exi_deca': fields.integer('Décalage exigibilité',digits=2),
        'depot_date': fields.selection([('debut','Début de mois'),('fin','Fin de mois'),('suivant','Mois suivant'),('non','Non imprimable')],'Date limite de dépôt'),
        'depot_deca': fields.integer('Décalage limite de dépôt',digits=2),
        'paie_date': fields.selection([('debut','Début de mois'),('fin','Fin de mois'),('suivant','Mois suivant'),('non','Non imprimable')],'Date paiement'),
        'paie_deca': fields.integer('Décalage paiement',digits=2),
        'vers_date': fields.selection([('debut','Début de mois'),('fin','Fin de mois'),('suivant','Mois suivant'),('non','Non imprimable')],'Date versement'),
        'vers_deca': fields.integer('Décalage versement',digits=2),
    }
    
    _defaults = {
        'exi_date':'non',
        'depot_date':'non',
        'paie_date':'non',
        'vers_date':'non',
    }
    
hr_gp_org_cotis()

class hr_gp_ducs(osv.osv):
    _name="hr_gp.ducs"
    
    def name_get(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if not len(ids):
            return []
        res = [(r['id'], r['code'] or ' ' + ' ' + r['name'] or ' ') for r in self.read(cr, uid, ids, ['code','name'], context)]
        return res
    
    _columns={
        'name': fields.char('Nom',size=50),
        'code': fields.char('Code',size=10),
    }
    
hr_gp_ducs()

class hr_gp_dadsu_group(osv.osv):
    _name="hr_gp.dadsu_group"
    
    _columns={
        'name': fields.char('Nom',size=200),
        'code': fields.char('Code',size=64),
        'dadsu_ids': fields.one2many('hr_gp.dadsu_code','dadsu_group',string='DADSUS'),
    }
    
hr_gp_dadsu_group()

class hr_gp_dadsu_cont(osv.osv):
    _name="hr_gp.dadsu_cont"
    
    _columns={
        
        'name': fields.char('Titre'),
        'company_id': fields.many2one('res.company','Société'),
        'dadsu_param_ids': fields.one2many('hr_gp.dadsu_params','cont_id',string='Paramètres')
    }
    
hr_gp_dadsu_cont()

class hr_gp_dadsu_params(osv.osv):
    _name="hr_gp.dadsu_params"
    
    _columns={
        
        'dadsu_id': fields.many2one('hr_gp.dadsu_code','Code DADSU'),
        'param_id': fields.many2one('hr_gp.params_dict','Paramètre'),
        'cont_id': fields.many2one('hr_gp.dadsu_cont','Container'),
        'operateur': fields.selection([('moins','-'),('plus','+')],string='Opérateur')
    }
    
hr_gp_dadsu_params()

class hr_gp_dadsu_code(osv.osv):
    _name="hr_gp.dadsu_code"
    
    def name_get(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if not len(ids):
            return []
        res = [(r['id'], r['code'] or ' ' + ' ' + r['name'] or ' ') for r in self.read(cr, uid, ids, ['code','name'], context)]
        return res
    
    _columns={
        'name': fields.char('Nom',size=200),
        'code': fields.char('Code',size=64),
        'dadsu_group': fields.many2one('hr_gp.dadsu_group','Groupe'),
    }
    
hr_gp_dadsu_code()


class en_construction(osv.osv):
    _name="en.construction"
    
    _columns={
        'name': fields.char('Nom',size=50),
    }
    
en_construction()

class module(osv.osv):
    _inherit = "ir.module.module"
    
    def _get_icon2_image(self, cr, uid, ids, field_name=None, arg=None, context=None):
        res = dict.fromkeys(ids, '')
        for module in self.browse(cr, uid, ids, context=context):
            path = addons.get_module_resource(module.name, 'static', 'src', 'img', 'icon2.png')
            if path:
                image_file = tools.file_open(path, 'rb')
                try:
                    res[module.id] = image_file.read().encode('base64')
                finally:
                    image_file.close()
        return res

    _columns = {
        'icon2': fields.char('Icon URL', size=128),
        'icon2_image': fields.function(_get_icon2_image, string='Image', type="binary"),
    }

module()
