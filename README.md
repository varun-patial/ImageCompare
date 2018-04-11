# ImageCompare
A tool that enables you to compare two images side by side. It highlights the area where there is a difference. It also comes with a feature called 'Looking Glass' that helps you select and compare only those areas where there is a difference. 

## Notes ##
You'll need python 2.7 to run it. The code has been tested on windows only.
Additional python modules: wx, PIL, distutils, py2exe

## How to run and use? ##
Run ImageCompare.py with python 2.7. The user interface is very simple. Currently it has only two options, open files to compare and save results of comparison in csv. You can also drag and drop two files that you want to compare. Batch of images can also be comapred by placing the two set on inputs in two different directories and open (or drag drop) those directories in ImageCompare. The result is dispayed in list form. If there is no difference in two images then that entry will be highlighted with green else yellow. To analyse the difference you can right click on an entry in this list select an option you want to exercise for analysing the difference. It can stack left image, right image and difference so you can analyse where images are different. If you want to closely examine the difference, exercise the 'looking glass' option. It'll open a new dialog with just bitmap of difference between two images. Here you can select an area which you want to examine and it'll stack those portions from left image, right image and difference. You can also zoom in and out in looking glass window using mouse scroll button.
