from __future__ import print_function # the future is now, and it is good
import time, os, datetime, argparse
import RPi.GPIO as GPIO
import shutil   as sh
import usb.core
from luma.core.interface.serial import spi
from luma.core.render           import canvas
from luma.oled.device           import sh1106
from subprocess                 import *
from collections                import OrderedDict

# there are two terms you're using
# 1: menu    -- menu entries that get displayed as a list on the screen 
# 2: actions -- menu entries that call functions to complete tasks (i.e  backing up the tape)

# GLOBALS
lowBat      = 4
VENDOR      = 0x2367
PRODUCT     = 0x0002
MOUNT_DIR   = '/media/op1'
STORAGE_DIR = '/home/ace/' # dir where you checkout the git repo
PROJECT_DIR = '/rpi_rp1/'
USBID_OP1   = '*Teenage_OP-1*'

OP1_PATH = MOUNT_DIR

# BUTTONS
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

    def __init__(self, _name, _exitable=True):
        self.entries      = OrderedDict()
        self.name         = _name 
        self.currSelected = 0 # current selected entry
        self.currTop      = 0 # current entry at top of menu
        self.exitable     = _exitable

    # these can probably be combined into add entry, and then do a try:except when you actually call the thing
    def addAction(self, actionName, action):
        # add a check here to make sure 'action' is an Action
         self.entries[actionName] = action

    def addSubMenu(self, menuName, menu):
        # add a check here to make sure 'entry' is of type Menu
        self.entries[menuName] = menu

    def size(self): # returns the number of options in this Menu
        return len(self.entries)

    # prints the Menu in its entirety -- not used.........
    def log(self):
        print(self.name)
        for i in range(1, self.size()+1):
            print("{} - {}".format( i, self.entries[i][0] ))
        print()
	
    def drawHeader(self, device, draw): # draw title and notifiers

	draw.rectangle((0,0,128,12), outline='white', fill='white')	    # draw header/title
	draw.text((2,0), self.name, 'black')
	if IsConnected()==1: # draw OP1 status marker in top corner 
	    draw.rectangle((116,2,124,10), outline='black', fill='black')
	else:
	    draw.rectangle((116,2,124,10), outline='black', fill='white')

        # it would be nice to eventually have a battery indicator, finish this at some point
        # if GPIO.event_detected(lowBat):
        # 	draw.rectangle((96,3,108,9), outline='black', fill='black')
        # else:
        # 	draw.rectangle((96,3,108,9), outline='black', fill='white')
		

    def display(self, device): # put this Menu onto the screen 

        # move these consts somewhere else that makes more sense
	xOffset = 10 
	yOffset = 4

        if self.size() != 0: 

            with canvas(device) as draw: # draw the menu with the current five entries and the highlighted entry
        	self.drawHeader(device, draw)
                pos = self.currSelected - self.currTop
        	draw.rectangle((xOffset, (pos+1)*10+yOffset, xOffset+100, ((pos+1)*10)+10+yOffset), outline='white', fill='white')
        
                # this draw the text for each entry in the menu
        	textColor = ['white']*self.size()
                textColor[self.currSelected] = 'black'
        	
        	for ind, entry in enumerate(self.entries.items()[self.currTop:self.currTop+5]):
                    entryName = entry[0]
        	    draw.text((xOffset+2,(ind+1)*10+yOffset), entryName, textColor[ind+self.currTop])
                    if textColor[self.currSelected] == 'black': # draw an arrow... finish this!
                        draw.rectangle((2, (ind+1)*10+8, 5, ((ind+1)*10)+10), outline='white', fill='white')
                    else:
                        draw.rectangle((2, (ind+1)*10+8, 5, ((ind+1)*10)+10), outline='white', fill='white')
        
        else: # menu was empty, display warning... shouldn't happen often
            currLoop = 0 
            indOff  = 0 
            while True:
                time.sleep(0.01) # don't need to poll for keys that often, high CPU without
                warnText = ['this', 'menu', 'is', 'empty', '...sorry...', 'press', 'key 1!']
                if currLoop==0:

		    with canvas(device) as draw:
			self.drawHeader(device,draw)
			dispInd = 0 
	                for textInd in range(indOff,indOff+5):
                            if textInd > len(warnText)-1: textInd = textInd - len(warnText)
	    	            print("... looping... %s -- %s" % (warnText[textInd],textInd))
                            draw.text((xOffset+2,(dispInd+1)*10+yOffset), warnText[textInd], "white")
		            draw.rectangle((2, (dispInd+1)*10+8, 5, ((dispInd+1)*10)+10), outline='white', fill='white')
			    dispInd +=1	
				
                    indOff  += 1 
                currLoop += 1 
                if indOff == len(warnText): indOff = 0
		if currLoop == 75: currLoop = 0
                if GPIO.event_detected(key['key1']): return

	
        # check for user input and act accordingly (update menu, run action, etc)
        # ... couldn't this be done using callbacks? might be weird with recursion
        # ... I think doing it this way makes more sense

        while True:
            time.sleep(0.01) # don't need to poll for keys that often, high CPU without
                
	    if GPIO.event_detected(key['down']):
		if self.currSelected < self.size()-1: # if not at the end of the menu entries
                    self.currSelected += 1
                    if self.currTop <= self.currSelected-5: # selected past current buffer, display next 5 entries
                        self.currTop = self.currSelected-4
                else:
                    self.currSelected = 0 
                    self.currTop = 0 
                    
                break # exit while loop which redraws the menu

	    elif GPIO.event_detected(key['up']): 
		if self.currSelected > 0: # if not at the top of the menu entries
                    self.currSelected -= 1
                    if self.currTop > self.currSelected: # selected past current buffer, display next 5 entries
                        self.currTop = self.currSelected
                else:
                    self.currSelected = self.size()-1
                    self.currTop = self.size()-5
                    if self.currTop < 0: self.currTop=0
                    
                break # exit loop and redraw menu

            # MAKE THIS "OR RIGHT ARROW" TOO
	    elif GPIO.event_detected(key['key2']): # key2 is a selection, follow the action/submenu selected
                currItem = self.entries.items()[self.currSelected]
		if currItem[1].__class__.__name__=='Menu': # display submenu
		    currItem[1].display(device)
		else: # call function that entry describes
		    currItem[1].run(device)
		break

            elif GPIO.event_detected(key['key1']):
                if self.exitable==True:
	            return
                else:
	            with canvas(device) as draw:
	                draw.rectangle((9,6,117,58), outline='white', fill='black')
	                draw.text((0,16),"      I'M SORRY         ",'white')
	                draw.text((0,38),"   I CAN'T DO THAT      ",'white')
	            time.sleep(2.0)
                    break

        # needs to be an exit condition somewhere...
        self.display(device) # recursion
  

class Action: 

    def __init__(self, _name, _function, _triggersExit=False):
        self.name   = _name
        self.action = _function
        self.triggersExit = _triggersExit

    def name(self):
        return self.name

    def run(self, device): 
        self.action(device)

# SYSTEM UTILITIES                                        
# def run_cmd(cmd):
# 	p = Popen(cmd, shell=True, stdout=PIPE)
# 	output = p.communicate()[0]
# 	return output

def IsConnected():
  return usb.core.find(idVendor=VENDOR, idProduct=PRODUCT) is not None

def GetMountPath():
  o = os.popen('readlink -f /dev/disk/by-id/' + USBID_OP1).read()
  if USBID_OP1 in o:
    raise RuntimeError('Error getting OP-1 mount path: {}'.format(o))
  else:
    return o.rstrip()

def MountDevice(source, target, fs, options=''):
  ret = os.system('mount {} {}'.format(source, target))
  if ret not in (0, 8192):
    raise RuntimeError('Error mounting {} on {}: {}'.format(source, target, ret))

def UnmountDevice(target):
  ret = os.system('umount {}'.format(target))
  if ret != 0:
    raise RuntimeError('Error unmounting {}: {}'.format(target, ret))

def ForceDir(path):
  if not os.path.isdir(path):
    os.makedirs(path)

# waits for a keypress 
def WaitForKey(waitkey):
	while True:
		if GPIO.event_detected(key[waitkey]):
                        print(waitkey)
                        return
		time.sleep(.01)

def Placeholder():
    print("\n this function hasn't been implemented yet")

def Shutdown(device):

    print("\n powering off...?") 
    DrawText(device,['SHUTDOWN?', '1-CANCEL', '2-CONFIRM'])
    while True:
	if GPIO.event_detected(key['key2']): # 
	    with canvas(device) as draw:
                DrawText(device,['GOODNIGHT?'])
		run_cmd('sudo poweroff')
                return
	elif GPIO.event_detected(key['key1']):
            return
# proposition user
def DrawText(device, textList):
        totCharWidth = 22
        strOneOff = 64-len(textList[0])/22*64
        strTwoOff = 64-len(textList[1])/22*64
        strThrOff = 64-len(textList[2])/22*64

	with canvas(device) as draw:
                draw.rectangle((2,2,124,62), outline='white', fill='black')
                if len(textList) == 1:
	                draw.text((strOneOff,27), strOne, 'white')
                if len(textList) == 1:
	                draw.text((strOneOff,16), strOne, 'white')
	                draw.text((strTwoOff,38), strTwo,'white')
                if len(textList) == 3:
	                draw.text((strOneOff,8), strOne, 'white')
	                draw.text((strOneOff,27), strTwo, 'white')
	                draw.text((strOneOff,46), strThr,'white')

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
	time.sleep(2.0)

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

        # get everything going
	serial = spi(device=0, port=0)
	device = sh1106(serial,rotate=2)

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
	#mainMenu.addAction  ('test'    , Placeholder)
    
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

        DrawSplash(device)
        Initgpio()
        mainMenu.display(device) # this should loop forever

if __name__ == '__main__':
        main()

