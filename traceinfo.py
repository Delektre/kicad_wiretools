# Copyright (c) 2018 Tommi Rintala, New Cable Corporation Ltd

import pcbnew

class TraceInfoGenerator(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "Generate Trace Info"
        self.category = "Info PCB"
        self.description = "This plugin gives some info about traces"

        self._board = pcbnew.GetBoard()

    def traceinfo(self):
        for trace in self._board.GetTrackWidthList():
            print("trace width: " + str(trace))
        for trace in self._board.GetTracks():
            print("track: " + str(trace))

    def Run(self):
        print("----------------------------------")
        print("Starting Traceinfo plugin")

        self.traceinfo()
