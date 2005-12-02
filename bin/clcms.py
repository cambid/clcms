#!/usr/bin/python

import os
from os.path import join, getsize
import stat
import shutil
import time
import re
import sys

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

def wiki_to_html_simple(line):
    line = line.rstrip("\n\r\t ")
    if line[:1] == '*' and line[-1:] == '*':
        return "<b>" + line[1:-1] + "</b>\n"
    if line[:1] == '_' and line[-1:] == '_':
        return "<i>" + line[1:-1] + "</i>\n"
    if line[:1] == '=' and line[-1:] == '=':
        return "<pre>" + line[1:-1] + "</pre>\n"
    return line + "\n"

def wiki_to_html(wiki_lines):
    html_lines = []
    i = 0
    while i < len(wiki_lines):
        line = wiki_lines[i]
        if line[:3] == "---":
            j = 3
            while line[j] == "+":
                j += 1
            if (j > 3):
                html_lines.append("<h" + str(j-3) + ">" + wiki_to_html_simple(line[i:]) + "</h" + str(j-3) +  ">\n")
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
                                            else:
                                                html_lines.append("\t</li>\n")
                                                html_lines.append("</ul>\n")
                                                in_list3 = False
                                                i -= 1
                                        else:
                                            html_lines.append("\t</li>\n")
                                            html_lines.append("</ul>\n")
                                            in_list3 = False
                                else:
                                    html_lines.append("\t</li>\n")
                                    html_lines.append("</ul>\n")
                                    in_list2 = False
                                    i -= 1
                            else:
                                html_lines.append("\t</li>\n")
                                html_lines.append("</ul>\n")
                                in_list2 = False
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

def oldwiki_to_html(wiki_lines):
    html_lines = []
    
    in_p = False
    l_depth = 0
    cur_bullet_depth = 0;
    for line in wiki_lines:
        line = line.rstrip('\n\r\t ')
        # bold
        if line == "":
            while cur_bullet_depth > 0:
                html_lines.append("</ul>\n")
                cur_bullet_depth -= 1
            if not in_p:
                html_lines.append("<p>\n")
                in_p = True
            if l_depth == 1:
                html_lines.append("</li>\n")
                l_depth = 0
        if line[:1] == "*" and line[-1:] == "*":
            if (in_p):
                html_lines.append("</p>\n")
                in_p = False
            while cur_bullet_depth > 0:
                if l_depth == 1:
                    html_lines.append("</li>\n")
                    l_depth = 0
                html_lines.append("</ul>\n")
                cur_bullet_depth -= 1
            html_lines.append(" <b>" + line[1:-1] + "</b> \n")
        elif line[:1] == "_" and line[-1:] == "_":
            if (in_p):
                html_lines.append("</p>\n")
                in_p = False
            while cur_bullet_depth > 0:
                if in_l:
                    html_lines.append("</li>\n")
                    in_l = False
                html_lines.append("</ul>\n")
                cur_bullet_depth -= 1
            html_lines.append(" <i>" + line[1:-1] + "</i> \n")
        elif line[:1] == "=" and line[-1:] == "=":
            if (in_p):
                html_lines.append("</p>\n")
                in_p = False
            while cur_bullet_depth > 0:
                if in_l:
                    html_lines.append("</li>\n")
                    in_l = False
                html_lines.append("</ul>\n")
                cur_bullet_depth -= 1
            html_lines.append(" <pre>" + line[1:-1] + "</pre> \n")
        elif line[:4] == "   *":
            if (in_p):
                html_lines.append("</p>\n")
                in_p = False
            while cur_bullet_depth < 1:
                html_lines.append("<ul>\n")
                cur_bullet_depth += 1
            if in_l:
                html_lines.append("</li>\n")
            html_lines.append("<li>" + line[4:] + "\n")
            in_l = True
        elif line[:7] == "      *":
            if (in_p):
                html_lines.append("</p>\n")
                in_p = False
            while cur_bullet_depth < 2:
                html_lines.append("<ul>\n")
                cur_bullet_depth += 1
            html_lines.append("<li>" + line[7:] + "\n")
            in_l = True
        elif line[:10] == "         *":
            if (in_p):
                html_lines.append("</p>\n")
                in_p = False
            while cur_bullet_depth < 3:
                html_lines.append("<ul>\n")
                cur_bullet_depth += 1
            html_lines.append("<li>" + line[10:] + "\n")
            in_l = True
        elif line[:3] == "---":
            if (in_p):
                html_lines.append("</p>\n")
                in_p = False
            while cur_bullet_depth > 0:
                if in_l:
                    html_lines.append("</li>\n")
                    in_l = False
                html_lines.append("</ul>\n")
                cur_bullet_depth -= 1
            i = 3
            while line[i] == "+":
                i += 1
            if (i > 3):
                html_lines.append("<h" + str(i-3) + ">" + line[i:] + "</h" + str(i-3) +  ">\n")
            else:
                if not in_p:
                    html_lines.append("<p>\n")
                    in_p = True
                html_lines.append(line)
        else:
            if in_l:
                html_lines.append("</li>\n")
                in_l = False
            if (in_p):
                html_lines.append("</p>\n")
                in_p = False
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
        if in_l:
            html_lines.append("</li>\n")
            in_l = False
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
                    result = o[m.end():].split(',')
                    if result != [ '' ]:
                        return result
                    else:
                        return []
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
options = add_option(options, "show_menu = yes")
options = add_option(options, "show_submenu = yes")
options = add_option(options, "menu_depth = 1")
options = add_option(options, "menu_start_files = menu_start.inc")
options = add_option(options, "menu_end_files = menu_end.inc")
options = add_option(options, "menu_item1_start = menu_item_start.inc")
options = add_option(options, "menu_item1_end = menu_item_end.inc")
options = add_option(options, "setup_file_name = .*\\.setup")
options = add_option(options, "wiki_parse = yes")
options = add_option(options, "show_item_title = yes")
# this option matches page file names
# it is a regular expression. The value between the first set of 
# brackets will be removed when outputting to a html file
options = add_option(options, "page_file_name = .*(\\.page)")
options = add_option(options, "page_file_option_delimiter = .*(\..*?)\..*")
options = add_option(options, "ignore_masks = \\.\\\\*,DEADJOE")

#
# Utility functions
#

# if filter contain any re's, only lines matching any of them are
# returned. If filter is empty, all lines are returned
def file_lines(file, filters = []):
    lines = []
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

# generate the menu with the given directory as its base
# returns a list of html lines
# TODO: recursively descend paths, (don't forget ../ then)
# TODO: only add if there are .page files?
# what to do if it is an empty nonterminal?
def create_menu_part(root_dir, dir_prefix, base_dir, cur_depth, cur_page_depth, options):
    menu_lines = []
    
    ignore_masks = get_options(options, "ignore_masks")
    ignore_masks.append('.*\.nm.*')
    
    dir_files = get_dir_files(".", ignore_masks)
    
    for d in dir_files:
        if os.path.isdir(d):
            pagefiles = get_dir_files(d, get_options(options, "page_file_name"), True)
            item_inc = get_option(options, "menu_item" + str(cur_depth) + "_start")
            if item_inc != '':
                if item_inc[:1] != '/':
                    item_inc = root_dir + "/" + item_inc
                menu_lines.extend(file_lines(item_inc))
            if pagefiles != []:
                i = 0
                back_prefix = ""
                while i < cur_page_depth:
                    back_prefix += "../"
                    i += 1
                menu_lines.append("\t<a href=\"" + escape_url(back_prefix + dir_prefix + file_base_name(d)) + "/index.html\">\n")
            i = 0
            while i < cur_depth:
                menu_lines.append("\t")
                i += 1
            menu_lines.append(file_base_name(d) + "\n")
            if pagefiles != []:
                menu_lines.append("\t</a>\n")
                
            if cur_depth < int(get_option(options, "menu_depth")):
                os.chdir(d)
                menu_lines.extend(create_menu_part(root_dir, dir_prefix + file_base_name(d) + "/", base_dir, cur_depth + 1, cur_page_depth, options))
                os.chdir("..")
            item_inc = get_option(options, "menu_item" + str(cur_depth) + "_end")
            if item_inc != '':
                if item_inc[:1] != '/':
                    item_inc = root_dir + "/" + item_inc
                menu_lines.extend(file_lines(item_inc))
                
    return menu_lines

def create_menu(root_dir, base_dir, options, cur_page_depth):
    orig_dir = os.getcwd()
    os.chdir(base_dir)
    menu_lines = []
    for hf in get_options(options, "menu_start_files"):
        if hf[:1] != '/':
            hf = root_dir + '/' + hf
        menu_lines.extend(file_lines(hf))
    menu_lines.extend(create_menu_part(root_dir, "", base_dir, 1, cur_page_depth, options))
    for hf in get_options(options, "menu_end_files"):
        if hf[:1] != '/':
            hf = root_dir + '/' + hf
        menu_lines.extend(file_lines(hf))
    os.chdir(orig_dir)
    return menu_lines
    

def origcreate_menu(root_dir, base_dir, options):
    ignore_masks = get_options(options, "ignore_masks")
    ignore_masks.append('.*\.nm.*')
    menu_lines = []
    menu_lines.extend(file_lines(root_dir + "/menu_start.inc"))
    first = True;
    menu_depth = int(get_option(options, "menu_depth"))
    for file in get_dir_files(base_dir, ignore_masks):
       #print "FILE: "+file
        if not first:
            menu_lines.extend(file_lines(root_dir + "/menu_item.inc"))
        else:
            first = False
        menu_lines.append("<a href=\"../" + escape_url(file_base_name(file)) + "/index.html\">" + file_base_name(file) + "</a>")
    menu_lines.extend(file_lines(root_dir + "/menu_end.inc"))
    return menu_lines



def create_page(root_dir, in_dir, out_dir, page_name, page_files, options, cur_dir_depth):
    # Should this be here or in the calling function (create_pages())?
    page_lines = []
    last_modified = os.stat(in_dir)[stat.ST_MTIME]

    
    # specific page options are stored in the file name between the dots
    extension_p = re.compile(get_option(options, "page_file_name"))
    dots_p = re.compile(get_option(options, "page_file_option_delimiter"))
    wiki_parse = False
    show_menu = False
    show_submenu = False
    show_item_title = False
    if get_option(options, "show_menu") == 'yes':
        show_menu = True
    if get_option(options, "show_submenu") == 'yes':
        show_submenu = True

    # header
    for hf in get_options(options, "header_files"):
        page_lines.extend(file_lines(root_dir + "/" + hf))

    # submenu
    # TODO: macro's etc.
    if show_submenu and len(page_files) > 1:
        page_lines.append("<div id=\"submenu\">\n")
        first = True
        for pf in page_files:
            if pf.find(".nosubmenu") < 0:
                if not first:
                    page_lines.append("<hr noshade=\"noshade\" size=\"1\" width=\"80%\" align=\"left\" />\n")
                else:
                    first = False
                page_lines.append("<a href=\"#" + escape_url(file_base_name(pf)) + "\">" + file_base_name(pf) + "</a>\n")
        page_lines.append("</div>\n")
    
    page_lines.append("<div id=\"content\">\n")

    # handle the .page items
    item_index = 1
    for pf_orig in page_files:
        wiki_parse = get_option(options, "wiki_parse") == 'yes'
        show_item_title = get_option(options, "show_item_title") == 'yes'

        pf = pf_orig
        dots_m = dots_p.match(pf)
        if dots_m:
            while dots_m:
                # handle option
                option_name = pf[dots_m.start(1):dots_m.end(1)]
                if option_name == ".nowiki":
                    wiki_parse = False
                elif option_name == ".wiki":
                    wiki_parse = True
                elif option_name == ".title":
                    show_item_title = True
                elif option_name == ".notitle":
                     show_item_title = False
                pf = pf[:dots_m.start(1)] + pf[dots_m.end(1):]
                dots_m = dots_p.match(pf)
        extension_m = extension_p.match(pf)
        if not extension_m:
            print "ERROR: Conflict in options:"
            print "page_file_name = " + get_option(options, "page_file_name")
            print "page_file_option_delimiter = " + get_option(options, "page_file_option_delimiter")
        else:
            # TODO: Macro
            # TODO: is this match necessary? file_base_name()?
            if item_index > 1:
                page_lines.append("<hr noshade=\"noshade\" size=\"3\" width=\"60%\" align=\"left\" />\n")
            pf = pf[:extension_m.start(1)]
            pf_lines = []
            if show_item_title:
                pf_lines.append("<h3>" + pf + "</h3>\n")
            pf_lines.extend(file_lines(pf_orig))
            if wiki_parse:
                pf_lines = wiki_to_html(pf_lines)
            page_lines.append("<a name=\"" + escape_url(file_base_name(pf)) + "\"></a>\n")
            page_lines.extend(pf_lines)
            if os.stat(in_dir)[stat.ST_MTIME] > last_modified:
                last_modified = os.stat(in_dir)[stat.ST_MTIME]
            item_index += 1
            
    page_lines.append("</div>\n")

    # footer
    for hf in get_options(options, "footer_files"):
        page_lines.extend(file_lines(root_dir + "/" + hf))

    # create dir and file
    if not os.path.isdir(out_dir):
        os.mkdir(out_dir)
    
    # TODO: Macro
    # TODO: Macro
    # TODO: Macro
    lines = page_lines
    lines2 = []
    for l in lines:
        l_p = re.compile("_DATE_FILE_")
        l_m = l_p.search(l)
        if l_m:
            lines2.append(l[:l_m.start()] + time.strftime("%Y-%m-%d", time.gmtime(last_modified)) + l[l_m.end():])
        else:
            lines2.append(l)
    lines = lines2
    lines2 = []
    for l in lines:
        l_p = re.compile("_DATE_")
        l_m = l_p.search(l)
        if l_m:
            lines2.append(l[:l_m.start()] + time.strftime("%Y-%m-%d") + l[l_m.end():])
        else:
            lines2.append(l)
    lines = lines2
    lines2 = []
    for l in lines:
        l_p = re.compile("_MENU_")
        l_m = l_p.search(l)
        if l_m:
            if get_option(options, "show_menu") == 'yes':
                for ml in create_menu(root_dir, in_dir, options, cur_dir_depth):
                    lines2.append(ml)
            else:
                lines2.append(l[:l_m.start()] + l[l_m.end():])
        else:
            lines2.append(l)
    lines = lines2
    lines2 = []
    for l in lines:
        l_p = re.compile("_TITLE_")
        l_m = l_p.search(l)
        if l_m:
            lines2.append(l[:l_m.start()] + page_name + l[l_m.end():])
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
            while i < cur_dir_depth:
                style_sheet_loc += "../"
                i += 1
            style_sheet_loc += get_option(options, "style_sheet")
            lines2.append(l[:l_m.start()] + style_sheet_loc + l[l_m.end():])
        else:
            lines2.append(l)
    lines = lines2
    lines2 = []

    page_lines = lines
    #
    # TODO Macro end
    #

    out_file = open(out_dir + "/index.html", "w")
    out_file.writelines(page_lines)
    out_file.close()
    #print "[CLCMS] Created " + out_dir + "/index.html"


def create_pages(root_dir, in_dir, out_dir, options, cur_dir_depth):
    out_dir = escape_url(out_dir)
    if not os.path.isdir(out_dir):
        os.mkdir(out_dir)
    
    dir_files = get_dir_files(".", get_options(options, "ignore_masks"))
    # store every file that has not been handled yet in a temp list
    # (removing elements from a list you're iterating over is a bad idea
    dir_files2 = []

    #
    # Read setup files
    setup_p = re.compile(get_option(options, "setup_file_name"))
    for df in dir_files:
        setup_m = setup_p.match(df)
        if setup_m:
            #options.extend(file_lines(df, ['^[^#].* *= *.+']))
            for o in file_lines(df, ['^[^#].* *= *.+']):
            	options.insert(0, o.lstrip("\t ").rstrip("\n\r\t "))
        else:
            dir_files2.append(df)
    dir_files = dir_files2
    dir_files2 = []
    
    #
    # Read page files
    #print "po: "+get_option(options, "page_file_name")
    page_p = re.compile(get_option(options, "page_file_name"))
    page_files = []
    for df in dir_files:
        page_m = page_p.search(df)
        if page_m:
            page_files.append(df)
        else:
            dir_files2.append(df)
    dir_files = dir_files2
    dir_files2 = []

    if page_files != []:
        # TODO: dotted page options here? (like in .page file names?)
        page_name = file_base_name(os.path.basename(out_dir))
        create_page(root_dir, in_dir, out_dir, page_name, page_files, options, cur_dir_depth)

    # 
    # Read directories
    for df in dir_files:
        if os.path.isdir(df):
            os.chdir(df)
            create_pages(root_dir, in_dir, out_dir + "/" + file_base_name(df), options, cur_dir_depth + 1)
            os.chdir("..")
        else:
            dir_files2.append(df)
    dir_files = dir_files2
    dir_files2 = []

    #
    # Copy rest
    for df in dir_files:
        shutil.copy(df, out_dir)
        #print "[CLCMS] Copied " + df + " to " + out_dir
    

#
#Initializer, argument parsing, and main loop call
# 

# read setup in current dir
setup_p = re.compile(get_option(options, "setup_file_name"))
for df in os.listdir("."):
    setup_m = setup_p.match(df)
    if setup_m:
        #options.extend(file_lines(df, ['^[^#].* *= *.+']))
        for o in file_lines(df, ['^[^#].* *= *.+']):
            options.insert(0, o.lstrip("\t ").rstrip("\n\r\t "))

# parse arguments
if len(sys.argv) > 1:
    for arg in sys.argv[1:]:
    	if arg == "-c" or arg == "--write-config":
    		for l in options:
    			print l
		sys.exit(0)
    else:
    	print "Unknown argument: "+arg
    	sys.exit(1)

in_dir = get_option(options, "in_dir")
if in_dir[:1] != "/":
    in_dir = os.getcwd() + "/" + in_dir
root_dir = get_option(options, "root_dir")
if root_dir[:1] != "/":
    root_dir = os.getcwd() + "/" + root_dir
out_dir = get_option(options, "out_dir")
if out_dir[:1] != "/":
    out_dir = os.getcwd() + "/" + out_dir
if not os.path.isdir(out_dir):
    os.mkdir(out_dir)

if not os.path.isdir(in_dir):
	print "No such directory: " + in_dir
	sys.exit(1)
os.chdir(in_dir)
create_pages(root_dir, in_dir, out_dir, options, 0)
os.chdir(root_dir)

