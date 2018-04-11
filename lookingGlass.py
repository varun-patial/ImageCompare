#!/usr/bin/python

# lookingGlass.py
#----------------------------------------------------------------------------
# Name:         lookingGlass.py
# Purpose:      Generate UI for image viewer and dislpay image.
#
# Author:       Varun Patial
#
# Created:      19-Mar-2018
#
# Copyright:    Copyright (C) 2018 Varun Patial
# Licence:      MIT License
#----------------------------------------------------------------------------

import gc
import wx
import os
import gettext
from rubberBand import wxPyRubberBander
import  wx.lib.scrolledpanel as scrolled
from PIL import Image, ImageTk, TiffImagePlugin, BmpImagePlugin, ImageFont, ImageDraw

# Declare GUI Constants
MENU_FILE_EXIT = wx.NewId()
DRAG_SOURCE    = wx.NewId()


###############################################
## Class for generating dialogue boxes       ##
class looking_glass(wx.Frame):
    
    def __init__(self, *args, **kw):
        kw["style"] = wx.DEFAULT_FRAME_STYLE
        #kw["style"] = (wx.FRAME_NO_TASKBAR | wx.NO_BORDER | wx.FRAME_SHAPED  )
        super(looking_glass, self).__init__(*args, **kw) 
        self.SetSize((800, 600))
        self.SetTitle("Looking Glass: Select a region to magnify.")
        
        
    def InitUI(self):

        ico = wx.Icon('lg.ico', wx.BITMAP_TYPE_ICO)
        self.SetIcon(ico)
   
        self.img_orig = wx.Image(self.diffFile, wx.BITMAP_TYPE_BMP)
        img = Image.open(self.diffFile, 'r')
        self.img_size = img.size
        self.img_scale = 1

        self.pnl = wx.PyScrolledWindow( self, -1 )
        self.pnl.SetScrollbars(1, 1, self.img_size[0], self.img_size[1])

        vbox = wx.BoxSizer(wx.HORIZONTAL)

        # Create a static bitmap for image to be put on looking glass
        self.bitmap_UGLASS = wx.StaticBitmap(self.pnl, wx.ID_ANY, wx.Bitmap(self.diffFile, wx.BITMAP_TYPE_ANY))

        vbox.Add(self.bitmap_UGLASS, proportion=1, 
            flag=wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL | wx.EXPAND, border=5)

        topSizer = wx.BoxSizer(wx.VERTICAL)
        topSizer.Add(vbox, 0, wx.CENTER)
        self.pnl.SetSizer(topSizer)

        # initialize rubber bands
        self.rBand = wxPyRubberBander( self.bitmap_UGLASS )
        self.rBand.setSources(self.fileName, self.source1, self.source2, self.diffFile)

        self.Bind(wx.EVT_SIZE, self.resize_space)
        self.Bind(wx.EVT_MOUSEWHEEL, self.set_scale)
        self.Bind(wx.EVT_KEY_UP, self.OnKeyDown)
        self.SetFocus()


    ###############################################
    ## Rescale image based on window size        ##
    def resize_space(self, event):
        img_new = self.img_orig.Copy()
        (window_width, window_height) = self.GetClientSizeTuple()

        if ( self.img_size[0] > self.img_size[1] and self.img_size[0] > window_width ):
            window_height = int(float(self.img_size[1]) * float(float(window_width) / float(self.img_size[0])))

        if ( self.img_size[1] > self.img_size[0] and self.img_size[1] > window_height ):
            window_width = int(float(self.img_size[0]) * float(float(window_height) / float(self.img_size[1])))

        self.img_scale = float(window_width) / float(self.img_size[0])
        self.rBand.setScale(self.img_scale)
        img_new.Rescale(window_width, window_height, wx.IMAGE_QUALITY_HIGH)

        img1 = wx.BitmapFromImage(img_new)
        self.bitmap_UGLASS.SetBitmap(img1)
        self.pnl.SetScrollbars(1, 1, window_width, window_height)
        self.pnl.Refresh()
        event.Skip()
        gc.collect()


    ###############################################
    ## Rescale image upon scoll action           ##
    def set_scale(self, event):
        amt = event.GetWheelRotation()
        units = amt/(-(event.GetWheelDelta())) 

        _bitmap_ = self.bitmap_UGLASS.GetBitmap()
        glass_img = wx.ImageFromBitmap(_bitmap_)
        width = glass_img.GetWidth()
        height = glass_img.GetHeight()
        glass_img.Destroy()

        # Check scale direction and scale accordingly
        if units > 0:
            width = int(width / 1.2)
            height = int(height / 1.2)
        else:
            width = int(width * 1.2)
            height = int(height * 1.2)

        if(self.img_size[0] < width or self.img_size[1] < height):
            event.Skip()
            return
        elif(width > 10 * self.img_size[0] or height > 10 * self.img_size[1]):
            event.Skip()
            return

        (window_width, window_height) = self.GetSizeTuple()
        if (window_width/2) > width and (window_height/2) > height:
            event.Skip()
            return

        # Scale the original image not the one being displayed
        img_new = self.img_orig.Copy()
        img_new.Rescale(width, height, wx.IMAGE_QUALITY_HIGH)

        self.img_scale = (width/float(self.img_size[0]))
        self.rBand.setScale(self.img_scale)

        # Get the scale bitmap and set it on looking glass
        img_bitmap = wx.BitmapFromImage(img_new)
        self.bitmap_UGLASS.SetBitmap(img_bitmap)
        img_new.Destroy()

        self.pnl.SetScrollbars(1, 1, width, height)
        self.pnl.Refresh()
        event.Skip()
        gc.collect()

    ###############################################
    ## Set source directories                    ##
    def setSources(self, fileName, src1, src2, diffFile):
        self.fileName = fileName
        self.source1  = src1
        self.source2  = src2
        self.diffFile = diffFile


    ###############################################
    ## Quit application on Esc or q              ##
    def OnKeyDown(self, event):
        """quit if user press q or Esc"""
        if event.GetKeyCode() == 27 or event.GetKeyCode() == ord('Q'): #27 is Esc
            self.Close(force=True)
        else:
            event.Skip()