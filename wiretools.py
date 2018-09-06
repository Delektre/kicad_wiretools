import pcb
import pcbnew
import wx
import wx.aui

import inspect
import os
filename = inspect.getframeinfo(inspect.currentframe()).filename
path = os.path.dirname(os.path.abspath(filename))

board = pcbnew.GetBoard()

SCALE = 1000000

if hasattr(pcbnew, "LAYER_ID_COUNT"):
    pcbnew.PCB_LAYER_ID_COUNT = pcbnew.LAYER_ID_COUNT

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

designsettings = board.GetDesignSettings()

def pan_and_zoom(x, y, width, height):
    xx = pcbnew.FromMM(x)
    yy = pcbnew.FromMM(y)
    ww = pcbnew.FromMM(width)
    hh = pcbnew.FromMM(height)
    pcbnew.WindowZoom(xx, yy, ww, hh)

def findPcbnewWindow():
    windows = wx.GetTopLevelWindows()
    pcbnew = [w for w in windows if w.GetTitle()[0:6] == "Pcbnew"]
    if len(pcbnew) != 1:
        raise Exception("Cannot find pcbnew window from title matching")
    return pcbnew[0]


# add toolbar buttons
pcbwin = findPcbnewWindow()

top_tb = pcbwin.FindWindowById(pcbnew.ID_H_TOOLBAR)
com_tb = pcbwin.FindWindowById(pcbnew.ID_V_TOOLBAR)
opt_tb = pcbwin.FindWindowById(pcbnew.ID_OPT_TOOLBAR)

def WireClearCallback(event):
    print("Got a click on my new button {}".format(str(event)))
    pcbnew.Refresh()

bitmap = wx.Bitmap(path + '/icons/26x26/wiretools.png', wx.BITMAP_TYPE_PNG)
# bitmap sizes:
# SMALL - for menus     - 16 x 16
# MID   - for toolbars  - 26 x 26
# BIG   - for programs  - 48 x 48

itemid = wx.NewId()

com_tb.AddTool(itemid, "wireclearbutton", bm, "Wire Clear", wx.ITEM_NORMAL)
com_tb.Bind(ex.EVT_TOOL, WireClearCallback, id=itemid)
com_tb.Realize()
