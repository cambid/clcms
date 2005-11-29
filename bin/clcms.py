#!/usr/bin/python

import os
import stat
import shutil
import time
import re

# default values
root_dir = 	1
in_dir = 	2
out_dir = 	3
style_sheet = 	4
header_files = 	5
footer_files = 	6
favicon = 	7
content_dir = 	8
resource_dir = 	9

settings = [ "", "", "", "", "", "", "", "", "", "", "", "" ]
settings[root_dir] = "."
settings[in_dir] = root_dir + "/in"
settings[out_dir] = root_dir + "/out"
settings[style_sheet] = root_dir + "/default.css"
settings[header_files] = [root_dir + "/header.inc" ]
settings[footer_files] = [root_dir + "/footer.inc" ]
settings[favicon] = root_dir + "/favicon.ico"
settings[content_dir] = "."
settings[resource_dir] = "."

# these files will be ignored when walking directories
# (these are read as regular expressions)
ignore_masks = [ "\\.\\\\*" ]

def append_file_lines(lines, file):
    f_lines = open(file, "r")
    for l in f_lines:
        lines.append(l)
    return lines

# returns the filename without the extension
def file_base_name(filename):
    p = re.compile("\\..+$")
    m = p.search(filename)
    if m:
        return filename[:m.start()]
    else:
        return filename

# returns the filename extension (without the .)
# optional value default is returned if there is no extension
def file_extension(filename, default = ""):
    p = re.compile("\\..+$")
    m = p.search(filename)
    if m:
        return filename[m.start() + 1:]
    else:
        return default

# returns a list of filenames in the directory,
# excluding all re matches from ignore_masks
# sorted by extension, then by last modified date
def get_dir_files(dir, ignore_masks):
    dirfiles = []
    if os.path.isdir(dir):
        os.chdir(dir)
        files = os.listdir(".")
        #files = map( lambda f: (os.stat(f)[stat.ST_MTIME], file_extension(f), f), files )
        files = map( lambda f: (file_extension(f, "ZZZ"), os.stat(f)[stat.ST_MTIME], f), files )
        #print files
        files.sort()
        #files.reverse()
        for fs in files:
            f = fs[2]
            for ignore_mask in ignore_masks:
                file_p = re.compile(ignore_mask)
                file_m = file_p.match(f)
                if not file_m:
                    dirfiles.append(f)
    os.chdir("..")
    return dirfiles

#    for l in lines:
#        l_p = re.compile("_MENU_")
#        l_m = l_p.match(l)
#        if l_m:
#            lines.append(create_menu(

# generate the menu with the given directory as its base
# returns a list of html lines
def create_menu(base_dir):
    menu_lines = []
    append_file_lines(menu_lines, root_dir + "/menu_start.inc")
    first = True;
    for file in get_dir_files(base_dir, ignore_masks):
        if not first:
            append_file_lines(menu_lines, root_dir + "/menu_item.inc")
        else:
            first = False
        menu_lines.append("<a href=\"" + file + ".html\">" + file_base_name(file) + "</a>")
    append_file_lines(menu_lines, root_dir + "/menu_end.inc")
    return menu_lines


def create_page(in_dir, page_dir, output_dir):
    output_file_name = page_dir + ".html"
    
    lines = []
    for f in header_files:
        append_file_lines(lines, f)

#    for l in create_menu(in_dir):
#        lines.append(l)
        
    os.chdir(in_dir)
    pagefiles = get_dir_files(page_dir, ignore_masks)
    os.chdir("..")
    
    if len(pagefiles) > 1:
        lines.append("<div id=\"submenu\">\n")
        first = True
        for pf in pagefiles:
            if not first:
                lines.append("<hr noshade=\"noshade\" size=\"1\" width=\"80%\" align=\"left\" />\n")
            else:
                first = False
            lines.append("<a href=\"" + output_file_name + "#" + pf + "\">" + file_base_name(pf) + "</a>\n")
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
        lines.append("<h3>" + file_base_name(pf) + "</h3>\n")
        append_file_lines(lines, in_dir + "/" + page_dir +    "/" + pf)
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


for f in get_dir_files(in_dir, ignore_masks):
    create_page(in_dir, f, out_dir)
    shutil.copy(style_sheet, out_dir)
    shutil.copy(favicon, out_dir)



