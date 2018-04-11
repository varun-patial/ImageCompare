#!/usr/bin/python

# listbox.py
#----------------------------------------------------------------------------
# Name:         listbox.py
# Purpose:      Generate list of results and process event against list items.
#
# Author:       Varun Patial
#
# Created:      08-Sep-2017
#
# Copyright:    Copyright (C) 2018 Varun Patial
# Licence:      MIT License
#----------------------------------------------------------------------------


import wx
import os
import sys
import string
from wxPython.wx import *
from lookingGlass import looking_glass
from wx.lib.mixins.listctrl import ColumnSorterMixin
from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin
from PIL import Image, ImageTk, TiffImagePlugin, BmpImagePlugin, ImageFont, ImageDraw

list_data = {}

## Right click options with menu items ##
menu_titles = [ "view Diff",
                "view Left-Right-Diff",
                "view Left-Right",
                "view Left",
                "view Right",
                "Looking glass", ]

result_types = { 1 : "Images are same.",
                 2 : "Images are different.",
                 3 : "Images have different resolution.",
                 4 : "Unknown response.",
                 5 : "Left Only.",
                 6 : "Right Only.",
                 7 : "Images have different colourspaces.", }
                 
result_menu = { 1 : ["view Left-Right","view Left","View Right"],
                2 : menu_titles,
                3 : ["view Left","View Right"],
                4 : [],
                5 : ["view Left"],
                6 : ["view Right"],
                7 : ["view Left-Right","view Left","View Right"],
              }

menu_title_by_id = {}

###############################################
## Sorted list control class.                ##  
class SortedListCtrl(wx.ListCtrl, ColumnSorterMixin, ListCtrlAutoWidthMixin):
    def __init__(self, parent):
        wx.ListCtrl.__init__(self, parent, -1, style=wx.LC_REPORT)
        ColumnSorterMixin.__init__(self, 3)
        ListCtrlAutoWidthMixin.__init__(self)
        self.itemDataMap = list_data

    def getItemDataMaps(self):
        return self.itemDataMap

    def GetListCtrl(self):
        return self

    def updateItemDataMap(self, op, key, data):
        if(op is "INSERT"):
          self.itemDataMap.update({key:data})
          list_data.update({key:data})
        else:
          list_data.update({key:data})
          pass

    def clearDataMaps(self):
        self.itemDataMap = {}


###############################################
## listBox class.                            ##        
class listBox(wx.Frame):
    def __init__(self, panel):
        self.list_index = 0
        self.hbox       = wx.BoxSizer(wx.VERTICAL)
        self.panel      = panel
        self.source1    = ""
        self.source2    = ""
        self.tiffDiffPath = "tiffdiff"
        self.singleScan = 0
        self.labels     = 1
        self.cs         = "RGB"
        self.list = SortedListCtrl(panel)
        self.list.InsertColumn(0, 'File', width=250)
        self.list.InsertColumn(1, 'Compare Results', width=200)
        self.list.InsertColumn(2, 'Decription', 200)

        ### 1. Register source's EVT_s to invoke launcher. ###
        EVT_LIST_ITEM_RIGHT_CLICK(self.list, -1, self.RightClickCb)
        EVT_LIST_ITEM_SELECTED(self.list, -1, self.setSelection)
        EVT_LIST_ITEM_ACTIVATED(self.list, -1, self.DoubleClickCb)
       
            
        self.hbox.Add(self.list, 1, wx.EXPAND)
        #panel.SetSizer(self.hbox)
        panel.SetSizerAndFit(self.hbox)

        #self.Centre()
        #self.Show(True)

    ###############################################
    ## Perform doubleclick operation             ##
    def setSelection( self, event):
        self.list_item_clicked = str(event.GetText())


    ###############################################
    ## Perform doubleclick operation             ##
    def DoubleClickCb( self, event ):
        self.rClick_vall(self.list_item_clicked)


    ###############################################
    ## Perform rightclick operation              ##
    def RightClickCb( self, event ):
        # record what was clicked
        menu_title_by_id.clear()
        point =  event.GetPoint()
        listCtl = event.GetEventObject()
        (indx, subindx) = listCtl.HitTest(point)
        self.list_item_clicked = listCtl.GetItem(indx).GetText()

        result = listCtl.GetItem(indx, col=1).GetText()
        ### 2. Launcher creates wxMenu. ###
        menu = wxMenu()

        menu_type = result_types.keys()[result_types.values().index(result)]
        menu_list = result_menu[menu_type]
        for title in menu_list:
            menu_title_by_id[ wxNewId() ] = title

        for (id,title) in menu_title_by_id.items():
            ### 3. Launcher packs menu with Append. ###
            menu.Append( id, title )
            ### 4. Launcher registers menu handlers with EVT_MENU, on the menu. ###
            EVT_MENU( menu, id, self.MenuSelectionCb )

        ### 5. Launcher displays menu with call to PopupMenu, invoked on the source component, passing event's GetPoint. ###
        self.panel.PopupMenu( menu, event.GetPoint() )
        menu.Destroy() # destroy to avoid mem leak

    ###############################################
    ## Report operation performed                ##
    def MenuSelectionCb( self, event ):
        # do something
        operation = menu_title_by_id[ event.GetId() ]
        target    = self.list_item_clicked
        #print 'Perform "%(operation)s" on "%(target)s."' % vars()

        if  (operation == menu_titles[0]):
            self.rClick_vdiff(target)
        elif(operation == menu_titles[1]):
            self.rClick_vall(target)
        elif(operation == menu_titles[2]):
            self.rClick_vboth(target)
        elif(operation == menu_titles[3]):
            self.rClick_vleft(target)
        elif(operation == menu_titles[4]):
            self.rClick_vright(target)
        elif(operation == menu_titles[5]):
            self.view_diff(target)
       
        menu_title_by_id.clear()

    ###############################################
    ## Insert elements at the bottom of the list ##
    def insertElement(self, element, color_flag=None, map_flag=None):
        self.list_index = self.list_index + 1
        index = self.list.InsertStringItem(sys.maxint, element[0])
        self.list.SetStringItem(index, 1, element[1])
        self.list.SetStringItem(index, 2, element[2])
        self.list.SetStringItem(index, 3, element[3])
        self.list.SetItemData(index, self.list_index)

        ## Color scheme.. To be implemented    ##
        #if "only" in element[1].lower():
        if element[1].find("Not a valid image") > -1 or element[1].find("not recognized as an internal or external command") > -1 or element[1].find("system cannot find the path specified") > -1:
            self.list.SetItemBackgroundColour(index, col='#FA5858')
        elif element[1].find("Images have different resolution") > -1:
            self.list.SetItemBackgroundColour(index, col='#FA5858')
        elif element[1].find("Images are same") > -1:
            self.list.SetItemBackgroundColour(index, col='#A9F5A9')
        elif element[1].find("Images are different") > -1:
            self.list.SetItemBackgroundColour(index, col='#F2F5A9')
        elif element[1].find("Images have different colourspaces") > -1:
            self.list.SetItemBackgroundColour(index, col='#F2F5A9')
        else:
            self.list.SetItemBackgroundColour(index, col='#E1E1E1')

        # update data map: Sort list functionality needs a backup of data
        if map_flag is None:
            self.list.updateItemDataMap("INSERT", self.list_index, element)
        else:
            self.list.updateItemDataMap("I_INSERT", self.list_index, element)

    ###############################################
    ## Clear the entire list                     ##
    def ClearAll(self, clrAll=None):
        self.list.DeleteAllItems()
        self.list_index = 0
        if clrAll is not None:
            self.list.clearDataMaps()

    ###############################################
    ## Funtion to view all images                ##
    def rClick_vall(self,file):
        imgPath1 = ""
        imgPath2 = ""
        if self.singleScan == 1:
            imgPath1 = self.source1
            imgPath2 = self.source2
        else:
            imgPath1 = self.source1 + "\\" + file
            imgPath2 = self.source2 + "\\" + file
        imgPath3 = self.tiffDiffPath + "\\" + string.rsplit(file, '.', 1)[0] + "-diff.bmp"
        self.StackAllImgView(imgPath1, imgPath2, imgPath3)

    ###############################################
    ## Funtion to view difference                ##
    def rClick_vdiff(self,file):
        imgPath = self.tiffDiffPath + "\\" + string.rsplit(file, '.', 1)[0] + "-diff.bmp"
        self.imgView(imgPath)

    ###############################################
    ## Funtion to view left and right images     ##
    def rClick_vboth(self, file):
        imgPath1 = ""
        imgPath2 = ""
        if self.singleScan == 1:
            imgPath1 = self.source1
            imgPath2 = self.source2
        else:
            imgPath1 = self.source1 + "\\" + file
            imgPath2 = self.source2 + "\\" + file

        self.cobmImgView(imgPath1, imgPath2)


    ###############################################
    ## Funtion to view left image                ##
    def rClick_vleft(self, file):
        imgPath = ""
        if self.singleScan == 1:
            imgPath = self.source1
        else:
            imgPath = self.source1 + "\\" + file
        self.imgView(imgPath)

    ###############################################
    ## Funtion to view left image                ##
    def rClick_vright(self, file):
        imgPath = ""
        if self.singleScan == 1:
            imgPath = self.source2
        else:
            imgPath = self.source2 + "\\" + file
        self.imgView(imgPath)


    ###############################################
    ## View left unique items only               ##
    def viewLeftUnique(self, event):
        items = self.list.getItemDataMaps()
        itemsMap = items.items()
        self.ClearAll()

        for key, data in itemsMap:
            if("left only" in data[1].lower()):
              self.insertElement(data, None, "FALSE")


    ###############################################
    ## View right unique items only              ##
    def viewRightUnique(self, event):
        items = self.list.getItemDataMaps()
        itemsMap = items.items()
        self.ClearAll()

        for key, data in itemsMap:
            if("right only" in data[1].lower()):
              self.insertElement(data, None, "FALSE")


    ###############################################
    ## View similar items only                   ##
    def viewSame(self, event):
        items = self.list.getItemDataMaps()
        itemsMap = items.items()
        self.ClearAll()

        for key, data in itemsMap:
            if("images are same" in data[1].lower()):
              self.insertElement(data, None, "FALSE")


    ###############################################
    ## View different items only                 ##
    def viewDifferent(self, event):
        items = self.list.getItemDataMaps()
        itemsMap = items.items()
        self.ClearAll()

        for key, data in itemsMap:
            if("images are different" in data[1].lower()):
              self.insertElement(data, None, "FALSE")


    ###############################################
    ## View right unique items only              ##
    def viewAll(self, event):
        items = self.list.getItemDataMaps()
        itemsMap = items.items()
        self.ClearAll()

        for key, data in itemsMap:
            self.insertElement(data, None, "FALSE")


    ###############################################
    ## Analyze difference using looking glass    ##
    def view_diff(self, fileName):
        lg = looking_glass(None, style = wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        diffFile = self.tiffDiffPath + "\\" + string.rsplit(fileName, '.', 1)[0] + "-diff.bmp"
        lg.setSources(fileName, self.source1, self.source2, diffFile)
        lg.InitUI()
        lg.Show()
              

    ###############################################
    ## Image viewer                              ##
    def imgView(self, path):
        img = Image.open(path, 'r')
        img.show()

    ###############################################
    ## set/reset labels                          ##
    def updateLabelFlag(self, flag):
        self.labels = flag

    ###############################################
    ## set/reset labels                          ##
    def updateCS(self, colourspace):
        self.cs = colourspace


    ###############################################
    ## Stack all images and call viewer          ##
    def StackAllImgView(self, path1, path2, path3):
      imgL = Image.open(path1, 'r')
      imgR = Image.open(path2, 'r')
      imgD = Image.open(path3, 'r')

      imgSize = imgL.size
      imgWidth = 3*imgSize[0]
      imgHeight = imgSize[1]
      FOREGROUND = (255, 0, 0, 255)

      # If any exception occurs while adding labels on page then ignore drawing labels #
      try:
        if self.labels == 1:
          fontSize = int(imgSize[1]/70)
          draw = ImageDraw.Draw(imgL)
          font = ImageFont.truetype("arial.ttf", fontSize)
          draw.text((int(imgSize[0]/7), 5), path1, font=font, fill=FOREGROUND)

          draw = ImageDraw.Draw(imgR)
          font = ImageFont.truetype("arial.ttf", fontSize)
          draw.text((int((imgSize[0]/7)), 5), path2, font=font, fill=FOREGROUND)

          #draw = ImageDraw.Draw(imgD)
          #font = ImageFont.truetype("arial.ttf", fontSize)
          #draw.text((int((imgSize[0]/7)), 5), path3, font=font, fill=1)
      except:
        pass

      imgNew = Image.new(self.cs, (imgWidth, imgHeight))
      imgNew.paste(imgL,(0,0)) 
      imgNew.paste(imgR,(imgWidth/3, 0))
      imgNew.paste(imgD,((2*imgWidth)/3, 0))
      imgNew.show()


    ###############################################
    ## Funtion to stack left and right images    ##
    def cobmImgView(self, path1, path2):
      imgL = Image.open(path1, 'r')
      imgR = Image.open(path2, 'r')
      imgSize = imgL.size
      imgWidth = 2*imgSize[0]
      imgHeight = imgSize[1]
      imgNew = Image.new(self.cs, (imgWidth, imgHeight))
      imgNew.paste(imgL,(0,0)) 
      imgNew.paste(imgR,(imgWidth/2, 0))
      imgNew.show()


    ###############################################
    ## Funtion to set source paths of images     ##
    def SetSource(self, src1, src2):
        self.source1=src1
        self.source2=src2
        if os.path.isfile(src1) and os.path.isfile(src2):
            self.singleScan = 1
        else:
            self.singleScan = 0

    ###############################################
    ## Funtion to set tiff diff paths            ##
    def SetTiffDiffPath(self, path):
        self.tiffDiffPath=path

    def OnColClick(self):
        pass