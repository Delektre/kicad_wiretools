import pcbnew

import inspect
import os

filename = inspect.getframeinfo(inspect.currentframe()).filename
path = os.path.dirname(os.path.abspath(filename))

board = pcbnew.GetBoard()

SCALE = 1000000

if hasattr(pcbnew, "LAYER_ID_COUNT"):
    pcbnew.PCB_LAYER_ID_COUNT = pcbnew.LAYER_ID_COUNT

if not board:
    Exception("Unable to get board handle")
    
def coordsFromPolySet(ps):
    str = ps.Format()
    lines = str.split('\n')
    numpts = int(lines[2])

    # there is extra two \n in each line
    pts = [[int(n) for n in x.split(" ")] for x in lines[3:-2]]
    return pts

"""Get all pads for a NET"""
def padsForNet(net):
    retval = []
    for pad in board.getPads():
        # first get the netinfo, then get the netcode (int)
        if pad.GetNet().GetNet() == net:
            retval.append(pad)
    return retval

# from collections import defaultdict

#ds = board.GetDesignSettings()

def pan_and_zoom(x, y, width, height):
    xx = pcbnew.FromMM(x)
    yy = pcbnew.FromMM(y)
    ww = pcbnew.FromMM(width)
    hh = pcbnew.FromMM(height)
    pcbnew.WindowZoom(xx, yy, ww, hh)

def dump_board_boundingbox():
    board = pcbnew.GetBoard()
    boardbox = board.ComputeBoundingBox()
    boardx1 = boardbox.GetX()
    boardy1 = boardbox.GetY()
    boardwidth = boardbox.GetWidth()
    boardheight = boardbox.GetHeight()
    print("this board is at position {},{} {} widde and {} high".format(boardx1, boardy1, boardwidth, boardheight))
    return (boardx1, boardy1, boardwidth, boardheight)
    
def get_layertable():
    board = pcbnew.GetBoard()
    layertable = {}
    numlayers = pcbnew.LAYER_ID_COUNT
    for i in range(numlayers):
        layertable[i] = board.GetLayerName(i)
        print("{} {}".format(i, board.GetLayerName(i)))
    return layertable
    
def dump_net_tracks(net):
    board = pcbnew.GetBoard()
    clktracks = board.TracksInNet(clknet.GetNet())
    for track in clktracks:
        print("{},{} -> {},{} width {} layer {}".format(track.GetStart().x/SCALE, track.GetStart().y/SCALE, track.GetEnd().x/SCALE, track.GetEnd().y/SCALE, track.GetWidth()/SCALE, layertable[track.GetLayer()]))

#tracks = board.GetTracks()
#for track in tracks:
#    print("track: {}".format(track))


class Wiretools(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "Wiretools utility"
        self.category = "Show Info from PCB"
        self.description = "Generate information from PCB"

    def _prepare_report(self):
        self.stream = None

    def Run(self):
        self._board = pcbnew.GetBoard()
        
