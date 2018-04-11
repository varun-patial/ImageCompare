#!/usr/bin/python

# dialog_window.py
#----------------------------------------------------------------------------
# Name:         dialog_window.py
# Purpose:      Class to generate file open/save dialogues.
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
import gettext
from cfgParse import configFileParser

## Declare GUI Constants ##
MENU_FILE_EXIT = wx.NewId()
DRAG_SOURCE    = wx.NewId()


###############################################
## Class for generating dialogue boxes       ##
class gen_dialog(wx.Dialog):
    
    def __init__(self, *args, **kw):
        super(gen_dialog, self).__init__(*args, **kw)
        self.SetSize((600, 200))
        self.SetTitle("Select files/folders to compare.")
        self.udf_path = "cfg\\default.udf"
        
        
    def InitUI(self):
        self.configParse = configFileParser()
        self.configEnv = self.configParse.get_cfg_hash(self.udf_path)
        pnl = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        sb = wx.StaticBox(pnl, label='Source')
        sbs = wx.StaticBoxSizer(sb, orient=wx.VERTICAL)     

        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        hbox1.Add(wx.StaticText(pnl, -1, "Source 1: ", style=wx.ALIGN_CENTRE))
  
        self.src1_txtCrtl = wx.TextCtrl(pnl, size=(400,-1))
        try:
            self.src1_txtCrtl.SetValue(self.configEnv['SRC1'])
        except KeyError:
            pass
        drop_target1 = FileDropTarget(self.src1_txtCrtl) 
        self.src1_txtCrtl.SetDropTarget(drop_target1)
        hbox1.Add(self.src1_txtCrtl, flag=wx.EXPAND, border=5)

        src1_bw_Btn = wx.Button(pnl, label='Browse')
        src1_bw_Btn.Bind(wx.EVT_BUTTON, lambda event: self.openFile(event, self.src1_txtCrtl))
        hbox1.Add(src1_bw_Btn)
        

        hbox2 = wx.BoxSizer(wx.HORIZONTAL)        
        hbox2.Add(wx.StaticText(pnl, -1, "Source 2: ", style=wx.ALIGN_CENTRE))
 
        self.src2_txtCrtl = wx.TextCtrl(pnl, size=(400,-1))
        try:
            self.src2_txtCrtl.SetValue(self.configEnv['SRC2'])
        except KeyError:
            pass
        drop_target2 = FileDropTarget(self.src2_txtCrtl)
        self.src2_txtCrtl.SetDropTarget(drop_target2)     
        hbox2.Add(self.src2_txtCrtl, flag=wx.EXPAND, border=5)

        src2_bw_Btn = wx.Button(pnl, label='Browse')
        src2_bw_Btn.Bind(wx.EVT_BUTTON, lambda event: self.openFile(event, self.src2_txtCrtl))
        hbox2.Add(src2_bw_Btn)


        hbox3 = wx.BoxSizer(wx.HORIZONTAL)        
        hbox3.Add(wx.StaticText(pnl, -1, "File Type: ", style=wx.ALIGN_CENTRE))
        selectionChoices=['*.*', '*.tif', '*.tif*', '*.tiff']  
        self.cmbBox = wx.ComboBox(pnl, choices=selectionChoices, size=(400,-1))
        selection = 2
        try:
            selection = selectionChoices.index(self.configEnv['SRCTYPE'])
        except:
            selection = 2
        self.cmbBox.SetSelection(selection)      
        hbox3.Add(self.cmbBox, flag=wx.EXPAND, border=5)

        sbs.Add(hbox1)
        sbs.Add(hbox2)
        sbs.Add(hbox3)
        
        pnl.SetSizer(sbs)
       
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        okButton = wx.Button(self, label='Ok')
        closeButton = wx.Button(self, wx.ID_CLOSE, label='Close')
        hbox2.Add(okButton)
        hbox2.Add(closeButton, flag=wx.LEFT, border=5)

        vbox.Add(pnl, proportion=1, 
            flag=wx.ALL|wx.EXPAND, border=5)
        vbox.Add(hbox2, 
            flag=wx.ALIGN_CENTER|wx.TOP|wx.BOTTOM, border=10)

        self.SetSizer(vbox)
        
        okButton.Bind(wx.EVT_BUTTON, self.OnOk)
        closeButton.Bind(wx.EVT_BUTTON, self.OnClose)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

        okButton.SetFocus()
 
    ###############################################
    ## Method to handle open file call.          ##
    def openFile(self, e, txtCtrl):
        dlg = wx.DirDialog(self, "Choose a directory", os.getcwd())
        if dlg.ShowModal() == wx.ID_OK :
            path = dlg.GetPath()
            txtCtrl.SetValue(path)
        dlg.Destroy()       

    ###############################################
    ## Method to handle close call.              ##        
    def OnClose(self, e):
        self.src1_txtCrtl.SetValue("")
        self.src2_txtCrtl.SetValue("")
        self.Destroy()

    ###############################################
    ## Process OK button event                   ## 
    def OnOk(self, e):
        if os.path.exists(self.src1_txtCrtl.GetValue()) == False:
          selectdialog = wx.MessageDialog(self, self.src1_txtCrtl.GetValue() + " : No such file or directory.", "Error", wx.OK)
          selectdialog.ShowModal() 
          selectdialog.Destroy()
          return

        if os.path.exists(self.src2_txtCrtl.GetValue()) == False:
          selectdialog = wx.MessageDialog(self, self.src2_txtCrtl.GetValue() + " : No such file or directory.", "Error", wx.OK)
          selectdialog.ShowModal() 
          selectdialog.Destroy()
          return

        self.Destroy()

    ###############################################
    ## return field values                       ##
    def getSources(self):
        return (self.src1_txtCrtl.GetValue(), self.src2_txtCrtl.GetValue(), self.cmbBox.GetValue())

    ###############################################
    ## return field values                       ##
    def setUDFPath(self, path):
        self.udf_path = path


###############################################
## Define File Drop Target class             ##
class FileDropTarget(wx.FileDropTarget):
   ## This object implements Drop Target functionality for Files ##
   def __init__(self, obj):
      ## Initialize the Drop Target, passing in the Object Reference to  ##
      ##    indicate what should receive the dropped files               ##

      # Initialize the wxFileDropTarget Object
      wx.FileDropTarget.__init__(self)

      # Store the Object Reference for dropped files
      self.obj = obj

   ##  Implement File Drop ##
   def OnDropFiles(self, x, y, filenames):
      self.obj.Clear()
      self.obj.SetInsertionPointEnd()

      # append a list of the file names dropped
      for file in filenames:
         self.obj.WriteText(file)