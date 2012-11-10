#!/usr/bin/env python
#from pylab import *
from math import *
from numpy import *
from matplotlib.pyplot import *
from matplotlib.path import *
from matplotlib.patches import *
from matplotlib.image import *
from scipy.interpolate import CloughTocher2DInterpolator
###############################################################################
def read_ef(ef_filename, geo_filename, rotated=False, inverse=False):
    ''' Read electric field strength and position from files.
    '''
    ef_file = open(ef_filename)
    geo_file = open(geo_filename)
    index = []
    ef_list=[]
    coord_list=[]
    for efline in ef_file:
        new_index = int(efline.split()[0])

        index.append(new_index)
        ef_list.append( (float(efline.split()[1]), (-1.0 if inverse else 1.0)*float(efline.split()[2])) )
        while True:
            geoline = geo_file.readline()
            if float(geoline.split()[0]) == new_index:
                if rotated:
                    coord_list.append( (float(geoline.split()[2]), 
                                        float(geoline.split()[1])) ) 
                else:
                    coord_list.append( (float(geoline.split()[1]), 
                                        float(geoline.split()[2])) ) 
                break
    coord = array(coord_list)
    ef = array(ef_list)
    return coord, ef
###############################################################################
def read_mobi(filename):
    ''' Read mobility data from file.
    '''
    mobi_file = open(filename)
    mobi_file.readline() #bypass the header
    coord_list=[]
    mobi_list=[]
    for line in mobi_file:
        coord_list.append( (float(line.split()[1]), float(line.split()[2])))
        mobi_list.append( (float(line.split()[7]), float(line.split()[8])))
    size = len(mobi_list)
    coord = empty([size,2])
    mobi = empty([size,2])
    for i in range(size):
        coord[i,0] = coord_list[i][0]
        coord[i,1] = coord_list[i][1]
        mobi[i,0] = mobi_list[i][0]
        mobi[i,1] = mobi_list[i][1]
    return coord, mobi
###############################################################################
def remove_corner(x, y, z):
    for i in range(len(z)):
        for j in range(len(z)):
            if x[i,j] < -122.5e-6 and y[i,j] < -116e-6:
                z[i,j] = NaN
            if x[i,j] < -122.5e-6 and y[i,j] >  116e-6:
                z[i,j] = NaN
            if x[i,j] >  122.5e-6 and y[i,j] < -116e-6:
                z[i,j] = NaN
            if x[i,j] >  122.5e-6 and y[i,j] >  116e-6:
                z[i,j] = NaN
###############################################################################
def flat(z, maxthre, minthre):
    for i in range(len(z)):
        for j in range(len(z)):
            if z[i, j] < minthre:
                z[i, j] = minthre
            elif z[i, j] > maxthre:
#                print i, j, z[i, j]
                z[i, j] = maxthre
###############################################################################
def get_grid(interpolator, n, grid_type):
    x, y = mgrid[-1e-3:1e-3:n*1j, -1e-3:1e-3:n*1j]
    z = interpolator(x, y)
    if grid_type is 'mobility':
        flat(z, 13e-9, 6e-9)
    elif grid_type is 'ef':
        remove_corner(x, y, z)
    return x, y, z
###############################################################################
def in_zone(point):
    ''' Check if a point is in the interest zone.
    '''
    if point[0] >= -1e-3 and point[0] <= 1e-3 \
            and point[1] >= -1e-3 and point[1] <= 1e-3:
        return True
    else:
        return False
###############################################################################
def derive(interpx, interpy, point, delta):
    ex = interpx(point[0], point[1]) * delta
    ey = interpy(point[0], point[1]) * delta
    return (point[0] - ex, point[1] - ey)
###############################################################################
def draw_efline(interpx, interpy, ax, startx, starty, delta):
    ''' Draw a electric field line start from (startx, starty).
    '''
    codes = [Path.MOVETO]
    verts = [(startx, starty)]
    point = (startx, starty)
    while in_zone(point):
        point = derive(interpx, interpy, point, delta)
        codes.append(Path.LINETO)
        verts.append(point)
    print len(codes)
    path = Path(verts, codes)
    patch = PathPatch(path, facecolor='none')
    ax.add_patch(patch)
###############################################################################
def draw_eflines(interpx, interpy, n, delta):
    ''' Draw a series of electric field lines.
    '''
    xs = linspace(-123e-6, 123e-6, n, endpoint = True)
    for i in range(n):
        draw_efline(interpx, interpy, ax, xs[i], 1e-3, delta)
###############################################################################
def draw_contour(x, y, z):
    #contour(x, y, z, 10, linewidths=0.5, colors='k')
    contourf(x, y, z, 500, cmap=cm.jet)
    colorbar()
#    scatter(coord[:,0], coord[:,1], marker='o', s=0.01)
###############################################################################
def show_plot(name):
    ratio = 2.47e6
    ix1 = -496.5 / ratio
    ix2 = 1004 / ratio + ix1
    iy2 = 429.5 / ratio
    iy1 = iy2 - 1002 / ratio
#    img = imread('bg.png')
#    imshow(img, origin='lower', alpha=0.8, extent=[ix1, ix2, iy1, iy2])
    xlim(ix1,ix2)
    ylim(iy1,iy2)
    savefig(name, dpi=300)
    show()
###############################################################################
def get_ex(ef, size):
    z = empty([size])
    for i in range(size):
        z[i] = ef[i,0]
    return z
###############################################################################
def get_ey(ef, size):
    z = empty([size])
    for i in range(size):
        z[i] = ef[i,1]
    return z
###############################################################################
def get_e2(ef, size):
    z = empty([size])
    for i in range(size):
        ex = ef[i,0]
        ey = ef[i,1]
        z[i] = ex**2 + ey**2
    return z
############################################################################### 
def get_ef(ef, size):
    z = empty([size])
    for i in range(size):
        z[i] = sqrt(ef[i,0]**2 + ef[i,1]**2)
    return z
###############################################################################
def get_mobix(mobi, size):
    z = empty([size])
    for i in range(size):
        z[i] = mobi[i,0]
    return z
###############################################################################
def get_mobiy(mobi, size):
    z = empty([size])
    for i in range(size):
        z[i] = mobi[i,1]
    return z
###############################################################################
def get_mobi(mobi, size):
    z = empty([size])
    for i in range(size):
        z[i] = sqrt(mobi[i,0]**2 + mobi[i,1]**2)
    return z
###############################################################################
def run_mobi(coord_mobi, mobi):
    size_mobi = len(coord_mobi)
    print 'Getting electric field...'
    mobix = get_mobix(mobi, size_mobi)
    mobiy = get_mobiy(mobi, size_mobi)
    mobi = get_mobi(mobi, size_mobi)
    print 'Creating interpolator...'
    mobix_interp = CloughTocher2DInterpolator(coord_mobi, mobix)
    mobiy_interp = CloughTocher2DInterpolator(coord_mobi, mobiy)
    mobi_interp = CloughTocher2DInterpolator(coord_mobi, mobi)
    print 'Interpolating grid data...'
    mx, my, mz = get_grid(mobiy_interp, 200, 'mobility')
    hold(True)
    print 'Drawing contour...'
    draw_contour(mx, my, mz)
    print 'Showing plot'
    show_plot('mobi')
###############################################################################
def draw_track(coord_mobi):
    size_mobi = len(coord_mobi)
    scatter(coord_mobi[:,0], coord_mobi[:,1], marker='o', s=0.1)

###############################################################################
def draw_interp(interp, resolution = 300):
    print 'Interpolating grid data...'
    gx, gy, gz = get_grid(interp, resolution, 'ef')
    print 'Drawing contour...'
    draw_contour(gx, gy, gz)
    #draw_contour(gy, gx, gz)
    #print 'Drawing tracks'
    #draw_track(coord_mobi)
    #print 'Drawing EF lines...'
    #draw_eflines(ex_interp, ey_interp, 40, 10e-10)
    print 'Showing plot'
    show_plot('ef')
    return gx, gy, gz
###############################################################################
def ef_interp(ef_filename, geo_filename, rotated=False, inverse=False):
    coord_ef, ef = read_ef(ef_filename, geo_filename, rotated, inverse)
    size_ef = len(coord_ef)
    print 'Getting electric field...'
    ex = get_ex(ef, size_ef)
    ey = get_ey(ef, size_ef)
    e2 = get_e2(ef, size_ef)
    print 'Creating interpolator...'
    ex_interp = CloughTocher2DInterpolator(coord_ef, ex)
    ey_interp = CloughTocher2DInterpolator(coord_ef, ey)
    e2_interp = CloughTocher2DInterpolator(coord_ef, e2)
    if rotated:
        return ey_interp, ex_interp, e2_interp
    else:
        return ex_interp, ey_interp, e2_interp
###############################################################################
def draw_e2_gradient(e2_interp, gx, gy, gz):
    print len(gz)
    e2gx, e2gy = gradient(gz) 
#    e2gx = e2gx * len(gz)
    for i in range(len(e2gx)):
        for j in range(len(e2gx)):
            if e2gx[i,j] < -2e6:
                e2gx[i,j] = NaN
            if e2gx[i,j] > 2e6:
                e2gx[i,j] = NaN
            if e2gy[i,j] < -2e6:
                e2gy[i,j] = NaN
            if e2gy[i,j] > 2e6:
                e2gy[i,j] = NaN
    draw_contour(gx, gy, e2gx)
    show_plot('e2gx')
    draw_contour(gx, gy, e2gy)
    show_plot('e2gy')
    return e2gx, e2gy
###############################################################################

def run():
    print 'Creating figure...'
    fig = figure()
    ax = fig.add_subplot(111)
    print 'Reading electric field data...'
    ex_interp, ey_interp, ef_interp = get_ef_interp('ef.txt', 'geo.txt')
    #print 'Reading mobility data'
    #coord_mobi, mobi = read_mobi('100.25-1.tif.mobility.txt')
    #run_mobi(coord_mobi, mobi)
    draw_interp(ex_interp)
    #hist(img.flatten())
    show()
