#!/usr/bin/env python
from __future__ import division
import roslib; roslib.load_manifest('save_ros_movie')
import rospy

import time
import sys, os, subprocess
from optparse import OptionParser

import pickle

from sensor_msgs.msg import Image
import cv
from cv_bridge import CvBridge, CvBridgeError

from save_ros_movie.srv import *

PNG_IMG_SUB_DIR = 'png_image_files'

def Chdir(dir):
    try:
        os.chdir(dir)
    except (OSError):
        os.mkdir(dir)
        os.chdir(dir)

###############################################################################
# Save() is a ROS node. It saves image messages as png files for the specified image topic.
# Once a save node is running, you can toggle recording on/off via the service, for example for topic camera/image_raw type this into the command line: 
#       $ rosservice call camera/image_raw/save PATH_TO_WHERE_YOU_WANT_TO_SAVE_MOVIE 1
# If the path exists, Save() will create a subdirectory with a unique date/time name. Otherwise it will create the directory you give it and will use that.
# Optionally Save() will convert the pngs to a .mov file after recording is done
#
class Save:
    def __init__(self, topicVideo="camera/image_raw", nframedigits=10, render_movie=True):
        self.topicVideo = topicVideo
        self.nframedigits = nframedigits
        self.render_movie = render_movie
        
        self.date = time.strftime("%Y%m%d")
        self.bSavingVideo = False
        
        # service for toggling saving video
        toggleSavingVideoService_name = topicVideo + '/save'
        self.toggleSavingVideoService = rospy.Service(toggleSavingVideoService_name, ToggleSavingVideo, self.toggleSavingVideoService_callback)
        
        # Image subscription stuff
        self.subImage = rospy.Subscriber(topicVideo, Image, self.Image_callback)
        self.bridge = CvBridge()
        self.sizeImage = None
        
    def toggleSavingVideoService_callback(self, toggleSavingVideo):
        if toggleSavingVideo.save is True:
        
            # get time, to generate unique names
            basename = self.topicVideo.lstrip('/')
            name = basename.replace('/', '_') + '_' + time.strftime("%Y%m%d_%s")
            self.filenameVideo = name + '.mov'
            self.filenameFrameInfo = name + '.pickle'
            
            # if path does not exist, make new dir
            # if path does exist, create subdirectory based on YMDS
            tmp_path = os.path.expanduser(toggleSavingVideo.path)
            if os.path.exists(tmp_path):
                print 'Path exists, creating new directory based on date and time'
                path = os.path.join(tmp_path, name)
            else:
                path = tmp_path
            self.path = os.path.expanduser(path)
            print
            print 'Saving video images to: ', self.path 
            Chdir(self.path)
            os.mkdir(PNG_IMG_SUB_DIR)
            Chdir(self.path)
            self.bSavingVideo = True
            
            
            self.frameInfo = {}
            self.iFrame = 0
        
            print self.filenameFrameInfo
            
        elif toggleSavingVideo.save is False:
            self.bSavingVideo = False
            self.WriteVideoFromFrames()
            
        return 1

    def OnShutdown_callback(self):
        pass
        
    def get_png_filenames(self):
        cmd = 'ls ' + self.path
        ls = os.popen(cmd).read()
        all_filelist = ls.split('\n')
        try:
            all_filelist.remove('')
        except:
            pass
            
        filelist = []
        for i, filename in enumerate(all_filelist):
            if '.png' in filename:
                filelist.append(filename)
        return filelist

    def WriteVideoFromFrames(self):
        
        # Save frame info file
        filenameFrameInfo_withPath = os.path.join(self.path, self.filenameFrameInfo)
        f = open(filenameFrameInfo_withPath, 'w')
        pickle.dump(self.frameInfo, f)
        
        # write .png files to .mov file
        if self.render_movie:
            print
            print "Saving video - this could take a moment if a long video"
            print
            cmdCreateVideoFile = 'avconv -r 30 -i ' + self.path + '/' + PNG_IMG_SUB_DIR + '/%0' + str(self.nframedigits) + 'd.png -r 30 ' + self.filenameVideo
            rospy.logwarn('Converting .png images to video using command:')
            rospy.logwarn (cmdCreateVideoFile)
            if 1: #try:
                subprocess.Popen(cmdCreateVideoFile, shell=True)
            else: #except:
                rospy.logerr('Exception running avconv')
                
            rospy.logwarn('Saved %s' % (self.filenameVideo))
            self.filenameVideo = None
            
    def WriteFilePng(self, cvimage, filenameImage):
        if self.sizeImage is None:
            self.sizeImage = cv.GetSize(cvimage)
        filenameImage_withPath = os.path.join(self.path, filenameImage)
        cv.SaveImage(filenameImage_withPath, cvimage)
        print filenameImage_withPath

    def Image_callback(self, image):
        if (self.bSavingVideo) and (image is not None):
            self.iFrame += 1
            # Convert ROS image to OpenCV image
            try:
              cvimage = cv.GetImage(self.bridge.imgmsg_to_cv(image, "passthrough"))
            except CvBridgeError, e:
              print e
            # cv.CvtColor(cvimage, self.im_display, cv.CV_GRAY2RGB)

            # Create unique filename: cameraIdentifier_year_month_day_secs_nsecs_frameNumber.png
            frameInfo = {   'cameraIdentifier': image.header.frame_id.strip('/'),
                            'date': self.date,
                            'secs': image.header.stamp.secs,
                            'nsecs': image.header.stamp.nsecs,
                            }
            s = "{num:0" + str(self.nframedigits) + "d}"
            frameNumber = s.format(num=self.iFrame)
            filenameImage = PNG_IMG_SUB_DIR + '/' + frameNumber + '.png' 
            self.frameInfo.setdefault(frameNumber, frameInfo)
    
            self.WriteFilePng(cvimage, filenameImage)
            
                

    def Main(self):
        rospy.spin()
        

if __name__ == '__main__':

    parser = OptionParser()
    parser.add_option("--topic", type="string", dest="topic", default="camera/image_raw",
                        help="topic name you wish to save images from, \n Default = camera/image_raw")
    parser.add_option("--nframedigits", type="int", dest="nframes", default=10,
                        help="max number of digits of frames you will be recording, eg. 3 means 999 frames. \nDefault = 10")
    parser.add_option("--render-movie", action="store_true", dest="render_movie",
                        help="render movie after recording")                 
    (options, args) = parser.parse_args()
    
    service_name = options.topic + '/save'
    save_to_path = "~/save_ros_movie_example_path"
    
    print
    print
    print 'Ready to save image stream!'
    print
    print 'Toggle data streaming using ROS service: ', service_name
    print 'Toggle on from command line: $ rosservice call', service_name, save_to_path, '1'
    print 'Toggle off from command line: $ rosservice call', service_name, save_to_path, '0'
    



    node_name = "Save_" + options.topic.split('/')[0]
    rospy.init_node(node_name, log_level=rospy.INFO)
    save = Save(options.topic, options.nframes, options.render_movie)
    save.Main()
    
    
    
