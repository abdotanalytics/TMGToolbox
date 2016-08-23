#---LICENSE----------------------
'''
    Copyright 2016 Travel Modelling Group, Department of Civil Engineering, University of Toronto

    This file is part of the TMG Toolbox.

    The TMG Toolbox is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    The TMG Toolbox is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with the TMG Toolbox.  If not, see <http://www.gnu.org/licenses/>.
'''
#---METADATA---------------------
'''
[TITLE]

    Authors: nasterska

    Latest revision by: nasterska
    
    
    [Description]
        
'''
#---VERSION HISTORY
'''
    0.0.1 Created on 2016-08-22 by nasterska
            
'''

import inro.modeller as _m
import traceback as _traceback
from contextlib import contextmanager
from contextlib import nested
from html import HTML
from re import split as _regex_split
_MODELLER = _m.Modeller() #Instantiate Modeller once.
_util = _MODELLER.module('tmg.common.utilities')
_tmgTPB = _MODELLER.module('tmg.common.TMG_tool_page_builder')

##########################################################################################################

class RemoveExtraLinks(_m.Tool()):
       
    version = '1.0.0'
    tool_run_msg = ""
    number_of_tasks = 4 # For progress reporting, enter the integer number of tasks here
    
    BaseScenario = _m.Attribute(_m.InstanceType) # common variable or parameter
    BaseNetwork = _m.Attribute(_m.InstanceType)
    NewScenarioId = _m.Attribute(int)
    NewScenarioTitle = _m.Attribute(str)
    PublishFlag = _m.Attribute(bool)
    
    TransferModeList = _m.Attribute(_m.ListType)
    
    AttributeAggregatorString = _m.Attribute(str)
    
    def __init__(self):
        #---Init internal variables
        self.TRACKER = _util.ProgressTracker(self.number_of_tasks) #init the ProgressTracker
        
        #---Set the defaults of parameters used by Modeller
        self.BaseScenario = _MODELLER.scenario #Default is primary scenario
        self.BaseNetwork = self.BaseScenario.get_network()
        self.PublishFlag = True 

    
    def page(self):
        pb = _tmgTPB.TmgToolPageBuilder(self, title="Remove Extra Links v%s" %self.version,
                     description="Removes unnecessary links from the network. <br><br> \
                                Three types of links are deleted: \
                                <ul>\
                                <li> First, links with no transit lines, which have only transit modes \
                                are deleted. \
                                <li> Next, non-connector dead-end links are removed. \
                                <li> Finally, links with transfer modes that do not connect two stations, \
                                or connect a station to the road network are deleted. Links of this nature \
                                which have other, non-transfer modes are not deleted; however, the transfer \
                                modes are removed from these links.",
                     branding_text="- TMG Toolbox")
        
        if self.tool_run_msg != "": # to display messages in the page
            pb.tool_run_status(self.tool_run_msg_status)
            
        pb.add_select_scenario(tool_attribute_name='BaseScenario',
                               title="Base Scenario",
                               allow_none=False)
        
        pb.add_new_scenario_select(tool_attribute_name='NewScenarioId',
                                   title="New Scenario Number")
        
        pb.add_text_box(tool_attribute_name='NewScenarioTitle',
                        size=60, title= "New Scenario Title")
        
        pb.add_checkbox(tool_attribute_name= 'PublishFlag',
                        label= "Publish network?")
        
        self.TransferModeList = [self.BaseScenario.mode('u'),
                                 self.BaseScenario.mode('t'),
                                 self.BaseScenario.mode('y')]

        pb.add_select_mode(tool_attribute_name='TransferModeList',
                           filter=[ 'AUX_TRANSIT'],
                           allow_none=False,
                           title='Transfer Modes:',
                           note='Select all transfer modes.')
        
        return pb.render()

    ##########################################################################################################
        
    def __call__(self, baseScen, newScenId, newScenTitle, transferModeList, pubFlag):
        self.tool_run_msg = ""
        self.TRACKER.reset()

        self.BaseScenario = _MODELLER.emmebank.scenario(baseScen)
        self.NewScenarioId = newScenId
        self.NewScenarioTitle = newScenTitle
        self.TransferModeList = []

        self.PublishFlag = pubFlag

        self.BaseNetwork = BaseScenario.get_network()

        for modechar in transferModeList:
            self.TransferModeList.append (self.BaseNetwork.mode(modechar))

        print self.TransferModeList

        try:
            
            self._Execute()
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(
                e, _traceback.format_exc(e))
            raise
        
        self.tool_run_msg = _m.PageBuilder.format_info("Done.")    

    ##########################################################################################################
        
    def run(self):
        self.tool_run_msg = ""
        self.TRACKER.reset()
        
        try:
            self._Execute()
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(
                e, _traceback.format_exc(e))
            raise
        
        self.tool_run_msg = _m.PageBuilder.format_info("Done.")
    
    ##########################################################################################################    
    
    
    def _Execute(self):
        with _m.logbook_trace(name="{classname} v{version}".format(classname=(self.__class__.__name__), version=self.version),
                                     attributes=self._GetAtts()):
            
            self.TRACKER.completeTask()
            
            self.BaseNetwork = self.BaseScenario.get_network()
            self.TRACKER.completeTask()
                        
            self._RemoveLinks(self.BaseNetwork)
            self.TRACKER.completeTask()
            
            self.TRACKER.startProcess(2)
            if self.PublishFlag:
                bank = _MODELLER.emmebank 
                newScenario = bank.copy_scenario(self.BaseScenario.id, self.NewScenarioId, copy_strat_files= False, copy_path_files= False)
                newScenario.title= self.NewScenarioTitle
                self.TRACKER.completeSubtask()
                newScenario.publish_network(self.BaseNetwork, True)
                self.TRACKER.completeSubtask()
                
                _MODELLER.desktop.refresh_needed(True)
            self.TRACKER.completeTask()

    ##########################################################################################################    
    
    #----SUB FUNCTIONS---------------------------------------------------------------------------------  
    
    def _GetAtts(self):
        atts = {
                "Base Scenario" : str(self.BaseScenario.id),
                "New Scenario": self.NewScenarioId,
                "Transfer Modes": self.TransferModeList,
                "Version": self.version, 
                "self": self.__MODELLER_NAMESPACE__}
            
        return atts 
    

    
    def _RemoveLinks(self,network):

        #remove transit-only links that have no transit lines
        for link in network.links():
            has_transit = False
            for segment in link.segments():
                has_transit = True
            transit_only = True
            if has_transit == False:
                for mode in link.modes:
                    if mode.type != "TRANSIT":
                        transit_only = False
                if transit_only == True:
                    network.delete_link(link.i_node,link.j_node) 
                     
        #remove dead-end links
        for link in network.links():
            has_transit = False
            for segment in link.segments():
                has_transit = True
            dead_start = True
            dead_end = True
            if has_transit == False:
                start_node = link.i_node
                end_node = link.j_node
                if start_node.is_centroid:
                    dead_start = False
                else:
                    for in_link in start_node.incoming_links():
                        if in_link.i_node != link.j_node:
                            dead_start = False 
                if end_node.is_centroid:
                    dead_end = False
                else:
                    for out_link in end_node.outgoing_links():
                        if out_link.j_node != link.i_node:
                            dead_end = False
                if dead_start or dead_end:
                    network.delete_link(start_node,end_node)

        #remove transfer links that do not connect to stops
        transfer_modes = set(self.TransferModeList)
        for link in network.links():
            linkmodes = link.modes
            #check if link has at least one transfer mode
            if len(transfer_modes.intersection(linkmodes))> 0:
                    start_node = link.i_node
                    end_node = link.j_node
                    start_stop = False
                    end_stop = False
                    start_road = False
                    end_road = False
                    for in_link in start_node.incoming_links():
                        #only check if non-reverse links are on the road network
                        if in_link.i_node != link.j_node:
                            for mode in in_link.modes:
                                if mode.type != 'TRANSIT' and mode not in transfer_modes:
                                    start_road = True
                    #check if start node has transit stops
                    for out_link in start_node.outgoing_links():
                        for segment in out_link.segments():
                            if segment.allow_boardings or segment.allow_alightings:
                                start_stop = True
                    for out_link in end_node.outgoing_links():
                        #only check if non-reverse links are on the road network
                        if out_link.j_node != link.i_node:
                            for mode in out_link.modes:
                                if mode.type != 'TRANSIT'and mode not in transfer_modes:
                                    end_road = True
                        #check to see if end node has transit stops
                        for segment in out_link.segments():
                            if segment.allow_boardings or segment.allow_alightings:
                                end_stop = True
                    #check to see if node is end-of-line stop
                    for segment in link.segments():
                        if segment.line.segment(str(end_node.number) + "-0") != False:
                            end_stop = True
                    keep = False
                    if start_stop == True and end_stop == True:
                        keep = True
                    elif start_stop == True and end_road == True:
                        keep = True
                    elif end_stop == True and start_road == True:
                        keep = True
                    if keep == False:
                        #check if link has non-transfer modes, in which case these modes are removed from link, otherwise link is deleted
                        if link.modes.issubset(transfer_modes):
                            network.delete_link(start_node,end_node)
                        else:
                            link.modes = link.modes.difference(transfer_modes)
        
    @_m.method(return_type=_m.TupleType)
    def percent_completed(self):
        return self.TRACKER.getProgress()
                
    @_m.method(return_type=unicode)
    def tool_run_msg_status(self):
        return self.tool_run_msg
        