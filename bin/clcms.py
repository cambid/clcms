#!/usr/bin/python

import os
import stat
import shutil
import time
import re

#
# Wiki style parser
#

# VERY simple parser for wiki style input
# takes a list of lines in wiki style
# returns a list of lines in HTML
# TODO: make this a general parser (i'd like it to work a lot better
# than for instance Twiki...)
def escape_url(url):
    url = url.replace(' ', '%20')
    return url

def wiki_to_html(wiki_lines):
    html_lines = []
    
    in_p = False
    cur_bullet_depth = 0;
    for line in wiki_lines:
        line = line.rstrip('\n\r\t ')
        # bold
        if line == "":
            if not in_p:
                html_lines.append("<p>\n")
            in_p = True
        if line[:1] == "*" and line[-1:] == "*":
            if (in_p):
                html_lines.append("</p>\n")
            while cur_bullet_depth > 0:
                html_lines.append("</ul>\n")
                cur_bullet_depth -= 1
            html_lines.append(" <b>" + line[1:-1] + "</b> \n")
        elif line[:1] == "_" and line[-1:] == "_":
            if (in_p):
                html_lines.append("</p>\n")
            while cur_bullet_depth > 0:
                html_lines.append("</ul>\n")
                cur_bullet_depth -= 1
            html_lines.append(" <i>" + line[1:-1] + "</i> \n")
        elif line[:1] == "=" and line[-1:] == "=":
            if (in_p):
                html_lines.append("</p>\n")
            while cur_bullet_depth > 0:
                html_lines.append("</ul>\n")
                cur_bullet_depth -= 1
            html_lines.append(" <pre>" + line[1:-1] + "</pre> \n")
        elif line[:4] == "   *":
            if (in_p):
                html_lines.append("</p>\n")
            while cur_bullet_depth < 1:
                html_lines.append("<ul>\n")
                cur_bullet_depth += 1
            html_lines.append("<li>" + line[4:] + "</li>\n")
        elif line[:3] == "---":
            if (in_p):
                html_lines.append("</p>\n")
            while cur_bullet_depth > 0:
                html_lines.append("</ul>\n")
                cur_bullet_depth -= 1
            i = 3
            while line[i] == "+":
                i += 1
            if (i > 3):
                html_lines.append("<h" + str(i-3) + ">" + line[i:] + "</h" + str(i-3) +  ">\n")
            else:
                html_lines.append(line)
        else:
            if (in_p):
                html_lines.append("</p>\n")
            while cur_bullet_depth > 0:
                html_lines.append("</ul>\n")
                cur_bullet_depth -= 1
            html_lines.append(line + " ")
    
    lines = html_lines
    html_lines = []
    
    # replace links and image refs
    #simple_link_p = re.compile('[^\"]http://.*')
    adv_link_p = re.compile('\[\[(.*)\]\[(.*)\]\]')
    img_p = re.compile('\{\{(.*)\}\{(.*)\}\}')
    for line in lines:
        adv_m = adv_link_p.search(line)
        #simple_m = simple_link_p.search(line)
        if adv_m:
            line = line[:adv_m.start()] + "<a href=\"" + escape_url(line[adv_m.start(1):adv_m.end(1)]) + "\">" + line[adv_m.start(2):adv_m.end(2)] + "</a>" + line[adv_m.end():]
        #elif simple_m:
        #    line = line[:simple_m.start()] + "<a href=\"" + line[simple_m.start():simple_m.end()] + "\">" + line[simple_m.start():simple_m.end()] + "</a>"

        img_m = img_p.search(line)
        if img_m:
            line = line[:img_m.start()] + "<img src=\"" + escape_url(line[img_m.start(1):img_m.end(1)]) + "\" alt=\"" + line[img_m.start(2):img_m.end(2)] + "\" />" + line[img_m.end():]
        html_lines.append(line)
    
    while cur_bullet_depth > 0:
        html_lines.append("</ul>")
        cur_bullet_depth -= 1


    #print html_lines
    return html_lines

#
# Option handling
#

def add_option(options, option):
	# todo: sort uniques?
	options.insert(0, option.replace('\n', ''))
	return options

def add_options(options, optionsa):
	for o in optionsa:
		options = add_option(options, o)
	return options

def get_option(options, option_name):
	p = re.compile("^\\s*" + option_name + "\\s*=\\s*");
	for o in options:
		m = p.match(o)
		if m:
			return o[m.end():]
	return ""
	
def get_options(options, option_name):
	p = re.compile("^\\s*" + option_name + "\\s*=\\s*");
	for o in options:
		m = p.match(o)
		if m:
			return o[m.end():].split(',')
	return []

# defaults
options = []
options = add_option(options, "root_dir = .")
options = add_option(options, "in_dir = in")
options = add_option(options, "out_dir = out")
options = add_option(options, "style_sheet = " + get_option(options, "root_dir") + "/default.css")
options = add_option(options, "header_files = header.inc")
options = add_option(options, "footer_files = footer.inc")
options = add_option(options, "favicon = " + get_option(options, "root_dir") + "/favicon.ico")
options = add_option(options, "content_dir = .")
options = add_option(options, "resource_dir = .")

# these files will be ignored when walking directories
# (these are read as regular expressions)
ignore_masks = [ "\\.\\\\*", ".gif$", ".png$", ".setup$" ]

#
# Utility functions
#

# if filter contain any re's, only lines matching any of them are
# added. If filter is empty, all lines are added
def append_file_lines(lines, file, filters = []):
    f_lines = open(file, "r")
    for l in f_lines:
        if filters == []:
                lines.append(l)
        else:
                for filter in filters:
                        p = re.compile(filter)
                        m = p.search(l)
                        if m:
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

# items must be of the form [indexnr, timestamp, name]
def sort_dir_files(a, b):
    try:
      if a[0] > b[0]:
        return 1
      elif a[0] < b[0]:
        return -1
      else:
        # sort timestamps in reverse order
        if a[1] > b[1]:
          return -1
        elif a[1] < b[1]:
          return 1
        else:
          if a[2] > b[2]:
            return 1
          elif a[2] < b[2]:
            return -1
          else:
            return 0
    except e:
      print e
      return 0

# returns a list of filenames in the directory,
# excluding all re matches from ignore_masks
# sorted by extension, then by last modified date
def get_dir_files(dir, ignore_masks, invert = False):
    dirfiles = []
    if os.path.isdir(dir):
    	orig_path = os.getcwd()
        os.chdir(dir)
        files = os.listdir(".")
        #files = map( lambda f: (os.stat(f)[stat.ST_MTIME], file_extension(f), f), files )
        files = map( lambda f: (file_extension(f, "ZZZ"), os.stat(f)[stat.ST_MTIME], f), files )
        #print files
        files.sort(sort_dir_files)
        for fs in files:
            f = fs[2]
            matches = False
            for ignore_mask in ignore_masks:
                file_p = re.compile(ignore_mask)
                file_m = file_p.match(f)
                if file_m:
                    matches = True
	    if matches and invert:
	        dirfiles.append(f)
	    elif not matches and not invert:
	    	dirfiles.append(f)
        os.chdir(orig_path)
    return dirfiles

def read_dir_options(options, dir):
	for f in get_dir_files(".", [ ".*\\.setup" ], True):
		#print "DIR: " + dir + " FILE: "+f
		options = add_options(options, append_file_lines([], f, ['^\s*[^#].+\s*=\s*.*\s*' ]))
	return options
	
#    for l in lines:
#        l_p = re.compile("_MENU_")
#        l_m = l_p.match(l)
#        if l_m:
#            lines.append(create_menu(

# generate the menu with the given directory as its base
# returns a list of html lines
def create_menu(base_dir, options):
    ignore_masks.append('.*\.nm.*')
    menu_lines = []
    append_file_lines(menu_lines, get_option(options, "root_dir") + "/menu_start.inc")
    first = True;
    for file in get_dir_files(base_dir, ignore_masks):
        #print "FILE: "+file
        if not first:
            append_file_lines(menu_lines, get_option(options, "root_dir") + "/menu_item.inc")
        else:
            first = False
        menu_lines.append("<a href=\"" + file + ".html\">" + file_base_name(file) + "</a>")
    append_file_lines(menu_lines, get_option(options, "root_dir") + "/menu_end.inc")
    return menu_lines


def create_page(in_dir, page_dir, output_dir, options, dir_depth):
    print "Creating page: "+in_dir+" <> "+page_dir
    output_file_name = page_dir + ".html"
    
    lines = []
    for f in get_options(options, "header_files"):
        append_file_lines(lines, f)

#    for l in create_menu(in_dir):
#        lines.append(l)

    orig_path = os.getcwd()
    os.chdir(in_dir)
    pagefiles = get_dir_files(page_dir, ignore_masks)
    os.chdir(orig_path)
    
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
        if os.path.isdir(in_dir+"/"+page_dir+"/"+pf):
            if not os.path.isdir(output_dir + "/" + page_dir):
                os.mkdir(output_dir + "/" + page_dir)
            create_page(in_dir, page_dir+"/"+pf, output_dir+"/"+page_dir, options, dir_depth+1)
        else:
            if not first:
                lines.append("<hr noshade=\"noshade\" size=\"3\" width=\"60%\" align=\"left\" />\n")
            else:
                first = False
            lines.append("<p>\n")
            lines.append("<a name=\"" + pf + " id=\"" + pf + "></a>\n")
            lines.append("<h3>" + file_base_name(pf) + "</h3>\n")
            #append_file_lines(lines, in_dir + "/" + page_dir +    "/" + pf)
            wikilines = append_file_lines([], in_dir + "/" + page_dir +    "/" + pf)
            lines.extend(wiki_to_html(wikilines))
            lines.append("</p>\n")

    lines.append("</div>\n")
    
    for f in get_options(options, "footer_files"):
        append_file_lines(lines, f)
    
    #lines = replace_macros(lines)
    # TODO: Macro
    lines2 = []
    for l in lines:
        l_p = re.compile("_MENU_")
        l_m = l_p.search(l)
        if l_m:
            for ml in create_menu(in_dir, options):
                lines2.append(ml)
        else:
            lines2.append(l)

    lines = lines2
    lines2 = []
    for l in lines:
        l_p = re.compile("_STYLE_SHEET_")
        l_m = l_p.search(l)
        if l_m:
            i = 0
            style_sheet_loc = ""
            while i < dir_depth:
                style_sheet_loc += "../"
                i += 1
            style_sheet_loc += get_option(options, "style_sheet")
            lines2.append(l[:l_m.start()] + style_sheet_loc + l[l_m.end():])
        else:
            lines2.append(l)

#    lines2 = wiki_to_html(lines2)

    of = open(out_dir + "/" + output_file_name, "w")
    for l in lines2:
        of.write(l)
    of.close()

options = read_dir_options(options, ".")

in_dir = get_option(options, "in_dir")
out_dir = get_option(options, "out_dir")
for f in get_dir_files(in_dir, ignore_masks):
    create_page(in_dir, f, out_dir, options, 0)
    shutil.copy(get_option(options, "style_sheet"), out_dir)
    shutil.copy(get_option(options, "favicon"), out_dir)



