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

	# is invoked when the button is clicked.  It just prints a message.
	def button_clicked(self, widget, data=None):
		print "button %s clicked" % data
		if (data == "ok" and self.textfield.get_text() != ""):
			self.handle_image()
			self.next_image()
		else:
			print "no text, leave name"

	def show_image(self, image_file):
		pixbuf = gtk.gdk.pixbuf_new_from_file(image_file)
		orig_width = pixbuf.get_width()
		orig_height = pixbuf.get_height()
		print "width: ", orig_width, " height: ", orig_height
		new_width = 640
		new_height = orig_height / (orig_width / new_width)
		scaled_buf = pixbuf.scale_simple(new_width, new_height, gtk.gdk.INTERP_BILINEAR)
		self.image.set_from_pixbuf(scaled_buf)
		self.textfield.grab_focus()

	def next_image(self):
		self.cur_image_nr = self.cur_image_nr + 1
		self.show_image(self.image_files[self.cur_image_nr][0])
		self.textfield.set_text("")
		self.textfield.grab_focus()

	def delete_image(self):
		image_file = self.image_files[self.cur_image_nr][0]
		print "Delete " + image_file
		os.remove(image_file)
	
	def handle_image(self):
		old_file_name = self.image_files[self.cur_image_nr][0]
		new_file_name = str(self.cur_image_nr) + "." + self.textfield.get_text() +"." +self.image_files[self.cur_image_nr][2]
		print "Rename " + old_file_name + " to " + new_file_name
		os.rename(old_file_name, new_file_name)
		

	def __init__(self, image_files, start_nr):
		# create the main window, and attach delete_event signal to terminating
		# the application
		window = gtk.Window(gtk.WINDOW_TOPLEVEL)
		window.connect("delete_event", self.close_application)
		window.set_border_width(10)
		window.show()

		# a horizontal box to hold the buttons
		vbox = gtk.VBox()
		vbox.show()
		hbox = gtk.HBox()
		hbox.show()
		hbox2 = gtk.HBox()
		hbox2.show()
		vbox.add(hbox)
		vbox.add(hbox2)
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
		self.cur_image_nr = start_nr
		
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
		
		self.show_image(self.image_files[self.cur_image_nr][0])




root_dir = os.getcwd()

dir_files = os.listdir(".")

# output names are of the form <nr>.<name>.<ext>
done_file_p = re.compile("([0-9]+)\.(.*)\.([a-zA-Z]+)")
image_p = re.compile("(.*)\.([a-zA-Z]+)")

# image_files[] contains arrays of the form [filename, name, extension]
image_files = []
subdirs = []

cur_nr = 1

dir_files.sort()

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
			print "Found image file: " + name

			done_file_m = done_file_p.match(f)
			if done_file_m:
				# remember number

				if (done_file_m.group(1) >= cur_nr):
					cur_nr = cur_nr + 1
			else:
				imgf = []
				imgf.append(f)
				imgf.append(name)
				imgf.append(extension)
				image_files.append(imgf)

def main():
	gtk.main()
	return 0;

if __name__ == "__main__":
	ImageCaptioner(image_files, cur_nr)
	main();

				
				