# Copyright (c) 2018 Tommi Rintala, New Cable Corporation Ltd

import sys
from pcbnew import *
from math import sqrt

#ToUnits = ToMM
#FromUnits = FromMM

RHO_CU = 1.72e-8  # Copper resistivity
CU_THICK = 35e-6  # Board thickness
MAX_TEMP = 20     # maximum temperature rise (degrees Celcius)

class TraceInfoGenerator(ActionPlugin):
    def defaults(self):
        self.name = "Generate Trace Info"
        self.category = "Info PCB"
        self.description = "This plugin gives some info about traces"

        self._board = GetBoard()

    def getArea(self, point1, point2, width):
        area = sqrt(pow(ToMM(point1.y)-ToMM(point2.y), 2) + pow(ToMM(point1.x)-ToMM(point2.x), 2)) * ToMM(width)
        return area

    def getResistance(self, start, end, width):
        """Calculate resistance (ignore temp)"""
        length = sqrt(pow(ToMM(end.y)-ToMM(start.y), 2) + pow(ToMM(end.x)-ToMM(start.x), 2))
        height = 35e-6
        area = ToMM(width) * height
        resistance = RHO_CU * length/area
        return resistance

    def getInductance(self, areaMM2):
        return 0

    
    def traceinfo(self):
        resistance = {0:0}
        inductance = {0:0}
        maxvoltage = {0:999999}
        for trace in self._board.GetTrackWidthList():
            print("trace width: " + str(trace))
        for item in self._board.GetTracks():
            print("track: " + str(trace))
            if type(item) is VIA:
                pos = item.GetPosition()
                drill = item.GetDrillValue()
                width = item.GetWidth()
                print(" * Via: ", (ToMM(pos), ToMM(drill), ToMM(width)))
            elif type(item) is TRACK:
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
                print(" * TRACK: ", net.GetNetname(), area)
                if net not in resistance:
                    resistance[net_id] = 0
                if net not in inductance:
                    inductance[net_id] = 0
                rr = self.getResistance(start, end, width)
                ii = self.getInductance(area)
                #vd = self.calculate_voltage_drop()
                print(" -> area= ", area, ", R= ", rr, " L= ", ii)
                resistance[net_id] += rr
                voltagedrop[net_id] += vd
                #inductance[net_id] += ii
                maxvolt = self.get_max_voltage_ipcc(0.024, 20, width, CU_THICK)
                maxvoltage[net_id] = min(maxvolt, maxvoltage[net_id])
                
        for net in resistance:
            print("Total resistance for net: ", net, " is ", resistance[net], " Ohm")
        for net in inductance:
            print("Total inductance for net: ", net, " is ", inductance[net], " Ohm")

    def get_max_voltage(self, K_const, temprise, width, thickness):
        return K_const * pow(temprise, 0.44) * pow(width * thickness, 0.725)

    def Run(self):
        print("----------------------------------")
        print("Starting Traceinfo plugin")

        self.traceinfo()
