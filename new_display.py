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
STORAGE_DIR = '/home/ace/' # where you checkout the repo... these dirs can probably be better organized (XDG etc)
PROJECT_DIR = '/rpi_rp1/'
USBID_OP1   = '*Teenage_OP-1*'

OP1_PATH = MOUNT_DIR

# BUTTONS
key={}
key['key1'] = 21 # used as 'go back' key 
key['key2'] = 20 # used as 'select entry' key
key['key3'] = 16 # not used yet

key['left']  = 5 # also used as go back (soon)
key['up']    = 6 # click through menu
key['down']  = 19 # click through menu
key['right'] = 26 # not used
key['press'] = 13 # could also be used to select entry
 
trackList  = ['/track_1.aif', '/track_2.aif','/track_3.aif','/track_4.aif']
trackNames = ['track 1', 'track 2','track 3','track 4']
nTracks    = len(trackList)

class Menu:

    def __init__(self, _name, _exitable=True):
        self.entries      = OrderedDict() # display menu items in order they're added
        self.name         = _name         # 
        self.currSelected = 0             # current selected entry to highlight
        self.currTop      = 0             # current entry displayed at top of menu screen
        self.exitable     = _exitable     # are you allowed to leave this particular menu

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
        # ... you'd need some sort of current menu global state variable
        # ... I think doing it with callbacks makes more sense
        status = IsConnected()
        while True:
            time.sleep(0.01) # don't need to poll for keys that often, high CPU without

            if status != IsConnected(): # state change!
                break
                
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

            # MAKE THIS "OR ARROW PRESS" TOO
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
  
# probably don't actually need this, just pass a function instead of a menu class when you add an entry... :\
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
def RunCmd(cmd):
    p = Popen(cmd, shell=True, stdout=PIPE)
    output = p.communicate()[0]
    return output

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

# proposition user, will only print first three strings in textList
def DrawText(device, textList):
        
    txtOff = list()
    for ind in range(len(textList)):
        # 64 is the number of pixels for half the screen, 6 is the pixel width of each letter
        txtOff.append(int(64-(len(textList[ind])/2.)*6))
        maxOff = min(txtOff) ## could be used to left align
        print("====================")
        print(maxOff)
    if maxOff < 0: maxOff=0

        # centered
	# with canvas(device) as draw:
        #         draw.rectangle((2,2,124,62), outline='white', fill='black')
        #         if len(textList) == 1:
 	#                 draw.text((txtOff[0],27) , textList[0], 'white')
        #         if len(textList) == 1:
	#                 draw.text((txtOff[0],16) , textList[0] , 'white')
	#                 draw.text((txtOff[1],38) , textList[1] , 'white')
        #         if len(textList) == 3:
	#                 draw.text((txtOff[0],8)  , textList[0] , 'white')
	#                 draw.text((txtOff[1],27) , textList[1] , 'white')
	#                 draw.text((txtOff[2],46) , textList[2] , 'white')

        # left justified
    with canvas(device) as draw:
        draw.rectangle((2,2,124,62), outline='white', fill='black')
        if len(textList) == 1:
 	    draw.text((maxOff,27) , textList[0], 'white')
        if len(textList) == 2:
	    draw.text((maxOff,16) , textList[0] , 'white')
	    draw.text((maxOff,38) , textList[1] , 'white')
        if len(textList) == 3:
	    draw.text((maxOff,8)  , textList[0] , 'white')
	    draw.text((maxOff,27) , textList[1] , 'white')
	    draw.text((maxOff,46) , textList[2] , 'white')

def DrawProgress(device, title, progress):
    with canvas(device) as draw:
	progpix=progress*64
	draw.text((16,8),title,'white')
	draw.rectangle((32,32,96,42), outline='white', fill='black')
	draw.rectangle((32,32,32+progpix,42), outline='white', fill='white')

# ##############################
# functions used for menu entries

def BackupTape(device):

	if IsConnected():
		ForceDir(MOUNT_DIR)
		mountpath = GetMountPath()
		print(' > OP-1 device path: %s', mountpath)
		MountDevice(mountpath, MOUNT_DIR, 'ext4', 'rw')
		print(' > Device mounted at %s' % MOUNT_DIR)
	        if os.path.exists(OP1_PATH)==1:

		    DrawText(device,['BACKUP TAPE?',' 1-CANCEL',' 2-CONFIRM'])
		    while True:
			if GPIO.event_detected(key['key2']):
			    print('copying')
			    cdate=datetime.datetime.now()
                            tdate=datetime.date.today()
			    dpath=STORAGE_DIR+PROJECT_DIR+'/op1-tapebackups/'+str(tdate)+' '+cdate.strftime('%I:%M%p')
                            copyList = [str(OP1_PATH)+'/tape/'+str(trackList[i]) for i in range(len(trackList))]
 
			    if os.path.exists(dpath)==0:
				os.mkdir(dpath)
			    #else throw exception?
                                
			    DrawProgress(device,'backing up tape...',0)
                            for iFile, fileName in enumerate(copyList):
				sh.copy(fileName,dpath)
				print('%s copied' % trackNames[iFile])
                                DrawProgress(device, ('backed up %s' % trackNames[iFile]), (iFile+1)*0.20)
                                
			    UnmountDevice(MOUNT_DIR)
			    DrawProgress(device,'back up done!',1)
			    time.sleep(.5)
			    return

			elif GPIO.event_detected(key['key1']):
				return
	else:
		print('no op1 detected')
		print('Is your device connected and in disk mode?')
		print('  1-Return to Menu')
		DrawText(device,['OP1 NOT CONNECTED','1-RETURN'])
		WaitForKey('key1')
		return
def WifiInfo(device):
    # clean this up
    getip    = "ip addr show wlan0 | grep inet | awk '{print $2}' | cut -d/ -f1 | awk '{print $1}'"
    getssid  = "iw dev wlan0 link | grep SSID"
    netstat = RunCmd(getip)
    ssidstat  = RunCmd(getssid)
    ip       = netstat.split('\n')[0]
    ssid     = ssidstat.split('\n')[0]

    print('wlan0 ip\n %s' % ip)
    print('wlan0 essid\n %s' % ssid)

    DrawText(device,['WIFI CONFIG!','IP: %s' % ip, 'SSID: %s' % ssid])
    WaitForKey('key1')

def Placeholder(device):
    print("\n this function hasn't been implemented yet")

def Shutdown(device):

    print("\n powering off...?") 
    DrawText(device,['SHUTDOWN?', '1-CANCEL', '2-CONFIRM'])
    while True:
	if GPIO.event_detected(key['key2']): # 
	    with canvas(device) as draw:
                DrawText(device,['GOODNIGHT?'])
		RunCmd('sudo poweroff')
                return
	elif GPIO.event_detected(key['key1']):
            return

def InitGPIO():

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

# ###################################################
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
        backupTape   = Action("BACKUP", BackupTape) # entry that calls backup tapes function
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

        wifiInfo       = Action("WIFI", WifiInfo) # entry that calls backup tapes function
        reloadFirmware = Action("FIRMWARE", Placeholder) # entry that calls backup tapes function
        sysMenu.addAction('wifi info', wifiInfo)
        sysMenu.addAction('load firmware', reloadFirmware)
        sysMenu.addAction('shutdown', shutdown)

        DrawSplash(device)
        InitGPIO()
        mainMenu.display(device) # this should loop forever

if __name__ == '__main__':
        main()
