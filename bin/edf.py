#!/usr/bin/env python

import efinterp
from sys import *
from math import *
from numpy import *
from matplotlib.pyplot import *
from matplotlib.path import *
from matplotlib.patches import *
from matplotlib.image import *
from scipy.interpolate import CloughTocher2DInterpolator
###############################################################################
def savitzky_golay(y, window_size, order, deriv=0, rate=1):
    import numpy as np
    from math import factorial

    try:
        window_size = np.abs(np.int(window_size))
        order = np.abs(np.int(order))
    except ValueError, msg:
        raise ValueError("window_size and order have to be of type int")
    if window_size % 2 != 1 or window_size < 1:
        raise TypeError("window_size size must be a positive odd number")
    if window_size < order + 2:
        raise TypeError("window_size is too small for the polynomials order")
    order_range = range(order+1)
    half_window = (window_size -1) // 2
    # precompute coefficients
    b = np.mat([[k**i for i in order_range] for k in range(-half_window, half_window+1)])
    m = np.linalg.pinv(b).A[deriv] * rate**deriv * factorial(deriv)
    # pad the signal at the extremes with
    # values taken from the signal itself
    firstvals = y[0] - np.abs( y[1:half_window+1][::-1] - y[0] )
    lastvals = y[-1] + np.abs(y[-half_window-1:-1][::-1] - y[-1])
    y = np.concatenate((firstvals, y, lastvals))
    return np.convolve( m[::-1], y, mode='valid')
###############################################################################
def smooth_track(track):
    lt = []
    lx = []
    ly = []
    for particle in track:
        lt.append(particle[5])
        lx.append(particle[0])
        ly.append(particle[1])
    t = array(lt)
    x = array(lx)
    y = array(ly)
    if len(t) > 51:
        win = 51
    else:
        win = len(t) - 4
        if win%2==0:
            win = win - 1
    xsg = savitzky_golay(x, window_size=win, order=3)
    ysg = savitzky_golay(y, window_size=win, order=3)

    for i in range(len(track)):
        track[i] = (xsg[i], ysg[i], track[i][0], track[i][1], track[i][2], 
                track[i][3], track[i][4], track[i][5], track[i][6], track[i][7])
###############################################################################
def read_tracks(filename, ex_interp, ey_interp):
    file = open(filename)
    file.readline() # bypass header

    x0 = 536.0
    y0 = 565.0

    tracks = []
    track = []
    last_track_id = -1
    for line in file:
        data = line.split()
        track_id = int(data[0])
        time = float(data[1]) * 0.044
        x = (float(data[2]) - x0)/ 2.47 * 1e-6
        y = (float(data[3]) - y0)/ 2.47 * 1e-6
        w = float(data[4]) / 2.47 * 1e-6
        h = float(data[5]) / 2.47 * 1e-6
        ey = ey_interp(x, y)
        ex = ex_interp(x, y)
        angle = float(data[6])
        if track_id != last_track_id and last_track_id > 0:
            if len(track) > 100:
                tracks.append(track)
            track = []
        last_track_id = track_id
        track.append((x,y, w,h, angle, time, ex, ey))
    if len(track) > 100:
        tracks.append(track)
    return tracks
###############################################################################
def draw_contour(x, y, z):
    #contour(x, y, z, 10, linewidths=0.5, colors='k')
    contourf(x, y, z, 500, cmap=cm.jet)
    colorbar()
    #scatter(coord[:,0], coord[:,1], marker='o', s=0.01)
###############################################################################
def get_ek_mobi(tracks):
    newtracks = []
    import matplotlib.pyplot as plt
    f, ax = plt.subplots(1,3)
    for track in tracks:
        #smooth_track(track)
        t  = []
        lx = []
        ly = []
        #lsx = []
        lsy = []
        ex = []
        ey = []
        if track[0][0] > -1.5e-4 or track[-1][0] < 1.5e-4:
            continue
        for particle in track:
            lx.append(particle[0])
            ly.append(particle[1])
            #lsx.append(particle[2])
            #lsy.append(particle[3])
            t.append(particle[5])
            ex.append(particle[6])
            ey.append(particle[7])
#        if len(t) > 51:
#            win = 51
#        else:
#            win = len(t) - 4
#            if win%2==0:
#                win = win - 1
#        lsx = savitzky_golay(lx, window_size=win, order=3)
#        lsy = savitzky_golay(ly, window_size=win, order=3)
        lx = array(lx)
        ly = array(ly)
        ex = array(ex)
        ey = array(ey)
        vx = gradient(array(lx))
        vy = gradient(array(ly))
        vsx = savitzky_golay(vx, window_size=31, order=3)
        vsy = savitzky_golay(vy, window_size=31, order=3)

        #vsx = gradient(array(lsx))
        mx = vsx / ex
        my = vsy / ey
        if abs(mx[0] - mx[30]) > 1e-9:
            continue
        mek = sum(mx[:5])/5.0
        vekx = ex * mek
        veky = ey * mek
        #print len(vx), len(vekx), vx, vekx
        vedx = vx - vekx
        vedy = vy - veky
        trimn = 1
        track = {'vx':vx, 'vy':vy, \
                'ex':ex, 'ey':ey, 'mx':mx, 'my':my, 't':t, 'mek':mek}
        ax[0].plot(lx, ly, '.')
        #ax[1].plot(newlx[:-trimn], vx[:-trimn])
        ax[1].plot(lx, vsx)
        #ax[2].plot(lx, lsx)
        ax[2].plot(lx, mx)
        newtracks.append(track)
    plt.show()
    return newtracks
###############################################################################
ex, ey, e2 = efinterp.ef_interp('ef.txt', 'geo.txt', rotated=True, inverse=True)
#gx, gy, gz = efinterp.draw_interp(e2, resolution=300)
#e2gx, e2gy = efinterp.draw_e2_gradient(e2, gx, gy, gz)
#e2gx, e2gy = gradient(gz)
tracks = read_tracks(argv[1], ex, ey)
tracks = get_ek_mobi(tracks)
get_efline = ()
