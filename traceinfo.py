# Copyright (c) 2018 Tommi Rintala, New Cable Corporation Ltd

import sys
from math import sqrt
from pcbnew import *

# some code stolen from:
# https://github.com/KiCad/kicad-source-mirror/blob/master/pcb_calculator/tracks_width_versus_current.cpp

#ToUnits = ToMM
#FromUnits = FromMM

RHO_CU = 1.72e-8  # Copper resistivity
CU_THICK = 35e-6  # Board thickness
MAX_TEMP = 20     # maximum temperature rise (degrees Celcius)

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
    return sqrt(pow(ToMM(point1.y)-ToMM(point2.y), 2)
                + pow(ToMM(point1.x)-ToMM(point2.x), 2))


class TraceInfoGenerator(ActionPlugin):
    def defaults(self):
        self.name = "Generate Trace Info"
        self.category = "Info PCB"
        self.description = "This plugin gives some info about traces"

        self._board = GetBoard()

    def getArea(self, point1, point2, width):
        area = calculate_length(point1, point2) * ToMM(width)
        #area = sqrt(pow(ToMM(point1.y)-ToMM(point2.y), 2) + pow(ToMM(point1.x)-ToMM(point2.x), 2)) * ToMM(width)
        return area

    def getResistance(self, start, end, width):
        """Calculate resistance (ignore temp)"""
        length = calculate_length(start, end)
        #sqrt(pow(ToMM(end.y)-ToMM(start.y), 2) + pow(ToMM(end.x)-ToMM(start.x), 2))
        height = 35e-6
        area = ToMM(width) * height
        resistance = RHO_CU * length/area
        return resistance

    def getInductance(self, areaMM2):
        return 0

    
    def traceinfo(self):
        resistance = {0:0}
        inductance = {0:0}
        #maxvoltage = {0:999999}
        maxcurrent = {0:999999}
        voltagedrop = {0:0}
        for trace in self._board.GetTrackWidthList():
            print("trace width: " + str(trace))
        for item in self._board.GetTracks():
            print("track: " + str(trace))
            if isinstance(item, VIA):
                pos = item.GetPosition()
                drill = item.GetDrillValue()
                width = item.GetWidth()
                print(" * Via: ", (ToMM(pos), ToMM(drill), ToMM(width)))
            elif isinstance(item, TRACK):
                if item.GetNet():
                    net = item.GetNet()
                    net_id = net.GetNet()
                else:
                    net_id = 'default'
                #net = item.GetNet() or 'default'
                start = item.GetStart()
                end = item.GetEnd()
                width = item.GetWidth()
                area = self.getArea(start, end, width)
                length = calculate_length(start, end)
                print(" * TRACK: ", net.GetNetname(), area)
                if net not in resistance:
                    resistance[net_id] = 0
                if net not in inductance:
                    inductance[net_id] = 0
                rr = self.getResistance(start, end, width)
                ii = self.getInductance(area)
                #vd = 0
                print(" -> area= ", area, ", R= ", rr, " L= ", ii)
                
                extResistance = (RHO_CU * length) / (width * CU_THICK)
                extV = extResistance * aCurrent
                
                resistance[net_id] += rr
                voltagedrop[net_id] += extV
                powerloss[net_id] += extV * aCurrent
                #inductance[net_id] += ii
                #maxvolt = self.get_max_voltage_ipcc(0.024, 20, width, CU_THICK)
                #maxvoltage[net_id] = min(maxvolt, maxvoltage[net_id])
                maxcurr = calculate_max_current(width, CU_THICK, 20, True)
                maxcurrent[net_id] = min(maxcurr, maxcurrent[net_id])
                
        for net in resistance:
            print("Total resistance for net: ", net, " is ", resistance[net], " Ohm")
            print(" voltagedrop: ", voltagedrop[net])
            print(" powerloss:   ", powerloss[net])
            print(" max current: ", maxcurrent[net])
        for net in inductance:
            print("Total inductance for net: ", net, " is ", inductance[net], " Ohm")

    def get_max_voltage(self, K_const, temprise, width, thickness):
        return K_const * pow(temprise, 0.44) * pow(width * thickness, 0.725)

    def Run(self):
        print("----------------------------------")
        print("Starting Traceinfo plugin")

        self.traceinfo()
