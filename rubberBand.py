#!/usr/bin/python

# rubberBand.py
#----------------------------------------------------------------------------
# Name:         rubberBand.py
# Purpose:      wxPyRubberBander class describes a generic method of drawing
#               rubberbands on a wxPython wxStaticBitmap object when the user 
#               presses the left mouse button and drags it over a rectangular
#               area. It has methods to return the selected area by the user 
#               as a rectangular 4 tuple / Clear the selected area.
#
# Author:       Varun Patial
#
# Created:      08-Sep-2017
#
# Copyright:    Copyright (C) 2018 Varun Patial
# Licence:      MIT License
#----------------------------------------------------------------------------

import gc
import wx
import os
import time
import tempfile
import subprocess
from PIL import Image, ImageTk, TiffImagePlugin, BmpImagePlugin, ImageFont, ImageDraw
from wxPython.wx import *

###################################################################################
## A class to manage mouse events/ rubberbanding of a wxPython canvas object.    ##
class wxPyRubberBander:

    def __init__(self, canvas):
        
        # canvas object
        self._canvas = canvas
        # mouse selection start point
        self.m_stpoint=wx.Point(0,0)
        # mouse selection end point
        self.m_endpoint=wx.Point(0,0)
        # mouse selection cache point
        self.m_savepoint=wx.Point(0,0)

        self.image_scale = 0.0
        
        # flags for left click/ selection
        self._leftclicked=False
        self._selected=False

        # Register event handlers for mouse
        self.RegisterEventHandlers()

    ###############################################################################
    ## Register event handlers for this object.                                  ##
    def RegisterEventHandlers(self):
        EVT_LEFT_DOWN(self._canvas, self.OnMouseEvent)
        EVT_LEFT_UP(self._canvas, self.OnMouseEvent)
        EVT_MOTION(self._canvas, self.OnMouseEvent)
        EVT_LEAVE_WINDOW(self._canvas, self.OnMouseEvent)

    ###############################################################################
    ## This function manages mouse events.                                       ##    
    def OnMouseEvent(self, event):
        if event:

            # set mouse cursor
            self._canvas.SetCursor(wxStockCursor(wxCURSOR_ARROW))
            # get device context of canvas
            dc= wxClientDC(self._canvas)
            
            # Set logical function to XOR for rubberbanding
            dc.SetLogicalFunction(wxXOR)
            
            # Set dc brush and pen
            # Here I set brush and pen to white and grey respectively
            # You can set it to your own choices
            
            # The brush setting is not really needed since we
            # dont do any filling of the dc. It is set just for 
            # the sake of completion.

            wbrush = wxBrush(wxColour(255,255,255), wxTRANSPARENT)
            wpen = wxPen(wxColour(200, 200, 200), 1, wxSOLID)
            dc.SetBrush(wbrush)
            dc.SetPen(wpen)

            
        if event.LeftDown():

           # Left mouse button down, change cursor to
           # something else to denote event capture
           self.m_stpoint = event.GetPosition()
           cur = wxStockCursor(wxCURSOR_CROSS)  
           self._canvas.SetCursor(cur)

           # invalidate current canvas
           self._canvas.Refresh()
           # cache current position
           self.m_savepoint = self.m_stpoint
           self._selected = false
           self._leftclicked = true

        elif event.Dragging():   
           
            # User is dragging the mouse, check if
            # left button is down
            
            if self._leftclicked:

                # reset dc bounding box
                dc.ResetBoundingBox()
                dc.BeginDrawing()
                w = (self.m_savepoint.x - self.m_stpoint.x)
                h = (self.m_savepoint.y - self.m_stpoint.y)
                
                # To erase previous rectangle
                dc.DrawRectangle(self.m_stpoint.x, self.m_stpoint.y, w, h)
                
                # Draw new rectangle
                self.m_endpoint =  event.GetPosition()
                
                w = (self.m_endpoint.x - self.m_stpoint.x)
                h = (self.m_endpoint.y - self.m_stpoint.y)
                
                # Set clipping region to rectangle corners
                dc.SetClippingRegion(self.m_stpoint.x, self.m_stpoint.y, w,h)
                dc.DrawRectangle(self.m_stpoint.x, self.m_stpoint.y, w, h) 
                dc.EndDrawing()
               
                self.m_savepoint = self.m_endpoint # cache current endpoint

        elif event.LeftUp():

            # User released left button, change cursor back
            self._canvas.SetCursor(wxStockCursor(wxCURSOR_ARROW))       
            self._selected = true  #selection is done
            self._leftclicked = false # end of clicking  
            box = self.GetCurrentSelection()
            diffImg = Image.open(self.diffFile, 'r')
            Dimg_out = diffImg.crop(box)

            Lfile = ""
            Rfile = ""
            if self.singleScan == 1:
                Lfile = self.source1
                Rfile = self.source2
            else:
                Lfile = self.source1 + "\\" + self.fileName
                Rfile = self.source2 + "\\" + self.fileName
                
            Limg = Image.open(Lfile, 'r')
            Limg_out = Limg.crop(box)
 
            Rimg = Image.open(Rfile, 'r')
            Rimg_out = Rimg.crop(box)

            imgSize = Dimg_out.size
            imgWidth = 3*imgSize[0]
            imgHeight = imgSize[1]

            img_out = Image.new('RGB', (imgWidth, imgHeight))
            img_out.paste(Limg_out,(0,0)) 
            img_out.paste(Rimg_out,(imgWidth/3, 0))
            img_out.paste(Dimg_out,((2*imgWidth)/3, 0))

            try:
                ## Save image in temporary directory and the call default viewer to show the image. ##
                temp = tempfile.NamedTemporaryFile(prefix="ImageCompare_", dir=os.path.dirname(self.diffFile))
                fileName = temp.name + ".bmp"
                temp.close()
                img_out.save(fileName, 'bmp')
                subprocess.Popen('start ' + fileName, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                ## Processes the file open operation in separate terminal ##
                #os.system('start ' + fileName)
                #img_out.show()   ## Not a very reliable funtion

                #for i, value in enumerate(img_out.histogram()):
                #   print i, value

            except SystemError:
                print "Warning : tile cannot extend outside image. Action ignored.\n"
            self.ClearCurrentSelection()
            gc.collect()
      
      
    ###############################################################################
    ## Return the current selected rectangle.                                    ##            
    def GetCurrentSelection(self):
        
        # if there is no selection, selection defaults to
        # current viewport
        
        left = wxPoint(0,0)
        right = wxPoint(0,0)
        
        # user dragged mouse to right
        if self.m_endpoint.y > self.m_stpoint.y:
            right = self.m_endpoint
            left = self.m_stpoint
        # user dragged mouse to left
        elif self.m_endpoint.y < self.m_stpoint.y:
            right = self.m_stpoint
            left = self.m_endpoint

        if self.image_scale < 1:
            left.x  = left.x / self.image_scale
            left.y  = left.y / self.image_scale
            right.x = right.x / self.image_scale
            right.y = right.y / self.image_scale


        if(left.x < right.x):  
          return (left.x, left.y, right.x, right.y)
        else:
          return (right.x, left.y, left.x, right.y)


    ###############################################################################
    ## Clear the current selected rectangle.                                     ##
    def ClearCurrentSelection(self):
        
        box = self.GetCurrentSelection()
        
        dc=wxClientDC(self._canvas)
        
        w = box[2] - box[0]
        h = box[3] - box[1]
        dc.SetClippingRegion(box[0], box[1], w, h)
        dc.SetLogicalFunction(wxXOR)
        
        # The brush is not really needed since we
        # dont do any filling of the dc. It is set for 
        # sake of completion.
        
        wbrush = wxBrush(wxColour(255,255,255), wxTRANSPARENT)
        wpen = wxPen(wxColour(200, 200, 200), 1, wxSOLID)
        dc.SetBrush(wbrush)
        dc.SetPen(wpen)
        dc.DrawRectangle(box[0], box[1], w,h)
        self._selected = false 
        
        # reset selection to canvas size
        self.ResetSelection()    

    ###############################################################################
    ## Resets the mouse selection to entire canvas.                              ##
    def ResetSelection(self):  
        self.m_stpoint = wxPoint(0,0)
        sz=self._canvas.GetSize()
        w,h=sz.GetWidth(), sz.GetHeight()
        self.m_endpoint = wxPoint(w,h)


    ###############################################################################
    ## Set image scale.                                                          ##
    def setScale(self, scale):
        self.image_scale = scale

    ###############################################################################
    ## Set source directories.                                                   ##
    def setSources(self, fileName, src1, src2, diffFile):
        self.fileName   = fileName
        self.source1    = src1
        self.source2    = src2
        self.singleScan = 0
        self.diffFile   = diffFile
        if os.path.isfile(self.source1) and os.path.isfile(self.source2):
            self.singleScan = 1
        else:
            self.singleScan = 0
