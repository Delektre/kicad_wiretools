# Copyright (c) 2018 Tommi Rintala, New Cable Corporation Ltd.

import base64
import pcbnew
import sys
import os
import os.path
import re
import wx
import traceback
import wx.aui
import wx.lib.filebrowsebutton as FBB
from pcbnew import *
from wx.lib.embeddedimage import PyEmbeddedImage
__version__ = "0.0.1"
WIDGET_SPACING = 5


"""Get the project directory name"""
def get_project_directory():
    return os.path.dirname(GetBoard().GetFilename())

def debug_dialog(msg, exception=None):
    if exception:
        msg = '\n'.join((msg, str(exception), traceback.format_exc()))
        dlg = wx.MessageDialog(None, msg, '', wx.OK)
        dlg.ShowModal()
        dlg.Destroy()

class shielding_based_layer(pcbnew.ActionPlugin):
    """
    A script to create a shielding based on boundarybox on other layer
    """


    def find_bounding_box(self, layerid = 0):
        #pcb = pcbnew.GetBoard()
        for draw in self._board.DrawingsList():
            # Handle the board outline segments
            if draw.GetClass() == 'DRAWSEGMENT' and draw.GetLayer() == layerid:
                if draw.GetType() == 0:
                    if draw.GetStart().x < self.minx:
                        self.minx = draw.GetStart().x
                    if draw.GetStart().y < self.miny:
                        self.miny = draw.GetStart().y
                    if draw.GetEnd().x > self.maxx:
                        self.maxx = draw.GetEnd().x
                    if draw.GetEnd().y > self.maxy:
                        self.maxy = draw.GetEnd().y
                else:
                    bbox = draw.GetBoundingBox()
                    msg = "Found element type " + str(draw.GetType()) + " with boundingbox: (" + bbox.GetLeft() + ", " + bbox.GetTop() + " -> " + bbox.GetRight() + ", " + bbox.GetBottom() + ")"
                    wx.LogMessage(msg)

    def defaults(self):
        self.name = "Draw a shielding layer"
        self.category = "Modify Drawing PCB"
        self.description = "Create a shielding to selected layer, based on BB"
        
        self._board = pcbnew.GetBoard()
        # set bounding box
        bbox = self._board.GetBoundingBox()
        self.minx = bbox.GetRight()
        self.maxx = bbox.GetLeft()
        self.miny = bbox.GetBottom()
        self.maxy = bbox.GetTop()
        # set offset defaults
        self.offsetTop = pcbnew.FromMM(1)
        self.offsetBottom = pcbnew.FromMM(1)
        self.offsetLeft = pcbnew.FromMM(5)
        self.offsetRight = pcbnew.FromMM(5)
        
    def dump_object(self, obj):
        for o in obj:
            print(" ", o.GetX(), ", ", o.GetY())

    def dump_layer_info(self, layer):
        brd = GetBoard()
        pads = [p for p in brd.GetPads()]
        tracks = [t for t in brd.GetTracks()]
        zones = [z for z in brd.GetZones()]
        drawings = [d for d in brd.Drawings()]
        self.dump_object("pads", pads)
        self.dump_object("tracks", tracks)
        self.dump_object("zones", zones)
        self.dump_object("drawings", drawings)
        net_codes = [p.GetNetCode() for p in pads]
        net_codes.extend([t.GetNetCode() for t in tracks]) # for tracks
        net_codes.extend([z.GetNetCode() for z in zones])  # for zones
        net_codes = list(set(net_codes))
        for code in net_codes:
            print("NET-CODE: ", code, brd.FindNet(code).GetNetname())
        print("Complete.")
        
    def Run(self):
        found_selected = False
        if not self.buttons:
            def findPcbnewWindow():
                windows = wx.GetTopLevelWindows()
                pcbnew = [w for w in windows if 'Pcbnew' in w.GetTitle()]
                if len(pcbnew) != 1:
                    raise Exception("Cannot find App window")
                return pcbnew[0]
            try:
                import inspect
                #import os
                filename = inspect.getframeinfo(inspect.currentframe()).filename
                path = os.path.dirname(os.path.abspath(filename))
                pcbwin = findPcbnewWindow()
                top_toolbar = pcbwin.FindWindowById(ID_H_TOOLBAR)

                shield_it_button = wx.NewId()
                shield_it_button_bm = wx.Bitmap(
                    os.path.join(path, 'icons', 'shield.png'), wx.BITMAP_TYPE_PNG)
                top_toolbar.AddTool(shield_it_button, "ShieldIT", shield_id_bm,
                                    "Create shielding", wx.ITEM_NORMAL)
                top_toolbar.Bind(
                    wx.EVT_TOOL, shield_it_callback, id=shield_id_button)
            except Exception as e:
                debug_dialog("Something went haywire", e)

        def switch(x):
            return {
                'Edge_Cuts': pcbnew.Edge_Cuts,
                'Eco1_User': pcbnew.Eco1_User,
                'Eco2_User': pcbnew.Eco2_User,
                'Dwgs_User': pcbnew.Dwgs_User,
                'Cmts_User': pcbnew.Cmts_User,
                'Margin'   : pcbnew.Margin,
                'F_CrtYd'  : pcbnew.F_CrtYd,
                'B_CrtYd'  : pcbnew.B_CrtYd,
                'F_Fab'    : pcbnew.F_Fab,
                'B_Fab'    : pcbnew.B_Fab,
                'F_SilkS'    : pcbnew.F_SilkS,
                'B_SilkS'    : pcbnew.B_SilkS,
            }[x]

        class displayDialog(wx.Dialog):
            def __init__(self, parent):
                wx.Dialog.__init__(self, parent, id=-1, title="Shielding")
                self.setIcon(PyEmbeddedImage(shielding_based_layer_ico_b64_data).GetIcon())
                self.panel = wx.Panel(self)

                self.ct = 0
                self.sourceLayer = "Edge_Cuts"
                self.targetLayer = "F_Fab"
                # TODO: Get layerlist
                layerList = ["Edge_Cuts", "Eco1_User", "Eco2_User", "Dwgs_User", "Cmts_User", "Margin", "F_CrtYd", "B_CrtYd", "F_Fab", "B_Fab", "F_SilkS", "B_SilkS"]
                self.comboSource = wx.ComboBox(self.panel, choices=layerList)
                self.comboSource.SetSelection(0)

                self.comboSource.Bind(wx.EVT_COMBOBOX, self.onComboSource)
                self.titleSource = wx.StaticText(self.panel, label="Source layer")

                self.comboTarget = wx.ComboBox(self.panel, choices=layerlist)
                self.comboTarget.SetSelection(8)
                self.comboTarget.Bind(wx.EVT_COMBOBOX, self.onComboTarget)
                self.titleTarget = wx.StaticText(self.panel, label="Target layer")

                # set sier for the frame, so we can change frame size to match widgets
                self.windowSizer = wx.BoxSizer()
                self.windowSizer.Add(self.panel, 1, wx.ALL | wx.EXPAND)

                # set sizer for the panel content
                self.sizer = wx.GridBagSizer(5, 0)
                self.sizer.Add(self.titleSource, (0, 0))
                self.sizer.Add(self.titleTarget, (0, 1))
                self.buttonRun = wx.Button(self.panel, label="Run")
                self.sizer.Add(self.buttonRun, (2, 0), (1, 2), flag=wx.Expand)

                self.buttonClose = wx.Button(self.panel, label="Close")
                self.sizer.Add(self.buttonClose, (2, 0), (2, 2), flag=wx.Expand)
                self.sizer.Add(self.comboSource, (1, 0))
                self.sizer.Add(self.comboTarget, (2, 0))


                # set simple sizer for a nice border
                self.border = wx.BoxSizer()
                self.border.Add(self.sizer, 1, wx.ALL | wx.EXPAND, 5)

                # use the sizers
                self.panel.SetSizerAndFit(self.border)
                self.SetSizerAndFit(self.windowSizer)

                self.buttonRun.Bind(wx.EVT_BUTTON, self.onRun)

                self.buttonClose.Bind(wx.EVT_BUTTON, self.onClose)
                self.Bind(wx.EVT_CLOSE, self.onClose)

            def onRun(self, event):
                # run the stuff
                pass

            def onClose(self, event):
                event.Skip()
                self.Close()

            def onComboSource(self, event):
                self.sourceLayer = self.comboSource.getValue()

            def onComboTarget(self, event):
                self.targetLayer = self.comboTarget.getValue()

        board = pcbnew.GetBoard()
        filename = GetBoard().GetFileName()
        if len(filename) == 0:
            wx.LogMessage("a board needs to be saved/loaded")
        else:
            LogMsg = ''
            msg = "'shield generator tool'\n"
            msg += "version = " + __version__
        frame = displayDialog(None)
        frame.Center()
        frame.ShowModal()
        frame.Destroy()

        dlg = wx.MessageBox('Clear target layer ('+frame.sourceLayer+') and create shielding?', 'Confirm', wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING)
        if dlg == wx.YES:
            wx.LogMessage('Now, create the shielding')
            pcbnew.Refresh()
        else:
            wx.LogMessage('Cancelled operation')

shielding_based_layer().register()


shielding_based_layer_ico_b64_data =\
"""iVBORw0KGgoAAAANSUhEUgAAABIAAAASCAYAAABWzo5XAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAKYQAACmEB/MxKJQAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAJrSURBVDiNnZRRSFNxFMa/s3vlLje3y0bpdKkwrcTCxbChQUIPUWBJ0IvQy3STCIkgoehFJIKCHkSCkLRBVNJT0EPQQ4W9bFmJDS0TSmwbc65ku7ZrY96dHsQ1yQfnB+flcPj9/985h0O+iz5nVtJGwGwjprEHg6N92IHErKSNTB9fcKmmDPa9qb3gdt9dmJg48hIQIswudaOwt7fXmhZXbzOhTdDgr7ZW3+rv78/lQWC2qaYMQIBSnjasrBqGAAawBqJ3ywDCACInzlod2dOT+xO1CtUFbVeFcHQawPM8iJjGGt7aPakK1Vg1Y02FYnu8AMkA7IVRJqfqv9YqlBNzWHIkTXLc0F4IImZGT09Pa06CU/udfeL3+5Nb9aD7Uvf1ZVv62pIjWbY3aP9jTgtHh4eHJzeBtqOBgQFdNB5t/x6xD4aCLksiUbGb2ZXNFzBzUQEEO4AgA8GOwrxuW9/ZJPEFgGUA5wuzRYPW7dBTAO1EH807Bq1LewRAD2jnCl4orkcbIUnj887me3M+n6+Vmbc/tUJ5PB45q9eHY01xo5zYlTT/0o8WZY1oSiYKnJybP/Q45lw0LDYmMNv2Q2biThHAlgtJBB3wvgHQWgBqAdAC4ACgo2+zdVl3JKSh4adYqkgAUUzsutx9R6lWPakK1Vg5VX7DaHx1P502HgbgBmAGCACiAAIAjwC6QDxeMmldEW5antV3gihWkhG8IhN3fjkWsYCA3JpgqXEsXPkcavwAwA9wABACzM3h/42e6gOQPzkiiGKlilSpmjIwL5UqVU1TZ2Y+dY0XOwCxJCN4D76u+XfYHg4VDQGAvyJXT3w3dEsJAAAAAElFTkSuQmCC"""
