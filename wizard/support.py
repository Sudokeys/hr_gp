# -*- coding: utf-8 -*-

import base64
from osv import fields,osv
import tools
import time
from xml.dom import minidom
import re


class hr_gp_support_export(osv.osv_memory):
    
    _name = "hr_gp.support_export"
    _description = "Exporter vos parametres de paye"
    _columns = {
                'dictionary' : fields.boolean('Dictionnaire', required=False),
                'model' : fields.boolean('Modèles', required=False),
                'ducs' : fields.boolean('DUCS', required=False),
                'org_cotis' : fields.boolean('Organismes', required=False),
                'data': fields.binary('File', readonly=True),
                'name': fields.char('Filename', 64, readonly=True),
                'state': fields.selection( ( ('choose','choose'), ('get','get'),) ),
                }
    
    def create_export(self,cr,uid,ids,context={}):
        this = self.browse(cr, uid, ids)[0]
        doc = minidom.Document()
        xml = doc.createElement("hr_gp_support")
        doc.appendChild(xml)
        
        if this.ducs :
            ducs_obj = self.pool.get('hr_gp.ducs')
            ducs_ids = ducs_obj.search(cr, uid, [])
            xml_ducs_list = doc.createElement("code_ducs_list")
            for ducs_id in ducs_ids :
                ducs = ducs_obj.browse(cr, uid, ducs_id) 
                xml_ducs = doc.createElement("code_ducs")
            
                data = ducs_obj.export_data(cr, uid, [ducs_id], ducs_obj._columns )
                colonnes = ducs_obj._columns
                
                for i in range(len(colonnes)) :
                    xml_entree = doc.createElement(colonnes.keys()[i])
                    valeurtxt = (u"%s" %data['datas'][0][i])
                    value = doc.createTextNode(valeurtxt)
                    xml_entree.appendChild(value)
                    xml_ducs.appendChild(xml_entree)
                                        
                xml_ducs_list.appendChild(xml_ducs)
            xml.appendChild(xml_ducs_list)
        
        if this.org_cotis :
            org_obj = self.pool.get('hr_gp.org_cotis')
            group_obj = self.pool.get('hr_gp.org_cotis_group')
            
            group_ids = group_obj.search(cr, uid, [('name', '!=', False)])
            xml_group_list = doc.createElement("group_list")
            for group_id in group_ids :
                group = group_obj.browse(cr, uid, group_id) 
                xml_group = doc.createElement("group")

                xml_entree = doc.createElement('name')
                xml_entree.appendChild(doc.createTextNode(group.name))
                xml_group.appendChild(xml_entree)

                xml_entree = doc.createElement('code')
                xml_entree.appendChild(doc.createTextNode(group.code))
                xml_group.appendChild(xml_entree)
            
                xml_orgs = doc.createElement('orgs')
                for org_id in org_obj.search(cr, uid, [('groupe', '=', group.id)]) :
                    xml_org = doc.createElement('org')
                    
                    data = org_obj.export_data(cr, uid, [org_id], org_obj._columns )
                    colonnes = org_obj._columns
                
                    for i in range(len(colonnes)) :
                        xml_entree = doc.createElement(colonnes.keys()[i])
                        valeurtxt = (u"%s" %data['datas'][0][i])
                        value = doc.createTextNode(valeurtxt)
                        xml_entree.appendChild(value)
                        xml_org.appendChild(xml_entree)
                        
                    xml_orgs.appendChild(xml_org)

                xml_group.appendChild(xml_orgs)
                xml_group_list.appendChild(xml_group)
                
            xml.appendChild(xml_group_list)

        if this.dictionary :
            dict_obj = self.pool.get('hr_gp.params_dict')
            dict_ids = dict_obj.search(cr, uid, [])
            xml_dict_list = doc.createElement("params_dict_list")
            for dict_id in dict_ids :
                dict = dict_obj.browse(cr, uid, dict_id) 
                xml_dict = doc.createElement("params_dict")
            
                data = dict_obj.export_data(cr, uid, [dict_id], dict_obj._columns )
                colonnes = dict_obj._columns
                
                for i in range(len(colonnes)) :
                    xml_entree = doc.createElement(colonnes.keys()[i])
                    valeurtxt = (u"%s" %data['datas'][0][i])
                    value = doc.createTextNode(valeurtxt)
                    xml_entree.appendChild(value)
                    xml_dict.appendChild(xml_entree)
                                        
                xml_dict_list.appendChild(xml_dict)
            xml.appendChild(xml_dict_list)

        if this.model :
            model_obj = self.pool.get('hr_gp.param_model')
            item_obj = self.pool.get('hr_gp.param_model_item')
            
            model_ids = model_obj.search(cr, uid, [('active', '=', True)])
            xml_model_list = doc.createElement("model_list")
            for model_id in model_ids :
                model = model_obj.browse(cr, uid, model_id) 
                xml_model = doc.createElement("model")

                xml_entree = doc.createElement('name')
                xml_entree.appendChild(doc.createTextNode(model.name))
                xml_model.appendChild(xml_entree)

                xml_entree = doc.createElement('entity_type')
                xml_entree.appendChild(doc.createTextNode(model.entity_type))
                xml_model.appendChild(xml_entree)
            
                xml_entree = doc.createElement('date_effet')
                xml_entree.appendChild(doc.createTextNode(model.date_effet))
                xml_model.appendChild(xml_entree)
            
                xml_entree = doc.createElement('descr')
                xml_entree.appendChild(doc.createTextNode("%s" %model.descr))
                xml_model.appendChild(xml_entree)
            
                xml_items = doc.createElement('items')
                for item_id in item_obj.search(cr, uid, [('model_id', '=', model.id)]) :
                    xml_item = doc.createElement('item')
                    
                    data = item_obj.export_data(cr, uid, [item_id], item_obj._columns )
                    colonnes = item_obj._columns
                
                    for i in range(len(colonnes)) :
                        xml_entree = doc.createElement(colonnes.keys()[i])
                        valeurtxt = (u"%s" %data['datas'][0][i])
                        value = doc.createTextNode(valeurtxt)
                        xml_entree.appendChild(value)
                        xml_item.appendChild(xml_entree)
                        
                    xml_items.appendChild(xml_item)

                xml_model.appendChild(xml_items)
                xml_model_list.appendChild(xml_model)
                
            xml.appendChild(xml_model_list)
        pretty_text = doc.toprettyxml().encode("utf-8")
        fix = re.compile(r'((?<=>)(\n[\t]*)(?=[^<\t]))|(?<=[^>\t])(\n[\t]*)(?=<)')
        fixed_output = re.sub(fix, '', pretty_text)
        out=base64.b64encode(fixed_output)
        self.write(cr, uid, ids, {'state':'get', 'data':out, 'name':"paie_%s.xml" %(time.strftime("%Y-%m-%d")) }, context=context)
        return {
         'type': 'ir.actions.act_window',
         'name': "Export",
         'res_model': 'hr_gp.support_export',
         'res_id': ids[0],
         'view_type': 'form',
         'view_mode': 'form',
         'view_id': False,
         'target': 'new',
         'nodestroy': True,
           }
        
    _defaults = { 
                 'state': lambda *a: 'choose',
                 'dictionary' : True,
                 'model' : True,
                 'ducs' : True,
                 'org_cotis' : True,
                }
hr_gp_support_export()



class hr_gp_support_import(osv.osv_memory):
    
    _name = "hr_gp.support_import"
    _description = "Importer des parametres de paye"
    _columns = {
                'data': fields.binary('File', filters='*.xml' ),
                }
    
    def create_import(self,cr,uid,ids,context={}):
        this = self.browse(cr, uid, ids)[0]
        xml = base64.decodestring(this.data)
        doc = minidom.parseString(xml)
        dict_obj = self.pool.get('hr_gp.params_dict')
        ducs_obj = self.pool.get('hr_gp.ducs')
        org_cotis_obj = self.pool.get('hr_gp.org_cotis')
        org_cotis_group_obj = self.pool.get('hr_gp.org_cotis_group')

        #Il y a des ducs dans le fichier
        if doc.getElementsByTagName('code_ducs_list') :
            ducs_list = doc.getElementsByTagName('code_ducs_list')[0]
            
            #premier balayage pour créer les ducs manquant 
            for ducs in ducs_list.childNodes :
                if ducs.nodeType == minidom.Node.ELEMENT_NODE :
                    code = ducs.getElementsByTagName('code')[0].firstChild.data
                    name = ducs.getElementsByTagName('name')[0].firstChild.data
                    id = ducs_obj.search(cr, uid, [('code', '=', code)])
                    if not id : ducs_obj.create(cr, uid, {'code' : code,'name':name}) 
        
        #Il y a des organismes à importer
        if doc.getElementsByTagName('group_list') :
            xml_list = doc.getElementsByTagName('group_list')[0]
           
            
            for xml_group in xml_list.childNodes :
                if xml_group.nodeType == minidom.Node.ELEMENT_NODE :
                    update = {}
                    group_id = org_cotis_group_obj.create(cr, uid, {})
                    for colonne in xml_group.childNodes :
                        if colonne.nodeType == minidom.Node.ELEMENT_NODE :
                            if colonne.nodeName == 'orgs' :
                               #création des orgs du group
                               for org in colonne.childNodes :
                                   if org.nodeType == minidom.Node.ELEMENT_NODE :
                                      create_org = {} 
                                      for org_colonne in org.childNodes :
                                          if org_colonne.nodeType == minidom.Node.ELEMENT_NODE :
                                              if org_colonne.nodeName=='groupe': 
                                                  create_org['groupe'] = group_id
                                              elif org_colonne.nodeName=='ducs': 
                                                  #if not org_colonne.firstChild.data == 'False' : create_org[org_colonne.nodeName] = ducs_obj.search(cr, uid, [('name', '=', org_colonne.firstChild.data)])[0]
                                                  if not org_colonne.firstChild.data == 'False' :
                                                        liaisons = org_colonne.firstChild.data.split(',')
                                                        liaison_ids = []
                                                        for liaison in liaisons :
                                                            liaison_ids.append(ducs_obj.search(cr, uid, [('code', '=', liaison)])[0])
                                                        create_org[org_colonne.nodeName] = [(6, 0, liaison_ids)]
                                              elif org_colonne.nodeName in ('exi_date','depot_date','paie_date','vers_date'): 
                                                  if org_colonne.firstChild.data == 'Début de mois':
                                                      create_org[org_colonne.nodeName] = 'debut'
                                                  if org_colonne.firstChild.data == 'Fin de mois':
                                                      create_org[org_colonne.nodeName] = 'fin'
                                                  if org_colonne.firstChild.data == 'Mois suivant':
                                                      create_org[org_colonne.nodeName] = 'suivant'
                                                  if org_colonne.firstChild.data == 'Non imprimable':
                                                      create_org[org_colonne.nodeName] = 'non'
                                              
                                              else : 
                                                  if not org_colonne.firstChild.data == 'False' : create_org[org_colonne.nodeName] = org_colonne.firstChild.data
                                      org_cotis_obj.create(cr, uid, create_org)
                                                 
                            #le reste : char, text, sélection, date ...
                            else :
                                if not colonne.firstChild.data == 'False' : update[colonne.nodeName] = colonne.firstChild.data     
                    
                    org_cotis_group_obj.write(cr, uid, [group_id], update)
                    
        #Il y a des params_dict dans le fichier
        if doc.getElementsByTagName('params_dict_list') :
            dict_list = doc.getElementsByTagName('params_dict_list')[0]
            
            #premier balayage pour créer les params dict manquant 
            for dict in dict_list.childNodes :
                if dict.nodeType == minidom.Node.ELEMENT_NODE :
                    name = dict.getElementsByTagName('name')[0].firstChild.data
                    id = dict_obj.search(cr, uid, [('name', '=', name)])
                    if not id : dict_obj.create(cr, uid, {'name' : name,}) 

            #Second balayage pour créer les liaisons 
            for dict in dict_list.childNodes :
                update = {}
                if dict.nodeType == minidom.Node.ELEMENT_NODE :
                    for colonne in dict.childNodes :
                        if colonne.nodeType == minidom.Node.ELEMENT_NODE :
                            if colonne.nodeName == 'name' :
                               ids = dict_obj.search(cr, uid, [('name', '=', colonne.firstChild.data)])
                            
                            #many2one
                            elif colonne.nodeName in ['a_','b_','c_', 'd_', 'e_', 'f_']  :
                                if not colonne.firstChild.data == 'False' : update[colonne.nodeName] = dict_obj.search(cr, uid, [('name', '=', colonne.firstChild.data)])[0]
                            elif colonne.nodeName in ['org_cotis']  :
                                if not colonne.firstChild.data == 'False' : update[colonne.nodeName] = org_cotis_group_obj.search(cr, uid, [('name', '=', colonne.firstChild.data)])[0]
                            elif colonne.nodeName in ['ducs']  :
                                if not colonne.firstChild.data == 'False' : update[colonne.nodeName] = ducs_obj.search(cr, uid, [('code', '=', colonne.firstChild.data)])[0]
                            #many2one non traités    
                            elif colonne.nodeName in ['account_e_d','account_e_c','account_r_d', 'account_r_c']  :
                                rien = True
                            
                            #Boolean    
                            elif colonne.nodeName in ['active','cum_epe','cum_ctt', 'cum_act', 'cum_cpy']  :
                                if colonne.firstChild.data == 'False' : update[colonne.nodeName] = False
                                else : update[colonne.nodeName] = True
                            
                            #many2many    
                            elif colonne.nodeName in ['epe_counter_add','epr_counter_add']  :
                                if not colonne.firstChild.data == 'False' :
                                    liaisons = colonne.firstChild.data.split(',')
                                    liaison_ids = []
                                    for liaison in liaisons :
                                        liaison_ids.append(dict_obj.search(cr, uid, [('name', '=', liaison)])[0])
                                    update[colonne.nodeName] = [(6, 0, liaison_ids)]

                            #le reste : char, text, sélection ...
                            else :
                                if not colonne.firstChild.data == 'False' : update[colonne.nodeName] = colonne.firstChild.data     
                    
                    
                    dict_obj.write(cr, uid, ids, update)
     

        #Il y a des modèles à importer
        if doc.getElementsByTagName('model_list') :
            xml_list = doc.getElementsByTagName('model_list')[0]
            model_obj = self.pool.get('hr_gp.param_model')
            item_obj = self.pool.get('hr_gp.param_model_item')
            
            
            for xml_model in xml_list.childNodes :
                if xml_model.nodeType == minidom.Node.ELEMENT_NODE :
                    update = {}
                    model_id = model_obj.create(cr, uid, {})
                    for colonne in xml_model.childNodes :
                        if colonne.nodeType == minidom.Node.ELEMENT_NODE :
                            if colonne.nodeName == 'items' :
                               #création des items du model
                               for item in colonne.childNodes :
                                   if item.nodeType == minidom.Node.ELEMENT_NODE :
                                      create_item = {} 
                                      for item_colonne in item.childNodes :
                                          if item_colonne.nodeType == minidom.Node.ELEMENT_NODE :
                                              if item_colonne.nodeName=='model_id': 
                                                  create_item['model_id'] = model_id
                                              elif item_colonne.nodeName=='params': 
                                                  if not item_colonne.firstChild.data == 'False' : create_item[item_colonne.nodeName] = dict_obj.search(cr, uid, [('name', '=', item_colonne.firstChild.data)])[0]
                                              elif item_colonne.nodeName=='name': 
                                                  rien =True
                                              else : 
                                                  if not item_colonne.firstChild.data == 'False' : create_item[item_colonne.nodeName] = item_colonne.firstChild.data
                                      item_obj.create(cr, uid, create_item)
                                                 
                            elif colonne.nodeName == 'name'  :
                                update[colonne.nodeName] = colonne.firstChild.data + " (Import du " + time.strftime("%d/%m/%Y") + ")" 
                                
                            #Boolean    
                            elif colonne.nodeName in ['active']  :
                                if colonne.firstChild.data == 'False' : update[colonne.nodeName] = False
                                else : update[colonne.nodeName] = True
                            
                            #le reste : char, text, sélection, date ...
                            else :
                                if not colonne.firstChild.data == 'False' : update[colonne.nodeName] = colonne.firstChild.data     
                    
                    model_obj.write(cr, uid, [model_id], update)

        return {'type':'ir.actions.act_window_close'}
    
hr_gp_support_import()
