#!/usr/bin/env python

from Tix import *
import tkFileDialog
import movit
import efinterp
import os
import cv
from PIL import Image , ImageTk

from numpy import *
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
from matplotlib.pyplot import cm

class ZProject:

    img_filename = ''
    ef_filename = ''
    geo_filename = ''
    track_filename = ''
    bg_filename = ''
    trackimg_filename = ''
    data_filename = ''
    filtered_filename = ''
    prj_dir = ''

    def __init__(self, master):


        #frame = Frame(master)
        #frame.pack(fill=BOTH, expand=1)

        self.nb = NoteBook(master)
        self.nb.pack(fill=BOTH, expand=1)
        tab = self.nb.add('tab', label='New Project')

        self.table = Frame(tab)
        self.table.pack(fill=BOTH, expand=1, side = LEFT)

        self.img_lbl, self.img_flag, self.img_info, self.img_btn, \
                self.img_view = \
                self.create_entry(self.table, 'Image', self.img_filename, \
                "Load", self.on_btn_img, self.on_view_img, 0)
        self.geo_lbl, self.geo_flag, self.geo_info, self.geo_btn , \
                self.geo_view = \
                self.create_entry(self.table, 'geo.txt', self.geo_filename, \
                "Load", self.on_btn_geo, self.on_view_geo,  1)
        self.ef_lbl, self.ef_flag, self.ef_info, self.ef_btn , \
                self.ef_view = \
                self.create_entry(self.table, 'ef.txt', self.ef_filename, \
                "Load", self.on_btn_ef, self.on_view_ef,  2)
        self.bg_lbl, self.bg_flag, self.bg_info, self.bg_btn, \
                self.bg_view = \
                self.create_entry(self.table, 'Background', self.bg_filename, \
                "Generate", self.on_btn_bg, self.on_view_bg,  3)
        self.data_lbl, self.data_flag, self.data_info, self.data_btn, \
                self.data_view = \
                self.create_entry(self.table, 'Data', self.data_filename, \
                "Generate", self.on_btn_data, self.on_view_data,  4)
        self.track_lbl, self.track_flag, self.track_info, self.track_btn, \
                self.track_view = \
                self.create_entry(self.table, 'Track', self.track_filename, \
                "Generate", self.on_btn_track, self.on_view_track,  5)
        self.filtered_lbl, self.filtered_flag, self.filtered_info, \
                self.filtered_btn , self.filtered_view = \
                self.create_entry(self.table, \
                'Filtered Data', self.filtered_filename, None, None,\
                self.on_view_filtered, 6)
        self.trackimg_lbl, self.trackimg_flag, self.trackimg_info, \
                self.trackimg_btn , self.trackimg_view = \
                self.create_entry(self.table, \
                'Track image', self.trackimg_filename, None, None, \
                self.on_view_trackimg, 7)
        self.efinterp_lbl, self.efinterp_flag, self.efinterp_info, \
                self.efinterp_btn, self.efinterp_view = \
                self.create_entry(self.table, 'EF interpolation', None, \
                "Generate", self.on_btn_efinterp, None, 8)
        self.efcontour_lbl, self.efcontour_flag, self.efcontour_info, \
                self.efcontour_btn, self.efcontour_view = \
                self.create_entry(self.table, 'EF contour', None, \
                "Generate", self.on_btn_efcontour, None, 9)

        self.view_frame = Frame(tab)
        self.view_frame.pack(fill = BOTH, expand = 1, side=LEFT)

        #im = Image.open('lena.jpg')
        #im = im.resize((600, 600), Image.ANTIALIAS)
        #photo = ImageTk.PhotoImage(im)
        #self.show_zone = Label(self.view_frame, image=photo)
        self.show_zone = Label(self.view_frame) #, image=photo)
        #self.show_zone.image = photo
        self.show_zone.pack_forget()

        self.figure = Figure(figsize=(6,6), dpi=100)
        self.ax = self.figure.add_subplot(111)
        t = arange(0.0,3.0,0.01)
        s = sin(2*pi*t)

        self.ax.plot(t,s)

        self.canvas = FigureCanvasTkAgg(self.figure, master = self.view_frame)
        self.canvas.show()
        self.canvas.get_tk_widget().pack(side=LEFT)
        self.update_ui()

    def create_entry(self, master, lbl_text, info_text, btn_text,\
            on_btn, on_view, nrow):
        entry_lbl = Label(master, text=lbl_text)
        entry_lbl.grid(column=0, row=nrow)
        entry_flag = Label(master, text="    ", bg="red")
        entry_flag.grid(column=1, row=nrow)
        entry_info = Label(master, text=info_text)
        entry_info.grid(column=2, row=nrow)
        if btn_text:
            entry_btn = Button(master, text=btn_text, command=on_btn)
            entry_btn.grid(column=3, row=nrow)
        else:
            entry_btn = None
        entry_view = Button(master, text='View', comman=on_view)
        entry_view.grid(column=4, row=nrow)
        return entry_lbl, entry_flag, entry_info, entry_btn, entry_view

    def update_entry(self, filename, info, flag, view):
        if os.path.exists(filename):
            #info.configure(text = filename)
            flag.configure(bg = 'green')
            view.configure(stat = NORMAL)
        else:
            #info.configure(text = "File not Loaded!")
            flag.configure(bg = 'red')
            view.configure(stat = DISABLED)

    def update_ui(self):
        if os.path.exists(self.img_filename):
            self.track_btn.configure(state = NORMAL)
        else:
            self.track_btn.configure(state = DISABLED)

        if os.path.exists(self.bg_filename):
            if hasattr(self, 'bg'):
                self.bg_btn.configure(text = 'Reload')
                self.bg_flag.configure(bg = 'green')
                self.bg_view.configure(stat = NORMAL)
            else:
                self.bg_btn.configure(text = 'Load')
                self.bg_flag.configure(bg = 'red')
                self.bg_view.configure(stat = DISABLED)
        else:
            self.bg_btn.configure(text = 'Generate')

        self.update_entry(self.img_filename, \
                self.img_info, self.img_flag, self.img_view)
        self.update_entry(self.geo_filename, \
                self.geo_info, self.geo_flag, self.geo_view)
        self.update_entry(self.ef_filename, \
                self.ef_info, self.ef_flag, self.ef_view)
        self.update_entry(self.track_filename, \
                self.track_info, self.track_flag, self.track_view)
        self.update_entry(self.data_filename, \
                self.data_info, self.data_flag, self.data_view)
        self.update_entry(self.trackimg_filename, \
                self.trackimg_info, self.trackimg_flag, self.trackimg_view)
        self.update_entry(self.filtered_filename, \
                self.filtered_info, self.filtered_flag, self.filtered_view)
        if hasattr(self, 'ef_interp'):
            self.efinterp_flag.configure(bg = 'green')
            self.efinterp_view.configure(stat = NORMAL)
        else:
            self.efinterp_flag.configure(bg = 'red')
            self.efinterp_view.configure(stat = DISABLED)
#        self.update_entry(self.bg_filename, \
#                self.bg_info, self.bg_flag, self.bg_view)

        self.table.pack()

    def on_btn_img(self):
        file_opt = options = {}
        options['defaultextension'] = '.tif'
        options['filetypes'] = [('TIFF images', '.tif')]
        options['title'] = 'Locate the video sequency file'

        self.img_filename = tkFileDialog.askopenfilename(**file_opt)
        self.work_dir = self.img_filename[:-4]
        if not os.path.isdir(self.work_dir):
            os.mkdir(self.work_dir)
        self.bg_filename = self.work_dir+'/bg.png'
        self.trackimg_filename = self.work_dir+'/track.png'
        self.data_filename = self.work_dir+'/data.txt'
        self.track_filename = self.work_dir+'/track.txt'
        self.filtered_filename = self.work_dir+'/filtered.txt'
        self.update_ui()

    def on_btn_geo(self):
        file_opt = options = {}
        options['defaultextension'] = '.txt'
        options['filetypes'] = [('Text file', '.txt'), ('all files', '.*')]
        options['title'] = 'Locate the geo.txt file'

        self.geo_filename = tkFileDialog.askopenfilename(**file_opt)
        self.update_ui()

    def on_btn_ef(self):
        file_opt = options = {}
        options['defaultextension'] = '.txt'
        options['filetypes'] = [('Text file', '.txt'), ('all files', '.*')]
        options['title'] = 'Locate the ef.txt file'

        self.ef_filename = tkFileDialog.askopenfilename(**file_opt)
        self.update_ui()

    def on_btn_track(self):
        pass
    def on_btn_bg(self):
        if os.path.exists(self.img_filename):
            self.bg, self.nframes = \
                    movit.get_bg(self.img_filename, self.bg_filename)
            self.update_ui()
        pass
    def on_btn_data(self):
        self.tracks = movit.get_tracks((self.bg, self.nframes),\
                self.data_filename, 10.0, 2.0, self.img_filename)
        movit.stat_tracks(self.tracks, 0.2, 0.9, 3.0, \
                self.img_filename, self.bg_filename, self.trackimg_filename)
        movit.output_tracks(self.tracks, self.img_filename, \
                self.data_filename, self.filtered_filename,self.track_filename)
        self.update_ui()
    def on_btn_efinterp(self):
        self.ex_interp, self.ey_interp, self.ef_interp = \
                efinterp.get_ef_interp(self.ef_filename, self.geo_filename)
        self.update_ui()
    def on_btn_efcontour(self):
        self.show_zone.pack_forget()
        self.a.cla()
        gx, gy, gz = efinterp.get_grid(self.ef_interp, 600, 'ef')
        self.ax.contourf(gx, gy, gz, 500, cmap=cm.jet)
        self.figure.colorbar()
        self.canvas.show()
        self.canvas.get_tk_widget().pack(fill=BOTH, expand=1)
        #efinterp.draw_ef(self.ex_interp, self.ey_interp, self.ef_interp)
        self.update_ui()
    def on_view_img(self):
        pass
    def on_view_geo(self):
        pass
    def on_view_ef(self):
        pass
    def on_view_data(self):
        pass
    def on_view_bg(self):
        self.canvas.get_tk_widget().pack_forget()
        cv_im = cv.LoadImage(self.bg_filename, cv.CV_LOAD_IMAGE_GRAYSCALE)
        cv_im2 = cv.CreateImage(cv.GetSize(cv_im), cv.IPL_DEPTH_8U, 1)
        cv.SubS(cv_im, 28.0, cv_im2)
        cv.ConvertScale(cv_im2, cv_im2, 12.0)
        #cv.ShowImage('image', cv_im2)
        #cv.WaitKey(0)
        im = Image.fromstring("L", cv.GetSize(cv_im2), cv_im2.tostring())
        im = im.resize((512, 512), Image.ANTIALIAS)
        bgimage = ImageTk.PhotoImage(im)
        self.show_zone.configure(image = bgimage)
        self.show_zone.image = bgimage
        self.show_zone.pack()
        pass
    def on_view_trackimg(self):
        pass
    def on_view_track(self):
        pass
    def on_view_filtered(self):
        pass

root = Tk()
app = ZProject(root)
root.mainloop()

