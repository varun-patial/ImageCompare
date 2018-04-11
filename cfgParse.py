#!/usr/bin/python

# cfgParse.py
#----------------------------------------------------------------------------
# Name:         cfgParse.py
# Purpose:      Parse user configuration file and generate configuration
#               environment variables.
#
# Author:       Varun Patial
#
# Created:      08-Sep-2017
#
# Copyright:    Copyright (C) 2018 Varun Patial
# Licence:      MIT License
#----------------------------------------------------------------------------

import re
import string


# #############################################################################
# Parse config file and create key value pairs
# #############################################################################
class configFileParser():
    def __init__(self):
        pass
      

    ## Parse and return hash of config variables ##
    def get_cfg_hash(self,configFile):
        cfgEnv = {}
        cfgHandle = open(configFile)
        
        for line in cfgHandle:
            if re.match('\S', line) is None:
                continue

            line = re.sub('^\s+', '', line)
            line = re.sub('\s$', '', line)

            if re.match('^#', line) is None:
                tokenAry = re.split('=', line, 1)
                cfgEnv[tokenAry[0]] = tokenAry[1]

        return cfgEnv
