#!/usr/bin/python

import os
import stat
import shutil
import time
import re

# default values
root_dir = "."
in_dir = root_dir + "/in"
out_dir = root_dir + "/out"
style_sheet = root_dir + "/default.css"
header_files = [root_dir + "/header.inc" ]
footer_files = [root_dir + "/footer.inc" ]
favicon = root_dir + "/favicon.ico"
content_dir = "."
resource_dir = "."

# these files will be ignored when walking directories
# (these are read as regular expressions)
ignore_masks = [ "\\.\\\\*" ]

def append_file_lines(lines, file):
  f_lines = open(file, "r")
  for l in f_lines:
    lines.append(l)
  return lines


#  for l in lines:
#    l_p = re.compile("_MENU_")
#    l_m = l_p.match(l)
#    if l_m:
#      lines.append(create_menu(

# generate the menu with the given directory as its base
# returns a list of html lines
def create_menu(base_dir):
  menu_lines = []
  append_file_lines(menu_lines, root_dir + "/menu_start.inc")
  first = True;
  if os.path.isdir(base_dir):
    for file in os.listdir(base_dir):
      for ignore_mask in ignore_masks:
        file_p = re.compile(ignore_mask)
        file_m = file_p.match(file)
        if not file_m:
          if not first:
            append_file_lines(menu_lines, root_dir + "/menu_item.inc")
          else:
            first = False
          menu_lines.append("<a href=\"" + file + ".html\">" + file + "</a>")
  append_file_lines(menu_lines, root_dir + "/menu_end.inc")
  return menu_lines


def create_page(in_dir, page_dir, output_dir):
  output_file_name = page_dir + ".html"
  
  lines = []
  for f in header_files:
    append_file_lines(lines, f)

#  for l in create_menu(in_dir):
#    lines.append(l)
    
  pagefiles = []
  
  os.chdir(in_dir + "/" + page_dir)
  files = os.listdir(".")
  files = map( lambda f: (os.stat(f)[stat.ST_MTIME], f), files )
  files.sort()
  #files.reverse()
  for fs in files:
    f = fs[1]
    print fs
    for ignore_mask in ignore_masks:
      file_p = re.compile(ignore_mask)
      file_m = file_p.match(f)
      if not file_m:
        pagefiles.append(f)
  os.chdir("../..")
  
  if len(pagefiles) > 1:
    lines.append("<div id=\"submenu\">\n")
    first = True
    for pf in pagefiles:
      if not first:
        lines.append("<hr noshade=\"noshade\" size=\"1\" width=\"80%\" align=\"left\" />\n")
      else:
        first = False
      lines.append("<a href=\"" + output_file_name + "#" + pf + "\">" + pf + "</a>\n")
    lines.append("</div>\n")
  
  lines.append("<div id=\"content\">\n")

  first = True
  for pf in pagefiles:
    if not first:
      lines.append("<hr noshade=\"noshade\" size=\"3\" width=\"60%\" align=\"left\" />\n")
    else:
      first = False
    lines.append("<p>\n")
    lines.append("<a name=\"" + pf + " id=\"" + pf + "></a>\n")
    lines.append("<h3>" + pf + "</h3>\n")
    append_file_lines(lines, in_dir + "/" + page_dir +  "/" + pf)
    lines.append("</p>\n")

  lines.append("</div>\n")
  
  for f in footer_files:
    append_file_lines(lines, f)
  
  #lines = replace_macros(lines)
  lines2 = []
  for l in lines:
    l_p = re.compile("_MENU_")
    l_m = l_p.search(l)
    if l_m:
      for ml in create_menu(in_dir):
        lines2.append(ml)
    else:
      lines2.append(l)

  of = open(out_dir + "/" + output_file_name, "w")
  for l in lines2:
    of.write(l)
  of.close()


for f in os.listdir(in_dir):
  for ignore_mask in ignore_masks:
    file_p = re.compile(ignore_mask)
    file_m = file_p.match(f)
    if not file_m:
      create_page(in_dir, f, out_dir)
  # and copy some files
  shutil.copy(style_sheet, out_dir)
  shutil.copy(favicon, out_dir)



