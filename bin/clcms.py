#!/usr/bin/env python

# Copyright (C) 2005  Jelte Jansen
#
# e-mail: Tjebbe@kanariepiet.com
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
# For the complete license, see the LICENSE file in this distribution

import os
from os.path import join, getsize
import stat
import shutil
import time
import re
import sys
import code
import traceback

version = "0.2"

no_macros = False

#
# Wiki style parser
#

# VERY simple parser for wiki style input
# takes a list of lines in wiki style
# returns a list of lines in HTML
# TODO: make this a general parser (i'd like it to work a lot better
# than for instance Twiki...)
def escape_url(url):
    url = url.replace(' ', '_')
    return url

def escape_html(line):
    line = line.replace('"', '\\"')
    return line.rstrip("\r\n\t")

def wiki_to_html_simple(line):
    line = line.rstrip("\n\r\t ")
    line = line.replace("<", "&lt;")
    line = line.replace(">", "&gt;")
    if line == "":
        return "<p></p>\n"
    if line[:1] == '*' and line[-1:] == '*':
        return "<b>" + line[1:-1] + "</b>\n"
    if line[:1] == '.' and line[-1:] == '.':
        return "<i>" + line[1:-1] + "</i>\n"
    if line[:1] == '=' and line[-1:] == '=':
        return "<pre>" + line[1:-1] + "</pre>\n"
    # replace links and image refs
    #simple_link_p = re.compile('[^\"]http://.*')
    adv_link_p = re.compile('\[\[(.*)\]\[(.*)\]\]')
    img_p = re.compile('\{\{(.*)\}\{(.*)\}\}')
    adv_m = adv_link_p.search(line)
    #simple_m = simple_link_p.search(line)
    if adv_m:
        line = line[:adv_m.start()] + "<a href=\"" + escape_url(line[adv_m.start(1):adv_m.end(1)]) + "\">" + line[adv_m.start(2):adv_m.end(2)] + "</a>" + line[adv_m.end():]
    #elif simple_m:
    #    line = line[:simple_m.start()] + "<a href=\"" + line[simple_m.start():simple_m.end()] + "\">" + line[simple_m.start():simple_m.end()] + "</a>"

    img_m = img_p.search(line)
    if img_m:
        line = line[:img_m.start()] + "<img src=\"" + escape_url(line[img_m.start(1):img_m.end(1)]) + "\" alt=\"" + line[img_m.start(2):img_m.end(2)] + "\" />" + line[img_m.end():]
    
    return line + "\n"

def wiki_to_html(wiki_lines):
    html_lines = []
    i = 0
    no_wiki = False
    whitespace_p = re.compile('^\s*\n$')
    while i < len(wiki_lines):
        line = wiki_lines[i]
        if no_wiki:
            if line[:14] == "_NO_WIKI_END_\n":
                no_wiki = False
            else:
                html_lines.append(line)
        else:
            if line[:10] == "_NO_WIKI_\n":
                no_wiki = True
            elif line[:3] == "---":
                j = 3
                while line[j] == "+":
                    j += 1
                if (j > 3):
                    html_lines.append("<h" + str(j-3) + ">" + wiki_to_html_simple(line[j:]) + "</h" + str(j-3) +  ">\n")
                else:
                    html_lines.append(wiki_to_html_simple(line))
            elif line[:5] == "   * ":
                html_lines.append("<ul>\n")
                html_lines.append("\t<li>\n")
                html_lines.append(wiki_to_html_simple(line[5:]))
                in_list1 = True
                while in_list1:
                    i += 1
                    if i < len(wiki_lines):
                        line = wiki_lines[i]
                        if line[:5] == "   * ":
                            html_lines.append("\t</li>\n")
                            html_lines.append("\t<li>\n")
			    html_lines.append(wiki_to_html_simple(line[5:]))
                        elif line[:8] == "      * ":
                            html_lines.append("<ul>\n")
                            html_lines.append("\t<li>\n")
                            html_lines.append(wiki_to_html_simple(line[8:]))
                            in_list2 = True
                            while in_list2:
                                i += 1
                                if i < len(wiki_lines):
                                    line = wiki_lines[i]
                                    if line[:8] == "      * ":
                                        html_lines.append("\t</li>\n")
                                        html_lines.append("\t<li>\n")
                                        html_lines.append(wiki_to_html_simple(line[8:]))
                                    #elif line[:8] == "      * ":
                                    elif line[:11] == "         * ":
                                        html_lines.append("<ul>\n")
                                        html_lines.append("\t<li>\n")
                                        html_lines.append(wiki_to_html_simple(line[11:]))
                                        in_list3 = True
                                        while in_list3:
                                            i += 1
                                            if i < len(wiki_lines):
                                                line = wiki_lines[i]
                                                if line[:11] == "         * ":
                                                    html_lines.append("\t</li>\n")
                                                    html_lines.append("\t<li>\n")
                                                    html_lines.append(wiki_to_html_simple(line[11:]))
                                                #elif line[:11] == "         * ":
 					        elif whitespace_p.match(line):
							html_lines.append("<br />\n")
                                                elif line[:11] == "           ":
							html_lines.append(wiki_to_html_simple(line[11:]))
                                                else:
                                                    html_lines.append("\t</li>\n")
                                                    html_lines.append("</ul>\n")
                                                    in_list3 = False
                                                    i -= 1
                                            else:
                                                html_lines.append("\t</li>\n")
                                                html_lines.append("</ul>\n")
                                                in_list3 = False
   				    elif whitespace_p.match(line):
					html_lines.append("<br />\n")
                                    elif line[:8] == "        ":
					html_lines.append(wiki_to_html_simple(line[8:]))
                                    else:
                                        html_lines.append("\t</li>\n")
                                        html_lines.append("</ul>\n")
                                        in_list2 = False
                                        i -= 1
                                else:
                                    html_lines.append("\t</li>\n")
                                    html_lines.append("</ul>\n")
                                    in_list2 = False
			elif whitespace_p.match(line):
                            	html_lines.append("<br />\n")
                        elif line[:5] == "     ":
                                html_lines.append(wiki_to_html_simple(line[5:]))
                        else:
                            html_lines.append("\t</li>\n")
                            html_lines.append("</ul>\n")
                            in_list1 = False
                            i -= 1
                    else:
                        html_lines.append("\t</li>\n")
                        html_lines.append("</ul>\n")
                        in_list1 = False
            else:
                html_lines.append(wiki_to_html_simple(line))
        i += 1
    return html_lines


#
# Macro handling
#

# The macro list is a list of lists of which the first object is the
# macro name (for instance "MENU" for the macro _MENU_) and the 
# second object is a source string that will be executed
# a macro function is supposed to return a string
# TODO: make correct html with header macros etc
macro_list = [
  ["MENU", "output = \"\"\nfor ml in create_menu(root_dir, in_dir, options, arguments[0], cur_dir_depth):\n\toutput += ml\n" ],
  ["SUBMENU", "output = \"\"\nfor ml in create_submenu(show_submenu, page_files, options):\n\toutput += ml\n" ],
  ["TITLE", "output = page_name\n" ],
  ["STYLESHEET", 'i = 0\noutput = ""\nwhile i < cur_dir_depth:\n\toutput += os.pardir + os.sep\n\ti += 1\noutput += get_option(options, "style_sheet")\n' ],
  ["DATE", "output = time.strftime(\"%Y-%m-%d\")\n" ],
  ["DATEFILE", "output = time.strftime(\"%Y-%m-%d\", time.gmtime(last_modified))\nprint\"datefile: \"+output\n" ],
  ["ITEM-SEPARATOR", " output = \"<hr noshade=\\\"noshade\\\" size=\\\"1\\\" width=\\\"60%\\\" align=\\\"left\\\" />\"" ],
  ["SUBMENU-ITEM-SEPARATOR", " output = \"<hr noshade=\\\"noshade\\\" size=\\\"1\\\" width=\\\"60%\\\" align=\\\"left\\\" />\"" ],
  ["header", "output = \"_MENU_1_\"\n" ],
  ["footer", "output = \"\"\n" ],
  ["menustart", "output = \"\"\n" ],
  ["menuend", "output = \"\"\n" ],
  ["menuitem1start", "output = \"\"\n" ],
  ["menuitem1end", "output = \"\"\n" ],
  ["menuitem2start", "output = \"\"\n" ],
  ["menuitem2end", "output = \"\"\n" ],
  ["menuitem3start", "output = \"\"\n" ],
  ["menuitem3end", "output = \"\"\n" ],
  ["menuitem4start", "output = \"\"\n" ],
  ["menuitem4end", "output = \"\"\n" ],
  ["menuitem5start", "output = \"\"\n" ],
  ["menuitem5end", "output = \"\"\n" ],
  ["DEBUG", "output = \"\"\nprint arguments[0]\n" ],
  ["DUMPMACROS", "for m in macro_list:\n\tprint m[0]\n\tprint m[1]\n\tprint \"\"\noutput=\"\"\n" ],
  ["FAKE", "output = \"\"\n" ]
]

#time.strftime("%Y-%m-%d", time.gmtime(last_modified))
#time.strftime("%Y-%m-%d")
def handle_macro(macro_name, macro_source, input_line, options, macro_list, page_name, root_dir, in_dir, cur_dir_depth, page_files, show_submenu, last_modified):
    result_line = input_line
    # TODO: surrounding characters disappear...
    macro_p = re.compile("(?:_"+macro_name+"_)(?:([a-zA-Z0-9_]+)_)?")
    macro_m = macro_p.search(input_line)
    if macro_m:
        # hmm can this be done in the original regexp?
        if macro_m.start() > 1 and macro_m.end() < len(input_line) and \
           input_line[macro_m.start() - 1] == '_' and \
           input_line[macro_m.end()] == '_':
             return result_line
        
        ip = code.InteractiveInterpreter()
        output = "<badmacro>"
#        print "Code:"
#        print macro_source
#        print "Macro: "+macro_name
        arg_string = macro_m.group(1)
        if arg_string == None:
            arguments = []
        else:
            arguments = macro_m.group(1).split('_')
#        print "number of arguments: ",
#        print len(arguments)
#        print "arguments: ",
#        print arguments
        # keep for error message
        orig_macro_source = macro_source
        # Hack to circumvent premature parser stoppage
        macro_lines = macro_source.split("\n")
        macro_source = "for zcxcvad in [\"vasdferqerqewr\"]:\n"
        for ml in macro_lines:
            macro_source += "\t" + ml + "\n"
        
        try:
            co = code.compile_command(macro_source)
        except SyntaxError, msg:
            print "Syntax error in macro: " + macro_name
            print "(Matching on: '" + macro_m.group() + "')"
            print "For page: "+page_name
            print "In directory: "+in_dir
            print "Input line: "+input_line,
            print "Error: ",
            print msg
            print "Maybe the macro expects an argument?"
            print "Macro code:"
            print orig_macro_source
            sys.exit(4)
        if co != None:
            try:
                exec co
            except IndexError, msg:
                print "Error parsing macro: "+macro_name
                print "(Matching on: '" + macro_m.group() + "')"
                print "For page: "+page_name
                print "In directory: "+in_dir
                print "Input line: "+input_line,
                print "Error: ",
                print msg
                print "Maybe the macro expects an argument?"
                print "Macro code:"
                print orig_macro_source
                sys.exit(2)
            if output == "<badmacro>":
                print "Warning: Bad macro: "+macro_name
                print "In line: "+input_line
                output = ""
            result_line = input_line[:macro_m.start()] + output + input_line[macro_m.end():]
        else:
            print "Warning: Bad macro: "+macro_name
        return result_line
    return result_line
    
#
# Check the input line for all macros in the given list
#
def handle_macros(macro_list, input_line, options, page_name, root_dir, in_dir, cur_dir_depth, page_files, show_submenu, last_modified):
    orig_input_line = input_line
    cur_line = input_line
    orig_line = ""
    i = 0
    while orig_line != cur_line:
        orig_line = cur_line
        for mo in macro_list:
            cur_line = handle_macro(mo[0], mo[1], cur_line, options, macro_list, page_name, root_dir, in_dir, cur_dir_depth, page_files, show_submenu, last_modified)
            if cur_line != orig_line:
                break
        i += 1
        if (i > 1000):
            print "Error, loop detected in macro. I have done 1000 macro expansions on the line:"
            print orig_input_line
            print "And it is still not done. Aborting. Your output may be incomplete."
            print "Last macro tried: "+mo[0]
            sys.exit(1)
    return cur_line

#
# Option handling (default options and those from .setup files)
#

def add_option(options, option):
	# todo: sort uniques?
	options.insert(0, option.replace('\n', ''))
	return options

def add_options(options, optionsa):
	for o in optionsa:
		options = add_option(options, o)
	return options

def have_option(options, option_name):
	p = re.compile("^\\s*" + option_name + "\\s*=\\s*");
	for o in options:
		m = p.match(o)
		if m:
			return True
        return False

def get_option(options, option_name):
	p = re.compile("^\\s*" + option_name + "\\s*=\\s*");
	for o in options:
		m = p.match(o)
		if m:
			return o[m.end():].rstrip("\n\r\t ")
	print "Error: get_option() called for unknown option: "+option_name
	print "Current directory: " + os.getcwd()
	(a,b,c) = sys.exc_info()
	raise NameError, "get_option() called for unknown option: " + option_name
	return ""
	
def get_options(options, option_name):
	p = re.compile("^\\s*" + option_name + "\\s*=\\s*");
	for o in options:
		m = p.match(o)
		if m:
                    result = o[m.end():].split(',')
                    if result != [ '' ]:
                        return result
                    else:
                        return []
	print "Error: get_options() called for unknown option: "+option_name
	print "Current directory: " + os.getcwd()
	(a,b,c) = sys.exc_info()
	raise NameError, "get_option() called for unknown option: " + option_name
	return ""

def get_option_dir(options, option_name):
	p = re.compile("^\\s*" + option_name + "\\s*=\\s*");
	d = ""
	for o in options:
		m = p.match(o)
		if m:
			d = o[m.end():].rstrip("\n\r\t ")
                        if d[:1] != os.sep:
                            d = os.getcwd()+os.sep+d
                        return d
        print "Error: unknown option name: " + option_name
	print "Current directory: " + os.getcwd()
	(a,b,c) = sys.exc_info()
	raise NameError, "get_option_dir() called for unknown option: " + option_name
	return ""
	

# default options
options = []
options = add_option(options, "root_dir = .")
options = add_option(options, "in_dir = in")
options = add_option(options, "out_dir = out")
options = add_option(options, "style_sheet = " + "default.css")
#options = add_option(options, "header_files = header.inc")
#options = add_option(options, "footer_files = footer.inc")
options = add_option(options, "resource_dir = .")
options = add_option(options, "show_menu = yes")
options = add_option(options, "show_submenu = yes")
#options = add_option(options, "menu_start_files = menu_start.inc")
#options = add_option(options, "menu_end_files = menu_end.inc")
#options = add_option(options, "menu_item1_start = menu_item_start.inc")
#options = add_option(options, "menu_item1_end = menu_item_end.inc")
options = add_option(options, "page_file_name = page")
options = add_option(options, "setup_file_name = setup")
options = add_option(options, "macro_file_name = macro")
options = add_option(options, "inc_file_name = inc")
options = add_option(options, "wiki_parse = yes")
options = add_option(options, "show_item_title = yes")
options = add_option(options, "show_item_title_date = no")
options = add_option(options, "ignore_masks = \\.\\\\*,DEADJOE")
options = add_option(options, "extension_separator = .")
options = add_option(options, "create_pages = yes")

#
# Utility functions
#

# if filter contain any re's, only lines matching any of them are
# returned. If filter is empty, all lines are returned
def file_lines(file, filters = []):
    lines = []
    try:
        f_lines = open(file, "r")
        for l in f_lines:
            if filters == []:
                    lines.append(l + "\n")
            else:
                    for filter in filters:
                            p = re.compile(filter)
                            m = p.search(l)
                            if m:
                                    lines.append(l + "\n")
    except IOError, msg:
        print "Error reading file: ",
        print msg
        print "Current directory: " + os.getcwd()
        raise IOError, msg
        sys.exit(1)
    return lines


#
# Returns the filename up to the first dot
#
def file_base_name(filename):
    try:
        result = filename[:filename.index(".")]
    except:
        result = filename
    return result

# returns the filename extension (without the .)
# optional value default is returned if there is no extension
def file_extension(filename, default = ""):
    p = re.compile("\\..+$")
    m = p.search(filename)
    if m:
        return filename[m.start() + 1:]
    else:
        return default

#
# sorter function for get_dir_files
# Sorts by file number, then reversed last modified date
# items must be of the form [indexnr, timestamp, name]
#
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

# returns the sorting order number of the file.
# ie the number after the first . (or specified spearator)
def file_sort_number(options, filename):
    file_name_parts = filename.split(get_option(options, "extension_separator"));
    result = 999
    if len(file_name_parts) > 1 and file_name_parts[1].isdigit():
        result = int(file_name_parts[1])
    return result

# returns a list of filenames in the directory,
# excluding all re matches from ignore_masks
# sorted by extension, then by last modified date
def get_dir_files(options, dir, ignore_masks, invert = False):
    dirfiles = []
    if os.path.isdir(dir):
    	orig_path = os.getcwd()
        os.chdir(dir)
        files = os.listdir(".")
        #files = map( lambda f: (os.stat(f)[stat.ST_MTIME], file_extension(f), f), files )
        files = map( lambda f: (file_sort_number(options, f), os.stat(f)[stat.ST_MTIME], f), files )
        files.sort(sort_dir_files)
        #print files
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

# generate the menu with the given directory as its base
# returns a list of html lines
# Makes a link when there are .page files in the directory
# what to do if it is an empty nonterminal?
def create_menu_part(root_dir, 
                     dir_prefix, 
                     base_dir, 
                     depth, 
                     cur_depth, 
                     cur_page_depth, 
                     options):
    menu_lines = []

    # TODO: where did cur_depth become a string?
    cur_depth = int(cur_depth)
    depth = int(depth)
    
    ignore_masks = get_options(options, "ignore_masks")
    ignore_masks.append('.*\.nomenu.*')
#    setup_p = re.compile(get_option(options, "setup_file_name"))
    
    dir_files = get_dir_files(options, ".", ignore_masks)
#    print "DIR: "+os.getcwd()
    #print "FILES: ",
    #print dir_files
    for d in dir_files:
    	file_name_parts = d.split(get_option(options, "extension_separator"))
#        setup_m = setup_p.match(d)
#        if setup_m:
        if file_name_parts[-1] == get_option(options, "setup_file_name"):
	    if not os.path.isdir(d):
		    new_options = file_lines(d, ['^[^#].* *= *.+'])
		    if have_option(new_options, "root_dir") and \
		       have_option(new_options, "in_dir"):
			root_dir = get_option_dir(new_options, "root_dir")
			print "root dir now " +root_dir
			in_dir = get_option_dir(new_options, "in_dir")
			print "in dir now " +in_dir
			return_dir = os.getcwd()
			os.chdir(in_dir)
			# this works, but fails to create in/ dir menu link
			menu_lines = create_menu_part(root_dir, dir_prefix, base_dir, depth, cur_depth + 1, cur_page_depth, options)
			os.chdir(return_dir)
			#return []
			return menu_lines
		    # TODO: is this right?
		    options.extend(new_options)
	    #else:
	    #	print "SETUP DIR: "+d
        elif os.path.isdir(d):
	    #print cur_depth * "\t",
	    #print "DIR: "+d
	    #print "back_prefix: "+back_prefix
	    #print cur_depth * "\t",
	    #print "dir_prefix: "+dir_prefix
	    
	    #print file_name_parts
	    #print get_option(options, "setup_file_name")
            # TODO: the extension_separator might be a re operator...
            # remove re list for get_dir_files, and replace with
            # something like the split() function seen in create_page
            pagefilematchlist = [".*"+get_option(options, "extension_separator")+get_option(options, "page_file_name")]
            pagefilematchlist.append("index.html")
            pagefiles = get_dir_files(options, d, pagefilematchlist, True)
            #item_inc = get_option(options, "menu_item" + str(cur_depth) + "_start")
            #if item_inc != '':
            #    if item_inc[:1] != os.sep:
            #        item_inc = root_dir + os.sep + item_inc
            #    menu_lines.extend(file_lines(item_inc))
            menu_lines.append("_menuitem" + str(cur_depth) + "start_\n")
            
            if pagefiles != []:
                i = 0
                back_prefix = ""
                while i < cur_page_depth:
                    back_prefix += os.pardir + os.sep
                    i += 1
                menu_lines.append("\t<a href=\"" + escape_url(back_prefix + dir_prefix + file_base_name(d)) + "/index.html\">\n")
            i = 0
            while i < cur_depth:
                menu_lines.append("\t")
                i += 1
            menu_lines.append(file_base_name(d) + "\n")
            if pagefiles != []:
                menu_lines.append("\t</a>\n")
                
            if cur_depth < depth:
                os.chdir(d)
                menu_lines.extend(create_menu_part(root_dir, dir_prefix + file_base_name(d) + os.sep, base_dir, depth, cur_depth + 1, cur_page_depth, options))
                os.chdir(os.pardir)
            #item_inc = get_option(options, "menu_item" + str(cur_depth) + "_end")
            #if item_inc != '':
            #    if item_inc[:1] != os.sep:
            #        item_inc = root_dir + os.sep + item_inc
            #    menu_lines.extend(file_lines(item_inc))
            menu_lines.append("_menuitem" + str(cur_depth) + "end_\n")
                
    return menu_lines

def create_menu(root_dir, base_dir, options, depth, cur_page_depth):
    orig_dir = os.getcwd()
    os.chdir(base_dir)
#    print "CREATE MENU IN "+base_dir
    
    menu_lines = []
#    for hf in get_options(options, "menu_start_files"):
#        if hf[:1] != os.sep:
#            hf = root_dir + os.sep + hf
#        menu_lines.extend(file_lines(hf))
    menu_lines.append("_menustart_\n")
    menu_lines.extend(create_menu_part(root_dir, "", base_dir, depth, 1, cur_page_depth, options))
#    for hf in get_options(options, "menu_end_files"):
#        if hf[:1] != os.sep:
#            hf = root_dir + os.sep + hf
#        menu_lines.extend(file_lines(hf))
    menu_lines.append("_menuend_\n")
    os.chdir(orig_dir)
    return menu_lines
    

def create_submenu(show_submenu, page_files, options):
    submenu_lines = []
    # submenu
    if show_submenu and len(page_files) > 1:
        submenu_lines.append("<div id=\"submenu\">\n")
        first = True
        for pf in page_files:
            if pf.find(".nomenu") < 0:
                if not first:
                    submenu_lines.append("_SUBMENU-ITEM-SEPARATOR_\n")
                #    submenu_lines.append("<hr noshade=\"noshade\" size=\"1\" width=\"80%\" align=\"left\" />\n")
                else:
                    first = False
                submenu_lines.append("<div class=\"submenu_item\">\n")
                submenu_lines.append("<a href=\"#" + escape_url(file_base_name(pf)) + "\">" + file_base_name(pf) + "</a>\n")
                submenu_lines.append("</div>\n")
        submenu_lines.append("</div>\n")
    return submenu_lines

def create_page(root_dir, in_dir, out_dir, page_name, page_files, options, macro_list, cur_dir_depth):
    page_lines = []
    page_lines.append("<!-- Created by clcms Version " + version + " -->\n")
    last_modified = os.stat(in_dir)[stat.ST_MTIME]

    
    # specific page options are stored in the file name between the dots
#    extension_p = re.compile(get_option(options, "page_file_name"))
#    dots_p = re.compile(get_option(options, "extension_separator"))
    show_menu = False
    show_submenu = False
    if get_option(options, "show_menu") == 'yes':
        show_menu = True
    if get_option(options, "show_submenu") == 'yes':
        show_submenu = True

    # header
    page_lines.append("_header_\n");
    #for hf in get_options(options, "header_files"):
    #    page_lines.extend(file_lines(root_dir + os.sep + hf))

    page_lines.append("<div id=\"content\">\n")

    # handle the .page items
    item_index = 1
    for pf in page_files:
        # Separate the parts of the file
        # First will contain name, last should be "page"
        # Everything in between is option data
        file_name_parts = pf.split(get_option(options, "extension_separator"))
        
        wiki_parse = get_option(options, "wiki_parse") == 'yes'
        show_item_title = get_option(options, "show_item_title") == 'yes'
        show_item_title_date = get_option(options, "show_item_title_date") == 'yes'

        for option_name in file_name_parts[1:-1]:
                if option_name == "nowiki":
                    wiki_parse = False
                elif option_name == "wiki":
                    wiki_parse = True
                elif option_name == "title":
                    show_item_title = True
                elif option_name == "notitle":
                     show_item_title = False
                     show_item_title_date = False
        else:
            if item_index > 1:
                page_lines.append("_ITEM-SEPARATOR_\n")
            pf_lines = []
            if show_item_title or show_item_title_date:
                pf_lines.append("<h3>")
                if show_item_title_date:
                    pf_lines.append(time.strftime("%Y-%m-%d", time.gmtime(os.stat(pf)[stat.ST_MTIME])))
                if show_item_title:
                    pf_lines.append(file_name_parts[0])
                pf_lines.append("</h3>\n")
            if wiki_parse:
                pf_lines.extend(wiki_to_html(file_lines(pf)))
            else:
                pf_lines.extend(file_lines(pf))
            page_lines.append("<a name=\"" + escape_url(file_name_parts[0]) + "\"></a>\n")
            page_lines.extend(pf_lines)
            if os.stat(pf)[stat.ST_MTIME] > last_modified:
                last_modified = os.stat(pf)[stat.ST_MTIME]
                #print in_dir + ": ",
                #print last_modified
            item_index += 1
            
    page_lines.append("</div>\n")

    # footer
    page_lines.append("_footer_\n")
    #for hf in get_options(options, "footer_files"):
    #    page_lines.extend(file_lines(root_dir + os.sep + hf))

    # create dir and file
    if not os.path.isdir(out_dir):
        os.mkdir(out_dir)
    
    lines = page_lines
    lines2 = []
	
    if not no_macros:
        for l in lines:
	    lines2.append(handle_macros(macro_list, l, options, page_name, root_dir, in_dir, cur_dir_depth, page_files, show_submenu, last_modified))

        lines = lines2
        lines2 = []

    page_lines = lines

    # only write if last_modified is past output file
    if not os.path.exists(out_dir + os.sep + "index.html") or \
       os.stat(out_dir + os.sep + "index.html")[stat.ST_MTIME] < last_modified:
        out_file = open(out_dir + os.sep + "index.html", "w")
        out_file.writelines(page_lines)
        out_file.close()
        print "[CLCMS] Created " + out_dir + "/index.html"


def create_pages(root_dir, in_dir, out_dir, default_options, default_macro_list, cur_dir_depth):
    out_dir = escape_url(out_dir)
    if not os.path.isdir(out_dir):
        os.mkdir(out_dir)
    
    options = []
    options.extend(default_options)
    macro_list = []
    macro_list.extend(default_macro_list)

    dir_files = get_dir_files(options, ".", get_options(options, "ignore_masks"))
    # store every file that has not been handled yet in a temp list
    # (removing elements from a list you're iterating over is a bad idea
    dir_files2 = []

    #
    # I use seperate loops for this, because the results of each
    # could have influence on the processing of others
    #

    #
    # Read setup files
    # TODO: recursive function?
    for df in dir_files:
        file_name_parts = df.split(get_option(options, "extension_separator"));
        if file_name_parts[-1] == get_option(options, "setup_file_name"):
	    # if it is a directory, read the .setup, .inc and .macro
	    # files in it as if they were in this directory
	    # no subirectories are handled and no root_dir change is recognized
	    if os.path.isdir(df):
	    	#print "SETUP DIR: "+df
	    	setup_orig_dir = os.getcwd()
	    	os.chdir(df)
	    	setup_dir_files = get_dir_files(options, ".", get_options(options, "ignore_masks"))
	    	for df2 in setup_dir_files:
			setup_file_name_parts2 = df2.split(get_option(options, "extension_separator"));
			if setup_file_name_parts2[-1] == get_option(options, "setup_file_name"):
			    new_options = file_lines(df, ['^[^#].* *= *.+'])
			    for o in new_options:
				options.insert(0, o.lstrip("\t ").rstrip("\n\r\t "))
			elif setup_file_name_parts2[-1] == get_option(options, "inc_file_name"):
			    # TODO: this is same as below, refactor
			    #print "INC FILE IN SETUP DIR: " + df2
			    macro_name = file_base_name(df2)
			    macro_lines = file_lines(df2, [])
			    moc = "output = \"\"\n"
			    for l in macro_lines:
				moc += "output += \""+escape_html(l)+"\\n\"\n"
			    mo = [macro_name, moc]
			    macro_list.insert(0, mo)
			elif file_name_parts[-1] == get_option(options, "macro_file_name"):
			    # TODO: this is same as below, refactor
			    macro_name = file_base_name(df)
			    macro_lines = file_lines(df, [])
			    moc = ""
			    for l in macro_lines:
				moc += l
			    mo = [macro_name, moc]
			    macro_list.insert(0, mo)
			    
	    	os.chdir(setup_orig_dir)
	    else:
		    # If root_dir and in_dir are changed, this is a subsite
		    new_options = file_lines(df, ['^[^#].* *= *.+'])
		    if have_option(new_options, "root_dir") and \
		       have_option(new_options, "in_dir"):
			root_dir = get_option_dir(options, "root_dir")
			#if root_dir[:1] != "/":
			#    root_dir = os.getcwd() + "/" + root_dir
			print "root dir now " +root_dir
			in_dir = get_option_dir(options, "in_dir")
			#if in_dir[:1] != "/":
			#    in_dir = os.getcwd() + "/" + in_dir
			print "in dir now " +in_dir
			return_dir = os.getcwd()
			os.chdir(in_dir)
			for o in new_options:
			    options.insert(0, o.lstrip("\t ").rstrip("\n\r\t "))
			create_pages(root_dir, in_dir, out_dir, options, macro_list, 0)
			print "Done, go back."
			os.chdir(return_dir)
			return

		    for o in new_options:
			options.insert(0, o.lstrip("\t ").rstrip("\n\r\t "))
        else:
            dir_files2.append(df)
    dir_files = dir_files2
    dir_files2 = []

    #
    # Read Macro files
    # 
    for df in dir_files:
        file_name_parts = df.split(get_option(options, "extension_separator"));
        if file_name_parts[-1] == get_option(options, "macro_file_name"):
            macro_name = file_base_name(df)
            macro_lines = file_lines(df, [])
            moc = ""
            for l in macro_lines:
                moc += l
            mo = [macro_name, moc]
            macro_list.insert(0, mo)
        else:
            dir_files2.append(df)
    dir_files = dir_files2
    dir_files2 = []
    
    #
    # Read inc files
    #
    # inc files are handles like macro's, but only contain string data,
    # and will not be executed
    for df in dir_files:
        file_name_parts = df.split(get_option(options, "extension_separator"));
        if file_name_parts[-1] == get_option(options, "inc_file_name"):
            macro_name = file_base_name(df)
            macro_lines = file_lines(df, [])
            moc = "output = \"\"\n"
            for l in macro_lines:
                moc += "output += \""+escape_html(l)+"\"\n"
            mo = [macro_name, moc]
            macro_list.insert(0, mo)
#            print "add from inc in "+os.getcwd()+": " + macro_name
#            print moc
#            print "MACRO LIST NOW:"
#            print macro_list
#            sys.exit(0)
        else:
            dir_files2.append(df)
    dir_files = dir_files2
    dir_files2 = []
    
    
    
    #
    # Read page files
    #
    if get_option(options, "create_pages") == "yes":
        page_files = []
        for df in dir_files:
            file_name_parts = df.split(get_option(options, "extension_separator"));
            if file_name_parts[-1] == get_option(options, "page_file_name"):
                page_files.append(df)
            else:
                #print "FILEEXT: "+file_name_parts[-1]
                dir_files2.append(df)
        dir_files = dir_files2
        dir_files2 = []

        if page_files != []:
            # TODO: dotted page options here? (like in .page file names?)
            page_name = file_base_name(os.path.basename(out_dir))
            create_page(root_dir, in_dir, out_dir, page_name, page_files, options, macro_list, cur_dir_depth)

    # 
    # Read directories
    #
    for df in dir_files:
        if os.path.isdir(df):
            # stoppage checkage action
#            handle_dir = True
#            file_name_parts = df.split(get_option(options, "extension_separator"))
#            for fp in file_name_parts[1:]:
#                if fp == "stop":
#                    print "Stop at dir: "+df
#                    handle_dir = False
#            if handle_dir:
            os.chdir(df)
                #print "Entering directory " + os.getcwd()
            create_pages(root_dir, in_dir, out_dir + os.sep + file_base_name(df), options, macro_list, cur_dir_depth + 1)
            os.chdir(os.pardir)
        else:
            dir_files2.append(df)
    dir_files = dir_files2
    dir_files2 = []

    #
    # Copy rest
    #
    for df in dir_files:
        # check if exists and if older
        if not os.path.exists(out_dir + os.sep + df) or \
            os.stat(out_dir + os.sep + df)[stat.ST_MTIME] < os.stat(df)[stat.ST_MTIME]:
                try:
                    shutil.copy(df, out_dir)
                except IOError,msg:
                    print "Error copying: "+df
                    print "Current directory: "+os.getcwd()
                    print "Error: "
                    print msg
                    sys.exit(1)
                print "[CLCMS] Copied " + df + " to " + out_dir
    

#
#Initializer, argument parsing, and main loop call
# 

# read setup in current dir
for df in os.listdir("."):
    file_name_parts = df.split(get_option(options, "extension_separator"))
    if file_name_parts[-1] == get_option(options, "setup_file_name"):
        #options.extend(file_lines(df, ['^[^#].* *= *.+']))
        print "Found .setup file in current directory: "+df
        for o in file_lines(df, ['^[^#].* *= *.+']):
            options.insert(0, o.lstrip("\t ").rstrip("\n\r\t "))

# parse arguments
if len(sys.argv) > 1:
    for arg in sys.argv[1:]:
    	if arg == "-m" or arg == "--no-macros":
    		no_macros = True
    	elif arg == "-c" or arg == "--write-config":
    		for l in options:
    			print l
		sys.exit(0)
        else:
        	print "Unknown argument: "+arg
    	        sys.exit(1)

in_dir = get_option_dir(options, "in_dir")
root_dir = get_option_dir(options, "root_dir")
out_dir = get_option_dir(options, "out_dir")

if not os.path.isdir(in_dir):
	print "No such directory: " + in_dir
	sys.exit(1)
print "Content directory: " + in_dir
print "Output directory: " + out_dir
if not os.path.isdir(out_dir):
    os.mkdir(out_dir)
os.chdir(in_dir)
create_pages(root_dir, in_dir, out_dir, options, macro_list, 0)
os.chdir(root_dir)

