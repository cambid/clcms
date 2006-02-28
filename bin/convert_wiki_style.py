#!/usr/bin/env python

import os
import shutil
import sys
import re

def wiki_to_new_simple(line):
    line = line.rstrip("\n\r\t ")
    if line == "":
        return "\n"
    if line[:1] == '*' and line[-1:] == '*' and line != "*":
        return "'''" + line[1:-1] + "'''\n"
    if line[:1] == '.' and line[-1:] == '.' and line != ".":
        return "''" + line[1:-1] + "''\n"
    if line[:1] == '=' and line[-1:] == '=' and line != "=":
        return " " + line[1:-1] + "\n"
    if line[:5] == "   * ":
    	return "* "+ wiki_to_new_simple(line[5:])
    if line[:8] == "      * ":
    	return "** "+ wiki_to_new_simple(line[8:])
    if line[:11] == "         * ":
    	return "*** "+ wiki_to_new_simple(line[11:])
    
    # replace links and image refs
#    adv_link_p = re.compile('\[\[(.*?)\]\[(.*?)\](?:\[(.*?)\])?\]')
#    img_p = re.compile('\{\{(.*?)\}\{(.*?)\}(?:\{(.*?)\})?\}')
#    adv_m = adv_link_p.search(line)
#    if adv_m:
#        name = line[adv_m.start(2):adv_m.end(2)]
#        href = escape_url(line[adv_m.start(1):adv_m.end(1)])
#        extra = ""
#        if len(adv_m.groups()) > 2:
#        	extra = " " + line[adv_m.start(3):adv_m.end(3)]
#        if href[0] == ':':
#        	targetPage = None
#        	if page:
#        		targetPage = page.getRootPage().findPageByID(href[1:])
#		if not targetPage:
#			print "Page with ID '"+href[1:]+"' not found. Quitting."
#			sys.exit(1)
#		if name == "":
#			name = targetPage.name
#		href = page.getBackDir() + targetPage.getTotalOutputDir() + "index.html"
#        line = line[:adv_m.start()] + "<a href=\"" + href + extra + "\">" + name + "</a>" + line[adv_m.end():]

#    img_m = img_p.search(line)
#    if img_m:
#        extra = ""
#        if img_m.group(2):
#        	extra = " " + line[img_m.start(3):img_m.end(3)]
#        line = line[:img_m.start()] + "<img src=\"" + escape_url(line[img_m.start(1):img_m.end(1)]) + "\" alt=\"" + line[img_m.start(2):img_m.end(2)] + "\"" + extra + "/>" + line[img_m.end():]
   
    return line + "\n"

def wiki_to_new(wiki_lines):
	new_lines = []
	for l in wiki_lines:
		new_lines.append(wiki_to_new_simple(l))
	return new_lines

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
# find all .page files in this dirtree
# copy them to .page.bak
# then translate to new wiki style and write to original .page file
#
page_file_list = []
for root, dirs, files in os.walk("."):
	for f in files:
		if f[-5:] == ".page":
			pagefilename = os.path.join(root, f)
			bakfilename = os.path.join(root, f+".bak")
			#shutil.copyfile(pagefilename, bakfilename)
			i_file = open(pagefilename, "r")
			o_lines = wiki_to_new(i_file.readlines())
			i_file.close()
			o_file = open(bakfilename, "w")
			for ol in o_lines:
				o_file.write(ol)
			o_file.close()

#print all_file_list


