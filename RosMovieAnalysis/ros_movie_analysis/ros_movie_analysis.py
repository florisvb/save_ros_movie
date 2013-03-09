import os, sys
import pickle

import cv, cv_numpy
import numpy as np

def get_filelist(path, filetype):
    cmd = 'ls ' + path
    ls = os.popen(cmd).read()
    all_filelist = ls.split('\n')
    try:
        all_filelist.remove('')
    except:
        pass
        
    filelist = []
    for i, filename in enumerate(all_filelist):
        if filetype in filename:
            filelist.append(filename)
    return filelist
    

class Movie(object):
    def __init__(self, path_to_movie):
        self.path = path_to_movie
        self.path_png = os.path.join(self.path, 'png_image_files')
        
        # load pickle data
        filelist = get_filelist(self.path, '.pickle')
        if len(filelist) == 1:
            frameinfo_filename = os.path.join(self.path, filelist[0])
        else:
            raise ValueError("Too many pickle files in directory!")
        f = open(frameinfo_filename)
        self.frameinfo = pickle.load(f)
        
        # calculate and save convenience attributes
        self.calc_framekeys()
        self.calc_timestamps()
        self.calc_framerate()
        
        self.current_frame = 0
        
    def calc_timestamps(self):
        
        self.timestamps = []
        for key in self.framekeys:
            frameinfo = self.frameinfo[key]
            t = float(frameinfo['secs']) + float(frameinfo['nsecs'])*1e-9
            self.timestamps.append(t)
        self.timestamps = np.array(self.timestamps)
        
    def calc_framerate(self):
        self.fps = 1./np.mean(np.diff(self.timestamps))
        self.fps_err_std = np.std(np.diff(self.timestamps))
        
    def calc_framekeys(self):
        self.framekeys = self.frameinfo.keys()
        self.framekeys.sort()
        
    def get_frame(self, n, format='cv'):
        '''
        format -- specifies image format, options: 'cv', 'pil', 'numpy'
        
        '''
        if type(n) is not str:
            n = self.framekeys[n]
        image_filename = n + '.png'
        image_filename = os.path.join(self.path_png, image_filename) 
        
        if format=='pil':
            im = Image.open(image_filename)
        else:
            im = cv.LoadImage(image_filename)
            if format == 'numpy' or format == 'np':
                im = cv_numpy.cv2array(im)
        self.current_frame = int(n)
                
        return im
        
    def get_next_frame(self, format='cv'):
        n = self.current_frame + 1
        im = self.get_frame(n, format)
        return im

    def timestamp_to_framenumber(self, t):
        f = np.argmin( np.abs(self.timestamps - t) )
        return f
        
    def get_frame_from_timestamp(self, t, format='cv'):
        f = self.timestamp_to_framenumber(t)
        im = get_frame(f, format)
        return im
        
