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
	
	def set_cur_image_done(self, done):
		self.image_files[self.cur_image_nr][3] = done
	
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
		new_width = orig_width
		new_height = orig_height
		if orig_width > 640:
			new_width = 640
			new_height = orig_height / ((orig_width / new_width) + 1)
		if orig_height > 640:
			new_height = 640
			new_widht = orig_width / ((orig_height / new_height) + 1)
		scaled_buf = pixbuf.scale_simple(new_width, new_height, gtk.gdk.INTERP_BILINEAR)
		self.image.set_from_pixbuf(scaled_buf)
		self.textfield.grab_focus()
		self.textfield.set_text(self.cur_image_name())
		self.textfield.select_region(0, len(self.textfield.get_text()))
		if (self.cur_image_nr == 0):
			self.first_button.set_sensitive(False)
			self.prev_button.set_sensitive(False)
		else:
			self.first_button.set_sensitive(True)
			self.prev_button.set_sensitive(True)
		if (self.cur_image_nr == len(self.image_files) - 1):
			self.last_button.set_sensitive(False)
			self.next_button.set_sensitive(False)
		else:
			self.last_button.set_sensitive(True)
			self.next_button.set_sensitive(True)

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
		self.set_cur_image_done(True)
		

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
		hbox_image = gtk.HBox()
		hbox_image.show()
		hbox_commands = gtk.HBox()
		hbox_commands.show()
		hbox_nav = gtk.HBox()
		hbox_nav.show()
		hbox_status = gtk.HBox()
		hbox_status.show()
		vbox.pack_start(hbox_status, False, False, 0)
		vbox.pack_start(hbox_nav, False, False, 0)
		vbox.pack_start(hbox_commands, False, False, 0)
		vbox.pack_start(hbox_image, False, False, 0)
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
		hbox_image.pack_start(button)
		button.connect("clicked", self.button_clicked, "next")
		
		self.textfield = gtk.Entry()
		self.textfield.show()
		self.textfield.set_activates_default(1)
		hbox_commands.pack_start(self.textfield)


		button = gtk.Button()
		button.set_label("Ok")
		button.show();
		hbox_commands.pack_start(button)
		button.connect("clicked", self.button_clicked, "ok")
#		button.connect("activate", self.button_clicked, "ok a")
		button.set_flags(gtk.CAN_DEFAULT)
		window.set_default(button)

		button = gtk.Button(label = "_Delete", use_underline = True)
		button.show();
		hbox_commands.pack_start(button)
		button.connect("clicked", self.button_clicked, "delete")
		
		button = gtk.Button(label = "_Quit", use_underline = True)
		button.show();
		hbox_commands.pack_start(button)
		button.connect("clicked", self.button_clicked, "quit")
		
		label = gtk.Label('')
		label.set_markup("Navigate:")
		hbox_nav.pack_start(label, False, False, 1)

		self.first_button = gtk.Button(label = "_First", use_underline = True)
		self.first_button.show();
		hbox_nav.pack_start(self.first_button)
		self.first_button.connect("clicked", self.button_clicked, "first")
		
		self.prev_button = gtk.Button(label = "_Prev", use_underline = True)
		self.prev_button.show();
		hbox_nav.pack_start(self.prev_button)
		self.prev_button.connect("clicked", self.button_clicked, "previous")
		
		self.next_button = gtk.Button(label = "_Next", use_underline = True)
		self.next_button.show();
		hbox_nav.pack_start(self.next_button)
		self.next_button.connect("clicked", self.button_clicked, "next")
		
		self.last_button = gtk.Button(label = "_Last", use_underline = True)
		self.last_button.show();
		hbox_nav.pack_start(self.last_button)
		self.last_button.connect("clicked", self.button_clicked, "last")
		
		button = gtk.Button(label = "_Skip done", use_underline = True)
		button.show();
		hbox_nav.pack_start(button)
		button.connect("clicked", self.button_clicked, "skip")
		
		self.top_label = gtk.Label()
		self.top_label.set_text("Image 0 of " + str(len(image_files)))
		hbox_status.pack_start(self.top_label)

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
		name = image_m.group(1)
		extension = image_m.group(2)
		if (extension == "jpg" or
		    extension == "JPG" or
		    extension == "png" or
		    extension == "PNG"):
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

if len(image_files) == 0:
	print "No images found in current working directory"
	exit()

def main():
	gtk.main()
	return 0;

if __name__ == "__main__":
	ImageCaptioner(image_files)
	main();

				
				