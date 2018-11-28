# Copyright (c) 2018 Tommi Rintala, New Cable Corporation Ltd

#import sys
from math import sqrt, log, exp

import wx
import wx.aui

#from pcbnew import *
import pcbnew

# some code stolen from:
# https://github.com/KiCad/kicad-source-mirror/blob/master/pcb_calculator/tracks_width_versus_current.cpp

#ToUnits = ToMM
#FromUnits = FromMM

RHO_CU = 1.72e-8  # Copper resistivity
CU_THICK = 18e-6  # Board thickness
MAX_TEMP = 20     # maximum temperature rise (degrees Celcius)

def format_number(inputvalue, dec=3):
    """Format number more nicely"""
    value = inputvalue
    post = ""
    if abs(value) >= 1e9:
        value /= 1e9
        post = "G"
    elif abs(value) >= 1e6:
        value /= 1e6
        post = "M"
    elif abs(value) >= 1e3:
        value /= 1e3
        post = "k"
    elif abs(value) >= 0:
        if abs(value) < 1e-12:
            value *= 1e12
            post = 'p'
        elif abs(value) < 1e-9:
            value *= 1e9
            post = 'n'
        elif abs(value) < 1e-6:
            value *= 1e6
            post = 'u'
        elif abs(value) < 1e-3:
            value *= 1000
            post = 'm'


    return "%.3f%s" % (value, post)


def calculate_resistance(start, end, width, height, rho_cu=RHO_CU):
    """Calculate resistance"""
    length = calculate_length(start, end)
    resistance = (rho_cu * length) / (width * height)
    #sqrt(pow(ToMM(end.y)-ToMM(start.y), 2) + pow(ToMM(end.x)-ToMM(start.x), 2))
    #height = 35e-6
    #area = pcbnew.ToMM(width) * height * 1000
    #resistance = rho_cu * length/area
    return resistance

def calculate_inductance(areaMM2):
    return 0



def calculate_area(point1, point2, width):
    area = calculate_length(point1, point2) * pcbnew.ToMM(width)
    return area


def calculate_trace_width(current_A, thickness_m, delta_T_C, use_internal_layer):
    if use_internal_layer:
        scale = 0.024
    else:
        scale = 0.048
    dtmp = log(current_A) - log(scale) - 0.44 * log(delta_T_C) - 0.725 * log(thickness_m)
    dtmp /= 0.725
    trackwidth = exp(dtmp)
    return trackwidth

def calculate_max_current(width_m, thickness_m, delta_T_C, use_internal_layer):
    if use_internal_layer:
        scale = 0.024
    else:
        scale = 0.048
    area = thickness_m * width_m
    current = scale * pow(delta_T_C, 0.44) * pow(area, 0.725)
    return current

def calculate_length(point1, point2):
    return sqrt(pow(pcbnew.ToMM(point1.y)-pcbnew.ToMM(point2.y), 2)
                + pow(pcbnew.ToMM(point1.x)-pcbnew.ToMM(point2.x), 2))

def traceinfo(cu_thick=CU_THICK, internal_layer=True):
    resistance = {0:0}
    inductance = {0:0}
    #maxvoltage = {0:999999}
    maxcurrent = {0:999999}
    voltagedrop = {0:0}
    powerloss = {0:0}
    netnames = {0:u'default'}
    lengths = {0:0}

    for trace in pcbnew.GetBoard().GetTrackWidthList():
        print("trace width: " + str(trace))
        for item in pcbnew.GetBoard().GetTracks():
            print("track: " + str(trace))
            if isinstance(item, pcbnew.VIA):
                pos = item.GetPosition()
                drill = item.GetDrillValue()
                width = item.GetWidth()
                print(" * Via: ", (pcbnew.ToMM(pos), pcbnew.ToMM(drill), pcbnew.ToMM(width)))
            elif isinstance(item, pcbnew.TRACK):
                if item.GetNet():
                    net = item.GetNet()
                    net_id = net.GetNet()
                    net_name = net.GetNetname() or u''
                else:
                    net_id = 0
                    net_name = u'default'

                start = item.GetStart()
                end = item.GetEnd()
                width = item.GetWidth()

                area = calculate_area(start, end, width)
                length = calculate_length(start, end)
                #net_name = net.GetNetname() or u''
                print(" * TRACK: ", net_name, area)
                if net_id not in resistance:
                    resistance[net_id] = 0
                if net_id not in inductance:
                    inductance[net_id] = 0
                if net_id not in voltagedrop:
                    voltagedrop[net_id] = 0
                if net_id not in powerloss:
                    powerloss[net_id] = 0
                if net_id not in maxcurrent:
                    maxcurrent[net_id] = 99999999
                if net_id not in netnames:
                    netnames[net_id] = net_name
                if net_id not in lengths:
                    lengths[net_id] = 0
                #rr = calculate_resistance(start, end, width)
                ii = calculate_inductance(area)

                #print(" -> area= ", area, ", R= ", rr, " L= ", ii)

                cable_current = 1

                extResistance = (RHO_CU * length) / (width * cu_thick)
                external_voltage = extResistance * cable_current
                lengths[net_id] += length
                resistance[net_id] += extResistance
                voltagedrop[net_id] += external_voltage
                powerloss[net_id] += external_voltage * cable_current
                #inductance[net_id] += ii
                maxcurr = calculate_max_current(width, cu_thick, 20, internal_layer)
                maxcurrent[net_id] = min(maxcurr, maxcurrent[net_id])

    for net in resistance:
        print("Total resistance for net: ", net, " (", netnames[net], ") is ", resistance[net], " Ohm")
        print(" voltagedrop: ", voltagedrop[net])
        print(" powerloss:   ", powerloss[net])
        print(" max current: ", maxcurrent[net])
    for net in inductance:
        print("Total inductance for net: ", net, " is ", inductance[net], " Ohm")
    return (resistance, inductance, powerloss, voltagedrop, maxcurrent, netnames, lengths)


class TraceInfoGenerator(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "Generate Trace Info"
        self.category = "Info PCB"
        self.description = "This plugin gives some info about traces"

        self._board = pcbnew.GetBoard()


    def get_max_voltage(self, K_const, temprise, width, thickness):
        return K_const * pow(temprise, 0.44) * pow(width * thickness, 0.725)

    def Run(self):
        print("----------------------------------")
        print("Starting Traceinfo plugin")

        class DisplayResults(wx.Dialog):
            def __init__(self, parent):
                wx.Dialog.__init__(self, parent, id=wx.ID_ANY, title="Traceinfo Results")
                #self.SetIcon()
                panel = wx.Panel(self)

                #pcb = pcbnew.GetBoard()
                #nets = pcb.GetNets()
                res, ind, pwr_loss, voltage_loss, max_current, net_names, length = traceinfo(CU_THICK, True)

                window_sizer = wx.BoxSizer()
                window_sizer.Add(panel, 1, wx.ALL | wx.EXPAND)

                sizer = wx.GridBagSizer(10, 0)
                panel.SetBackgroundColour("white")
                #sizer = wx.BoxSizer(wx.VERTICAL)
                sizer.Add(wx.StaticText(panel, label="Net#"), border=4, pos=(0, 0))
                sizer.Add(wx.StaticText(panel, label="Name"), border=4, pos=(0, 1))
                sizer.Add(wx.StaticText(panel, label="Length [mm]"), border=4, pos=(0, 2))
                sizer.Add(wx.StaticText(panel, label="Resistance [Ohm]"), border=4, pos=(0, 3))
                sizer.Add(wx.StaticText(panel, label="Inductance [H]"), border=4, pos=(0, 4))
                sizer.Add(wx.StaticText(panel, label="Power loss [W]"), border=4, pos=(0, 5))
                sizer.Add(wx.StaticText(panel, label="Voltage loss [V]"), border=4, pos=(0, 6))
                sizer.Add(wx.StaticText(panel, label="Max Current [A]"), border=4, pos=(0, 7))
                self.lb_net = {}
                self.lb_name = {}
                self.lb_res = {}
                self.lb_ind = {}
                self.lb_pwr = {}
                self.lb_vdo = {}
                self.lb_max = {}
                self.lb_len = {}
                self.row = {}
                row = 1
                for net in res:
                    self.lb_net[row] = wx.StaticText(panel, label=str(net))
                    self.lb_name[row] = wx.StaticText(panel, label=str(net_names[net]))
                    self.lb_len[row] = wx.StaticText(panel, label=format_number(length[net]))
                    self.lb_res[row] = wx.StaticText(panel, label=format_number(res[net]))
                    self.lb_ind[row] = wx.StaticText(panel, label=format_number(ind[net]))
                    self.lb_pwr[row] = wx.StaticText(panel, label=format_number(pwr_loss[net]))
                    self.lb_vdo[row] = wx.StaticText(panel, label=format_number(voltage_loss[net]))
                    self.lb_max[row] = wx.StaticText(panel, label=format_number(max_current[net]))
                    self.lb_net[row].SetBackgroundColour('#cfcfcf')
                    #lb_max[row] = wx.StaticText(panel, label=str("%.2e"%([net]))

                    sizer.Add(self.lb_net[row], flag=wx.ALL|wx.EXPAND, border=4, pos=(row, 0))
                    sizer.Add(self.lb_name[row], flag=wx.ALL|wx.EXPAND, border=4, pos=(row, 1))
                    sizer.Add(self.lb_len[row], flag=wx.ALL|wx.EXPAND, border=4, pos=(row, 2))
                    sizer.Add(self.lb_res[row], flag=wx.ALL|wx.EXPAND, border=4, pos=(row, 3))
                    sizer.Add(self.lb_ind[row], flag=wx.ALL|wx.EXPAND, border=4, pos=(row, 4))
                    sizer.Add(self.lb_pwr[row], flag=wx.ALL|wx.EXPAND, border=4, pos=(row, 5))
                    sizer.Add(self.lb_vdo[row], flag=wx.ALL|wx.EXPAND, border=4, pos=(row, 6))
                    sizer.Add(self.lb_max[row], flag=wx.ALL|wx.EXPAND, border=4, pos=(row, 7))
                    self.row[net] = row
                    row += 1

                bottom = wx.BoxSizer(wx.HORIZONTAL)

                self.thickradio = wx.RadioBox(panel, wx.ID_ANY, label="Thickness [um]", choices=['18', '35', '70'])
                self.thickradio.Bind(wx.EVT_RADIOBOX, self.update_display)
                bottom.Add(self.thickradio, 0, wx.RIGHT, 4) #, (row, 1))
                self.intext = wx.RadioBox(panel, wx.ID_ANY, label="Internal/External", choices=['int', 'ext'])
                self.intext.Bind(wx.EVT_RADIOBOX, self.update_display)
                bottom.Add(self.intext, 0, wx.RIGHT, 4)
                # ------------------
                close_button = wx.Button(panel, label="Close")
                close_button.Bind(wx.EVT_BUTTON, self.on_button_close)
                bottom.Add(close_button, 0, wx.LEFT, 4) #, (row, 6))
                self.maxrows = row

                border = wx.BoxSizer(wx.VERTICAL)
                border.Add(sizer, 3, wx.ALL | wx.EXPAND, 5)
                border.Add(bottom, 3, wx.TOP | wx.EXPAND, 5)
                panel.SetSizerAndFit(border)
                self.SetSizerAndFit(window_sizer)
                #self.Fit()

            def update_display(self, event):
                event.Skip()
                if self.thickradio.GetSelection() == 0:
                    thickness = 18e-6
                elif self.thickradio.GetSelection() == 1:
                    thickness = 35e-6
                elif self.thickradio.GetSelection() == 2:
                    thickness = 70e-6
                if self.intext.GetSelection() == 0:
                    internal = True
                else:
                    internal = False
                res, ind, pwr_loss, voltage_loss, max_current, net_names, length = traceinfo(thickness, internal)
                for net in res:
                    row = self.row[net]
                    self.lb_net[row].SetLabel(str(net))
                    self.lb_name[row].SetLabel(str(net_names[net]))
                    self.lb_len[row].SetLabel(format_number(length[net]))
                    self.lb_res[row].SetLabel(format_number(res[net]))
                    self.lb_ind[row].SetLabel(format_number(ind[net]))
                    self.lb_pwr[row].SetLabel(format_number(pwr_loss[net]))
                    self.lb_vdo[row].SetLabel(format_number(voltage_loss[net]))
                    self.lb_max[row].SetLabel(format_number(max_current[net]))


            def on_button_close(self, event):
                event.Skip()
                self.Close()
        frame = DisplayResults(None)
        frame.Center()
        frame.ShowModal()
        frame.Destroy()
