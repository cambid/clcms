#!/usr/bin/env python

import os
from os.path import join, getsize
import stat
import shutil
import re
import pygtk
import gtk

class ImageCaptioner:
	# when invoked (via signal delete_event), terminates the application.
	def close_application(self, widget, event, data=None):
		gtk.main_quit()
		return False

	def button_clicked(self, widget, data=None):
		if (data == "ok" and self.textfield.get_text() != ""):
			self.handle_image()
			self.next_image()
		elif (data == "first"):
			self.first_image()
		elif (data == "previous"):
			self.prev_image()
		elif (data == "next"):
			self.next_image()
		elif (data == "last"):
			self.last_image()
		elif (data == "skip"):
			self.skip_done()
		elif (data == "delete"):
			self.delete_image()
		elif (data == "quit"):
			self.close_application(widget, None)
		else:
			print "unknown event"


	def cur_image_file(self):
		return self.image_files[self.cur_image_nr][0]
	
	def set_cur_image_file(self, file):
		self.image_files[self.cur_image_nr][0] = file
	
	def cur_image_name(self):
		return self.image_files[self.cur_image_nr][1]
	
	def set_cur_image_name(self, name):
		self.image_files[self.cur_image_nr][1] = name  
	
	def cur_image_extension(self):
		return self.image_files[self.cur_image_nr][2]
	
	def cur_image_done(self):
		return self.image_files[self.cur_image_nr][3]
	
	def skip_done(self):
		while ((self.cur_image_done()) and self.cur_image_nr < len(self.image_files) - 1):
			self.cur_image_nr = self.cur_image_nr + 1
		self.show_image(self.cur_image_file())

	def first_image(self):
		self.cur_image_nr = 0
		self.show_image(self.cur_image_file())

	def last_image(self):
		self.cur_image_nr = len(self.image_files) - 1
		self.show_image(self.cur_image_file())

	def show_image(self, image_file):
		pixbuf = gtk.gdk.pixbuf_new_from_file(image_file)
		orig_width = pixbuf.get_width()
		orig_height = pixbuf.get_height()
		new_width = 640
		new_height = orig_height / (orig_width / new_width)
		scaled_buf = pixbuf.scale_simple(new_width, new_height, gtk.gdk.INTERP_BILINEAR)
		self.image.set_from_pixbuf(scaled_buf)
		self.textfield.grab_focus()
		self.textfield.set_text(self.cur_image_name())
		self.textfield.select_region(0, len(self.textfield.get_text()))
		if (self.cur_image_nr == 0):
			self.first_button.set_sensitive(False)
		else:
			self.first_button.set_sensitive(True)
		if (self.cur_image_nr == len(self.image_files) - 1):
			self.last_button.set_sensitive(False)
		else:
			self.last_button.set_sensitive(True)

	def prev_image(self):
		if (self.cur_image_nr > 0):
			self.cur_image_nr = self.cur_image_nr - 1
			self.show_image(self.cur_image_file())
	
	def next_image(self):
		if (self.cur_image_nr < len(self.image_files) - 1):
			self.cur_image_nr = self.cur_image_nr + 1
			self.show_image(self.cur_image_file())

	def delete_image(self):
		image_file = self.cur_image_file()
		print "Delete " + image_file
		os.remove(image_file)
		self.image_files.remove(self.image_files[self.cur_image_nr])
		self.show_image(self.cur_image_file())
	
	def handle_image(self):
		old_file_name = self.cur_image_file()
		new_file_name = str(self.cur_image_nr + 1) + "." + self.textfield.get_text() +"." + self.cur_image_extension()
		print "Rename " + old_file_name + " to " + new_file_name
		os.rename(old_file_name, new_file_name)
		self.set_cur_image_file(new_file_name)
		self.set_cur_image_name(self.textfield.get_text())
		
		

	def __init__(self, image_files):
		# create the main window, and attach delete_event signal to terminating
		# the application
		window = gtk.Window(gtk.WINDOW_TOPLEVEL)
		window.connect("delete_event", self.close_application)
		window.set_border_width(10)
		window.show()

		# a horizontal box to hold the buttons
		vbox = gtk.VBox(False, 10)
		vbox.show()
		hbox = gtk.HBox()
		hbox.show()
		hbox2 = gtk.HBox()
		hbox2.show()
		hbox3 = gtk.HBox()
		hbox3.show()
		vbox.add(hbox)
		vbox.add(hbox2)
		vbox.add(hbox3)
		window.add(vbox)
		

#		pixbufanim = gtk.gdk.PixbufAnimation("goalie.gif")
#		image = gtk.Image()
#		image.set_from_animation(pixbufanim)
#		image.show()
		# a button to contain the image widget
#		button = gtk.Button()
#		button.add(image)
#		button.show()
#		hbox.pack_start(button)
#		button.connect("clicked", self.button_clicked, "1")

		# create several images with data from files and load images into
		# buttons
#		image = gtk.Image()
#		image.set_from_file("apple-red.png")
#		image.show()
		# a button to contain the image widget
#		button = gtk.Button()
#		button.add(image)
#		button.show()
#		hbox.pack_start(button)
#		button.connect("clicked", self.button_clicked, "2")

#		image = gtk.Image()
#		image.set_from_file("chaos.jpg")
#		image.show()
		# a button to contain the image widget
#		button = gtk.Button()
#		button.add(image)
#		button.show()
#		hbox.pack_start(button)
#		button.connect("clicked", self.button_clicked, "3")

#		image = gtk.Image()
#		image.set_from_file("important.tif")
#		image.show()
		# a button to contain the image widget
#		button = gtk.Button()
#		button.add(image)
#		button.show()
#		hbox.pack_start(button)
#		button.connect("clicked", self.button_clicked, "4")
		self.image_files = image_files
		self.cur_image_nr = 0
		
		self.image = gtk.Image()
		self.image.show()

		# a button to contain the image widget
		button = gtk.Button()
		button.add(self.image)
		button.show()
		hbox.pack_start(button)
		button.connect("clicked", self.button_clicked, "ok")
		
		self.textfield = gtk.Entry()
		self.textfield.show()
		self.textfield.set_activates_default(1)
		hbox2.pack_start(self.textfield)


		button = gtk.Button()
		button.set_label("Ok")
		button.show();
		hbox2.pack_start(button)
		button.connect("clicked", self.button_clicked, "ok")
#		button.connect("activate", self.button_clicked, "ok a")
		button.set_flags(gtk.CAN_DEFAULT)
		window.set_default(button)

		button = gtk.Button()
		button.set_label("Delete")
		button.show();
		hbox2.pack_start(button)
		button.connect("clicked", self.button_clicked, "delete")
		
		button = gtk.Button()
		button.set_label("Quit")
		button.show();
		hbox2.pack_start(button)
		button.connect("clicked", self.button_clicked, "quit")
		
		label = gtk.Label()
		label.set_text("Navigate:")
		hbox3.pack_start(label)

		self.first_button = gtk.Button()
		self.first_button.set_label("First")
		self.first_button.show();
		hbox3.pack_start(self.first_button)
		self.first_button.connect("clicked", self.button_clicked, "first")
		
		button = gtk.Button()
		button.set_label("Prev")
		button.show();
		hbox3.pack_start(button)
		button.connect("clicked", self.button_clicked, "previous")
		
		button = gtk.Button()
		button.set_label("Next")
		button.show();
		hbox3.pack_start(button)
		button.connect("clicked", self.button_clicked, "next")
		
		self.last_button = gtk.Button()
		self.last_button.set_label("Last")
		self.last_button.show();
		hbox3.pack_start(self.last_button)
		self.last_button.connect("clicked", self.button_clicked, "last")
		
		button = gtk.Button()
		button.set_label("Skip done")
		button.show();
		hbox3.pack_start(button)
		button.connect("clicked", self.button_clicked, "skip")
		
		self.show_image(self.cur_image_file())




root_dir = os.getcwd()

dir_files = os.listdir(".")

# output names are of the form <nr>.<name>.<ext>
done_file_p = re.compile("([0-9]+)\.(.*)\.([a-zA-Z]+)")
image_p = re.compile("(.*)\.([a-zA-Z]+)")

# image_files[] contains arrays of the form [filename, name, extension]
image_files = []
subdirs = []

dir_files.sort()

for f in dir_files:
	image_m = image_p.match(f)
	if image_m:
		image_files.append(["empty", "empty", "empty", False])

for f in dir_files:
	image_m = image_p.match(f)
	if image_m:
		name = image_m.group(1)
		extension = image_m.group(2)
		if (extension == "jpg" or
		    extension == "JPG" or
		    extension == "png" or
		    extension == "PNG"):

			# remember number
			done_file_m = done_file_p.match(f)
			if done_file_m:
				# remember number

				#if (done_file_m.group(1) >= cur_nr):
					#cur_nr = cur_nr + 1
				nr = int(done_file_m.group(1))
				name = done_file_m.group(2)
				extension = done_file_m.group(3)
				imgf = []
				imgf.append(f)
				imgf.append(name)
				imgf.append(extension)
				imgf.append(True)
				image_files[nr - 1] = imgf
				
			else:
				# find first empty
				i = 0
				while (image_files[i][0] != "empty"):
					i = i + 1
				
				imgf = []
				imgf.append(f)
				imgf.append(name)
				imgf.append(extension)
				imgf.append(False)
				image_files[i] = imgf

def main():
	gtk.main()
	return 0;

if __name__ == "__main__":
	ImageCaptioner(image_files)
	main();

				
				