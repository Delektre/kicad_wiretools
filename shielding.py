# Copyright (c) 2018 Tommi Rintala, New Cable Corporation Ltd.

# Copyright (c) 2018 Tommi Rintala, New Cable Corporation Ltd.

import re
import datetime
import traceback
import wx
import wx.aui
import base64
from wx.lib.embeddedimage import PyEmbeddedImage

import pcbnew



DEFAULT_OFFSET_LEFT_MM = 5
DEFAULT_OFFSET_RIGHT_MM = 5
DEFAULT_OFFSET_TOP_MM = 1
DEFAULT_OFFSET_BOTTOM_MM = 1
DEFAULT_LAYER_SOURCE = pcbnew.Edge_Cuts
DEFAULT_LAYER_TARGET = pcbnew.F_Fab
DEFAULT_LINE_WIDTH_MM = 0.3
DEFAULT_LINE_ANGLE = 45

def debug_dialog(msg, exception=None):
    if exception:
        msg = '\n'.join((msg, str(exception), traceback.format_exc()))
        dlg = wx.MessageDialog(None, msg, '', wx.OK)
        dlg.ShowModal()
        dlg.Destroy()

class HashShieldGenerator(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "Generate Hash Shielding"
        self.category = "Modify PCB"
        self.description = "Generate hash shielding for PCB"

        self._board = pcbnew.GetBoard()
        bbox = pcbnew.GetBoard().GetBoundingBox()

        self.flag_delete_old = True

        self.minx = bbox.GetRight()
        self.maxx = bbox.GetLeft()
        self.miny = bbox.GetBottom()
        self.maxy = bbox.GetTop()

        self.offset_top = pcbnew.FromMM(DEFAULT_OFFSET_TOP_MM)
        self.offset_bottom = pcbnew.FromMM(DEFAULT_OFFSET_BOTTOM_MM)
        self.offset_left = pcbnew.FromMM(DEFAULT_OFFSET_LEFT_MM)
        self.offset_right = pcbnew.FromMM(DEFAULT_OFFSET_RIGHT_MM)

        self.layer_source = DEFAULT_LAYER_SOURCE
        self.layer_target = DEFAULT_LAYER_TARGET

    def find_bounding_box(self, layerid=-1):
        """Find bounding box, defaults to EdgeCuts -layer"""
        if layerid == -1:
            print "Fail back to default layer: {}".format(DEFAULT_LAYER_SOURCE)
            layerid = DEFAULT_LAYER_SOURCE
        else:
            print "Finding limits from layer {}".format(layerid)

        if not self._board:
            raise Exception("Board missing!")

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


    def Run(self):
        pcb = pcbnew.GetBoard()
        self._board = pcb
        self.find_bounding_box()
        for draw in pcb.DrawingsList():
            if draw.GetClass() == 'PTEXT':
                txt = re.sub("\$date\$ [0-9]{4}-[0-9]{2}-[0-9]{2}", "$date$", draw.GetText())
                if txt == "$date$":
                    draw.SetText("$date$ %s"%datetime.date.today())
            #else:
                #print("Found object: ", draw.GetClass())
            elif draw.GetClass() == 'DRAWSEGMENT':
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
                    print "[{}, {}, {}, {}] type={}".format(
                        bbox.GetLeft(),
                        bbox.GetTop(),
                        bbox.GetRight(),
                        bbox.GetBottom(),
                        draw.GetType())
                    msg = "Found element type " + str(draw.GetType()) + " with boundingbox: (" + bbox.GetLeft() + ", " + bbox.GetTop() + " -> " + bbox.GetRight() + ", " + bbox.GetBottom() + ")"
                    print msg
                    debug_dialog(msg)
            else:
                print "Found: {}".format(draw.GetClass())

        box = " (" + str(pcbnew.ToMM(self.minx)) + ", " + str(pcbnew.ToMM(self.miny)) + " -> " + str(pcbnew.ToMM(self.maxx)) + ", " + str(pcbnew.ToMM(self.maxy)) + ")"

        # show dialog and ask stuff

        class DisplayDialog(wx.Dialog):
            def __init__(self, parent):
                wx.Dialog.__init__(self, parent, id=wx.ID_ANY, title="Hash Shielding Generator")
                self.SetIcon(PyEmbeddedImage(shield_generator_ico_b64).GetIcon())
                self.panel = wx.Panel(self)

                self.action_go = False
                self.delete_old = True

                #self.ct = 0
                self.source_layer = DEFAULT_LAYER_SOURCE
                self.target_layer = DEFAULT_LAYER_TARGET
                self.lineWidth = DEFAULT_LINE_WIDTH_MM
                self.pitch = 10 * self.lineWidth
                self.angle = DEFAULT_LINE_ANGLE
                self.offset_top = DEFAULT_OFFSET_TOP_MM
                self.offset_left = DEFAULT_OFFSET_LEFT_MM
                self.offset_right = DEFAULT_OFFSET_RIGHT_MM
                self.offset_bottom = DEFAULT_OFFSET_BOTTOM_MM

                pcb = pcbnew.GetBoard()

                self.layertable = {}
                layertable = []
                numlayers = pcbnew.PCB_LAYER_ID_COUNT
                for ind in range(numlayers):
                    #layertable[ind] = self._board.GetLayerName(ind)
                    layertable.append(pcb.GetLayerName(ind))
                    self.layertable[pcb.GetLayerName(ind)] = ind

                self.combo_source = wx.ComboBox(self.panel, choices=layertable)
                self.combo_source.SetSelection(self.source_layer)
                self.combo_source.Bind(wx.EVT_COMBOBOX, self.onComboSource)

                self.title_source = wx.StaticText(self.panel, label="Souce layer")

                self.combo_target = wx.ComboBox(self.panel, choices=layertable)
                self.combo_target.SetSelection(self.target_layer)
                self.combo_target.Bind(wx.EVT_COMBOBOX, self.onComboTarget)

                self.title_target = wx.StaticText(self.panel, label="Target layer")

                self.spin_angle = wx.TextCtrl(self.panel, value=str(self.angle), style=wx.TE_READONLY)
                self.title_angle = wx.StaticText(self.panel, label="Angle")

                self.title_offset_left = wx.StaticText(self.panel, label="Offset left [mm]")
                self.text_offset_left = wx.TextCtrl(self.panel, value=str(self.offset_left))
                self.text_offset_left.Bind(wx.EVT_TEXT, self.onTextChange)
                self.title_offset_right = wx.StaticText(self.panel, label="Offset right [mm]")
                self.text_offset_right = wx.TextCtrl(self.panel, value=str(self.offset_right))
                self.text_offset_right.Bind(wx.EVT_TEXT, self.onTextChange)
                self.title_offset_top = wx.StaticText(self.panel, label="Offset top [mm]")
                self.text_offset_top = wx.TextCtrl(self.panel, value=str(self.offset_top))
                self.text_offset_top.Bind(wx.EVT_TEXT, self.onTextChange)
                self.title_offset_bottom = wx.StaticText(self.panel, label="Offset bottom [mm]")
                self.text_offset_bottom = wx.TextCtrl(self.panel, value=str(self.offset_bottom))
                self.text_offset_bottom.Bind(wx.EVT_TEXT, self.onTextChange)
                self.title_linewidth = wx.StaticText(self.panel, label="Line width [mm]")
                self.title_pitch = wx.StaticText(self.panel, label="Pitch [mm]")

                self.spin_angle.Bind(wx.EVT_TEXT, self.onTextChange)
                self.text_linewidth = wx.TextCtrl(self.panel, value=str(self.lineWidth))
                self.text_linewidth.Bind(wx.EVT_TEXT, self.onTextChange)
                self.text_pitch = wx.TextCtrl(self.panel, value=str(self.pitch))
                self.text_pitch.Bind(wx.EVT_TEXT, self.onTextChange)

                # set sizer
                self.window_sizer = wx.BoxSizer()
                self.window_sizer.Add(self.panel, 1, wx.ALL | wx.EXPAND)

                self.button_run = wx.Button(self.panel, label="Run")
                self.button_run.Bind(wx.EVT_BUTTON, self.onButtonRun)

                self.button_cancel = wx.Button(self.panel, label="Cancel")
                self.button_cancel.Bind(wx.EVT_BUTTON, self.onButtonCancel)

                self.Bind(wx.EVT_CLOSE, self.onButtonCancel)

                self.title_delete_old = wx.StaticText(self.panel, label="Delete old?")
                self.checkbox_delete_old = wx.CheckBox(self.panel)
                self.checkbox_delete_old.Bind(wx.EVT_TEXT, self.onCheckBox)

                # set sizer for panel content
                self.sizer = wx.GridBagSizer(10, 0)
                self.sizer.Add(self.title_delete_old, (0, 0))
                self.sizer.Add(self.checkbox_delete_old, (0, 1))
                self.sizer.Add(self.title_source, (1, 0))
                self.sizer.Add(self.combo_source, (1, 1))
                self.sizer.Add(self.title_target, (2, 0))
                self.sizer.Add(self.combo_target, (2, 1))
                self.sizer.Add(self.title_linewidth, (3, 0))
                self.sizer.Add(self.text_linewidth, (3, 1))
                self.sizer.Add(self.title_pitch, (4, 0))
                self.sizer.Add(self.text_pitch, (4, 1))
                self.sizer.Add(self.title_angle, (5, 0))
                self.sizer.Add(self.spin_angle, (5, 1))
                self.sizer.Add(self.title_offset_left, (6, 0))
                self.sizer.Add(self.text_offset_left, (6, 1))
                self.sizer.Add(self.title_offset_right, (7, 0))
                self.sizer.Add(self.text_offset_right, (7, 1))
                self.sizer.Add(self.title_offset_top, (8, 0))
                self.sizer.Add(self.text_offset_top, (8, 1))
                self.sizer.Add(self.title_offset_bottom, (9, 0))
                self.sizer.Add(self.text_offset_bottom, (9, 1))
                self.sizer.Add(self.button_run, (10, 0))
                self.sizer.Add(self.button_cancel, (10, 1))


                # border for nice look
                self.border = wx.BoxSizer()
                self.border.Add(self.sizer, 1, wx.ALL | wx.EXPAND, 5)
                self.panel.SetSizerAndFit(self.border)
                self.SetSizerAndFit(self.window_sizer)

            def onCheckBox(self, event):
                self.delete_old = self.checkbox_delete_old.GetValue()

            def onButtonRun(self, event):
                self.action_go = True
                event.Skip()
                self.onTextChange(None)
                self.Close()

            def onButtonCancel(self, event):
                event.Skip()
                self.Close()

            def onComboSource(self, event):
                self.source_layer = self.combo_source.GetSelection()

            def onComboTarget(self, event):
                self.target_layer = self.combo_target.GetSelection()

            def onTextChange(self, event):
                self.lineWidth = self.text_linewidth.GetValue()
                self.pitch = self.text_pitch.GetValue()
                self.angle = self.spin_angle.GetValue()
                self.offset_left = self.text_offset_left.GetValue()
                self.offset_right = self.text_offset_right.GetValue()
                self.offset_top = self.text_offset_top.GetValue()
                self.offset_bottom = self.text_offset_bottom.GetValue()

        frame = DisplayDialog(None)
        frame.Center()
        frame.ShowModal()
        # get the values
        if frame.action_go:
            self.layer_source = int(frame.source_layer)
            self.layer_target = int(frame.target_layer)
            self.line_width = float(frame.lineWidth)
            self.line_pitch = float(frame.pitch)
            self.line_angle = float(frame.angle)

            self.offset_left = pcbnew.FromMM(float(frame.offset_left))
            self.offset_right = pcbnew.FromMM(float(frame.offset_right))
            self.offset_top = pcbnew.FromMM(float(frame.offset_top))
            self.offset_bottom = pcbnew.FromMM(float(frame.offset_bottom))

            print "Source layer: {} Target layer: {}".format(self.layer_source, self.layer_target)
            print "Line Angle: {}".format(self.line_angle)
            print "Line Width: {}".format(self.line_width)
            print "Line Pitch: {}".format(self.line_pitch)

            print "Offsets {}-{}/{}-{}".format(self.offset_left, self.offset_top,
                                               self.offset_right, self.offset_bottom)

            self.find_bounding_box(self.layer_source)

            print "Bounding box: ({}, {} -> {}, {})".format(self.minx, self.miny,
                                                            self.maxx, self.maxy)

            # create shielding
            self.draw_shielding(self.line_width, self.layer_target)

        else:
            print "Cancelled shielding creation!"

        frame.Destroy()

        print "Final result:"
        print box

    def draw_outline_and_hash(self, width, layer):
        PADDING_mm = 0.0
        zx1 = self.minx
        zx2 = self.maxx
        zy1 = self.miny
        zy2 = self.maxy
        #deltax = (zx2 - zx1)
        #deltay = (zy2 - zy1)
        zx1 += self.offset_left
        zx2 -= self.offset_right
        zy1 += self.offset_top
        zy2 -= self.offset_bottom

        # intellity check
        if zy1 > zy2:
            print "Cannot draw hash: y2 > y1!!"
            return

        zx1 += PADDING_mm
        zx2 -= PADDING_mm
        zy1 += PADDING_mm
        zy2 -= PADDING_mm

        # fix -> not using centerline, but edge of hashline
        zx1 += width / 2
        zx2 -= width / 2
        zy1 += width / 2
        zy2 -= width / 2

        print "draw_shielding: ({}, {} -> {}, {})".format(zx1, zy1, zx2, zy2)

        self.draw_segment(zx1, zy1, zx2, zy1, width, layer)
        self.draw_segment(zx2, zy1, zx2, zy2, width, layer)
        self.draw_segment(zx2, zy2, zx1, zy2, width, layer)
        self.draw_segment(zx1, zy2, zx1, zy1, width, layer)

        # TODO: Fix this calculate accurate step from coverage:
        try:
            if self.line_pitch:
                step = pcbnew.FromMM(float(self.line_pitch))
            else:
                # failback
                step = pcbnew.FromMM(float(width * 10))
        except Exception as ouch:
            step = pcbnew.FromMM(3)


        ent = -(zy2-zy1)
        print "Starting from {} with step {}".format(ent, step)
        lines_drawn = 0
        while ent < (zx2-zx1):
            self.draw_line(zx1+ent, zy1, zx1+ent+(zy2-zy1), zy2, zx1, zy1, zx2, zy2, width, layer)
            self.draw_line(zx1+ent, zy2, zx1+ent+(zy2-zy1), zy1, zx1, zy1, zx2, zy2, width, layer)
            ent += step
            lines_drawn += 1
            #print "ent {}, lines drawn: {}".format(ent, lines_drawn)

    def draw_shielding(self, width_mm=DEFAULT_LINE_WIDTH_MM, layer=DEFAULT_LAYER_TARGET):

        if self.flag_delete_old:
            drawings = [draw for draw in self._board.DrawingsList() if draw.GetClass() == 'DRAWSEGMENT' and draw.GetLayer() == layer and draw.GetType() == 0]
            for draw in drawings:
                self._board.Remove(draw)

        layertable = {}

        numlayers = pcbnew.PCB_LAYER_ID_COUNT
        for ind in range(numlayers):
            layertable[ind] = self._board.GetLayerName(ind)
            msg = "{} {}".format(ind, self._board.GetLayerName(ind))
            print msg
            self.draw_text(pcbnew.FromMM(30), pcbnew.FromMM(100 + ind*8), msg)

        self.draw_outline_and_hash(pcbnew.FromMM(width_mm), layer)
        pcbnew.Refresh()

    def draw_line(self, pos_x1, pos_y1, pos_x2, pos_y2, rx1, ry1, rx2, ry2, width, layer_id):
        px1 = pos_x1
        px2 = pos_x2
        py1 = pos_y1
        py2 = pos_y2
        deltaz = (pos_y2-pos_y1)/(pos_x2-pos_x1)

        if pos_y1 > pos_y2:
            if px1 < rx1:
                # left up cut
                px1 = rx1
                py1 = ry1 + (rx1-pos_x1)*deltaz - (py2-py1)
            if px2 > rx2:
                px2 = rx2
                py2 = ry2 - (pos_x2-rx2)*deltaz + (py2-py1)
        else:
            if px1 < rx1:
                # left cut
                px1 = rx1
                py1 = ry1 + (rx1-pos_x1)*deltaz
            if px2 > rx2:
                # right cut
                px2 = rx2
                py2 = ry2 - (pos_x2-rx2)*deltaz
        self.draw_segment(px1, py1, px2, py2, width, layer_id)

    def draw_segment(self, pos_x0, pos_y0, pos_x1, pos_y1, width, layer_id):
        #print("Drawing: ", pos_x0, ", ", pos_y0, " -> ", pos_x1, ", ", pos_y1, " W", width)
        print "Drawing: ({}, {}) -> ({}, {}) W {}".format(pos_x0, pos_y0, pos_x1, pos_y1, width)
        drawseg = pcbnew.DRAWSEGMENT(self._board)
        self._board.Add(drawseg)
        drawseg.SetStart(pcbnew.wxPoint(pos_x0, pos_y0))
        drawseg.SetEnd(pcbnew.wxPoint(pos_x1, pos_y1))
        drawseg.SetLayer(layer_id)
        drawseg.SetWidth(width)


    def draw_text(self, xpos, ypos, message):
        text = pcbnew.TEXTE_PCB(self._board)
        self._board.Add(text)
        text.SetTextX(xpos)
        text.SetTextY(ypos)
        text.SetText(message)
        #ts.SetTextSize(pcbnew.FromMM(5))

shield_generator_ico_b64 = \
"""iVBORw0KGgoAAAANSUhEUgAAABIAAAASCAYAAABWzo5XAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAKYQAACmEB/MxKJQAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAJrSURBVDiNnZRRSFNxFMa/s3vlLje3y0bpdKkwrcTCxbChQUIPUWBJ0IvQy3STCIkgoehFJIKCHkSCkLRBVNJT0EPQQ4W9bFmJDS0TSmwbc65ku7ZrY96dHsQ1yQfnB+flcPj9/985h0O+iz5nVtJGwGwjprEHg6N92IHErKSNTB9fcKmmDPa9qb3gdt9dmJg48hIQIswudaOwt7fXmhZXbzOhTdDgr7ZW3+rv78/lQWC2qaYMQIBSnjasrBqGAAawBqJ3ywDCACInzlod2dOT+xO1CtUFbVeFcHQawPM8iJjGGt7aPakK1Vg1Y02FYnu8AMkA7IVRJqfqv9YqlBNzWHIkTXLc0F4IImZGT09Pa06CU/udfeL3+5Nb9aD7Uvf1ZVv62pIjWbY3aP9jTgtHh4eHJzeBtqOBgQFdNB5t/x6xD4aCLksiUbGb2ZXNFzBzUQEEO4AgA8GOwrxuW9/ZJPEFgGUA5wuzRYPW7dBTAO1EH807Bq1LewRAD2jnCl4orkcbIUnj887me3M+n6+Vmbc/tUJ5PB45q9eHY01xo5zYlTT/0o8WZY1oSiYKnJybP/Q45lw0LDYmMNv2Q2biThHAlgtJBB3wvgHQWgBqAdAC4ACgo2+zdVl3JKSh4adYqkgAUUzsutx9R6lWPakK1Vg5VX7DaHx1P502HgbgBmAGCACiAAIAjwC6QDxeMmldEW5antV3gihWkhG8IhN3fjkWsYCA3JpgqXEsXPkcavwAwA9wABACzM3h/42e6gOQPzkiiGKlilSpmjIwL5UqVU1TZ2Y+dY0XOwCxJCN4D76u+XfYHg4VDQGAvyJXT3w3dEsJAAAAAElFTkSuQmCC"""
