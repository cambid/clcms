#!/usr/bin/env python

import os;
import os.path;

for root, dirs, files in os.walk("."):
	for f in files:
		if f[-5:] == ".page":
			#print f
			total_f = os.path.join(root, f);
			file_name_parts = f.split(".")
			page_name = file_name_parts[0]
			file_name_parts = file_name_parts[1:-1]
			
			sort_order = ""
			wiki_parse = ""
			show_title = ""
			show_menu= ""
			
			if len(file_name_parts) > 0:
				for option in file_name_parts:
					if option.isdigit():
						sort_order = option
					elif option == "nowiki":
						wiki_parse = "False"
					elif option == "wiki":
						wiki_parse = "True"
					elif option == "title":
						show_title = "True"
					elif option == "notitle":
						show_title = "False"
#					elif option == "menu":
#						show_menu = "True"
#					elif option == "nomenu":
#						show_menu = "True"
					#print option
					
					#
					# backup? nah
					#
	 
					i_file = open(total_f, "r")
					i_lines = i_file.readlines()
					i_file.close()
					
					o_file = open(os.path.join(root, page_name+".page"), "w")
					
					if sort_order and sort_order != "":
						o_file.write("attr: sort order "+sort_order+"\n")
					if wiki_parse and wiki_parse != "":
						o_file.write("attr: wiki "+wiki_parse+"\n")
					if show_title and show_title != "":
						o_file.write("attr: showtitle "+show_title+"\n")
#					if show_menu and show_menu != "":
#						o_file.write("attr: showmenu "+show_menu+"\n")
					
					o_file.write("\n\n")
					for il in i_lines:
						o_file.write(il)
					o_file.close()
					
				if page_name+".page" != f:
					os.remove(total_f)


				
				