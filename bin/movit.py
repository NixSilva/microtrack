#!/usr/bin/env python
import Tkinter, Tkconstants, tkFileDialog
#import cv
import os.path
#import cProfile
from sys import *
from numpy import *
from math import sqrt

if platform.startswith('linux'):
    import cv
    import Image
    from munkres import *
elif platform.startswith('win'):
    import cv2.cv as cv
    from PIL import Image

###############################################################################
def get_bg(filename, bg_filename):
    nframes=0
    pi = Image.open(filename)
    bg = cv.CreateImage(pi.size, cv.IPL_DEPTH_32F, 1)
    if os.path.isfile(bg_filename):
        print "Reading Background from bg.png"
        bgtmp = cv.LoadImage(bg_filename, cv.CV_LOAD_IMAGE_UNCHANGED)
        cv.ConvertScale(bgtmp, bg, 1.0/65536.0)
        nframes=300 #TODO: read from output
    else:
        print "Calculation Background"
        try:
            while True:
                nframes+=1
                image=cv.CreateImage(pi.size, cv.IPL_DEPTH_16U, 1)
                cv.SetData(image, pi.tostring())
                pi.seek(pi.tell() + 1)
                fimage = cv.CreateImage(cv.GetSize(image), cv.IPL_DEPTH_32F, 1)
                cv.ConvertScale(image, fimage, 1.0/65536.0)
                cv.AddWeighted(fimage, 1, bg, 1, 0, bg );
        except EOFError:
            cv.ConvertScale(bg, bg, 1.0/nframes)
            bgtmp = cv.CreateImage(cv.GetSize(bg), cv.IPL_DEPTH_16U, 1)
            cv.ConvertScale(bg, bgtmp, cv.Round(65536.0))
            cv.SaveImage(bg_filename, bgtmp)
    return bg, nframes
###############################################################################
def filter_image(img, bg):
    cv.Div(bg,img,img)
    cv.Log(img,img)
    cv.Smooth(img,img,cv.CV_GAUSSIAN,5,0,0,0)
    cv.Threshold(img,img,0.03,1,cv.CV_THRESH_BINARY)
###############################################################################
def get_ellipses(fimage, time):
    image8uc1  = cv.CreateImage(cv.GetSize(fimage), cv.IPL_DEPTH_8U,  1)
    cv.ConvertScale(fimage, image8uc1, 256)
    storage = cv.CreateMemStorage(0)
    contour = cv.FindContours(image8uc1, storage, 
            cv.CV_RETR_CCOMP, cv.CV_CHAIN_APPROX_SIMPLE)
    ellipses = []
    while contour:
        if len(contour) >= 6:
            PointArray2D32f = cv.CreateMat(1, len(contour), cv.CV_32FC2) 
            for (i, (x, y)) in enumerate(contour):
                PointArray2D32f[0, i] = (x, y)
            (center, size, angle) = cv.FitEllipse2(PointArray2D32f)
            if (size[0]!=0 and size[1]!=0 and 
                    size[1]/size[0]<5.0 and size[1]>5.0):
                ellipses.append((center,size,angle,time))
        contour = contour.h_next()
    return ellipses
###############################################################################
def get_particles((bg, nframes), img_filename):
    print "Getting Particles"
    particles = []
    filename = img_filename
    pi = Image.open(filename)
    for i in range(nframes):
        pi.seek(i)
        image=cv.CreateImage(pi.size, cv.IPL_DEPTH_16U, 1)
        cv.SetData(image, pi.tostring())
        fimage = cv.CreateImage(cv.GetSize(image), cv.IPL_DEPTH_32F, 1)
        cv.ConvertScale(image,fimage,1.0/65536.0)
        filter_image(fimage, bg)
        particles.append(get_ellipses(fimage,i))
    return particles
###############################################################################
def show_frame(frame, img_filename):
    image = cv.LoadImage(img_filename+'-bg.png', cv.CV_LOAD_IMAGE_UNCHANGED)
    for particle in frame:
        cv.Ellipse(image, 
                ((int)(round(particle[0][0])),(int)(round(particle[0][1]))), 
                ((int)(round(particle[1][0]/2.0)),(int)(round(particle[1][1]/2.0))), 
                particle[2], 0, 360, cv.CV_RGB(0, 0, 65535))
    cv.ShowImage('image', image)
###############################################################################
def distance(loc1, loc2):
    return sqrt((loc1[0]-loc2[0])**2 + (loc1[1]-loc2[1])**2)
###############################################################################
class Track:
    data = []
#    if len(argv) != 3:
#        threshold1 = 100.0
#        threshold2 = 20.0
#    else:
#        threshold1 = float(argv[2])
#        threshold2 = threshold1/5.0
    def __init__(self, threshold1, threshold2):
        self.data = []
        self.threshold1 = threshold1
        self.threshold2 = threshold2
    def predict(self):
        if len(self.data) >= 2:
            dx = self.data[-1][0][0] - self.data[-2][0][0]
            dy = self.data[-1][0][1] - self.data[-2][0][1]
            return (self.data[-1][0][0] + dx, self.data[-1][0][1] + dy)
    def accept(self, particle2):
        particle1 = self.data[-1]
        if len(self.data) < 2:
            return distance(particle1[0], particle2[0]) < self.threshold1
        else:
            position = self.predict()
            return distance(particle2[0], position) < self.threshold2
    def distance(self, position):
        particle1 = self.data[-1]
        if len(self.data) < 2:
            return distance(particle1[0], position)/self.threshold1*self.threshold2
        else:
            predict_position = self.predict()
            return distance(predict_position, position)
###############################################################################
def pad_matrix(matrix, pad_value=0):
    max_columns = 0
    total_rows = len(matrix)

    for row in matrix:
        max_columns = max(max_columns, len(row))

    total_rows = max(max_columns, total_rows)

    new_matrix = empty([total_rows, total_rows])
    new_matrix.fill(pad_value)
    for i in range(len(matrix)):
        row = matrix[i]
        for j in range(len(row)):
            new_matrix[i, j] = matrix[i, j]

#	for row in matrix:
#		row_len = len(row)
#		new_row = row[:]
#		if total_rows > row_len:
#			# Row too short. Pad it.
#			new_row += [pad_value] * (total_rows - row_len)
#		new_matrix.append(new_row)
#
#	while len(new_matrix) < total_rows:
#		new_matrix.append([pad_value] * total_rows)

    return new_matrix
###############################################################################

def get_tracks_new(particles, threshold1, threshold2):
    finished_tracks = []
    running_tracks = []
    for frame in particles:
        #show_frame(frame)
        #cv.WaitKey(1)
        dist = zeros((len(running_tracks), len(frame)))
        for j in range(len(running_tracks)):
            track = running_tracks[j]
            for i in range(len(frame)):
                dist[j, i] = track.distance(frame[i][0])
        if len(dist) != 0:
            m = Munkres()
            dist_copy = dist[:]
            dist_pad = pad_matrix(dist_copy, 9999.9)
            indexes = m.compute(dist_pad)
            indexes.sort(key=lambda indexes: indexes[1], reverse=True) 
            for row, column in indexes:
                if (row < shape(dist)[0] and column < shape(dist)[1]):
                    value = dist[row, column]
                    if value < 4:
                        running_tracks[row].data.append(frame.pop(column))
        print len(frame)
#		for j in reversed(range(len(running_tracks))):
#			track = running_tracks[j]
#			found = False
#			for i in reversed(range(len(frame))):
#				particle = frame[i]
#				if track.accept(particle):
#					track.data.append(frame.pop(i))
#					found = True
#					break
#			if found != True:
#				finished_tracks.append(running_tracks.pop(j))
        while len(frame) != 0:
            new_track = Track(threshold1, threshold2)
            new_track.data.append(frame.pop(-1))
            running_tracks.append(new_track)
        print len(running_tracks), len(finished_tracks)
    finished_tracks.extend(running_tracks)
    for i in reversed(range(len(finished_tracks))):
        track = finished_tracks[i]
        if len(track.data) < 5:
            finished_tracks.pop(i)
    return finished_tracks
###############################################################################
def get_tracks(bg, data_filename, threshold1, threshold2, img_filename):
    finished_tracks = []
    if os.path.isfile(data_filename):
        file = open(data_filename)
        file.readline()
        track = Track(threshold1, threshold2)
        track_id_old = 0
        for line in file:
            data = line.split()
            track_id = int(data[0])
            time = int(data[1])
            x = float(data[2])
            y = float(data[3])
            w = float(data[4])
            h = float(data[5])
            angle = float(data[6])
            if track_id != track_id_old:
                finished_tracks.append(track)
                track = Track(threshold1, threshold2)
                track_id_old = track_id
            track.data.append(((x,y), (w,h), angle, time))
        finished_tracks.append(track)
    else:
        particles = get_particles(bg, img_filename)
        running_tracks = []
        for frame in particles:
            #show_frame(frame, img_filename)
            #show_tracks(running_tracks)
            #cv.WaitKey(1)
            for j in reversed(range(len(running_tracks))):
                track = running_tracks[j]
                found = False
                for i in reversed(range(len(frame))):
                    particle = frame[i]
                    if track.accept(particle):
                        track.data.append(frame.pop(i))
                        found = True
                        break
                if found != True:
                    finished_tracks.append(running_tracks.pop(j))
            while len(frame) != 0:
                new_track = Track(threshold1, threshold2)
                new_track.data.append(frame.pop(-1))
                running_tracks.append(new_track)
        finished_tracks.extend(running_tracks)
        for i in reversed(range(len(finished_tracks))):
            track = finished_tracks[i]
            if len(track.data) < 5:
                finished_tracks.pop(i)
    return finished_tracks
###############################################################################
def show_tracks(tracks, img_filename, bg_filename, trackimg_filename):
    image = cv.LoadImage(bg_filename, cv.CV_LOAD_IMAGE_UNCHANGED)
    for track in tracks:
        if track.info[7]:
            for i in range(len(track.data) - 1):
                particle1 = track.data[i+1]
                particle2 = track.data[i]
                cv.Ellipse(image, 
                        ((int)(round(particle1[0][0])),(int)(round(particle1[0][1]))), 
                        ((int)(round(particle1[1][0]/2.0)),(int)(round(particle1[1][1]/2.0))), 
                        particle1[2], 0, 360, cv.CV_RGB(0, 0, 65535))
                cv.Line(image,
                        ((int)(round(particle1[0][0])),(int)(round(particle1[0][1]))), 
                        ((int)(round(particle2[0][0])),(int)(round(particle2[0][1]))), 
                        cv.CV_RGB(0, 0, 65535), thickness = 1, lineType=4)
    cv.ShowImage('image', image)
    cv.SaveImage(trackimg_filename, image)
    cv.WaitKey(1)
###############################################################################
def stat_tracks(tracks, min_length_ratio, min_width_ratio, max_width_ratio, img_filename, bg_filename, trackimg_filename):
    #track_info = []
    for track in tracks:
        #sumx = 0.0
        #sumy = 0.0
        sumw = 0.0
        sumw2 = 0.0
        sumh = 0.0
        sumh2 = 0.0
        for particle in track.data:
            #sumx += particle[0][0]
            #sumy += particle[0][1]
            sumw += particle[1][0]
            sumw2 += particle[1][0]**2
            sumh += particle[1][1]
            sumh2 += particle[1][1]**2
        #avex = sumx/len(track.data)
        #avey = sumy/len(track.data)
        size = len(track.data)
        avew = sumw/size
        aveh = sumh/size
        rmsdw = sqrt( (sumw2 - avew**2 * size) / (size - 1) )
        rmsdh = sqrt( (sumh2 - aveh**2 * size) / (size - 1) )
        head = track.data[0]
        tail = track.data[-1]
        velx = (tail[0][0] - head[0][0]) / size
        vely = (tail[0][1] - head[0][1]) / size
        track.info = list((size,avew,aveh,rmsdw,rmsdh,velx,vely,True))
        #track_info.append((size,avew,aveh,rmsdw,rmsdh,velx,vely,True))
    sumsize = 0
    sumw = 0.0
    sumh = 0.0
    sumvx = 0.0
    sumvy = 0.0
    for track in tracks:
        sumsize += track.info[0]
        sumw += track.info[1]
        sumh += track.info[2]
        sumvx += track.info[5]
        sumvy += track.info[6]
    avesize = sumsize/len(tracks)
    avew = sumw/len(tracks)
    aveh = sumh/len(tracks)
    avevx = sumvx/len(tracks)
    avevy = sumvy/len(tracks)
    print avesize, avew, aveh, avevx, avevy
    #show_tracks(tracks, img_filename, bg_filename, trackimg_filename)
    #cv.WaitKey(0)
    for track in tracks:
        if track.info[0] < avesize * float(min_length_ratio):
            track.info[7] = False
        elif track.info[1] < avew * float(min_width_ratio) or \
                track.info[1] > avew * float(max_width_ratio):
            track.info[7] = False
    #show_tracks(tracks, img_filename, bg_filename, trackimg_filename)
    #cv.WaitKey(0)

#	exit(0)
#
#	out_file = open(argv[1]+'-tracks.txt','w')
#	out_file.write('{0:15s} {1:15s} {2:15s} {3:15s} {4:15s} {5:15s} {6:15s}\n'\
#			.format('size', 'vx(ms-1)', 'evx(ms-1)', 'vy(ms-1)', 'evy(ms-1)', 'width(m)', 'height(m)'))
#	for track in tracks:
#		track_velx   = 0.0
#		track_velxsq = 0.0
#		track_vely   = 0.0
#		track_velysq = 0.0
#		track_avgw   = 0.0
#		track_avgh   = 0.0
#		size   = len(track.data) - 1
#		for i in range(size):
#			particle1 = track.data[i+1]
#			particle2 = track.data[i]
#			dx = (particle1[0][0] - particle2[0][0]) / 2.47 * 1e-6 / 0.044
#			dy = (particle1[0][1] - particle2[0][1]) / 2.47 * 1e-6 / 0.044
#			w = particle1[1][0] / 2.47 * 1e-6
#			h = particle2[1][0] / 2.47 * 1e-6
#			track_velx   += dx
#			track_velxsq += dx**2
#			track_vely   += dy
#			track_velysq += dy**2
#			track_avgw   += w
#			track_avgh   += h
#		track_avg_velx   = track_velx   / size
#		track_avg_vely   = track_vely   / size
#		track_avgw   = track_avgw   / size
#		track_avgh   = track_avgh   / size
#		track_rmsdx = sqrt ((track_velxsq - track_avg_velx**2 * size) / (size - 1))
#		track_rmsdy = sqrt ((track_velysq - track_avg_vely**2 * size) / (size - 1))
#		if track_avgw > 0: #TODO change threshold
#			out_file.write('{0:15d} {1:15e} {2:15e} {3:15e} {4:15e} {5:15e} {6:15e}\n'.format(size+1, track_avg_velx, track_rmsdx, 
#						track_avg_vely, track_rmsdy, track_avgw, track_avgh))
###############################################################################
def output_tracks(tracks, img_filename, data_filename, filtered_filename,\
        track_filename):
    if not os.path.isfile(data_filename):
        out_file = open(data_filename,'w')
        out_file.write('{0:15s} {1:15s} {2:15s} {3:15s} {4:15s} {5:15s} {6:15s}\n'\
                .format('id', 'time', 'x(m)', 'y(m)', 'width(m)', 'height(m)', 'angle'))
        track_id = 0
        for track in tracks:
            for particle in track.data:
                x,y = particle[0]
                w,h = particle[1]
                angle = particle[2]
                time  = particle[3]
                out_file.write('{0:10d} {1:10d} {2:15f} {3:15f} {4:15f} {5:15f} {6:15f}\n'\
                        .format(track_id, time, x, y, w, h, angle))
            track_id = track_id + 1

    out_file = open(filtered_filename,'w')
    out_file.write('{0:15s} {1:15s} {2:15s} {3:15s} {4:15s} {5:15s} {6:15s}\n'\
            .format('id', 'time', 'x(m)', 'y(m)', 'width(m)', 'height(m)', 'angle'))
    track_id = 0
    for track in tracks:
        if track.info[7]:
            for particle in track.data:
                x,y = particle[0]
                w,h = particle[1]
                angle = particle[2]
                time  = particle[3]
                out_file.write('{0:10d} {1:10d} {2:15f} {3:15f} {4:15f} {5:15f} {6:15f}\n'\
                        .format(track_id, time, x, y, w, h, angle))
        track_id = track_id + 1

    out_file = open(track_filename,'w')
    out_file.write('{0:15s} {1:15s} {2:15s} {3:15s}\n'\
            .format('id', 'time', 'vx(m/s)', 'vy(m/s)'))
    track_id = 0
    for track in tracks:
        if track.info[7]:
            head = track.data[0]
            tail = track.data[-1]
            dx,dy = (array(tail[0]) - array(head[0])) / 2.47 * 1e-6
            time = (tail[3] - head[3]) * 0.044
            out_file.write('{0:10d} {1:10e} {2:15e} {3:15e}\n'\
                    .format(track_id, time, dx/time, dy/time))
        track_id = track_id + 1
###############################################################################
def output_tracks_old(tracks, img_filename):
    out_file = open(img_filename+'.txt','w')
    out_file.write('{0:15s} {1:15s} {2:15s} {3:15s} {4:15s} {5:15s} {6:15s} {7:15}\n'\
            .format('id', 'time', 'x(m)', 'y(m)', 'dx(ms-1)', 'dy(ms-1)', 'width(m)', 'height(m)'))
    track_id = 0
    for track in tracks:
        size   = len(track.data) - 1
        for i in range(size):
            particle1 = track.data[i+1]
            particle2 = track.data[i]
            time = (particle1[3] + particle2[3]) / 2.0
            dx = (particle1[0][0] - particle2[0][0]) / 2.47 * 1e-6 / 0.044
            dy = (particle1[0][1] - particle2[0][1]) / 2.47 * 1e-6 / 0.044
            x = (particle1[0][0] + particle2[0][0]) / 2 / 2.47 * 1e-6
            y = (particle1[0][1] + particle2[0][1]) / 2 / 2.47 * 1e-6
            w = particle1[1][0] / 2.47 * 1e-6
            h = particle2[1][0] / 2.47 * 1e-6
            out_file.write('{0:15d} {1:15f} {2:15e} {3:15e} {4:15e} {5:15e} {6:15e} {7:15e}\n'\
                    .format(track_id, time, x, y, dx, dy, w, h))
        track_id = track_id + 1
###############################################################################
def run(img_filename, threshold1, threshold2, \
        min_length_ratio, min_width_ratio, max_width_ratio, \
        bg_filename, trackimg_filename, data_filename, track_filename, \
        filtered_filename):
    nframes = 0
    #cv.NamedWindow('image', cv.CV_WINDOW_AUTOSIZE)
    #cv.NamedWindow('image', cv.CV_WINDOW_NORMAL)
#	tracks = get_tracks_new(particles)
    bg, nframes = get_bg(img_filename, bg_filename)
    tracks = get_tracks((bg, nframes), data_filename, threshold1, threshold2, \
            img_filename)
    stat_tracks(tracks, min_length_ratio, min_width_ratio, max_width_ratio, \
            img_filename, bg_filename, trackimg_filename)
    output_tracks(tracks, img_filename, data_filename, filtered_filename, \
            track_filename)
    #show_tracks(tracks)
    #cv.WaitKey(0)
    return
###############################################################################
#run()
