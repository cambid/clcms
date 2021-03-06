#!/usr/bin/env python

import os
import shutil
import sys
import re

def wiki_to_new_simple(line):
    line = line.rstrip("\n\r\t ")
    if line == "":
        return "\n"
    line = line.replace("<", "<<")
    line = line.replace(">", ">>")
    if line[:5] == "   * ":
    	return "* "+ wiki_to_new_simple(line[5:])
    elif line[:8] == "      * ":
    	return "** "+ wiki_to_new_simple(line[8:])
    elif line[:11] == "         * ":
    	return "*** "+ wiki_to_new_simple(line[11:])
    elif line[:3] == "---":
	j = 3
	while line[j] == "+":
	    j += 1
	if (j > 3):
	    line = (j-3)*"=" + wiki_to_new_simple(line[j:]).rstrip("\n") + (j-3)*"="
	    line += "\n"
	    return line
    elif line[:1] == '*' and line[-1:] == '*' and line != "*":
        return "'''" + line[1:-1] + "'''\n"
    elif line[:1] == '.' and line[-1:] == '.' and line != ".":
        return "''" + line[1:-1] + "''\n"
    elif line[:1] == '=' and line[-1:] == '=' and line != "=":
        return "__" + line[1:-1] + "\n"

    img_p = re.compile('\{\{(.*?)\}\{(.*?)\}(?:\{(.*?)\})?\}')
    img_m = img_p.search(line)
    if img_m:
#        extra = ""
#        if img_m.group(2):
#        	extra = " " + line[img_m.start(3):img_m.end(3)]
        line = line[:img_m.start()] + "[[Image:" + line[img_m.start(1):img_m.end(1)] + "|" + line[img_m.start(2):img_m.end(2)] + "]]" + line[img_m.end():]
   
    return line + "\n"

def wiki_to_new(wiki_lines):
	new_lines = []
	no_wiki = False
	for l in wiki_lines:
		if l[:13] == "_NO_WIKI_END_":
			no_wiki = False
			new_lines.append(l)
		elif l[:9] == "_NO_WIKI_":
			no_wiki = True
			new_lines.append(l)
		elif not no_wiki:
			new_lines.append(wiki_to_new_simple(l))
		else:
			new_lines.append(l)
	return new_lines

def usage():
	print "Usage: convert_wiki_style.py [OPTIONS]"
	print "Replaces syntax in .page files in current directory and below from"
	print "clcms 0.4 and before by the syntax of 0.5"
	print ""
	print "For each .page file, a backup will be made called <file>.page.bak"
	print "You can then regenerate your site and check if the conversion worked"
	print "If so, run this program again with -d to delete the backup files"
	print ""
	print "Remember that the .bak files are not recognized by clcms and"
        print "therefore copied when you run it"
	print ""
	print "Options:"
	print "-c or --convert\tperform the actual conversion"
	print "-d or --delete\tdelete the backup files (if original run went well)"
	print "-r or --revert\trevert changes (backup files will be copied back"
	print "\t\tand deleted)"
	print "-h or --help\tshow this text"
	print ""



#
# command line arguments
#
delete = False
revert = False

if len(sys.argv) > 1:
    i = 1
    while i < len(sys.argv):
    #for arg in sys.argv[1:]:
    	arg = sys.argv[i]
    	if arg == "-c" or arg == "--convert":
    		print "Converting .page files"
    	elif arg == "-d" or arg == "--delete":
    		if revert:
    			print "delete and revert cannot both be specified"
    			sys.exit(2)
    		delete = True
    	elif arg == "-r" or arg == "--revert":
    		if delete:
    			print "delete and revert cannot both be specified"
    			sys.exit(2)
    		revert = True
	elif arg == "-h" or arg == "--help":
		usage()
		sys.exit(0)
	i += 1
else:
    usage()
    sys.exit(0)


if delete:
	#
	# find all .page.bak files in this dirtree
	# copy them to .page.bak
	# then translate to new wiki style and write to original .page file
	#
	page_file_list = []
	for root, dirs, files in os.walk("."):
		for f in files:
			if f[-5:] == ".page":
				if os.path.exists(os.path.join(root, f+".bak")):
					os.remove(os.path.join(root, f+".bak"))
elif revert:
	page_file_list = []
	for root, dirs, files in os.walk("."):
		for f in files:
			if f[-5:] == ".page":
				if os.path.exists(os.path.join(root, f+".bak")):
					shutil.copyfile(os.path.join(root, f+".bak"), os.path.join(root, f))
					shutil.copystat(os.path.join(root, f+".bak"), os.path.join(root, f))
					os.remove(os.path.join(root, f+".bak"))
else:
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
				if os.path.exists(bakfilename):
				    print "Error: "+bakfilename+" already exists. Use -r to revert or rename the conflicting file.\n";
				    sys.exit(9);
				shutil.copyfile(pagefilename, bakfilename)
				shutil.copystat(pagefilename, bakfilename)
				i_file = open(bakfilename, "r")
				o_lines = wiki_to_new(i_file.readlines())
				i_file.close()
				o_file = open(pagefilename, "w")
				for ol in o_lines:
					o_file.write(ol)
				o_file.close()
				shutil.copystat(bakfilename, pagefilename)



