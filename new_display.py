from __future__ import print_function # the future is now, and it is good

import time, os, datetime, argparse

import RPi.GPIO as GPIO
import shutil   as sh
import usb.core

from luma.core.interface.serial import spi
from luma.core.render           import canvas
from luma.oled.device           import sh1106
from subprocess                 import *

# there are two terms you're using
# 1: menu    -- menu entries that get displayed as a list on the screen 
# 2: actions -- menu entries that call functions to complete tasks (i.e  backing up the tape)

#GLOBALS
lowBat      = 4
VENDOR      = 0x2367
PRODUCT     = 0x0002
MOUNT_DIR   = '/media/op1'
STORAGE_DIR = '/home/ace/' # dir where you checkout the git repo
PROJECT_DIR = '/rpi_rp1/'
USBID_OP1   = '*Teenage_OP-1*'

OP1_PATH = MOUNT_DIR

#KEYS
key={}
key['key1'] = 21 # used as 'go back' key 
key['key2'] = 20 # used as 'select item' key
key['key3'] = 16

key['left']  = 5 
key['up']    = 6
key['down']  = 19
key['right'] = 26
key['press'] = 13
 
trackList  = ['/track_1.aif', '/track_2.aif','/track_3.aif','/track_4.aif']
trackNames = ['track 1', 'track_2','track 3','track 4']
nTracks    = len(trackList)

class Menu:

    # Constructor
    def __init__(self, _name, _exitable=True):
        self.entries  = {} 
        self.name     = _name 
        self.exitable = _exitable

    def addAction(self, actionName, action):
        # add a check here to make sure 'action' is an Action
         self.entries[self.size] = [actionName, action]

    def addSubMenu(self, menuName, menu):
        # add a check here to make sure 'entry' is of type Menu
        self.entries[self.size] = [menuName, menu, False]

    # Returns the number of options in this Menu
    def size(self):
         return len(self.entries)

    # Prints the Menu in its entirety
    def log(self):
        print(self.name)
        for i in range(1, self.size()+1):
            print("{} - {}".format( i, self.entries[i][0] ))
        print()


    # Runs this Menu
    def display(self, device):

        # move these consts somewhere else that makes more sense

	#offsets
	xOffset = 5 
	yOffset = 4
	
	#menu
	width = 100 #width of hilight
	mlistc=['white']*self.size
	if pos != 0: #setup cursor
		mlistc[pos-1]='black'

	#action menu
	axdist=64
	alistc=['white']*len(alist)
	if apos != 0:
		alistc[apos-1]='black'

        while True:
	    with canvas(device) as draw:

	        # draw header/title
	        draw.rectangle((0,0,128,12), outline='white', fill='white')
                draw.text((2,0), self.name, 'black')

	        # draw OP1 status marker in top corner 
	        if is_connected()==1:
		    draw.rectangle((116,2,124,10), outline='black', fill='black')
	        else:
		    draw.rectangle((116,2,124,10), outline='black', fill='white')

                # it would be nice to eventually have a battery indicator
	        # if GPIO.event_detected(lowBat):
 	        # 	draw.rectangle((96,3,108,9), outline='black', fill='black')
	        # else:
	        # 	draw.rectangle((96,3,108,9), outline='black', fill='white')

                # this highlights the currently selected item
	        if pos != 0:
		    draw.rectangle((xOffset, pos*10+yOffset, xOffset+width, (pos*10)+10+yOffset), outline='white', fill='white')
                
                # this draw the text for each entry in the menu
	        for idx,line in enumerate(mlist):
		    draw.text((xOffset,(idx+1)*10+yOffset),line,mlistc[idx])

                # what does this do
	        if apos != 0:
		    draw.rectangle((60,13,128,64), outline='black', fill='black')
		    draw.rectangle((60,13,61,48), outline='white', fill='white')
		    draw.rectangle((axdist, apos*10+yOffset, axdist+width, (apos*10)+10+yOffset), outline='white', fill='white')
		    for idx,line in enumerate(alist):
		        #print('idx: ',idx,'line: ',line,'fill: ',flist[idx])
		        draw.text((axdist,(idx+1)*10+yOffset),line,alistc[idx])


class Action: 

    def __init__(self, _name, _function, _triggersExit=False):
        self.name   = _name
        self.action = _function
        self.triggersExit = _triggersExit

    def name(self):
        return self.name

    def run(self): 
        self.action()

def Placeholder():
    print("\n this function hasn't been implemented yet")

def Shutdown():

    print("\n powering off...") 
    drawText(device,['powering off?','','   1-cancel','   2-confirm'])
    while True:
	if GPIO.event_detected(key['key2']): # 
	    with canvas(device) as draw:
		draw.rectangle((10,3,118,61), outline='white', fill='black')
		draw.text((0,8),'       GOODNIGHT?      ','white')
                #eyes
		draw.rectangle((40,30,45,35), outline='black', fill='white')
		draw.rectangle((83,30,88,35), outline='black', fill='white')
                #mouth
		draw.rectangle((40,45,88,50), outline='black', fill='white')
                
		run_cmd('sudo poweroff')
                return
	elif GPIO.event_detected(key['key1']):
            return

def is_connected():
  return usb.core.find(idVendor=VENDOR, idProduct=PRODUCT) is not None


def Initgpio():

	verboseprint('Initializing GPIO')
	GPIO.setmode(GPIO.BCM)

	GPIO.setup(key['key1'], GPIO.IN, pull_up_down=GPIO.PUD_UP)
	GPIO.setup(key['key2'], GPIO.IN, pull_up_down=GPIO.PUD_UP)
	GPIO.setup(key['key3'], GPIO.IN, pull_up_down=GPIO.PUD_UP)

	GPIO.setup(key['left'],  GPIO.IN, pull_up_down=GPIO.PUD_UP)
	GPIO.setup(key['up'],    GPIO.IN, pull_up_down=GPIO.PUD_UP)
	GPIO.setup(key['press'], GPIO.IN, pull_up_down=GPIO.PUD_UP)
	GPIO.setup(key['down'],  GPIO.IN, pull_up_down=GPIO.PUD_UP)
	GPIO.setup(key['right'], GPIO.IN, pull_up_down=GPIO.PUD_UP)
	
	#LIPO LOW BATTERY
	GPIO.setup(lowBat, GPIO.IN,pull_up_down=GPIO.PUD_UP) # figure this out...?

	GPIO.add_event_detect(key['key1'],  GPIO.FALLING)
	GPIO.add_event_detect(key['key2'],  GPIO.FALLING, bouncetime=300)
	GPIO.add_event_detect(key['key3'],  GPIO.FALLING, bouncetime=300)
	GPIO.add_event_detect(key['left'],  GPIO.FALLING, bouncetime=300)
	GPIO.add_event_detect(key['up'],    GPIO.FALLING, bouncetime=300)
	GPIO.add_event_detect(key['press'], GPIO.FALLING, bouncetime=300)
	GPIO.add_event_detect(key['down'],  GPIO.FALLING, bouncetime=300)
	GPIO.add_event_detect(key['right'], GPIO.FALLING, bouncetime=300)

def DrawSplash(device):
	with canvas(device) as draw:
		draw.rectangle((18,12,108,52), outline='white', fill='black')
		draw.text((0,16),'         RP1         ','white')
		draw.text((0,38),'         ACE         ','white')

# parse args and run the code!
def main():

        parser = argparse.ArgumentParser()
        parser.add_argument('-v', '--verbose', action='count', 
                            help='print verbose log messages')
        args = parser.parse_args()
        
        # print generic console messages only on --verbose flag 
        v_print = print if args.verbose else lambda *a, **k: None
        global verboseprint
        verboseprint = v_print

        # ##########################
        # there will be the main menu 
        mainMenu = Menu("MAIN", _exitable=False) ## don't let someone leave the main menu

        # and these will be entries in the menu
        backupTape   = Action("BACKUP", Placeholder) # entry that calls backup tapes function
        tapeDownMenu = Menu("MAIN>TAPES") # a menu that lists the btapes on the rpi, available for upload to the OP1
        samplesMenu  = Menu("MAIN>SAMPLES") # a menu that lists system entries, such as wifi, etc. 
        sysMenu      = Menu("MAIN>SYS") # a menu that lists system entries, such as wifi, etc. 
        shutdown     = Action("SHUTDOWN", Shutdown) # entry that calls backup tapes function

        # add the entries to the menu, the order you add them is the order they're listed
        mainMenu.addAction  ('backup tape' , backupTape)
        mainMenu.addSubMenu ('tape deck'   , tapeDownMenu)
        mainMenu.addSubMenu ('sample packs', samplesMenu)
        mainMenu.addSubMenu ('system info' , sysMenu)
        mainMenu.addAction  ('shutdown'    , shutdown)
    
        # ##########################
        # samples submenus
        synthSamplesMenu = Menu("MAIN>SAMPLES>SYNTH") # a menu that lists system entries, such as wifi, etc.         
        drumSamplesMenu  = Menu("MAIN>SAMPLES>DRUM") # a menu that lists system entries, such as wifi, etc.         
        samplesMenu.addSubMenu('synth samples', synthSamplesMenu)
        samplesMenu.addSubMenu('drum samples', drumSamplesMenu)

        wifiInfo       = Action("WIFI", Placeholder) # entry that calls backup tapes function
        reloadFirmware = Action("FIRMWARE", Placeholder) # entry that calls backup tapes function
        sysMenu.addAction('wifi info', wifiInfo)
        sysMenu.addAction('load firmware', reloadFirmware)
        sysMenu.addAction('shutdown', shutdown)

        # get everything going
	serial = spi(device=0, port=0)
	device = sh1106(serial,rotate=2)
        drawSplash(device)
        Initgpio()
        mainMenu.display(device) # this should loop forever

if __name__ == '__main__':
        main()

