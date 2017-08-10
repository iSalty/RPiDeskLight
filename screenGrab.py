# This Program Gets the colors of pixels on the screen (Only works in Windows)
# Date: 5/27/2017
# Author: Ian Saltwick
# Revision History

from __future__ import print_function
import time
from desktopmagic.screengrab_win32 import (getScreenAsImage)
from PIL import Image
import web

NUM_SECTIONS = 30
time_start = time.time()

file_path = "E:/Users/iSaltwick/Documents/EE Projects/RPi deskBacklight/screenGrab/"

urls = ('/', 'index')
app = web.application(urls, globals())

class index:
    def GET(self): # When someone querries a GET on the server calculate the colors and return it
        # Open the screencapture with PIL
        monitors = getScreenAsImage()
        #Image.open(file_path + "bothMonitors.png") USE THIS WHEN OPENING EXISTING PIC

        size = [NUM_SECTIONS, 1]
        monitors_small = monitors.resize(size, Image.ANTIALIAS)
        monitors_small.save(file_path + "bothMonitorsSmall.png", format='png')

        colors = [0 for i in range(0, NUM_SECTIONS, 1)]
        for x in range(0, NUM_SECTIONS, 1):
            colors[x] = monitors_small.getpixel((x, 0))

        return colors
    def POST(self):
        return "Post"

if __name__ == "__main__":
    app.run()
