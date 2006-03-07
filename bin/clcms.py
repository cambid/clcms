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
import copy

version = "0.5"
verbosity = 1;

no_macros = False
force_output = False
inhibit_output = False
show_macro_names = False

# is there a built-in function for this?
def copy_list(l):
	result = []
	for li in l:
		result.append(li)
	return result

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

def escapes_wiki_to_html(line):
    line = line.replace("<<", "&lt;")
    line = line.replace(">>", "&gt;")
    return line

def break_wiki_to_html(line):
    #line=line.strip()
#    if line == "\n":
#        line = "</p><p>\n"
    #line=line.replace('\n','</p><p>')
    #line=line.replace('\n',' ')
    return line

def bold_wiki_to_html(line):
#    line_p=re.compile('(\'\'\'.{1,}?\'\'\')')
    line_p=re.compile('(\'\'\'.{1,}?\'\'\')')
    result=line_p.search(line)
    while result:
#          line=line_p.sub("<b>" +line[result.start()+3:result.end()-3] +"</b>",line,0)
          line=line_p.sub("<b>" +line[result.start()+3:result.end()-3] +"</b>",line,1)
          result=line_p.search(line)
    return line

def italic_wiki_to_html(line):
    line_p=re.compile('(\'\'.{1,}?\'\')')
    result=line_p.search(line)
    while result:
          line=line_p.sub("<i>" +line[result.start()+2:result.end()-2] +"</i>",line,1)
          result=line_p.search(line)
    return line

def heading_wiki_to_html(line):
    line_p = re.compile('(==.{1,}==)')
    result = line_p.search(line)
    if result:
        text = result.group(1)
        heading_level = 0
        while len(text) > 1 and text[0] == '=' and text[-1] == '=':
        	heading_level += 1
        	text = text[1:-1]
	line = "<h" + str(heading_level) + ">"
	text = text.lstrip(" \t")
	text = text.rstrip(" \t")
	line += text
	line += "</h" + str(heading_level) + ">"
    return line

def link_wiki_to_html(line, page):
    # we need to be able to do nested expressions
    # if you want to include an image in a link
    # so regexps won't work
    open_pos = line.find("[[")
    while open_pos >= 0:
        nesting_level = 1
        cur_pos = open_pos + 2
        while nesting_level > 0 and cur_pos < len(line):
            if line[cur_pos:cur_pos + 2] == ']]':
                nesting_level -= 1
	    elif line[cur_pos:cur_pos + 2] == '[[':
	        nesting_level += 1
            cur_pos += 1
	if nesting_level > 0:
	    print "Link nesting error in line:"
	    print line
	    sys.exit(3)
	is_image = False
    	parts = line[open_pos + 2:cur_pos - 1].split("][");
        url = parts[0]
        name = ""
        html = ""
        if len(parts) > 1:
	        name = parts[1]
	if len(parts) > 2:
		html = " " + parts[2]
	if url[:6] == 'Image:':
	    # this is an image
	    url = url[6:]
	    parts = url.split('|')
	    image = parts[0]
	    alt = image
	    width = ""
	    thumb = False
	    frame = False
	    position = ""
	    if len(parts) > 0:
	        # last part is alt/caption
	        alt = parts[-1]
	        parts = parts[1:-1]
                for part in parts:
                    if part[-2:] == "px":
                    	width = part
		    elif part == "thumb":
		        thumb = True
		    elif part == "frame":
		        frame = True
		    elif part == "left" or part == "right" or part == "center":
		        if position:
		            print "Error in image link: "+line
		            print "Position specified more than once"
		        position = part
	            else:
	                print "Error in image link: "+line
	                print "Unknown argument: "+part
	    
	    img_html = "<img src=\"" + image + "\" alt=\"" + alt + "\""
	    if width:
	    	img_html += " width = \"" + width + "\""
	    if frame:
	        img_html += " border = \"1\""
	    img_html += "/>"
	    if thumb:
	        img_html = "<a href=\"" + image + "\">" + img_html + "</a>"
	    
            line = line[:open_pos] + img_html + line[cur_pos + 1:]
            is_image = True
        elif url[:1] == ':':
            # this is an id
            if page:
                targetPage = page.getRootPage().findPageByID(url[1:])
                if not targetPage:
                    print "Page with ID '"+url[1:]+"' not found. Quitting."
                    sys.exit(1)
                if name == "":
                    name = targetPage.name
                url = page.getBackDir() + targetPage.getTotalOutputDir() + "index.html"
        if name == "":
            name = url
        if not is_image:
            line = line[:open_pos] + "<a href=\"" + escape_url(url) + "\"" + html + ">"+name+"</a>" + line[cur_pos + 1:]
        open_pos = line.find("[[")
    return line

# deprecated, part of link now
def img_wiki_to_html(line, page):
    line_p = re.compile('\{\{(.{1,}?)\}\}');
    line_m = line_p.search(line);
    while line_m:
    	parts = line_m.group(1).split("}{");
        url = parts[0]
        name = ""
        html = ""
        if len(parts) > 1:
	        name = parts[1]
	if len(parts) > 2:
		html = " " + parts[2]
        if url[:1] == ':':
            # this is an id
            print "ID for images not implemented (yet?)"
            sys.exit(12)
            if page:
                targetPage = page.getRootPage().findPageByID(url[1:])
                if not targetPage:
                    print "Page with ID '"+url[1:]+"' not found. Quitting."
                    sys.exit(1)
                if name == "":
                    name = targetPage.name
                url = page.getBackDir() + targetPage.getTotalOutputDir() + "index.html"
        if name == "":
            name = url
	line = line[:line_m.start()] + "<img src=\"" + url + "\"" + html + " alt=\"" + name + "\" />" + line[line_m.end():]
	line_m = line_p.search(line)
    return line

    return line

def wiki_to_html_simple(line, page):
    # if line starts with __, do not do rest
    if line[:2] == "__":
    	line = "<pre>"+escapes_wiki_to_html(line[2:])+"</pre>"
    else:
        line = escapes_wiki_to_html(line)
        line = break_wiki_to_html(line)
        line = bold_wiki_to_html(line)
        line = italic_wiki_to_html(line)
        line = heading_wiki_to_html(line)
        line = link_wiki_to_html(line, page)
        #line = img_wiki_to_html(line, page)
    return line + "\n"
#    return line

def wiki_handle_lists(prev_list_part, list_part, html_lines):
    same_part = ""
    new_item = False
    html_lines.append("<!-- plp: "+prev_list_part+" lp: "+list_part+" -->\n")
    # for html code layout
    cur_depth = 0
    
    if list_part != "":
        new_item = True
    
    while len(prev_list_part) > 0 and len(list_part) > 0 \
          and prev_list_part[0] == list_part[0]:
        same_part = same_part + list_part[0]
        prev_list_part = prev_list_part[1:]
        list_part = list_part[1:]
    
    cur_depth = len(same_part)
    
    html_lines.append("<!-- sp: "+same_part +" plp: "+prev_list_part+" lp: "+list_part+" -->\n")
    if same_part != "" or prev_list_part != "":
        if prev_list_part != "":
            cur_depth += 1
        html_lines.append((cur_depth * "\t") + "</li>\n");

    # go back in lists 
    cur_depth = len(same_part)
    while len(prev_list_part) > 0:
        if prev_list_part[-1] == '*':
            html_lines.append((cur_depth * "\t") + "</ul>\n")
        elif prev_list_part[-1] == '#':
            html_lines.append((cur_depth * "\t") + "</ol>\n")
        else:
            print "Error in prev_list_part: "+prev_list_part[0]+" should not appear here. please file a bug report"
            sys.exit(1)
        prev_list_part = prev_list_part[:-1]
        cur_depth += 1

    cur_depth = len(same_part)
    while len(list_part) > 0:
        if list_part[0] == '*':
            html_lines.append((cur_depth * "\t") + "<ul>\n")
        elif list_part[0] == '#':
            html_lines.append((cur_depth * "\t") + "<ol>\n")
        else:
            print "Error in list_part: "+list_part[0]+" should not appear here. please file a bug report"
            sys.exit(1)
        list_part = list_part[1:]
        cur_depth += 1

    if new_item:
        html_lines.append((cur_depth * "\t") + "<li>\n")

def wiki_to_html(wiki_lines, page = None):
    html_lines = []
    i = 0
    no_wiki = False
    whitespace_p = re.compile('^\s*\n$')
    html_lines.append("<p>\n")
    list_p = re.compile('^([#*]+) (.*)$')
    prev_list_part = ""
    line = ""
    
    while i < len(wiki_lines):
        
        prev_line = line
        line = wiki_lines[i]
        line = line.lstrip("\n\t ")
#        if line == "":
#            line = "\n"
#        if line == "" and prev_list_part == "" and not no_wiki:
        if line == "" and prev_list_part == "":
            if no_wiki:
                html_lines.append("\n")
            else:
                html_lines.append("</p><p>\n")
        elif no_wiki:
            if line[:14] == "_NO_WIKI_END_\n":
                no_wiki = False
            else:
                html_lines.append(line)
        else:
            if line[:10] == "_NO_WIKI_\n":
	        no_wiki = True
	    else:
	        # in lists, single line breaks are <br />, but not end of lists
	        list_m = list_p.match(line)
	        if list_m:
	            wiki_handle_lists(prev_list_part, list_m.group(1), html_lines)
	            prev_list_part = list_m.group(1)
	            line = list_m.group(2)
	        #elif prev_list_part != "":
	        #    wiki_handle_lists(prev_list_part, "", html_lines)
	        #    prev_list_part = ""
	        else:
	            if line == "" and prev_line == "":
			if prev_list_part != "":
			    wiki_handle_lists(prev_list_part, "", html_lines)
			    prev_list_part = ""
		    elif line == "" and prev_list_part != "":
	                html_lines.append("<br/>\n")
	        html_lines.append(wiki_to_html_simple(line, page))
	        
	i += 1
    if prev_list_part != "":
        wiki_handle_lists(prev_list_part, "", html_lines)
        prev_list_part = ""
    html_lines.append("</p>\n")
    return html_lines

def old_wiki_to_html(wiki_lines, page = None):
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
                    html_lines.append("<h" + str(j-3) + ">" + wiki_to_html_simple(line[j:], page) + "</h" + str(j-3) +  ">\n")
                else:
                    html_lines.append(wiki_to_html_simple(line, page))
            elif line[:5] == "   * ":
                html_lines.append("<ul>\n")
                html_lines.append("\t<li>\n")
                html_lines.append(wiki_to_html_simple(line[5:], page))
                in_list1 = True
                while in_list1:
                    i += 1
                    if i < len(wiki_lines):
                        line = wiki_lines[i]
                        if line[:5] == "   * ":
                            html_lines.append("\t</li>\n")
                            html_lines.append("\t<li>\n")
			    html_lines.append(wiki_to_html_simple(line[5:], page))
                        elif line[:8] == "      * ":
                            html_lines.append("<ul>\n")
                            html_lines.append("\t<li>\n")
                            html_lines.append(wiki_to_html_simple(line[8:], page))
                            in_list2 = True
                            while in_list2:
                                i += 1
                                if i < len(wiki_lines):
                                    line = wiki_lines[i]
                                    if line[:8] == "      * ":
                                        html_lines.append("\t</li>\n")
                                        html_lines.append("\t<li>\n")
                                        html_lines.append(wiki_to_html_simple(line[8:], page))
                                    #elif line[:8] == "      * ":
                                    elif line[:11] == "         * ":
                                        html_lines.append("<ul>\n")
                                        html_lines.append("\t<li>\n")
                                        html_lines.append(wiki_to_html_simple(line[11:], page))
                                        in_list3 = True
                                        while in_list3:
                                            i += 1
                                            if i < len(wiki_lines):
                                                line = wiki_lines[i]
                                                if line[:11] == "         * ":
                                                    html_lines.append("\t</li>\n")
                                                    html_lines.append("\t<li>\n")
                                                    html_lines.append(wiki_to_html_simple(line[11:], page))
                                                #elif line[:11] == "         * ":
 					        elif whitespace_p.match(line):
							html_lines.append("<br />\n")
                                                elif line[:11] == "           ":
							html_lines.append(wiki_to_html_simple(line[11:], page))
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
					html_lines.append(wiki_to_html_simple(line[8:], page))
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
                                html_lines.append(wiki_to_html_simple(line[5:], page))
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
                html_lines.append(wiki_to_html_simple(line, page))
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
#  ["menu", "output = \"\"\nfor ml in create_menu(root_dir, in_dir, options, arguments[0], cur_dir_depth):\n\toutput += ml\n", 0 ],
#  ["submenu", "output = \"\"\nfor ml in create_submenu(show_submenu, page_files, options):\n\toutput += ml\n", 0 ],
#  ["datefile", "output = time.strftime(\"%Y-%m-%d\", time.gmtime(last_modified))\n", 0 ],
#  ["stylesheet", 'i = 0\noutput = ""\nwhile i < page.getPageDepth():\n\toutput += os.pardir + os.sep\n\ti += 1\noutput += get_option(page.options, "style_sheet")\n', 0 ],
#  ["stylesheet", "output = ((os.pardir + os.sep)*page.getPageDepth()) + get_options(page.options, 'stylesheet')\n", 0 ],
system_macro_list = [
  ["menu", "menu_depth = 1\nmenu_start_depth = 0\nif len(arguments) > 0:\n\tmenu_depth = int(arguments[0])\nif len(arguments) > 1:\n\tmenu_start_depth = int(arguments[1])\nml = page.getRootPage().createMenu(page, menu_depth, menu_start_depth)\noutput = \"_menustart_\\n\"\nfor l in ml:\n\toutput += l\noutput += \"_menuend_\\n\"\n", 0],
  ["submenu", "output = \"\"\nsml = page.createAnchorMenu()\nfor l in sml:\n\toutput += l", 0],
  ["stylesheet", "output = (os.pardir + os.sep)*(page.getPageDepth())+get_option(page.options, 'stylesheet')\n", 0 ],
  ["title", "output = page.name\n", 0 ],
  ["date", "output = time.strftime(\"%Y-%m-%d\")\n", 0 ],
  ["datefile", "output = time.strftime(\"%Y-%m-%d\", page.findPageDate())\n", 0],
  ["itemseparator", " output = \"<hr noshade=\\\"noshade\\\" size=\\\"1\\\" width=\\\"60%\\\" align=\\\"left\\\" />\"", 0 ],
  ["submenuitemseparator", " output = \"<hr noshade=\\\"noshade\\\" size=\\\"1\\\" width=\\\"60%\\\" align=\\\"left\\\" />\"", 0 ],
  ["header", "\
output = \"\"\n\
output += \"<!DOCTYPE html PUBLIC \\\"-//W3C//DTD HTML 4.01 Transitional//EN\\\" \\\"http://www.w3.org/TR/html4/loose.dtd\\\">\\n\"\n\
output += \"<html>\\n\"\n\
output += \"     <head>\\n\"\n\
output += \"             <META HTTP-EQUIV=\\\"Content-Type\\\" CONTENT=\\\"text/html; charset=UTF-8\\\">\\n\"\n\
output += \"             <link REL=\\\"stylesheet\\\" TYPE=\\\"text/css\\\" href=\\\"../../default.css\\\">\\n\"\n\
output += \"             <title>\\n\"\n\
output += \"                     Tutorial\\n\"\n\
output += \"             </title>\\n\"\n\
output += \"     </head>\\n\"\n\
output += \"     <body>\\n\"\n\
output += \"     _menu_1_\\n\"\n\
output += \"     <div id=\\\"main\\\">\\n\"\n\
output += \"     _submenu_\\n\"\n\
", 0 ],
  ["footer", "\
output = \"\"\n\
output += \"    </div>\\n\"\n\
output += \"    </body>\\n\"\n\
output += \"</html>\\n\"\n\
", 0 ],
  ["menustart", "output = \"\"\n", 0 ],
  ["menuend", "output = \"\"\n", 0 ],
  ["menuitem1start", "output = \"\"\n", 0 ],
  ["menuitem1end", "output = \"\"\n", 0 ],
  ["menuitem1selected", "output = \"\"\n", 0 ],
  ["menuitem2start", "output = \"\"\n", 0 ],
  ["menuitem2end", "output = \"\"\n", 0 ],
  ["menuitem2selected", "output = \"\"\n", 0 ],
  ["menuitem3start", "output = \"\"\n", 0 ],
  ["menuitem3end", "output = \"\"\n", 0 ],
  ["menuitem3selected", "output = \"\"\n", 0 ],
  ["menuitem4start", "output = \"\"\n", 0 ],
  ["menuitem4end", "output = \"\"\n", 0 ],
  ["menuitem4selected", "output = \"\"\n", 0 ],
  ["menuitem5start", "output = \"\"\n", 0 ],
  ["menuitem5end", "output = \"\"\n", 0 ],
  ["menuitem5selected", "output = \"\"\n", 0 ],
  ["menuitem1start-arg", "output = \"_menuitem1start_\\n\"\nif arguments != []:\n\toutput += arguments[0]\n", 0], 
  ["menuitem2start-arg", "output = \"_menuitem2start_\\n\"\nif arguments != []:\n\toutput += arguments[0]\n", 0], 
  ["menuitem3start-arg", "output = \"_menuitem3start_\\n\"\nif arguments != []:\n\toutput += arguments[0]\n", 0], 
  ["menuitem4start-arg", "output = \"_menuitem4start_\\n\"\nif arguments != []:\n\toutput += arguments[0]\n", 0], 
  ["menuitem5start-arg", "output = \"_menuitem5start_\\n\"\nif arguments != []:\n\toutput += arguments[0]\n", 0], 
  ["submenustart", "output = \"<div id = \\\"submenu\\\">\"\n", 0],
  ["submenuend", "output = \"</div>\"\n", 0],
  ["debug", "output = \"\"\nprint arguments[0]\n", 0 ],
  ["dumpmacros", "for m in macro_list:\n\tprint m[0]\n\tprint m[1]\n\tprint m[2]\n\tprint \"\"\noutput=\"\"\n", 0 ],
  ["submenuitemstart", "output = \"<div class=\\\"submenu_item\\\">\"\n", 0 ],
  ["submenuitemend", "output = \"</div>\"\n", 0 ],
  ["backdir", "output = page.getBackDir()\n", 0 ],
  ["nextpage", "output = \"\"\nnp = page.getNextPage()\nif np:\n\toutput = \"<a href=\\\"\"+page.getBackDir()+np.getTotalOutputDir()+\"index.html\\\">\"+np.name+\"</a>\"\n", 0],
  ["prevpage", "output = \"\"\npp = page.getPreviousPage()\nif pp:\n\toutput = \"<a href=\\\"\"+page.getBackDir()+pp.getTotalOutputDir()+\"index.html\\\">\"+pp.name+\"</a>\"\n", 0],
  ["uppage", "output = \"\"\nup = page.parent\nif up:\n\toutput = \"<a href=\\\"\"+page.getBackDir()+up.getTotalOutputDir()+\"index.html\\\">\"+up.name+\"</a>\"\n", 0],  
  ["fake", "output = \"\"\n", 0 ]
]

# TODO: always set output to "" when reading new macro definitions

def handle_macro(macro_name, macro_source, input_line, page):
    result_line = input_line
    macro_p = re.compile("(?:_"+macro_name+")((?:_[a-zA-Z0-9]+|_\(.*\))*)_")

    #macro_p = re.compile("_"+macro_name+"_");
    macro_m = macro_p.search(input_line)
    if macro_m:
        ip = code.InteractiveInterpreter()
        output = "<badmacro>"

        arguments = []
        if macro_m.lastindex != None:
        	macro_arg_str = macro_m.group(1)
        	macro_arg_p = re.compile("_(\(.*\)|[a-zA-Z0-9]+)")
        	macro_arg_m = macro_arg_p.search(macro_arg_str)
        	while macro_arg_m:
        		macro_arg_val = macro_arg_str[macro_arg_m.start() + 1:macro_arg_m.end()]
        		if len(macro_arg_val) > 1 and macro_arg_val[0] == '(' and macro_arg_val[-1] == ')':
        			macro_arg_val = macro_arg_val[1:-1]
        		macro_arg_str = macro_arg_str[macro_arg_m.end():]
        		macro_arg_m = macro_arg_p.search(macro_arg_str)
        		arguments.append(macro_arg_val)
        if (verbosity >= 4):
		print "Line: "+input_line
		print "Match: "+input_line[macro_m.start():macro_m.end()]
	        print "Macro: "+macro_name
	        print "number of arguments: ",
	        print len(arguments)
		print "arguments: ",
		print arguments

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
            print "For page: "+page.name
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
	    result_line = input_line[:macro_m.start()]
	    if show_macro_names:
	        result_line += "<!-- macro " + macro_name + " start -->"
	        #result_line = input_line[:macro_m.start()] + output + input_line[macro_m.end():]
	    result_line += output
	    if show_macro_names:
	        result_line += "<!-- macro " + macro_name + " end -->"
	    result_line += input_line[macro_m.end():]
        else:
            print "Warning: Bad macro: "+macro_name
        return result_line
    return result_line
    
def handle_macros(page, input_line):
    orig_input_line = input_line
    cur_line = input_line
    orig_line = ""
    i = 0
    
    while orig_line != cur_line:
        orig_line = cur_line
        for mo in page.macros:
            cur_line = handle_macro(mo[0], mo[1], cur_line, page)
            if cur_line != orig_line:
            	if verbosity >= 5:
            		print "Macro substitution: "
            		print "<<<<<<<<<<<<<<<<<<BEFORE<<<<<<<<<<<<<<<"
            		print orig_line
            		print ">>>>>>>>>>>>>>>>>>AFTER>>>>>>>>>>>>>>>>"
            		print cur_line
                #if mo[2] > macro_last_modified:
		    #print "MACRO CHANGED!"
                #    macro_last_modified = mo[2]
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
	print options
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
system_options = []
system_options = add_option(system_options, "root_dir = .")
system_options = add_option(system_options, "in_dir = in")
system_options = add_option(system_options, "out_dir = out")
system_options = add_option(system_options, "stylesheet = " + "default.css")
system_options = add_option(system_options, "resource_dir = .")
system_options = add_option(system_options, "show_menu = yes")
system_options = add_option(system_options, "show_submenu = yes")
system_options = add_option(system_options, "page_file_name = page")
system_options = add_option(system_options, "setup_file_name = setup")
system_options = add_option(system_options, "macro_file_name = macro")
system_options = add_option(system_options, "inc_file_name = inc")
system_options = add_option(system_options, "wiki_parse = yes")
system_options = add_option(system_options, "show_item_title = yes")
system_options = add_option(system_options, "show_item_title_date = no")
system_options = add_option(system_options, "ignore_masks = \\.\\\\*,DEADJOE")
system_options = add_option(system_options, "extension_separator = .")
system_options = add_option(system_options, "create_pages = yes")

#options = default_options

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
            l = l.rstrip(" \t\n");
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

def create_submenu(show_submenu, page_files, options):
    submenu_lines = []
    # submenu
    if show_submenu and len(page_files) > 1:
        submenu_lines.append("_submenustart_\n")
        first = True
        for pf in page_files:
            if pf.find(".nomenu") < 0:
                if not first:
                    submenu_lines.append("_submenuitemseparator_\n")
                else:
                    first = False
                submenu_lines.append("_submenuitemstart_\n");
                submenu_lines.append("<a href=\"#" + escape_url(file_base_name(pf)) + "\">" + file_base_name(pf) + "</a>\n")
                submenu_lines.append("_submenuitemend_\n");
        submenu_lines.append("_submenuend_\n")
    return submenu_lines

def print_indentation(depth):
	print "  "*depth,
    
################## NEW STUFF CLASS PUT IN OTHER .py? ##########
class Page:
	"A page object"

	def __init__(self, name, basedir, pagedir, parent = None):
		#print "Add page", dir
		self.input_dir = basedir
		self.page_dir = pagedir
		self.parent = parent
		
		self.name = name

		# By default, the id is the input directory
		self.id = basedir + os.sep + pagedir
		self.sort_order = -1

		self.contents = []
		self.files = []
		self.children = []
		
		self.macros = []
		self.options = []
		
		self.show_menu_item = True
		self.show_submenu = True
		self.is_subsite = False
		
		self.recreate = False

	def addContent(self, content):
		#print "Adding",content.name, "to page", self.name
		self.contents.append(content)
	
	def addFile(self, file):
		self.files.append(file)
	
	def addChild(self, child):
		self.children.append(child)

	def getPageDepth(self):
		if self.parent == None:
			return 0
		else:
			return 1 + self.parent.getPageDepth()
	
	def isParent(self, page):
		if page.parent == None:
			return False
		elif page.parent == self:
			return True
		else:
			return self.isParent(page.parent)
	
	def getRootPage(self):
		if self.parent == None:
			return self
		else:
			return self.parent.getRootPage()

	def printOverview(self, depth = 0):
		print_indentation(depth)
		print self.name
		print_indentation(depth+1)
		print "Contents:"
		for c in self.contents:
			c.printOverview(depth+2)
		print_indentation(depth+1)
		print "Files:"
		for f in self.files:
			f.printOverview(depth+2)
		print_indentation(depth+1)
		print len(self.children), "Children:"
		for c in self.children:
			c.printOverview(depth+2)
	
	def printAll(self, max_depth = -1):
		print "-----------PAGE-------------"
		print "Name:", self.name
		print "id:", self.id
		print "input dir:", self.input_dir
		print "sort order: ",self.sort_order
		print "contents:"
		for c in self.contents:
			c.printAll()
		print "files:"
		for f in self.files:
			f.printAll()
		# print macros?
		# print options?
		for c in self.children:
			if max_depth > 0:
				c.printAll(max_depth - 1)
			elif max_depth == -1:
				c.printAll(-1)
	
	def getOutputDir(self):
		#dir_parts = self.page_dir.split(get_option(self.options, "extension_separator"))
		#return escape_url(dir_parts[0])
		return escape_url(self.page_dir)
	
	def getTotalOutputDir(self):
		if self.parent == None:
			if not self.is_subsite and self.name != "":
				return self.name + os.sep
			else:
				return ""
		else:
			return self.parent.getTotalOutputDir() + self.getOutputDir() + os.sep
		
	def toHTML(self):
		page_lines = []
		page_lines.append("_header_\n");
		page_lines.append("<div id=\"content\">\n")
		i = 1
		for c in self.contents:
			page_lines.extend(c.toHTML())
			if i < len(self.contents):
				page_lines.append("_itemseparator_")
		page_lines.append("</div>\n");
		page_lines.append("_footer_");

		if not no_macros:
			macro_new_lines = []
			do_handle_macros = True
			for l in page_lines:
  				if l[:14] == "_NO_MACRO_END_":
  				    do_handle_macros = True
  				elif l[:10] == "_NO_MACRO_":
  				    do_handle_macros = False
			        elif do_handle_macros:
  				    macro_new_lines.append(handle_macros(self, l))
  				else:
  				    macro_new_lines.append(l)
			page_lines = macro_new_lines
		return page_lines
	
	def getBackDir(self):
		return (os.pardir + os.sep)*(self.getPageDepth())
		
	def createMenu(self, calling_page, depth, start_depth = 0):
		cur_depth = self.getPageDepth()
		menu_lines = []
		#menu_lines.append("menu for level "+ str(self.getPageDepth()) + " ("+self.name+") has " + str(len(self.children)) + "children\n")
		back_dir = ""
		if calling_page.getPageDepth() > 0:
			back_dir =  calling_page.getBackDir()
		for c in self.children:
			if self.show_menu_item:
				link = ""
				if len(c.contents) > 0:
					#link = "<a href=\""+(os.pardir + os.sep)*(calling_page.getPageDepth()) + os.pardir + c.getTotalOutputDir() + os.sep + "index.html\""
					link = "<a href=\""+ back_dir + c.getTotalOutputDir() + "index.html\""
					if c == calling_page or c.isParent(calling_page):
						link += " _menuitem"+str(self.getPageDepth()+1)+"selected_"
					link += ">"
					#menu_lines.append(link)
				link += c.name
				if len(c.contents) > 0:
					link += "</a>"
				if cur_depth >= start_depth:
					if start_depth > 0 and cur_depth <= calling_page.getPageDepth():
						if self.isParent(calling_page) or self == calling_page:
							menu_lines.append("_menuitem"+str(cur_depth+1)+"start-arg_("+link+")_\n")
					else:
						menu_lines.append("_menuitem"+str(cur_depth+1)+"start-arg_("+link+")_\n")
				if depth > 1:
					if c.is_subsite:
						cc = copy.deepcopy(c)
						cc.parent = self
						menu_lines.extend(cc.createMenu(calling_page, depth - 1, start_depth))
					else:
						menu_lines.extend(c.createMenu(calling_page, depth - 1, start_depth))
				if cur_depth >= start_depth:
						menu_lines.append("_menuitem"+str(cur_depth+1)+"end_\n")
		return menu_lines
	
	def createAnchorMenu(self):
		anchor_menu_lines = []
		if get_option(self.options, "show_submenu") == 'yes' and len(self.contents) > 1:
			anchor_menu_lines += "_submenustart_"
			i = 1
			for c in self.contents:
				anchor_menu_lines += "_submenuitemstart_"
				anchor_menu_lines += "<a href=\"#" + c.getAnchorName() + "\">"
				anchor_menu_lines += c.name
				anchor_menu_lines += "</a>\n"
				if i < len(self.contents):
					anchor_menu_lines += "_submenuitemseparator_"
				i += 1
				anchor_menu_lines += "_submenuitemend_"
			anchor_menu_lines += "_submenuend_"		
		return anchor_menu_lines
	
	def copyFiles(self, output_directory):
		# copies to output_directory argument, does NOT append its own subdir itself
		for f in self.files:
			shutil.copy(f.input_file, output_directory)
	
	def createPage(self, output_directory, recursive):
		out_dir = output_directory + os.sep + self.getOutputDir()
		#print "out_dir: "+out_dir
		if  not os.path.isdir(out_dir):
		        os.mkdir(out_dir)
		if self.recreate:
			if verbosity >= 1:
				print "Creating page '"+self.name+"'"
			out_file = open(out_dir + os.sep + "index.html", "w")
			out_file.writelines(self.toHTML())
			out_file.close()
		self.copyFiles(out_dir)
		if recursive:
			for c in self.children:
				c.createPage(out_dir, recursive)
	
	def prepare(self, output_directory):
		# todo: add update checks here too?
		# how about file/page dates?
		# walk through the tree, and update times and sort orders
		out_time = 0
		out_dir = output_directory + os.sep + self.getOutputDir()
		#if os.path.isdir(out_dir):
		if os.path.exists(out_dir + os.sep + "index.html"):
			out_time = time.gmtime(os.stat(out_dir + os.sep + "index.html")[stat.ST_MTIME])
		in_time = self.findPageDate()
		if in_time > out_time or force_output:
			self.children.sort(compare_pages)
			self.contents.sort(compare_contents)
			self.recreate = True
		for c in self.children:
			c.prepare(out_dir)

	def findPageDate(self):
		# searches this page and its contents for the last modified date
		# todo: add macro changes? (need seperate class?)
		# todo: store it so we can reuse it ;)
		last_date = time.gmtime(os.stat(self.input_dir)[stat.ST_MTIME])
		for c in self.contents:
			cld = time.gmtime(os.stat(c.input_file)[stat.ST_MTIME])
			if cld > last_date:
				last_date = cld
		return last_date
	
	def findPageByID(self, id):
		if not self:
			return None
		if self.id == id:
			return self
		else:
			for c in self.children:
				p = c.findPageByID(id)
				if p:
					return p
			return None

	# Returns the first page after this one that has content
	# if return_children is true (default) then the first child
	# (if any) is returned, otherwise it's first sibling
	# Returns None if this is the last page
	def getNextPage(self, return_children = True):
		next_page = None
		if return_children and len(self.children) > 0:
			next_page = self.children[0]
		elif self.parent:
			lp = None
			for p in self.parent.children:
				if lp == self:
					next_page = p
				lp = p
			if not next_page:
				next_page = self.parent.getNextPage(False)
		if next_page and len(next_page.contents) == 0:
			return next_page.getNextPage(return_children)
		else:
			return next_page
			
	# Returns the last page before this one that has content
	# if return_children is true (default) then the last child
	# (if any) is returned, otherwise it's last sibling
	# Returns None if this is the first page
	def getPreviousPage(self, return_children = True):
		prev_page = None
		if self.parent:
			lp = None
			for p in self.parent.children:
				if p == self:
					prev_page = lp
				lp = p
		if not prev_page:
			prev_page = self.parent
		else:
			while return_children and len(prev_page.children) > 0:
				prev_page = prev_page.children[-1]
		if prev_page and len(prev_page.contents) == 0:
			return prev_page.getPreviousPage(return_children)
		else:
			return prev_page

class Content:
	"A page content object"
	def __init__(self, page, file):
		self.input_file = page.input_dir + os.sep + file

		name_parts = file.split(get_option(page.options, "extension_separator"))
		
		self.name = name_parts[0]
		# By default, the id is the input file
		self.id = file
		self.sort_order = -1
		self.parse_wiki = True
		self.show_item_title = True
		self.show_item_title_date = False

		# parent page
		self.page = page
	
	def printOverview(self, depth = 0):
		print_indentation(depth)
		print self.name
	
	def getAnchorName(self):
		return escape_url(self.name)
	
	def printAll(self):
		print "name:", self.name
		print "id:", os.getcwd() + os.sep + self.id
		print "sort order:", self.sort_order
		print "input file: ", self.input_file

	def toHTML(self):
		page_lines = []
		page_lines.append("<a name=\"" + self.getAnchorName() + "\"></a>\n")
		if self.show_item_title or self.show_item_title_date:
			title_line = "<h3>"
			if self.show_item_title_date:
				title_line += time.strftime("%Y-%m-%d", time.gmtime(os.stat(self.input_file)[stat.ST_MTIME]))
			if self.show_item_title:
				title_line += self.name
			title_line += "</h3>\n"
			page_lines.append(title_line)
		if self.parse_wiki:
			page_lines.extend(wiki_to_html(file_lines(self.input_file), self.page))
		else:
			page_lines.extend(file_lines(self.input_file))
		return page_lines

class File:
	"A file object"
	def __init__(self, file):
		self.input_file = os.getcwd() + os.sep + file
		# By default, the id is the input file
		self.id = os.getcwd() + os.sep + file
	
	def printOverview(self, depth = 0):
		print_indentation(depth)
		print self.input_file
	
	def printAll(self):
		print "id:", self.id
		print "file:", self.input_file

#
# 'compares' pages based on their sort order, then on the last modified date of
# their input directories (backwards)
#
# pages with a sort order come before those without (ie. have value -1)
def compare_pages(a, b):
	if a.sort_order == -1 and b.sort_order > -1:
		return 1
	elif a.sort_order > -1 and b.sort_order == -1:
		return -1
	elif a.sort_order > b.sort_order:
		return 1
	elif a.sort_order < b.sort_order:
		return -1
	else:
		if os.stat(a.input_dir)[stat.ST_MTIME] > os.stat(b.input_dir)[stat.ST_MTIME]:
			return 1
		elif os.stat(a.input_dir)[stat.ST_MTIME] < os.stat(b.input_dir)[stat.ST_MTIME]:
			return -1
		else:
			return 0

#
# 'compares' page content items based on their sort order, then on the 
# last modified date of their input files (backwards)
#
# contents with a sort order come before those without (ie. have value -1)
def compare_contents(a, b):
	if a.sort_order == -1 and b.sort_order > -1:
		return 1
	elif a.sort_order > -1 and b.sort_order == -1:
		return -1
	elif a.sort_order > b.sort_order:
		return 1
	elif a.sort_order < b.sort_order:
		return -1
	else:
		if os.stat(a.input_file)[stat.ST_MTIME] > os.stat(b.input_file)[stat.ST_MTIME]:
			return -1
		elif os.stat(a.input_file)[stat.ST_MTIME] < os.stat(b.input_file)[stat.ST_MTIME]:
			return 1
		else:
			return 0

		


def build_page_tree(root_dir, page_dir, default_options, default_macro_list, cur_depth):
	page = None
	page_dir_parts = page_dir.split(get_option(default_options, "extension_separator"))
	page = Page(page_dir_parts[0], os.getcwd(), page_dir)
	#print "NEW PAGE!!!!!!!!!!!!!!!!"
	#page.printOverview()
	#print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
	
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
		file_name_parts = df.split(get_option(options, "extension_separator"))
		if file_name_parts[-1] == get_option(options, "setup_file_name"):
			# if it is a directory, read the .setup, .inc and .macro
			# files in it as if they were in this directory
			# no subirectories are handled and no root_dir change is recognized
			if verbosity >= 3:
				print "Found setup dir: " + os.getcwd() + os.sep + df
			if os.path.isdir(df):
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
						macro_name = file_base_name(df2)
						macro_lines = file_lines(df2, [])
						moc = "output = \"\"\n"
						for l in macro_lines:
							if l == macro_lines[-1]:
								moc += "output += \""+escape_html(l.rstrip())+"\"\n"
							else:
								moc += "output += \""+escape_html(l.rstrip())+"\\n\"\n"
						# TODO ADD MACRO FILE TIME
						mo = [macro_name, moc, os.stat(df2)[stat.ST_MTIME]]
						macro_list.insert(0, mo)
					elif setup_file_name_parts2[-1] == get_option(options, "macro_file_name"):
						# TODO: this is same as below, refactor
						macro_name = file_base_name(df2)
						macro_lines = file_lines(df2, [])
						moc = ""
						for l in macro_lines:
							moc += l
						# TODO ADD MACRO FILE TIME
						mo = [macro_name, moc, os.stat(df2)[stat.ST_MTIME]]
						macro_list.insert(0, mo)
					else:
						print "NOT SETUP INC OR MACRO: "+df2	
					
				os.chdir(setup_orig_dir)
			else:
				# If root_dir and in_dir are changed, this is a subsite
				new_options = file_lines(df, ['^[^#].* *= *.+'])
				if have_option(new_options, "root_dir") and \
				   have_option(new_options, "in_dir"):
					if verbosity >= 2:
						print "Found subsite in " + os.getcwd() + os.sep + df
					root_dir = get_option_dir(options, "root_dir")
					in_dir = get_option_dir(options, "in_dir")
					return_dir = os.getcwd()
					os.chdir(in_dir)
					s_options = copy.deepcopy(system_options)
					s_macro_list = copy.deepcopy(system_macro_list)
					for o in new_options:
						s_options.insert(0, o.lstrip("\t ").rstrip("\n\r\t "))
						#create_pages(root_dir, in_dir, out_dir, options, macro_list, 0)
					subsite_page = build_page_tree(in_dir, page_dir, s_options, s_macro_list, 0)
					os.chdir(return_dir)
					#page.addChild(subsite_page)
					subsite_page.is_subsite = True
					return subsite_page
				else:
					for o in new_options:
						options.insert(0, o.lstrip("\t ").rstrip("\n\r\t "))
		else:
			dir_files2.append(df)
	dir_files = dir_files2
	dir_files2 = []

	page.options = options

	for df in dir_files:
		# TODO: option
		if df == "page.meta":
			for l in file_lines(df):
				if l.rstrip() != "":
					if l[:4] == "id: ":
						page.id = l[4:].rstrip()
					elif l[:12] == "sort order: ":
						page.sort_order = int(l[12:].rstrip())
					else:
						print "Warning: unknown option line in page.meta file"
						print "File: " + os.getcwd()+ os.sep + "page.meta:"
						print l
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
				# TODO ADD MACRO FILE TIME
				mo = [macro_name, moc, os.stat(df)[stat.ST_MTIME]]
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
				#moc += "output += \""+l+"\"\n"
				# TODO ADD MACRO FILE TIME
			mo = [macro_name, moc, os.stat(df)[stat.ST_MTIME]]
			macro_list.insert(0, mo)
		else:
			dir_files2.append(df)
	dir_files = dir_files2
	dir_files2 = []

	page.macros = macro_list
	
	#
	# add .page content
	#
	# check options for here
        wiki_parse = get_option(options, "wiki_parse") == 'yes'
        show_item_title = get_option(options, "show_item_title") == 'yes'
        show_item_title_date = get_option(options, "show_item_title_date") == 'yes'

	for df in dir_files:
		file_name_parts = df.split(get_option(options, "extension_separator"));
		if file_name_parts[-1] == get_option(options, "page_file_name"):
                        # add to current page
                        content = Content(page, df)

			# check extension options
			for option_name in file_name_parts[1:-1]:
		                if option_name == "nowiki":
				    wiki_parse = False
				elif option_name == "wiki":
				    wiki_parse = True
				elif option_name == "title":
				    show_item_title = True
				elif option_name == "notitle":
				     show_item_title = False
				elif option_name.isdigit():
					content.sort_order = int(option_name)

			content.parse_wiki = wiki_parse
			content.show_item_title = show_item_title
			content.show_item_title_date = show_item_title_date
                        page.addContent(content)
                else:
                        #print "FILEEXT: "+file_name_parts[-1]
                        dir_files2.append(df)
        dir_files = dir_files2
        dir_files2 = []


	# 
	# Read directories
	#
	for df in dir_files:
		if os.path.isdir(df):
			if verbosity >= 3:
				print "Reading page from directory: " + os.getcwd() + os.sep + df
			# stoppage checkage action
			#handle_dir = True
			#file_name_parts = df.split(get_option(options, "extension_separator"))
			#sort_order = -1
			#for fp in file_name_parts[1:]:
			#	if fp == "stop":
			#		if verbosity >= 2:
			#			print "Stop at dir: "+df
			#		handle_dir = False
			#	elif fp.isdigit():
			#		sort_order = int(fp)
			#if handle_dir:
			sub_page_orig_dir = os.getcwd()
			os.chdir(df)
			#print "Entering directory " + os.getcwd()
			child_page = build_page_tree(root_dir, df, options, macro_list, cur_depth+1)
			if child_page.is_subsite == False:
				child_page.parent = page
			#if child_page.sort_order >= 0:
			#	if sort_order >= 0:
			#		print "Warning, sort order for page '"+child_page.name+"' specified twice, taking order from directory name"
			#		child_page.sort_order = sort_order
			#else:
			#	child_page.sort_order = sort_order
			
			page.addChild(child_page)
				#create_pages(root_dir, in_dir, out_dir + os.sep + file_base_name(df), options, macro_list, cur_dir_depth + 1)
				#os.chdir(os.pardir)
			os.chdir(sub_page_orig_dir)
		else:
			dir_files2.append(df)
	dir_files = dir_files2
	dir_files2 = []

	#
	# Copy rest
	#
	for df in dir_files:
		file = File(df)
		page.addFile(file)

	return page

def print_usage():
	print "Usage: clcms.py [OPTIONS]"
	print "Options:"
    	print "-c or --write-config:\t\tprint the default options to stdout"
	print "-f or --force-output:\t\tforce creation of all pages even if their"
	print "\t\t\t\tsources are not changed"
	print "-h or --help:\t\t\tshow this help"
	print "-i or --inhibit-output\t\tinhibit creation for all pages"
	print "\t\t\t\t(ie. do a test run)"
    	print "-n or --no-macros\t\tdo not evaluate macros"
    	print "-m or --macro-names\t\tSurround macro expansions with the name names"
    	#print "-s <file>\t\t\tJust wiki-parse <file> and print output to\n\t\t\t\tstdout\n";
	print "-v <lvl> or --verbosity <lvl>\tset verbosity: 0 for no output, 5 for a lot"
	

#
#Initializer, argument parsing, and main loop call
# 

# parse arguments
if len(sys.argv) > 1:
    i = 1
    while i < len(sys.argv):
    #for arg in sys.argv[1:]:
    	arg = sys.argv[i]
    	if arg == "-c" or arg == "--write-config":
    		for l in system_options:
    			print l
		sys.exit(0)
	elif arg == "-f" or arg == "--force-output":
		force_output = True
	elif arg == "-h" or arg == "--help":
		print_usage()
		sys.exit(0)
	elif arg == "-i" or arg == "--inhibit-output":
		inhibit_output = True
    	elif arg == "-n" or arg == "--no-macros":
    		no_macros = True
    	elif arg == "-m" or arg == "--macro-names":
    		show_macro_names = True
	elif arg == "-v" or arg == "--verbosity":
		if (i < len(sys.argv)):
			i = i + 1
			verbosity = int(sys.argv[i])
		else:
			print "-v requires argument"
			sys.exit(1)
        else:
        	print "Unknown argument: "+arg
    	        sys.exit(1)
    	i = i + 1

# read setup in current dir
base_options = copy.deepcopy(system_options)

for df in os.listdir("."):
    file_name_parts = df.split(get_option(base_options, "extension_separator"))
    if file_name_parts[-1] == get_option(base_options, "setup_file_name"):
        #options.extend(file_lines(df, ['^[^#].* *= *.+']))
        if verbosity >= 2:
        	print "Found .setup file in current directory: "+df
        if not os.path.isdir(df):
            for o in file_lines(df, ['^[^#].* *= *.+']):
                base_options.insert(0, o.lstrip("\t ").rstrip("\n\r\t "))

# sanity checks on arguments
if inhibit_output and force_output:
	print "inhibit-output and force-output cannot be used at the same time. Aborting."
	sys.exit(1)

in_dir = get_option_dir(base_options, "in_dir")
root_dir = get_option_dir(base_options, "root_dir")
out_dir = get_option_dir(base_options, "out_dir")

if not os.path.isdir(in_dir):
	print "No such directory: " + in_dir
	sys.exit(1)
if verbosity >= 1:
	print "Content directory: " + in_dir
	if inhibit_output:
		print "Inhibiting output."
	else:
		print "Output directory: " + out_dir
os.chdir(in_dir)

# Read pages rfom input directory tree
site = build_page_tree(root_dir, "", base_options, system_macro_list, 0)

# Check sorting and updates
site.prepare(out_dir)

# Create output directory and HTML pages
if not inhibit_output:
	os.chdir(root_dir)
	if not os.path.isdir(out_dir) and not inhibit_output:
		os.mkdir(out_dir)
	site.createPage(out_dir, True)

if verbosity >= 5:
	site.printAll(2)
elif verbosity >= 2:
	site.printOverview()


