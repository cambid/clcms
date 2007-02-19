#!/usr/bin/env python

#
# This script will create clcms compatible gallery pages for the current directory
#
# The images in the current directory must be of the form:
# <nr>.<title>.<extension>
#

# Prerequisites: ImageMagick (for the convert tool)
# TODO: implement this with pixbuf?

# 
# The default input directory is galleries,
# Every subdir of that should be a directory with images
# the output will be put in out/
#

# for now, most values are default only, command line options are in the TODO

import os
from os.path import join, getsize
import stat
import shutil
import re
import commands

in_dir = "galleries"
out_dir = "out"
root_dir = os.getcwd()

thumbnail_size = "64x64"

image_file_p = re.compile("([0-9]+)\.(.*)\.([a-zA-Z]+)")

if in_dir[0] != "/":
	in_dir = root_dir + os.sep + in_dir
if out_dir[0] != "/":
	out_dir = root_dir + os.sep + out_dir

if not os.path.isdir(in_dir):
	print "No such directory: " + in_dir
	sys.exit(1)


if not os.path.isdir(out_dir):
	os.mkdir(out_dir)

os.chdir(in_dir)

gallery_names = []

dir_files = os.listdir(".")

top_page_lines = []
cur_gallery_lines = []

for d in dir_files:
	if d != "." and d != ".." and os.path.isdir(d):
		print "Gallery: " + d
		
		cur_output_dir = out_dir + os.sep + d
		if not os.path.isdir(cur_output_dir):
			os.mkdir(cur_output_dir)
		
		os.chdir(d)
		
		image_files = os.listdir(".")
		
		cur_gallery_lines = []

		for i in image_files:
			# TODO copy every .page to out/<Gallery>
			
			
			image_file_m = image_file_p.match(i)
			if image_file_m:
				# Copy image, and create thumbnail
				# escape spaces:

				output_file = cur_output_dir + os.sep + i
				cur_file_name = output_file.replace(" ", "\\ ")
				cur_file_name = cur_file_name.replace("&", "\\&")
				thumbnail_file = image_file_m.group(1) + "." + image_file_m.group(2) + "_small." + image_file_m.group(3)
				thumbnail_abs = cur_output_dir + os.sep + thumbnail_file
				cur_thumbnail_name = thumbnail_abs.replace(" ", "\\ ")
				cur_thumbnail_name = cur_thumbnail_name.replace("&", "\\&")
				
				shutil.copy2(i, cur_output_dir)
				
				(result, output) = commands.getstatusoutput("convert -scale " + thumbnail_size + " " + cur_file_name + " " + cur_thumbnail_name)

				if result != 0:
					print "convert -scale " + thumbnail_size + " " + output_file + " " + thumbnail_abs
					print "Error: "+str(result)
					print "Output: "+output
					print ""
#				cur_gallery_lines.append("[[Image:"+thumbnail_file+"|"+image_file_m.group(2)+"]")
				cur_gallery_lines.append("[[" + i + "][[[Image:"+thumbnail_file+"|"+image_file_m.group(2)+"]]]]")

		o_file = open(cur_output_dir + os.sep + "gallery.page", "w")
		for l in cur_gallery_lines:
			o_file.write(l + "\n")
		o_file.close
