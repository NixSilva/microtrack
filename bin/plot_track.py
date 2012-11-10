#!/usr/bin/env python

import sys
import efinterp as ei
import filter_track as ft
import matplotlib.pyplot as plt

if __name__ == '__main__':
    ex, ey, e2 = ei.ef_interp('ef.txt', 'geo.txt', rotated=True, inverse=True)
    tracks = ft.filter_track(sys.argv[1], ex, ey)

    fig = plt.figure()
    for track in tracks:
        lx = track['lx']*1e6
        ly = track['ly']*1e6
        tlx = track['tlx']*1e6
        tly = track['tly']*1e6

        ax1 = fig.add_subplot(2,3,1)
        plt.plot(lx, ly)

        ax2 = fig.add_subplot(2,3,2)
        plt.plot(tlx, tly)
        plt.xlim(ax1.get_xlim())
        plt.ylim(ax1.get_ylim())

        ax3 = fig.add_subplot(2,3,3)
        plt.plot(lx, ly, 'r')
        plt.plot(tlx, tly, 'b')
        plt.xlim(ax1.get_xlim())
        plt.ylim(ax1.get_ylim())

        ax4 = fig.add_subplot(2,3,4)
        plt.plot(lx, track['mx'])
        plt.ylim(0, 1.5e-8)

        ax5 = fig.add_subplot(2,3,5)
        plt.plot(lx, track['my'])
        plt.ylim(0, 1.5e-8)

        ax6 = fig.add_subplot(2,3,6)
        plt.plot(lx, track['me'])
        plt.ylim(0, 1.5e-8)
    plt.savefig('trackall.png')
    plt.show()

    all_xlim = ax1.get_xlim()
    all_ylim = ax1.get_ylim()

    for track in tracks:
        fig = plt.figure()
        lx = track['lx']*1e6
        ly = track['ly']*1e6
        tlx = track['tlx']*1e6
        tly = track['tly']*1e6

        ax1 = fig.add_subplot(2,3,1)
        plt.plot(lx, ly)
        plt.xlim(all_xlim)
        plt.ylim(all_ylim)

        ax2 = fig.add_subplot(2,3,2)
        plt.plot(tlx, tly)
        plt.xlim(all_xlim)
        plt.ylim(all_ylim)

        ax3 = fig.add_subplot(2,3,3)
        plt.plot(lx, ly, 'r')
        plt.plot(tlx, tly, 'b')
        plt.xlim(all_xlim)
        plt.ylim(all_ylim)

        ax4 = fig.add_subplot(2,3,4)
        plt.plot(lx, track['mx'])
        plt.ylim(0, 1.5e-8)

        ax5 = fig.add_subplot(2,3,5)
        plt.plot(lx, track['my'])
        plt.ylim(0, 1.5e-8)

        ax6 = fig.add_subplot(2,3,6)
        plt.plot(lx, track['me'])
        plt.ylim(0, 1.5e-8)

        plt.savefig('track'+str(tracks.index(track))+'.png')
