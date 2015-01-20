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

from osv import osv
from osv import fields
from datetime import datetime, timedelta, date

class create_model_wizard(osv.osv_memory):
    _name='hr_gp.create.model.wizard'
    
    _columns= {
               'name': fields.char('Model name', size=32),
               'description': fields.char('Description', size=256),
    }

    def _default_get_session(self,cr,uid, ids, context=None):
        if not context :
            return False
        if 'active_id' in context :
            return context.get('active_id')
    
    def action_create_model(self, cr, uid, ids, context=None):
        if not context.get('active_model', False) :
            return False
        wizard=self.browse(cr, uid, ids[0], context=context)

        # creation du model 
        tabcod={'hr_gp.contractframe':u'ctt',
                'hr.employee':u'emp',
                'hr_gp.activity':u'act',
                'hr_gp.legal_frame':u'leg',
                'hr_gp.payslip':u'pay',
                'hr_gp.company':u'cny'}
        model = self.pool.get('hr_gp.param_model')
        model_id = model.create(cr, uid,
                                    { 'name': wizard.name,
                                     'descr' : wizard.description,
                                     'entity_type' : tabcod[context.get('active_model')],
                                     })

        #Creation des items du model
        item = self.pool.get('hr_gp.param_model_item')
        ref_obj = self.pool.get(context.get('active_model'))
        for obj in ref_obj.browse(cr, uid, context.get('active_ids'), context=None):
            if tabcod[context.get('active_model')] == 'pay' : lines = obj.payslip_lines
            else : lines = obj.params
            
            for line in lines:
                save ={}
                save['params'] = line.param_name.id
                save['model_id'] = model_id
                if tabcod[context.get('active_model')] == 'pay' : 
                   save['sequence'] = line.sequence
                   save['printable'] = line.printable
                else :
                    save['input'] = line.inp
                           
                item.create(cr, uid, save)
            
        return {'type':'ir.actions.act_window_close'}

create_model_wizard()


class import_model_wizard(osv.osv_memory):
    _name='hr_gp.import.model.wizard'

    def _get_models(self, cr, uid, context=None):
        if not context.get('active_model', False) :
            return False
        retour = []
        tabcod={'hr_gp.contractframe':u'ctt',
            'hr.employee':u'emp',
            'hr_gp.activity':u'act',
            'hr_gp.legal_frame':u'leg',
            'hr_gp.payslip':u'pay',
            'hr_gp.company':u'cny'}
        param_entity_cod = tabcod[context.get('active_model')]
        model_obj = self.pool.get('hr_gp.param_model')
        models_ids = model_obj.search(cr, uid, [('entity_type','=',param_entity_cod)])        
        for model in model_obj.browse(cr, uid, models_ids, context=None):
            retour.append((model.id, model.name));
        
        return retour
    
    _columns= {
         'models_list': fields.selection(_get_models,'Models list'),
    }

    def _default_get_session(self,cr,uid, ids, context=None):
        if not context :
            return False
        if 'active_id' in context :
            return context.get('active_id')
    
    def action_import_model(self, cr, uid, ids, context=None):
        
        wizard_obj=self.browse(cr, uid, ids[0], context=context)
        model_obj = self.pool.get('hr_gp.param_model')
        payslip_line_obj = self.pool.get('hr_gp.payslip_line')
        paramsval_obj = self.pool.get('hr_gp.params_val')
        save ={}
        
        tabkey={'hr_gp.contractframe':u'contractframe_key',
            'hr.employee':u'employee_key',
            'hr_gp.activity':u'activityframe_key',
            'hr_gp.legal_frame':u'legalframe_key',
            'hr_gp.payslip':u'pay_id',
            'hr_gp.company':u'company_key'}
        
        
        if tabkey[context.get('active_model')] == 'pay_id' : line_obj = payslip_line_obj
        else : line_obj = paramsval_obj
        
        #Suppression des lignes présentes Si c'est une paye
        if tabkey[context.get('active_model')] == 'pay_id' :
            unlink_ids = line_obj.search(cr, uid, [(tabkey[context.get('active_model')], '=', context.get('active_id'))]) 
            line_obj.unlink(cr, uid, unlink_ids, context=None)
        
        #sinon "fermeture" des dates pour les valeurs ACTIVES et PRESENTENT dans le modèle 
        else :    
            for model in model_obj.browse(cr, uid, [int(wizard_obj.models_list)], context=None):
                for item in model.params:
                    ferme_ids = line_obj.search(cr, uid, [(tabkey[context.get('active_model')], '=', context.get('active_id')),('param_name', '=', item.params.id),('date_end2', '>=', model.date_effet)]) 
                    line_obj.write(cr, uid, ferme_ids, {'date_end' : model.date_effet}, context=None)


        #Remplacement par le model
        relation = tabkey[context.get('active_model')]
        for model in model_obj.browse(cr, uid, [int(wizard_obj.models_list)], context=None):
            for item in model.params:
                save.clear()
                save['param_name'] = item.params.id
                save[relation]= context.get('active_id')
                
                if tabkey[context.get('active_model')] == 'pay_id' :
                    save['sequence']= item.sequence
                    save['printable']= item.printable
                else :
                    save['inp'] = item.input
                    save['date_begin'] = model.date_effet

                line_obj.create(cr, uid, save)
               
        return {'type':'ir.actions.act_window_close'}
    
import_model_wizard()    
