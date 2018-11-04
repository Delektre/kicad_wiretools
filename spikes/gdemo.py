#!/usr/bin/env python

from math import sin, cos, pi, fabs, tan, sqrt
from graphics import *
    

def draw_hash(screen, angle, left, top, right, bottom, offset_left=5, offset_right=5, offset_top=5, offset_bottom=5):
    x = left
    y = top

    width = 5
    
    real_left = left + offset_left
    real_right = right - offset_right
    real_top = top + offset_top
    real_bottom = bottom - offset_bottom
    
    line = Line(Point(real_left, real_top),
                Point(real_right, real_top))
    line.setOutline('red')
    line.setWidth(width)
    line.draw(screen)

    line = Line(Point(real_left, real_bottom),
                Point(real_right, real_bottom))
    line.setOutline('red')
    line.setWidth(width)
    line.draw(screen)

    line = Line(Point(real_left, real_top),
                Point(real_left, real_bottom))
    line.setOutline('red')
    line.setWidth(width)
    line.draw(screen)

    line = Line(Point(real_right, real_top),
                Point(real_right, real_bottom))
    line.setOutline('red')
    line.setWidth(width)
    line.draw(screen)
    

    alfa = angle*pi/180.0
    

    pitch = 20
    nn = sqrt(pow(real_bottom - real_top, 2) +
              pow(real_right - real_left, 2)) / (pitch/cos(alfa)) - 1

    n = 0
    xx = 0
    yy = 0

    my = real_bottom - real_top
    mx = real_right - real_left

    dy = pitch / cos(alfa)

    print "pitch({}, -> {}) => n={}".format(pitch, dy, nn)
    
    while n < nn:
        n += 1

        zy = n * pitch / cos(alfa)
        zx = zy / tan(alfa)       

        ax0 = real_left
        ax1 = zx + real_left
        ay0 = real_top + zy
        ay1 = real_top

        if zy > my:
            ax0 += (zy-my) / tan(alfa)
            ay0 = real_bottom
        if zx > mx:
            ay1 = real_top + ( (zx - mx) * tan(alfa) )
            ax1 = real_right            


        qx = n * pitch / cos(alfa)
        qy = qx / tan(alfa)


        bx0 = real_left
        bx1 = qx+real_left
        by0 = real_bottom-qy
        by1 = real_bottom

        if qy > my:
            by0 = real_top
            bx0 += (qy-my) * tan(alfa)
        if qx > mx:
            bx1 = real_right
            by1 -= ((qx-mx) / tan(alfa))
        print "Got[{}]: ({}, {}, -> {}, {}) zy={}, zx={}".format(n, ax0, ay0, ax1, ay1, zy, zx)
        line = Line(Point(ax0, ay0), Point(ax1, ay1))
        line.setOutline('red')
        line.setWidth(width)
        line.draw(screen)

        print "Got[{}]: ({}, {}, -> {}, {}) qy={}, qx={}".format(n, bx0, by0, bx1, by1, qy, qx)
        line = Line(Point(bx0, by0), Point(bx1, by1))
        line.setOutline('red')
        line.setWidth(width)
        line.draw(screen)



def main():
    mx1, my1, mx2, my2 = (0, 0, 640, 640)
    x1, y1, x2, y2 = (mx1+80, my1+80, mx2-80, my2-80)

    win = GraphWin('Main', mx2-mx1, my2-my1)

    pad = Rectangle(Point(x1, y1), Point(x2, y2))
    pad.setOutline('gray')
    pad.draw(win)

    oleft = 5
    oright = 5
    otop = 5
    obottom = 5

    ang = 22.5

    draw_hash(win, ang, x1, y1, x2, y2, oleft, oright, otop, obottom)

    line = Line(Point(20,20), Point(200,200))
    line.setWidth(10)
    line.setOutline('black')
    line.draw(win)
    
    # wait for mouse event
    win.getMouse()
    win.close()


if __name__ == '__main__':
    main()

