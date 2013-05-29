#!/usr/bin/python
# Htsnapp - create snapshots of websites from urls, nmap xml, and txr files.
# Author - Nikhil 'Nix' Sreekumar
# Contact: nik@pentest.7safe.com
# Supports urls, files with urls, and nmap.xml files

# Primary source for screenshot code: 
# PyWebShot - create webpage thumbnails. Originally based on 
# http://burtonini.com/computing/screenshot-tng.py
# Ben Dowling - http://www.coderholic.com

# License:
# HTsnapp is licensed under the GNU-General Public License version 3 and later.
# Please visit http://www.gnu.org/copyleft/gpl.html for more information

import urlparse
import os
import sys

try:
	import gtk
	from optparse import OptionParser
	import xml.dom.minidom as xmll
	import gtk.gdk as gdk
	import gobject
	import gtkmozembed
except ImportError:
	print "Required modules are not installed. Please run with '-i or --install' with root privs"

class PyWebShot:
	def __init__(self, urls, screen, thumbnail, delay, outfile, location):
		self.parent = gtk.Window(gtk.WINDOW_TOPLEVEL)
		self.parent.set_border_width(10)
		self.urls = urls
		self.delay = delay
		self.location = location
		
		# Get resoltion information
		(x,y) = screen.split('x')
		x = int(x)
		y = int(y)
		(t_x, t_y) = thumbnail.split('x')
		t_x = int(t_x)
		t_y = int(t_y)

		# Calculate the x scale factor
		scale_x = float(t_x) / x
		scale_y = float(t_y) / y
		
		self.t_x = t_x
		self.t_y = t_y
		self.scale = scale_x

		self.widget = gtkmozembed.MozEmbed()
		self.widget.set_size_request(x + 18, y)

		# Connect signal
		self.widget.connect("net_stop", self.on_net_stop)
		if outfile:
			(self.outfile_base, ignore) = outfile.split('.png')
		else:
			self.outfile_base = None
		self.parent.add(self.widget)
		self.url_num = 0
		self.load_next_url()
		self.parent.show_all()

	def load_next_url(self):
		#print len(self.urls)
		#print self.url_num
		
		if self.url_num > len(self.urls) - 1:
			gtk.main_quit()
			return
		self.current_url = self.urls[self.url_num]
		self.countdown = self.delay
		print "Loading " + self.current_url + "..." 
		self.url_num += 1
		self.widget.load_url(self.current_url)
	
	def on_net_stop(self, data = None):
		if self.delay > 0: gobject.timeout_add(1500,self.do_countdown,self)
		else: self.do_countdown()

	def do_countdown(self, data = None):
		self.countdown -= 1
		if(self.countdown > 0):
			return True
		else:
			self.screenshot()
			self.load_next_url()
			return False
	
	def screenshot(self, data = None):
		window = self.widget.window
		(x,y,width,height,depth) = window.get_geometry()

		width -= 16

		pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB,False,8,width,height)
		pixbuf.get_from_drawable(window,self.widget.get_colormap(),0,0,0,0,width,height)
		thumbnail = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB,False,8,self.t_x,self.t_y)
		pixbuf.scale(thumbnail, 0, 0, self.t_x, self.t_y, 0, 0, self.scale, self.scale, gdk.INTERP_HYPER)
		if self.outfile_base:
			if len(self.urls) == 1:
				filename = "%s.png" % (self.outfile_base)
			else:
				filename = "%s-%d.png" % (self.outfile_base, self.url_num)
		else:
			parts = urlparse.urlsplit(self.current_url)
			
			if ':' in parts.netloc:			# replace : in netlocation to _ for filename support		
				parts.netloc = parts.netloc.replace(':', '_')
				
			filename = parts.netloc + parts.path.replace('/', '.') + ".png"
		os.chdir(self.location)
		thumbnail.save(filename,"png")
		print "saved as " + filename
		return True
	
def __windowExit(widget, data=None):
	gtk.main_quit()
	
class HtSnapp(PyWebShot):
	def __init__(self, option):
		# Process input received from user
		
		# options.screen 	- 		Screen resolution
		# options.thumbnail	- 		Thumbnail size
		# options.delay 	- 		Delay for page load
		# options.filename 	- 		Output filename. Default is by hostname
		# options.xml 		- 		Nmap XML file
		# options.note 		- 		File input with hosts
		# options.url 		- 		URL or URLs (separated by comma)
		# options.location	-		Directory location to save all the files
		
		print '''++++++++++++ Htsnapp (beta):: by Nikhil 'roo7break' Sreekumar ++++++++++++
		contact: nik@pentest.7safe.com
		'''
			
		option = option[0]
		self.max_pro = 5		#	Max mumber of processes
		
		if option.instal:
			if self.installation():
				print 'Installation complete'
			else:
				print 'Some error occured during installation.'
				sys.exit(1)
				
		if not os.path.exists(option.location):
			os.makedirs(option.location)
		if option.xml:			# If there is value in XML
			nurl = self.nmapparser(option.xml)
			if PyWebShot.__init__(self,urls=nurl, screen=option.screen, thumbnail=option.thumbnail, delay=option.delay, outfile=option.filename, location=option.location):
				print "All done with xml"
			else:
				print "Something went wrong"
		elif option.note:		# If there is value in file
			lurl = self.fileparse(option.note)
			if PyWebShot.__init__(self,urls=lurl, screen=option.screen, thumbnail=option.thumbnail, delay=option.delay, outfile=option.filename, location=option.location):
				print "All done with files"
			else:
				print "Something went wrong"
		else:
			if PyWebShot.__init__(self,urls=option.url, screen=option.screen, thumbnail=option.thumbnail, delay=option.delay, outfile=option.filename, location=option.location):
				print "All done with urls"
			else:
				print "Something went wrong"
			
	def installation(self):
		print "Installing WebKit libraries"
		os.system('sudo apt-get install python-webkit')
		print "------ Done ------"
		print "Installing XML libraries"
		os.system('sudo apt-get install python-libxml2')
		print "------ Done ------"
		print "Installing Embedded GTK libraries.."
		os.system('sudo apt-get install python-gtkmozembed')
		print "------ Done ------"
	
	def nmapparser(self, fxml):
		# Parse nmap xml for targets (http service)
		try:
			fp = xmll.parse(fxml)
			
		except Exception,e:
			print "Error ", e
			return []
		listt = []
			
		for hst in fp.getElementsByTagName('host'):
			for prt in hst.getElementsByTagName('port'):
				port = prt.getAttributeNode('portid').value
				for info in hst.getElementsByTagName('address'):
					typee = info.getAttributeNode('addrtype').value
					if typee == 'ipv4':
						ip = info.getAttributeNode('addr').value
				
				for ser in prt.getElementsByTagName('service'):
					if 'http' in ser.getAttributeNode('name').value:
						if port == '80':
							listt.append(ip)
						elif port == '443':
							listt.append('https://' + ip)
						else:
							listt.append(ip + ":" + port)
		return listt
	
	def fileparse(self, files):
		# Read file for targets in format ipaddress:port
		fl = open(files, 'r')
		listt = []
		for target in fl.readlines():
			target = target.strip('\n')
			if ":" in target:
				if target.split(":")[1] == '443':
					listt.append('https://' + target)
				else:
					listt.append(target)
			else:
				listt.append(target)
		return listt
	
if __name__ == "__main__":
	
	parser = OptionParser(version='htsnapp v0.2', description = '''++++++++++++ Htsnapp (beta):: by Nikhil 'roo7break' Sreekumar ++++++++++++''')
	parser.add_option('-s', dest = 'screen', action='store', type='string', help='Screen resolution at which to capture the webpage (default %default)', default="1024x769")
	parser.add_option('-t', dest = 'thumbnail', action='store', type='string', help='Thumbnail resolution (default %default)', default="350x200")
	parser.add_option('-d', dest = 'delay', action='store', type='int', help='Delay in seconds to wait after page load before taking the screenshot (default %default)', default=0)
	parser.add_option('-f', dest = 'filename', action='store', type='string', help='PNG output filename with .png extension, otherwise default is based on url name and given a .png extension')
	parser.add_option('-x', dest = 'xml', action='store', type='string', help='Nmap XML file to parse', default='')
	parser.add_option('-r', dest = 'range', action='store', type='string', help='IP range to sweep. Provide port number', default='')
	parser.add_option('-p', dest = 'port', action='store', type='string', help='Port number to sweep on range', default='80')
	parser.add_option('-n', dest = 'note', action='store', type='string', help='File with targets:port', default='')
	parser.add_option('-u', dest = 'url', action='store', type='string', help='Provide single url or mulitple urls (separated by comma. no spaces.)', default='')
	parser.add_option('-l', dest = 'location', action='store', type='string', help='Directory location to save files', default=os.getcwd())
	parser.add_option('-i', dest = 'instal', action='store_true', help='Install required dependencies')
	options = parser.parse_args()
	temp = []
	if options[0].url:
		temp = options[0].url.split(',')
	options[0].url = [x.strip() for x in temp]
	print options[0].url
	snapp = HtSnapp(options)
	options = options[0]
	os.chdir(options.location)

	if options.url == None and options.xml == None and options.note == None:
		parser.error('No targets specified')
		
	gtk.main()
