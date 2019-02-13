# Copyright (c) 2018 Tommi Rintala, New Cable Corporation Ltd.

import re
import datetime
import traceback
import wx
import wx.aui
import base64
from math import cos, sin, sqrt, pow, pi, tan
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

def between(value, low_limit, high_limit):
    return value >= low_limit and value <= high_limit

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

        print "find_bounding_box( {} )".format(layerid)

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
                    try:
                        bbox = draw.GetBoundingBox()
                        msg = "Found element type " + str(draw.GetType()) + " with boundingbox: (" + bbox.GetLeft() + ", " + bbox.GetTop() + " -> " + bbox.GetRight() + ", " + bbox.GetBottom() + ")"
                    except Exception as ouch:
                        print "Got exception: {}".format(ouch)


    def Run(self):
        print("-------------------------")
        print("Starting plugin: shielding")
        pcb = pcbnew.GetBoard()
        self._board = pcb
        self.find_bounding_box()
        print "got bounding box"
        for draw in pcb.DrawingsList():
            if draw.GetClass() == 'PTEXT':
                txt = re.sub("\$date\$ [0-9]{4}-[0-9]{2}-[0-9]{2}", "$date$", draw.GetText())
                if txt == "$date$":
                    draw.SetText("$date$ %s"%datetime.date.today())
            else:
                print "Found: {}".format(draw.GetClass())

            box = " (" + str(self.minx) + ", " + str(self.miny) + " -> " + str(self.maxx) + ", " + str(self.maxy) + ")"
            print "Bounding box: "
            print box

        # show dialog and ask stuff

        class DisplayDialog(wx.Dialog):
            def __init__(self, parent):
                wx.Dialog.__init__(self, parent, id=wx.ID_ANY, title="Hash Shielding Generator")
                self.SetIcon(PyEmbeddedImage(shield_generator_ico_b64).GetIcon())
                self.panel = wx.Panel(self)

                self.action_go = False
                self.delete_old = True

                self.source_layer = DEFAULT_LAYER_SOURCE
                self.target_layer = DEFAULT_LAYER_TARGET
                self.line_width = DEFAULT_LINE_WIDTH_MM
                self.pitch = 10 * self.line_width
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
                # -----------------------------------------
                self.combo_source = wx.ComboBox(self.panel, choices=layertable)
                self.combo_source.SetSelection(self.source_layer)
                self.combo_source.Bind(wx.EVT_COMBOBOX, self.readvalues)
                self.title_source = wx.StaticText(self.panel, label="Source layer")
                # -----------------------------------------
                self.combo_target = wx.ComboBox(self.panel, choices=layertable)
                self.combo_target.SetSelection(self.target_layer)
                self.combo_target.Bind(wx.EVT_COMBOBOX, self.readvalues)
                self.title_target = wx.StaticText(self.panel, label="Target layer")
                # -----------------------------------------
                self.title_angle = wx.StaticText(self.panel, label="Angle [0-90]")

                self.spin_angle = wx.TextCtrl(self.panel, value=str(self.angle))
                self.spin_angle.Bind(wx.EVT_TEXT, self.readvalues)
                # -----------------------------------------
                self.title_offset_left = wx.StaticText(self.panel, label="Offset left [mm]")
                self.text_offset_left = wx.TextCtrl(self.panel, value=str(self.offset_left))
                self.text_offset_left.Bind(wx.EVT_TEXT, self.readvalues)
                # -----------------------------------------
                self.title_offset_right = wx.StaticText(self.panel, label="Offset right [mm]")
                self.text_offset_right = wx.TextCtrl(self.panel, value=str(self.offset_right))
                self.text_offset_right.Bind(wx.EVT_TEXT, self.readvalues)
                # -----------------------------------------
                self.title_offset_top = wx.StaticText(self.panel, label="Offset top [mm]")
                self.text_offset_top = wx.TextCtrl(self.panel, value=str(self.offset_top))
                self.text_offset_top.Bind(wx.EVT_TEXT, self.readvalues)
                # -----------------------------------------
                self.title_offset_bottom = wx.StaticText(self.panel, label="Offset bottom [mm]")
                self.text_offset_bottom = wx.TextCtrl(self.panel, value=str(self.offset_bottom))
                self.text_offset_bottom.Bind(wx.EVT_TEXT, self.readvalues)
                # -----------------------------------------
                self.title_linewidth = wx.StaticText(self.panel, label="Line width [mm]")
                self.text_linewidth = wx.TextCtrl(self.panel, value=str(self.line_width))
                self.text_linewidth.Bind(wx.EVT_TEXT, self.readvalues)
                # -----------------------------------------
                self.title_pitch = wx.StaticText(self.panel, label="Pitch [mm]")
                self.text_pitch = wx.TextCtrl(self.panel, value=str(self.pitch))
                self.text_pitch.Bind(wx.EVT_TEXT, self.readvalues)
                # -----------------------------------------
                self.title_coverage = wx.StaticText(self.panel, label="Coverage %")
                self.text_coverage = wx.StaticText(self.panel, label="-")
                # -----------------------------------------
                # set sizer
                self.window_sizer = wx.BoxSizer()
                self.window_sizer.Add(self.panel, 1, wx.ALL | wx.EXPAND)

                self.button_run = wx.Button(self.panel, label="Run")
                self.button_run.Bind(wx.EVT_BUTTON, self.onButtonRun)

                self.button_cancel = wx.Button(self.panel, label="Cancel")
                self.button_cancel.Bind(wx.EVT_BUTTON, self.onButtonCancel)

                self.Bind(wx.EVT_CLOSE, self.onButtonCancel)

                self.title_delete_old = wx.StaticText(self.panel, label="Delete old values?")
                self.checkbox_delete_old = wx.CheckBox(self.panel)
                self.checkbox_delete_old.SetValue(self.delete_old)
                self.checkbox_delete_old.Bind(wx.EVT_TEXT, self.readvalues)

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
                self.sizer.Add(self.title_coverage, (5, 0))
                self.sizer.Add(self.text_coverage, (5, 1))
                self.sizer.Add(self.title_angle, (6, 0))
                self.sizer.Add(self.spin_angle, (6, 1))
                self.sizer.Add(self.title_offset_left, (7, 0))
                self.sizer.Add(self.text_offset_left, (7, 1))
                self.sizer.Add(self.title_offset_right, (8, 0))
                self.sizer.Add(self.text_offset_right, (8, 1))
                self.sizer.Add(self.title_offset_top, (9, 0))
                self.sizer.Add(self.text_offset_top, (9, 1))
                self.sizer.Add(self.title_offset_bottom, (10, 0))
                self.sizer.Add(self.text_offset_bottom, (10, 1))
                self.sizer.Add(self.button_run, (11, 0))
                self.sizer.Add(self.button_cancel, (11, 1))

                # border for nice look
                self.border = wx.BoxSizer()
                self.border.Add(self.sizer, 1, wx.ALL | wx.EXPAND, 5)
                self.panel.SetSizerAndFit(self.border)
                self.SetSizerAndFit(self.window_sizer)

                print "Dialog init completed."


            def onButtonRun(self, event):
                print "--onButtonRun()"
                self.action_go = True
                event.Skip()
                self.readvalues()
                print "--returned from readvalues()"
                self.Close()
                print "done self.Close()"

            def readvalues(self, event=None):
                print "--readvalues()"
                self.line_width = self.text_linewidth.GetValue()
                self.pitch = self.text_pitch.GetValue()
                if self.line_width and self.pitch:
                    pitch = float(self.pitch)
                    width = float(self.line_width)
                    if pitch > width and pitch > 0 and width > 0 and pitch - width > 0:
                        coverage = 100.0 * pow((pitch - width), 2) / pow(pitch, 2)
                        self.text_coverage.SetLabel(str('{0:.1f}'.format(coverage)))
                    else:
                        self.text_coverage.SetLabel('-')
                self.angle = self.spin_angle.GetValue()
                self.offset_left = self.text_offset_left.GetValue()
                self.offset_right = self.text_offset_right.GetValue()
                print "get offset-top"
                self.offset_top = self.text_offset_top.GetValue()
                print "get offset-bottom"
                self.offset_bottom = self.text_offset_bottom.GetValue()
                print "get checkbox value"
                self.delete_old = self.checkbox_delete_old.GetValue()
                print "get source layer"
                self.source_layer = self.combo_source.GetSelection()
                print "get target layer"
                self.target_layer = self.combo_target.GetSelection()

            def onButtonCancel(self, event):
                event.Skip()
                self.Close()

       

        frame = DisplayDialog(None)
        frame.Center()
        frame.ShowModal()

        print "-> Dialog closed"

        # get the values
        if frame.action_go:
            self.layer_source = int(frame.source_layer)
            self.layer_target = int(frame.target_layer)
            self.line_width = float(frame.line_width)
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
        #print box

    def draw_outline_and_hash(self, width, layer):
        PADDING_mm = 0.0
        real_left = self.minx
        real_right = self.maxx
        real_top = self.miny
        real_bottom = self.maxy

        real_left += self.offset_left
        real_right -= self.offset_right
        real_top += self.offset_top
        real_bottom -= self.offset_bottom

        # intellity check
        if real_top > real_bottom:
            print "Cannot draw hash: y2 > y1!!"
            return

        real_left += PADDING_mm
        real_right -= PADDING_mm
        real_top += PADDING_mm
        real_bottom -= PADDING_mm

        # fix -> not using centerline, but edge of hashline
        real_left += width / 2
        real_right -= width / 2
        real_top += width / 2
        real_bottom -= width / 2

        print "draw_shielding: ({}, {} -> {}, {})".format(real_left, real_top, real_right, real_bottom)

        self.draw_segment(real_left, real_top, real_right, real_top, width, layer, 'top border')
        self.draw_segment(real_right, real_top, real_right, real_bottom, width, layer, 'right border')
        self.draw_segment(real_right, real_bottom, real_left, real_bottom, width, layer, 'bottom border')
        self.draw_segment(real_left, real_bottom, real_left, real_top, width, layer, 'left border')

 

        if not self.line_pitch:
            pitch = pcbnew.FromMM(5)
        else:
            pitch = pcbnew.FromMM(float(self.line_pitch))

        diag = sqrt(pow(real_right-real_left, 2) + pow(real_bottom-real_top, 2))
        alfa = self.line_angle * pi / 180.0
        dy = pitch / cos(alfa)
        nn = diag / pitch - 1
        n = 0
        my = real_bottom - real_top
        mx = real_right - real_left

        print "diagonal={} mm pitch({} -> {}) => n={}".format(pcbnew.ToMM(diag), pcbnew.ToMM(pitch), pcbnew.ToMM(dy), nn)

        while n < nn:
            n += 1

            zy = n * dy
            zx = zy / tan(alfa)

            ax0 = real_left
            ax1 = zx + real_left
            ay0 = real_top + zy
            ay1 = real_top

            if zy > my:
                ax0 += (zy-my) / tan(alfa)
                ay0 = real_bottom
            if zx > mx:
                ay1 = real_top + ((zx-mx) * tan(alfa))
                ax1 = real_right

            qx = n * dy
            qy = qx / tan(alfa)

            bx0 = real_left
            bx1 = qx + real_left
            by0 = real_bottom - qy
            by1 = real_bottom

            if qy > my:
                by0 = real_top
                bx0 += (qy-my) * tan(alfa)
            if qx > mx:
                bx1 = real_right
                by1 -= ((qx-mx) / tan(alfa))

            if between(ax0, real_left, real_right) and between(ax1, real_left, real_right) and between(ay0, real_top, real_bottom) and between(ay1, real_top, real_bottom):
                self.draw_segment(ax0, ay0, ax1, ay1, width, layer, 'a-' + str(n))
            if between(bx0, real_left, real_right) and between(bx1, real_left, real_right) and between(by0, real_top, real_bottom) and between(by1, real_top, real_bottom):
                self.draw_segment(bx0, by0, bx1, by1, width, layer, 'b-' + str(n))


                
    def draw_shielding(self, width_mm=DEFAULT_LINE_WIDTH_MM, layer=DEFAULT_LAYER_TARGET):
        if self.flag_delete_old:
            drawings = [draw for draw in self._board.DrawingsList() if draw.GetClass() == 'DRAWSEGMENT' and draw.GetLayer() == layer and draw.GetType() == 0]
            for draw in drawings:
                self._board.Remove(draw)

        self.draw_outline_and_hash(pcbnew.FromMM(width_mm), layer)

        pcbnew.Refresh()

    def draw_layer_list(self, layer=DEFAULT_LAYER_TARGET):
        numlayers = pcbnew.PCB_LAYER_ID_COUNT
        for ind in range(numlayers):
            msg = "{} {}".format(ind, self._board.GetLayerName(ind))
            self.draw_text(pcbnew.FromMM(30), pcbnew.FromMM(100 + ind*8), msg)
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

    def draw_segment(self, pos_x0, pos_y0, pos_x1, pos_y1, width, layer_id, idx=None):
        print "Drawing[{}]: ({}, {}) -> ({}, {}) width={} mm".format(idx, pcbnew.ToMM(pos_x0), pcbnew.ToMM(pos_y0), pcbnew.ToMM(pos_x1), pcbnew.ToMM(pos_y1), pcbnew.ToMM(width))
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



# this is not image drawn by me... It is taken from example code
# TODO: Replace this with real icon
shield_generator_ico_b64 = \
"""iVBORw0KGgoAAAANSUhEUgAAABIAAAASCAYAAABWzo5XAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAKYQAACmEB/MxKJQAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAJrSURBVDiNnZRRSFNxFMa/s3vlLje3y0bpdKkwrcTCxbChQUIPUWBJ0IvQy3STCIkgoehFJIKCHkSCkLRBVNJT0EPQQ4W9bFmJDS0TSmwbc65ku7ZrY96dHsQ1yQfnB+flcPj9/985h0O+iz5nVtJGwGwjprEHg6N92IHErKSNTB9fcKmmDPa9qb3gdt9dmJg48hIQIswudaOwt7fXmhZXbzOhTdDgr7ZW3+rv78/lQWC2qaYMQIBSnjasrBqGAAawBqJ3ywDCACInzlod2dOT+xO1CtUFbVeFcHQawPM8iJjGGt7aPakK1Vg1Y02FYnu8AMkA7IVRJqfqv9YqlBNzWHIkTXLc0F4IImZGT09Pa06CU/udfeL3+5Nb9aD7Uvf1ZVv62pIjWbY3aP9jTgtHh4eHJzeBtqOBgQFdNB5t/x6xD4aCLksiUbGb2ZXNFzBzUQEEO4AgA8GOwrxuW9/ZJPEFgGUA5wuzRYPW7dBTAO1EH807Bq1LewRAD2jnCl4orkcbIUnj887me3M+n6+Vmbc/tUJ5PB45q9eHY01xo5zYlTT/0o8WZY1oSiYKnJybP/Q45lw0LDYmMNv2Q2biThHAlgtJBB3wvgHQWgBqAdAC4ACgo2+zdVl3JKSh4adYqkgAUUzsutx9R6lWPakK1Vg5VX7DaHx1P502HgbgBmAGCACiAAIAjwC6QDxeMmldEW5antV3gihWkhG8IhN3fjkWsYCA3JpgqXEsXPkcavwAwA9wABACzM3h/42e6gOQPzkiiGKlilSpmjIwL5UqVU1TZ2Y+dY0XOwCxJCN4D76u+XfYHg4VDQGAvyJXT3w3dEsJAAAAAElFTkSuQmCC"""
