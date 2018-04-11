#!/usr/bin/env python

#----------------------------------------------------------------------------
# Name:         ImageCompare.py
# Purpose:      Tool for comparing tiff files.
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
import sys
import glob
import string
import gettext
import subprocess
import threading
from listbox import listBox
from dialog_window import gen_dialog
from cfgParse import configFileParser
from PIL import ImageChops, ImageOps
from PIL import Image, ImageDraw, TiffImagePlugin, BmpImagePlugin



# Declare GUI Constants
MENU_FILE_EXIT = wx.NewId()
DRAG_SOURCE    = wx.NewId()
compare_list   = None
event          = None
sbar_status    = "Idle"
udf_path       = os.path.dirname(os.path.realpath(sys.argv[0])) + "\\cfg\\default.udf"
tiff_diff_path = "tiffdiff"
app_data_path  = os.environ['APPDATA'] + "\\ImageKompare"
temp_data_path  = os.environ['TEMP']


###############################################
## Frame class for main window.              ## 
class MainFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        # begin : MainFrame.__init__
        kwds["style"] = wx.DEFAULT_FRAME_STYLE

        (h_size, v_size) = wx.DisplaySize()
        kwds["size"] = (h_size-100, v_size-100)
        wx.Frame.__init__(self, *args, **kwds)

        # Quit application if Esc or q key is pressed
        self.Bind(wx.EVT_KEY_UP, self.OnKeyDown)

        global udf_path
        global tiff_diff_path
        global app_data_path
        global temp_data_path

        self.configParse = configFileParser()
        self.configEnv = self.configParse.get_cfg_hash(udf_path)

        # Always use APPDATA dir as there may may not be enough permissions #
        # to write in installation dir. This is to fix issues with Win7.    #
        if True:
          if not os.path.exists(app_data_path):
            os.makedirs(app_data_path)
            os.makedirs(app_data_path + "\\cfg")

          udf_path = app_data_path + "\\" + "cfg\\default.udf"
          if not os.path.exists(udf_path):
            with open(udf_path,"w") as f:
              for key in self.configEnv:
                  print >>f, key + "=" + str(self.configEnv[key])
          self.configEnv = self.configParse.get_cfg_hash(udf_path)

        # Always use temp dir as there may may not be enough permissions to #
        # write in installation dir. This is to fix issues with Win7.       #
        if True:
          if not os.path.exists(temp_data_path + "\\" + tiff_diff_path):
            os.makedirs(temp_data_path + "\\" + tiff_diff_path)
          tiff_diff_path = temp_data_path + "\\" + tiff_diff_path


        # Create panel to add widgets
        self.panel = wx.Panel(self, -1)

        global sbar_status
        global compare_list
        compare_list = listBox(self.panel)
        compare_list.SetTiffDiffPath(tiff_diff_path)

        ico = wx.Icon('icon.ico', wx.BITMAP_TYPE_ICO)
        self.SetIcon(ico)

        # Menu Bar
        self.main_window_menubar = wx.MenuBar()

        wxglade_tmp_menu = wx.Menu()
        m_open = wxglade_tmp_menu.Append(wx.ID_OPEN, "&Open\tCtrl+O", "Open files to compare.", wx.ITEM_NORMAL)
        m_save = wxglade_tmp_menu.Append(wx.ID_SAVE, "&Save\tCtrl+S", "", wx.ITEM_NORMAL)
        m_cler = wxglade_tmp_menu.Append(wx.ID_ANY, _("Clear"), "", wx.ITEM_NORMAL)
        m_exit = wxglade_tmp_menu.Append(wx.ID_EXIT, "E&xit\tAlt+Q", "", wx.ITEM_NORMAL)
        self.main_window_menubar.Append(wxglade_tmp_menu, _("File"))

        wxglade_tmp_menu = wx.Menu()
        m_lu = wxglade_tmp_menu.Append(wx.ID_ANY, _("Left Unique"), "View left unique items.", wx.ITEM_NORMAL)
        m_ru = wxglade_tmp_menu.Append(wx.ID_ANY, _("Right Unique"), "View right unique items.", wx.ITEM_NORMAL)
        m_sa = wxglade_tmp_menu.Append(wx.ID_ANY, _("Same"), "View similar items.", wx.ITEM_NORMAL)
        m_df = wxglade_tmp_menu.Append(wx.ID_ANY, _("Different"), "View different items.", wx.ITEM_NORMAL)
        m_va = wxglade_tmp_menu.Append(wx.ID_ANY, _("View all"), "View all items.", wx.ITEM_NORMAL)
        self.main_window_menubar.Append(wxglade_tmp_menu, _("View"))

        wxglade_tmp_menu = wx.Menu()
        #m_cfg = wxglade_tmp_menu.Append(wx.ID_ANY, _("Configure"), "", wx.ITEM_NORMAL)
        self.m_lbl = wxglade_tmp_menu.Append(wx.ID_ANY, _("Disable labels"), "Enable/Disable labels.", wx.ITEM_NORMAL)
        self.img_menu = wx.Menu()
        #self.m_image_cs_auto = self.img_menu.Append(wx.ID_ANY, _("ColourSpace Auto"), "ImageCompare will determine colourspace automatically.", kind=wx.ITEM_CHECK)
        self.m_image_cs_cmyk = self.img_menu.Append(wx.ID_ANY, _("ColourSpace CMYK"), "Set image colour space as CMYK.", kind=wx.ITEM_CHECK)
        self.m_image_cs_rgb  = self.img_menu.Append(wx.ID_ANY, _("ColourSpace RGB"), "Set image colour space as RGB.", kind=wx.ITEM_CHECK)
        #self.img_menu.Check(self.m_image_cs_auto.GetId(), False)
        self.img_menu.Check(self.m_image_cs_rgb.GetId(),  True )
        self.img_menu.Check(self.m_image_cs_cmyk.GetId(), False)
        wxglade_tmp_menu.AppendMenu(wx.ID_ANY, 'Image', self.img_menu)
        self.main_window_menubar.Append(wxglade_tmp_menu, _("Tools"))

        wxglade_tmp_menu = wx.Menu()
        m_abt = wxglade_tmp_menu.Append(wx.ID_ANY, _("About"), "", wx.ITEM_NORMAL)
        self.main_window_menubar.Append(wxglade_tmp_menu, _("Help"))
        #self.SetMenuBar(self.main_window_menubar)
        # Menu Bar end

        # Menu Bar bindings
        self.Bind(wx.EVT_MENU, self.open_diag, m_open)
        self.Bind(wx.EVT_MENU, ClearList, m_cler)
        self.Bind(wx.EVT_MENU, self.onSaveFile, m_save)
        self.Bind(wx.EVT_MENU, compare_list.viewLeftUnique, m_lu)
        self.Bind(wx.EVT_MENU, compare_list.viewRightUnique, m_ru)
        self.Bind(wx.EVT_MENU, compare_list.viewSame, m_sa)
        self.Bind(wx.EVT_MENU, compare_list.viewDifferent, m_df)
        self.Bind(wx.EVT_MENU, compare_list.viewAll, m_va)
        self.Bind(wx.EVT_MENU, self.OnAboutBox, m_abt)
        self.Bind(wx.EVT_MENU, self.OnFileExit, m_exit)
        self.Bind(wx.EVT_MENU, self.toggleLabel, self.m_lbl)
        #self.Bind(wx.EVT_MENU, lambda event: self.SetCS(event, "RGB"), self.m_image_cs_auto)
        self.Bind(wx.EVT_MENU, lambda event: self.SetCS(event, "RGB"), self.m_image_cs_rgb)
        self.Bind(wx.EVT_MENU, lambda event: self.SetCS(event, "CMYK"), self.m_image_cs_cmyk)
        # Menu bar binding end
        
        # Status Bar
        #self.Bind(EVT_ONCHANGE_VAR, self.update_statusbar, sbar_status)
        self.main_window_statusbar = self.CreateStatusBar(1, 0)
        
        # Tool Bar
        self.main_window_toolbar = wx.ToolBar(self, -1)
        self.SetToolBar(self.main_window_toolbar)
        t_open = self.main_window_toolbar.AddLabelTool(wx.ID_ANY, _("Open"), wx.Bitmap(os.path.dirname(os.path.realpath(sys.argv[0])) + "\\res\\open.png", wx.BITMAP_TYPE_ANY), wx.NullBitmap, wx.ITEM_NORMAL, "Open files to compare", "Open files to compare")
        self.Bind(wx.EVT_MENU, self.open_diag, t_open)

        t_save = self.main_window_toolbar.AddLabelTool(wx.ID_ANY, _("Save"), wx.Bitmap(os.path.dirname(os.path.realpath(sys.argv[0])) + "\\res\\save.png", wx.BITMAP_TYPE_ANY), wx.NullBitmap, wx.ITEM_NORMAL, "Save results as csv file", "Save results as csv file")
        self.Bind(wx.EVT_MENU, self.onSaveFile, t_save)

        #t_tools = self.main_window_toolbar.AddLabelTool(wx.ID_ANY, _("Options"), wx.Bitmap(os.path.dirname(os.path.realpath(sys.argv[0])) + "\\res\\options.png", wx.BITMAP_TYPE_ANY), wx.NullBitmap, wx.ITEM_NORMAL, "Options", "Options")
        #self.Bind(wx.EVT_MENU, self.updateToolBar, t_tools)

        t_lbl  = self.main_window_toolbar.AddLabelTool(wx.ID_ANY, _("Enable label"), wx.Bitmap(os.path.dirname(os.path.realpath(sys.argv[0])) + "\\res\\labels.png", wx.BITMAP_TYPE_ANY), wx.NullBitmap, wx.ITEM_NORMAL, "Enable/Disable labels.", "Enable/Disable labels.")
        self.Bind(wx.EVT_MENU, self.toggleLabel, t_lbl)
        # Tool Bar end

        # Add drag and drop feature to main frame
        drop_target = FileDropTarget(None)
        self.SetDropTarget(drop_target)

        # Set properties and layout
        self.__set_properties()
        #self.__do_layout()

        self.Centre()
        self.Show(True)

        # Process any input files passed as arguments
        if len(sys.argv) > 1:
           self.context_switch()

        # end

    ###############################################
    ## Set properties of main window             ## 
    def __set_properties(self):
        # begin wxGlade: MyFrame.__set_properties
        self.SetTitle(_("Image Compare"))
        self.main_window_statusbar.SetStatusWidths([-1])
        # statusbar fields
        main_window_statusbar_fields = [_("Compare status")]
        for i in range(len(main_window_statusbar_fields)):
            self.main_window_statusbar.SetStatusText(main_window_statusbar_fields[i], i)
        self.main_window_toolbar.SetToolBitmapSize((16, 15))
        self.main_window_toolbar.SetToolPacking(20)
        self.main_window_toolbar.SetToolSeparation(20)
        self.main_window_toolbar.Realize()
        #self.compare_list.Hide()
        # end

    ###############################################
    ## Set layout of main window                 ## 
    def __do_layout(self):
        # begin wxGlade: MyFrame.__do_layout
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        #main_sizer.Add(self.compare_list, 1, wx.EXPAND, 0)
        self.SetSizer(main_sizer)
        main_sizer.Fit(self)
        self.Layout()
        # end wxGlade

    ###############################################
    ## Function for selcting file/directory      ## 
    ## window.                                   ##
    def updateToolBar(self, event):
       self.main_window_toolbar.Show(False)
       self.SendSizeEvent() 
       event.Skip()

    ###############################################
    ## Function for selcting file/directory      ## 
    ## window.                                   ##
    def open_diag(self, event):
        global udf_path
        self.diag = gen_dialog(None, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        self.diag.setUDFPath(udf_path)
        self.diag.InitUI()
        self.diag.ShowModal()
        (self.source_1, self.source_2, self.file_type) = self.diag.getSources()
        self.diag.Destroy()
        if(os.path.exists(self.source_1) and os.path.exists(self.source_2)):
          self.configEnv['SRC1']    = self.source_1
          self.configEnv['SRC2']    = self.source_2
          self.configEnv['SRCTYPE'] = self.file_type

          with open(udf_path,"w") as f:
              for key in self.configEnv:
                  print >>f, key + "=" + str(self.configEnv[key])
          ClearList(event)
          process_cmp_action(self.source_1, self.source_2, self.file_type)
        else:
          pass


    ###############################################
    ## Function for selcting file/directory      ## 
    ## window from windows rightclick context.   ##
    def context_switch(self):
        global udf_path      
        configParse = configFileParser()
        configEnv = configParse.get_cfg_hash(udf_path)
        self.diag = gen_dialog(None, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        self.diag.setUDFPath(udf_path)
        self.diag.InitUI()
        try:
            if len(sys.argv) == 2:
                self.diag.src1_txtCrtl.SetValue(sys.argv[1])
            
            if len(sys.argv) == 3:
                self.diag.src2_txtCrtl.SetValue(sys.argv[2])
        except IndexError:
            pass
        self.diag.ShowModal()
        (self.source_1, self.source_2, self.file_type) = self.diag.getSources()
        self.diag.Destroy()

        if(os.path.exists(self.source_1) and os.path.exists(self.source_2)):
            self.configEnv['SRC1']    = self.source_1
            self.configEnv['SRC2']    = self.source_2
            self.configEnv['SRCTYPE'] = self.file_type
            with open(udf_path,"w") as f:
                for key in self.configEnv:
                    print >>f, key + "=" + str(self.configEnv[key])
            ClearList(event)
            process_cmp_action(self.source_1, self.source_2, self.file_type)
        else:
            pass

    ###############################################
    ## Function to update status bar             ## 
    def update_statusbar(self, text="Compare status"):
        main_window_statusbar.SetStatusText(text, 0)


    ###############################################
    ## Generate Info window funtion              ##
    def OnAboutBox(self, e):
        
        description = """
ImageCompare is a tool for comparing images. Enables you analyze
 image differences in details.

------------------------------------------------------------------------------
Portions utilize Pillow 2.9.0 (Python Imaging Library), wx and wxPython.
------------------------------------------------------------------------------

Note: ImageCompare creates all images in RGB colour space by default. Some
images may look different (in terms of colour) when viewed outside ImageCompare
or with some other application. You can change image colour space from menu 
tools->image->ColourSpace CMYK
"""

        licence = """Copyright (C)"""

        info = wx.AboutDialogInfo()

        info.SetIcon(wx.Icon('icon.ico', wx.BITMAP_TYPE_ICO))
        info.SetName('ImageCompare')
        info.SetVersion('1.0')
        info.SetDescription(description)
        info.SetCopyright('(C) 2018 Varun Patial')
        info.SetWebSite('')
        info.SetLicence(licence)
        info.AddDeveloper('Varun Patial')
        info.AddDocWriter('Varun Patial')
        #info.AddTranslator('Varun Patial')

        wx.AboutBox(info)


    ###############################################
    ## Close funtion for exit event              ##
    def OnFileExit(self, e):
        self.Close(True)


    ###############################################
    ## Set colourspace                           ##
    def SetCS(self, e, cs_val):
        global compare_list
        if(cs_val == "Auto"):
            compare_list.updateCS("Auto")
            #self.img_menu.Check(self.m_image_cs_auto.GetId(), True)
            self.img_menu.Check(self.m_image_cs_rgb.GetId(), False)
            self.img_menu.Check(self.m_image_cs_cmyk.GetId(), False)
        if(cs_val == "RGB"):
            compare_list.updateCS("RGB")
            #self.img_menu.Check(self.m_image_cs_auto.GetId(), False)
            self.img_menu.Check(self.m_image_cs_rgb.GetId(), True)
            self.img_menu.Check(self.m_image_cs_cmyk.GetId(), False)
        if(cs_val == "CMYK"):
            compare_list.updateCS("CMYK")
            #self.img_menu.Check(self.m_image_cs_auto.GetId(), False)
            self.img_menu.Check(self.m_image_cs_rgb.GetId(), False)
            self.img_menu.Check(self.m_image_cs_cmyk.GetId(), True)

    ###############################################
    ## toggle label flag                         ##
    def toggleLabel(self, e):
        if(self.m_lbl.GetItemLabel() == "Disable labels"):
            self.m_lbl.SetItemLabel("Enable labels")
            global compare_list
            compare_list.updateLabelFlag(0)
        else:
            self.m_lbl.SetItemLabel("Disable labels")
            compare_list.updateLabelFlag(1)

    ###############################################
    ## Create and show the Save FileDialog       ##
    def onSaveFile(self, event):
        global udf_path
        wildcard = "CSV file (*.csv)|*.csv|" \
                   "All files (*.*)|*.*"
 
        ## Default current working directory to USER HOME. ##
        workingDir = "%userprofile%"
        try:
            workingDir = self.configEnv['PWD']
        except:
            self.configEnv['PWD'] = "%userprofile%"
            workingDir = "%userprofile%"

        dlg = wx.FileDialog(
            self, message="Save file as ...", 
            defaultDir=workingDir, 
            defaultFile="", wildcard=wildcard, style=wx.SAVE
            )

        ## Write csv file with current data avaiable. ## 
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            h_file = open(path, "w")
            h_file.write("FILE,COMPARE RESULTS,DESCRIPTION,LEFT SOURCE,RIGHT SOURCE,\n")
            global compare_list
            ref_items = compare_list.list.getItemDataMaps()
            items = ref_items.items()
            for key, data in items:
              for token in data:
                h_file.write(token + ",")
              h_file.write("\n")
            h_file.close()
           
            ## Update the udf file with new current working directory. ## 
            workingDir, tmp = path.rsplit('\\',1)
            if self.configEnv['PWD'] != workingDir:
              self.configEnv['PWD'] = workingDir
              with open(udf_path,"w") as f:
                for key in self.configEnv:
                  print >>f, key + "=" + str(self.configEnv[key])

        dlg.Destroy()

    ###############################################
    ## Quit application on Esc or q              ##
    def OnKeyDown(self, event):
        """quit if user press q or Esc"""
        if event.GetKeyCode() == 27 or event.GetKeyCode() == ord('Q'): #27 is Esc
            self.Close(True)
        else:
            event.Skip()


###############################################
## Define File Drop Target class             ##
class FileDropTarget(wx.FileDropTarget):

   ## Initialize the Drop Target, passing in the Object Reference to ##
   ## indicate what should receive the dropped files                 ##
   def __init__(self, obj):
      global udf_path
      # Initialize the wxFileDropTarget Object
      wx.FileDropTarget.__init__(self)
      # Store the Object Reference for dropped files
      self.obj = obj

      self.configParse = configFileParser()
      self.configEnv   = self.configParse.get_cfg_hash(udf_path)

   ###############################################
   ## Function for performing on drop action.   ## 
   ## Only first two targets will be considered ##
   def OnDropFiles(self, x, y, filenames):
      global udf_path      
      configParse = configFileParser()
      configEnv = configParse.get_cfg_hash(udf_path)
      self.diag = gen_dialog(None, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
      self.diag.setUDFPath(udf_path)
      self.diag.InitUI()
      try:
          self.diag.src1_txtCrtl.SetValue(filenames[0])
          self.diag.src2_txtCrtl.SetValue(filenames[1])
      except IndexError:
          pass
      self.diag.ShowModal()
      (self.source_1, self.source_2, self.file_type) = self.diag.getSources()
      self.diag.Destroy()

      if(os.path.exists(self.source_1) and os.path.exists(self.source_2)):
          self.configEnv['SRC1']    = self.source_1
          self.configEnv['SRC2']    = self.source_2
          self.configEnv['SRCTYPE'] = self.file_type
          with open(udf_path,"w") as f:
              for key in self.configEnv:
                  print >>f, key + "=" + str(self.configEnv[key])
          ClearList(event)
          process_cmp_action(self.source_1, self.source_2, self.file_type)
      else:
          pass


###############################################
## Clear contents of list.                   ##
def ClearList(event):
    try: 
        ## Send "CLEAR" flag for global reset ##
        compare_list.ClearAll("CLEAR")
    except AttributeError:
        print "Clear Failed"
        pass



###############################################
## Compute union of two file sets and call   ##
## compare_files to start comparison         ##
def process_cmp_action(source1, source2, file_type):
    global sbar_status
    global tiff_diff_path
    determinate = 1

    if os.path.isfile(source1):
        src1_file_list = [source1]
    else:
        src1_file_list = glob.glob(os.path.join(source1,file_type))

    if os.path.isfile(source2):
        src2_file_list = [source2]
    else:
        src2_file_list = glob.glob(os.path.join(source2,file_type))

    ## If both directories are empty, just ignore and return. ##
    if len(src1_file_list) == 0 and len(src2_file_list) == 0:
        return
    else:
        tmpfiles = glob.glob(tiff_diff_path + '\\*')
        for f in tmpfiles:
            try:
              os.remove(f)
            except:
              selectdialog = wx.MessageDialog(sys.exc_info()[0], "Error", wx.OK)
              selectdialog.ShowModal() 
              selectdialog.Destroy()
              

    indx = 0
    for file in src1_file_list:
        path, file = os.path.split(file)
        src1_file_list[indx] = file
        indx += 1

    indx = 0
    for file in src2_file_list:
        path, file = os.path.split(file)
        src2_file_list[indx] = file
        indx += 1


    ## Calculate union of files in given directories. ##
    general_cmp_list = set(src1_file_list) | set(src2_file_list)
    max = len(general_cmp_list)

    ## Set source information with list control
    compare_list.SetSource(source1, source2)

    if(determinate == 1):
        dlg = wx.ProgressDialog("Comparing files...",
                                "Please wait..",
                                maximum = max,
                                parent=None,
                                style = wx.PD_CAN_ABORT
                                | wx.PD_AUTO_HIDE
                                #| wx.PD_APP_MODAL
                                | wx.PD_ELAPSED_TIME
                                | wx.PD_ESTIMATED_TIME
                                | wx.PD_REMAINING_TIME
                               )
    dlg.SetSize((280,180))

    if os.path.isfile(source1) and os.path.isfile(source2):
        thd = threading.Thread(target=chop_file, args=(source1, source2, dlg,))
        thd.start()
    else: 
        thd = threading.Thread(target=chop_files, args=(general_cmp_list, source1, source2, dlg,))
        thd.start()

    return

###############################################
## Compare files using PIL ImageChops module ##
## and update entries in list control and    ##
## progressbar                               ##
def chop_file(source1, source2, dlg):
    keepGoing = True
    count = 0

    path1, fileName1 = os.path.split(source1)
    path2, fileName2 = os.path.split(source2)
    result = "Unknown response."
    description = "Not available."
    (keepGoing, skip) = dlg.Update(count, str(fileName1 + " - " + fileName2))
    fileSuffix1 = string.rsplit(fileName1, '.', 1)
    fileSuffix2 = string.rsplit(fileName2, '.', 1)
         
    im1 = Image.open(source1)
    im2 = Image.open(source2)

    diff = ImageChops.difference(im2, im1)
    del im1
    del im2

    if diff.getbbox() is None:
       result = "Images are same."
       description = "Maximum Delta is 0.0"
    else:
       mtx = (1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1, 0)

       if diff.mode == '1' or diff.mode == 'RGBA' or diff.mode == 'P':
          diff = diff.convert('L')
       else:
          diff = diff.convert('L', mtx)

       diff = ImageChops.invert(diff)
       diff = diff.point(lambda x: 0 if x<255 else 255, '1')

       mask = Image.new(diff.mode, diff.size, None)
       mask2 = Image.new(diff.mode, diff.size, None)
       mask.paste(diff);
       mask2.paste(diff);
       draw = ImageDraw.Draw(mask)
       draw2 = ImageDraw.Draw(mask2)
       diffData = diff.load()

       for y in xrange(diff.size[1]):
          for x in xrange(diff.size[0]):
             if diffData[x, y] == 0:
                draw.rectangle((x-41,y-41,x+41,y+41), fill='black')
                draw2.rectangle((x-40,y-40,x+40,y+40), fill='black')
             else:
                pass

       maskData = mask.load()
       for y in xrange(mask.size[1]):
          for x in xrange(mask.size[0]):
             if diffData[x, y] == 0:
                maskData[x, y] = 255

       maskdiff = ImageChops.difference(mask, mask2)
       maskdiff = ImageChops.invert(maskdiff)

       colors = diff.getcolors()

       if (colors[0][1] == 0 and colors[0][0] != 0):
          result = "Images are different."
          description = str(colors[0][0]) + " pixels differ"
       else:
          result = "Images are same."
          description = "Maximum Delta-E is 0.0"

       maskdiff.save(tiff_diff_path + "\\" + fileSuffix1[0] + "-" + fileSuffix2[0] + "-diff.bmp", 'bmp')

       del mask
       del mask2
       del maskdiff
       del draw
       del draw2
       del diffData
       del maskData
       del colors

    del diff
    compare_list.insertElement((fileSuffix1[0] + "-" + fileSuffix2[0], result, description, source1, source2))
    count += 1
    (keepGoing, skip) = dlg.Update(count, str(fileName1 + " - " + fileName2))
    if not keepGoing:
        return
 
    dlg.Destroy()
    return


###############################################
## Compare files using PIL ImageChops module ##
## and update entries in list control and    ##
## progressbar                               ##
def chop_files(general_cmp_list, source1, source2, dlg):
    keepGoing = True
    count = 0

    for file in general_cmp_list:
        path, fileName = os.path.split(file)
        result = "Unknown Error."
        description = "Not available."
        (keepGoing, skip) = dlg.Update(count, str(fileName))

        if not os.path.exists(os.path.join(source1,fileName)):
            result = "Right Only."
        elif not os.path.exists(os.path.join(source2,fileName)):
            result = "Left Only."
        else:
          fileSuffix = string.rsplit(fileName, '.', 1)
          im1 = Image.open(source1 + "\\" + fileName)
          im2 = Image.open(source2 + "\\" + fileName)

          diff = ImageChops.difference(im2, im1)
          del im1
          del im2

          if diff.getbbox() is None:
             result = "Images are same."
             description = "Maximum Delta-E is 0.0"
          else:
             mtx = (1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1, 0)

             if diff.mode == '1' or diff.mode == 'RGBA' or diff.mode == 'P':
                diff = diff.convert('L')
             else:
                diff = diff.convert('L', mtx)

             diff = ImageChops.invert(diff)
             diff = diff.point(lambda x: 0 if x<255 else 255, '1')

             mask = Image.new(diff.mode, diff.size, None)
             mask2 = Image.new(diff.mode, diff.size, None)
             mask.paste(diff);
             mask2.paste(diff);
             draw = ImageDraw.Draw(mask)
             draw2 = ImageDraw.Draw(mask2)
             diffData = diff.load()

             for y in xrange(diff.size[1]):
                for x in xrange(diff.size[0]):
                   if diffData[x, y] == 0:
                      draw.rectangle((x-41,y-41,x+41,y+41), fill='black')
                      draw2.rectangle((x-40,y-40,x+40,y+40), fill='black')

             maskData = mask.load()
             for y in xrange(mask.size[1]):
                for x in xrange(mask.size[0]):
                   if diffData[x, y] == 0:
                      maskData[x, y] = 255

             maskdiff = ImageChops.difference(mask, mask2)
             maskdiff = ImageChops.invert(maskdiff)
             if maskdiff.mode == 'L':
                maskdiff = maskdiff.convert('1')

             colors = diff.getcolors()

             if (colors[0][1] == 0 and colors[0][0] != 0):
                result = "Images are different."
                description = str(colors[0][0]) + " pixels differ"
             else:
                result = "Images are same."
                description = "Maximum Delta-E is 0.0"

             maskdiff.save(tiff_diff_path + "\\" + fileSuffix[0] + "-diff.bmp", 'bmp')
             del mask
             del mask2
             del maskdiff
             del draw
             del draw2
             del diffData
             del maskData
             del colors

        del diff
        gc.collect()
        (keepGoing, skip) = dlg.Update(count, str(fileName))
        compare_list.insertElement((file, result, description, source1, source2))
        count += 1
        if not keepGoing:
            break
 
    dlg.Destroy() 
    return


# end of class MyFrame
if __name__ == "__main__":
    gettext.install("app") # replace with the appropriate catalog name

    app = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    main_frame = MainFrame(None, -1, "")
    app.SetTopWindow(main_frame)
    main_frame.Show()
    app.MainLoop()
