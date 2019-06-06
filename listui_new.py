from __future__ import print_function # the future is now, and it is good

import time, os, datetime, argparse

import RPi.GPIO as GPIO
import shutil   as sh
import usb.core

from luma.core.interface.serial import spi
from luma.core.render           import canvas
from luma.oled.device           import sh1106
from subprocess                 import *


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

#LIST OF SAMPLE PACKS AND PATHS
sampleListSynth=[
		['_josh',STORAGE_DIR+PROJECT_DIR+'/samplepacks/_josh/' ],
		['courtyard',STORAGE_DIR+PROJECT_DIR+'/samplepacks/courtyard/' ],
		['dawless',STORAGE_DIR+PROJECT_DIR+'/samplepacks/dawless/' ],
		['C-MIX',STORAGE_DIR+PROJECT_DIR+'/samplepacks/C-MIX/' ],
		['inkd',STORAGE_DIR+PROJECT_DIR+'/samplepacks/op1_3.2/inkdd/' ],
		['Dark Energy',STORAGE_DIR+PROJECT_DIR+'/samplepacks/op1_3.2/Dark Energy/'],
		['memories',STORAGE_DIR+PROJECT_DIR+'/samplepacks/CUCKOO OP-1 MEGA PACK/CUCKOO OP-1 MEGA PACK/OP-1 patches/Put in synth/memories/'],
		['opines',STORAGE_DIR+PROJECT_DIR+'/samplepacks/CUCKOO OP-1 MEGA PACK/CUCKOO OP-1 MEGA PACK/OP-1 patches/Put in synth/opines/'],
		['vanilla sun',STORAGE_DIR+PROJECT_DIR+'/samplepacks/vanilla sun/'],
		['mellotron',STORAGE_DIR+PROJECT_DIR+'/samplepacks/mellotronAifs/'],
		['hs dsynth',STORAGE_DIR+PROJECT_DIR+'/samplepacks/hs dsynth vol1/'],
		['cassette',STORAGE_DIR+PROJECT_DIR+'/samplepacks/cassette/'],
		['SammyJams',STORAGE_DIR+PROJECT_DIR+'/samplepacks/SammyJams Patches'],
		]

sampleListSynth=[['test','test']]
sampleListDrum=[['test','test']]

#List of tapes and paths
tapeList=[ 
		['recycling bin v1',STORAGE_DIR+PROJECT_DIR+'/tapes/recycling bin v1/tape'],
		['recycling bin v2',STORAGE_DIR+PROJECT_DIR+'/tapes/recycling bin v2'],
		['fun with sequencers',STORAGE_DIR+PROJECT_DIR+'/op1-tapebackups/fun with sequencers'],
		['lofi family',STORAGE_DIR+PROJECT_DIR+'/op1-tapebackups/lofi family'],
		['primarily pentatonic',STORAGE_DIR+PROJECT_DIR+'/op1-tapebackups/primarily pentatonic'],
		['2018-02-24',STORAGE_DIR+PROJECT_DIR+'/op1-tapebackups/2018-02-24'],
		['lets start with guitar',STORAGE_DIR+PROJECT_DIR+'/op1-tapebackups/lets start with guitar this time'],
		['spaceman',STORAGE_DIR+PROJECT_DIR+'/op1-tapebackups/2018-03-25'],
		['slow & somber',STORAGE_DIR+PROJECT_DIR+'/op1-tapebackups/slow & somber'],
		['cool solo',STORAGE_DIR+PROJECT_DIR+'/op1-tapebackups/cool solo'],
		['technical advantage',STORAGE_DIR+PROJECT_DIR+'/op1-tapebackups/technical advantage'],
		['heartbeat slide',STORAGE_DIR+PROJECT_DIR+'/op1-tapebackups/heartbeat slide']

		]
#print tapeList
keys={}
tapeList=[['test','test']]


# INITIALIZATION
def init():

	serial = spi(device=0, port=0)
	device = sh1106(serial,rotate=2)
	drawText(device,['Initializing GPIO'])
	initgpio()
	drawText(device,['Initializing GPIO','Scanning Tapes'])
	scanTapes(device)
	drawText(device,['Initializing GPIO','Scanning Tapes','Scanning Samples'])
	scanSamples('dummy')
	drawText(device,['Initializing GPIO','Scanning Tapes','Scanning Samples','done.'])
	drawSplash(device)
	time.sleep(2)

	return device

def initgpio():

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
	GPIO.setup(lowBat, GPIO.IN,pull_up_down=GPIO.PUD_UP)

	GPIO.add_event_detect(key['key1'],  GPIO.FALLING)
	GPIO.add_event_detect(key['key2'],  GPIO.FALLING, bouncetime=300)
	GPIO.add_event_detect(key['key3'],  GPIO.FALLING, bouncetime=300)
	GPIO.add_event_detect(key['left'],  GPIO.FALLING, bouncetime=300)
	GPIO.add_event_detect(key['up'],    GPIO.FALLING, bouncetime=300)
	GPIO.add_event_detect(key['press'], GPIO.FALLING, bouncetime=300)
	GPIO.add_event_detect(key['down'],  GPIO.FALLING, bouncetime=300)
	GPIO.add_event_detect(key['right'], GPIO.FALLING, bouncetime=300)
                                                          
# SYSTEM UTILITIES                                        
def run_cmd(cmd):
	p = Popen(cmd, shell=True, stdout=PIPE)
	output = p.communicate()[0]
	return output

def is_connected():
  return usb.core.find(idVendor=VENDOR, idProduct=PRODUCT) is not None

def getmountpath():
  o = os.popen('readlink -f /dev/disk/by-id/' + USBID_OP1).read()
  if USBID_OP1 in o:
    raise RuntimeError('Error getting OP-1 mount path: {}'.format(o))
  else:
    return o.rstrip()

def mountdevice(source, target, fs, options=''):
  ret = os.system('mount {} {}'.format(source, target))
  if ret not in (0, 8192):
    raise RuntimeError('Error mounting {} on {}: {}'.format(source, target, ret))

def unmountdevice(target):
  ret = os.system('umount {}'.format(target))
  if ret != 0:
    raise RuntimeError('Error unmounting {}: {}'.format(target, ret))

def forcedir(path):
  if not os.path.isdir(path):
    os.makedirs(path)

# waits for a keypress 
def wait(keys,waitkey):
	while True:
		if GPIO.event_detected(key[waitkey]):
                        print(waitkey)
                        return
		time.sleep(.01)

# handles actions when in the menus and changes display accordingly , 
def actionhandler(device,pos,apos,mname,draw=0):

	#returning 1 escapes calling function to return
	print('action handler @%s' % mname)
	print('pos: %s apos: %s' % (pos,apos))

	if mname=='MAIN':
		if pos==1 and apos==0:
			print('main: tape menu')
			#MAIN MENU
			tapeMenu(device)
			return(1)
		elif pos==2:
			backupTape(device)

		elif pos==3:
			if apos==1:
				sampleMenuSynth(device)
			if apos==2:
				sampleMenuDrum(device)

		elif pos==4: 
			sysMenu(device)
			return(1)

		elif pos==5 and apos==0:
			drawText(device,['powering off?','','   1-cancel','   2-confirm'])
		        while True:
		                if GPIO.event_detected(key['key2']): # 
	                                with canvas(device) as draw:
		                                draw.rectangle((10,3,118,61), outline='white', fill='black')
		                                draw.text((0,8),'       GOODNIGHT?      ','white')
                                                #eyes
			                        draw.rectangle((35,30,40,35), outline='black', fill='white')
			                        draw.rectangle((83,30,88,35), outline='black', fill='white')
                                                #mouth
			                        draw.rectangle((35,45,88,50), outline='black', fill='white')

			                run_cmd('sudo poweroff')
                                        return
			        elif GPIO.event_detected(key['key1']):
                                        return

	elif mname=='MAIN>TAPES':
		print('tape actions @POS: %s, apos: %s' % (pos,apos))

		if apos==1: #assuming pos is valid becasue menuList was built from tapeList
			loadTape(device,tapeList[pos-1][1])

	elif mname=='MAIN>SYNTH SAMPLES':	
		
		#if pos==1 or 2 or 3 or 4 or 5 or 6 or 7: 
		#assuming pos is valid bc was built from sampleList
		spath=sampleListSynth[pos-1][1]
		dpath=OP1_PATH+'/synth/_' + str(sampleListSynth[pos-1][0]) + '/'
		if apos==1:
			loadUnloadSample(device,spath,dpath,sampleListSynth[pos-1][0],'load')
		elif apos==2:
			loadUnloadSample(device,spath,dpath,sampleListSynth[pos-1][0],'delete')

	elif mname=='MAIN>DRUM SAMPLES':	
		
		#if pos==1 or 2 or 3 or 4 or 5 or 6 or 7: 
		#assuming pos is valid bc was built from sampleList
		spath=sampleListDrum[pos-1][1]
		dpath=OP1_PATH+'/drum/_' + str(sampleListDrum[pos-1][0]) + '/'
		if apos==1:
			loadUnloadSample(device,spath,dpath,sampleListDrum[pos-1][0],'load')
		elif apos==2:
			loadUnloadSample(device,spath,dpath,sampleListDrum[pos-1][0],'delete')

	elif mname=='MAIN>SYS':

		if pos==1:
			getip="ip addr show wlan0 | grep inet | awk '{print $2}' | cut -d/ -f1 | awk '{print $1}'"
			netstat=run_cmd(getip)
			ip=netstat.split('\n')[0]

			print('wlan0 status\n %s' % ip)

			drawText(device,['wlan0 status',ip])
			wait({},'key1')

		elif pos==2: # poweroff
			drawText(device,['powering off...'])
			run_cmd('sudo poweroff')
			return

		elif pos==3:
			print('nestTest')
			nestMenu(device)

		elif pos==4:
			print('loading firmware')
			loadFirmware(device)

		elif pos==5:
			print('testing progress')
			drawProgress(device,'progress!',0)
                        for i in range(10):
			        time.sleep(0.25)
			        drawProgress(device,'progress!', (i+1)*0.1)
		elif pos==6:
			print('deleting synth')
			dpath=OP1_PATH+'/synth/'
			loadUnloadSample(device,'',dpath,'','delete')
	return(0)

# DISPLAY UTILITIES, THIS IS THE PRIMARY LOOP... 
# THERE ART TWO MENU LEVELS, PRIMARY AND SECONDARY 
def listMenuScroll(device, mlist, alist, mname, draw=0, actions=False, exit=True):

	#mlist: menu list
	#alist: action list
	#mname: menu name for action context
	title=mname
	print(mlist)

	#initial settings
	keys = {}
	pos  = 1 # this is the position on the screen menu [1-5], as dictated by screen size
	vpos = 0 # this is the position in the data menu, as dictated by the number of folders etc.
	vmax = 0 # holds how many possible menu locations there are
	apos = 0 # I don't understand apos

	if len(mlist)>5:
		print('long list')
		vmax=len(mlist)-5

	dispListMenu(device,title,mlist,alist,pos,0,vpos) 
	while True:

		# fix me, no need to update the display every loop I don't think
                # there needs to be an "if gpio.even_detected(any) then -> update screen 
		time.sleep(.05)

		if GPIO.event_detected(key['down']):
			#pos=pos+1
			if pos==5 and vpos<vmax:
				vpos+=1
			else:
				pos=posDown(pos)
				if pos==1:vpos=0
		        dispListMenu(device,title,mlist,alist,pos,0,vpos)

		elif GPIO.event_detected(key['up']):
			#pos=pos+1
			if pos==1 and vpos>0:
				vpos-=5
			else:
				pos=posUp(pos,5)
				if pos==5:vpos=vmax
		        dispListMenu(device,title,mlist,alist,pos,0,vpos)

		elif GPIO.event_detected(key['key2']): # go into next menu level! 
			actionhandler(device,pos+vpos,apos,mname)
			
			if actions==True:
				done=0
				apos=1
			else:
				done=1
				apos=0

			#action loop
			while done==0:
				time.sleep(.05)

				if GPIO.event_detected(key['down']):
					#pos=pos+1
					apos=posDown(apos,3)
					dispListMenu(device,title,mlist,alist,pos,apos,0,vpos)

				elif GPIO.event_detected(key['up']):
					#pos=pos+1
					apos=posUp(apos,3)
					dispListMenu(device,title,mlist,alist,pos,apos,0,vpos)

				elif GPIO.event_detected(key['key2']):
					actionhandler(device,pos+vpos,apos,mname,vpos)
					apos=0
					done=1

				# back exit
				elif GPIO.event_detected(key['key1']):
					done=1
					apos=0

                        dispListMenu(device,title,mlist,alist,pos,0,vpos)

		#// EXIT STRATEGY
		elif GPIO.event_detected(key['key1']):
			if exit==True:
				return

def dispListMenu(device, title, plist, alist, pos, apos=0, vpos=999):
	
	if vpos!=999:
		mlist=plist[vpos:vpos+5]
	else:
		mlist=plist

	#offsets
	xdist=5 #x offset
	yoffset=4
	
	#menu
	width=100 #width of hilight
	#mlist=['list1', 'list2','list3','list4','list5'] #will be parameter
	mlistc=['white']*len(mlist)
	if pos != 0: #setup cursor
		mlistc[pos-1]='black'

	#action menu
	axdist=64
	#alist=['action1', 'action2','action3']
	alistc=['white']*len(alist)
	if apos != 0:
		alistc[apos-1]='black'

	with canvas(device) as draw:

		#draw title
		draw.rectangle((0,0,128,12), outline='white', fill='white')
		#draw.rectangle((1,10,126,11), outline='black', fill='black')
		draw.text((2,0),title,'black')

		# // STATUS BAR //
		if is_connected()==1:
			draw.rectangle((116,2,124,10), outline='black', fill='black')
		else:
			draw.rectangle((116,2,124,10), outline='black', fill='white')

		# if GPIO.event_detected(lowBat):
 		# 	draw.rectangle((96,3,108,9), outline='black', fill='black')
		# else:
		# 	draw.rectangle((96,3,108,9), outline='black', fill='white')

		if pos != 0:
			draw.rectangle((xdist, pos*10+yoffset, xdist+width, (pos*10)+10+yoffset), outline='white', fill='white')
		
		for idx,line in enumerate(mlist):
			#print('idx: ',idx,'line: ',line,'fill: ',flist[idx])
			draw.text((xdist,(idx+1)*10+yoffset),line,mlistc[idx])

		if apos != 0:

			draw.rectangle((60,13,128,64), outline='black', fill='black')
			draw.rectangle((60,13,61,48), outline='white', fill='white')

			draw.rectangle((axdist, apos*10+yoffset, axdist+width, (apos*10)+10+yoffset), outline='white', fill='white')
		
			for idx,line in enumerate(alist):
				#print('idx: ',idx,'line: ',line,'fill: ',flist[idx])
				draw.text((axdist,(idx+1)*10+yoffset),line,alistc[idx])

def posUp(pos, lmax=5):
	if pos != 1:
		pos=pos-1
	else:
		pos=lmax
	return pos

def posDown(pos, lmax=5):
	if pos != lmax:
		pos+=1
	else:
		pos=1
	return pos

def drawText(device,textlist):
	with canvas(device) as draw:
		for idx,text in enumerate(textlist):
			#print text, ', ', idx
			draw.text((0,idx*10),text,'white')

def drawProgress(device,title,progress):
	with canvas(device) as draw:
		progpix=progress*64
		draw.text((16,8),title,'white')
		draw.rectangle((32,32,96,42), outline='white', fill='black')
		draw.rectangle((32,32,32+progpix,42), outline='white', fill='white')

def drawSplash(device):
	with canvas(device) as draw:
		draw.rectangle((18,12,108,52), outline='white', fill='black')
		draw.text((0,16),'         RP1         ','white')
		draw.text((0,38),'         ACE         ','white')

# MENUS
def sampleMenuSynth(device):
	mlist=[]
	for item in sampleListSynth: #build menu list from sampleList global
		print(item)
		mlist.append(item[0])

	alist=['load', 'unload','[empty]']
	listMenuScroll(device,mlist,alist,'MAIN>SYNTH SAMPLES',None,True)

def sampleMenuDrum(device):
	mlist=[]
	for item in sampleListDrum: #build menu list from sampleList global
		print(item)
		mlist.append(item[0])

	alist=['load', 'unload','[empty]']
	listMenuScroll(device,mlist,alist,'MAIN>DRUM SAMPLES',None,True)	

def tapeMenu(device):
	mlist=[]
	for item in tapeList: #build menu list from tapeList global
		mlist.append(item[0])
	
	alist=['load', '[empty]','[empty]']
	listMenuScroll(device,mlist,alist,'MAIN>TAPES',None,True)

	if ['test', 'test'] in tapeList: 
		tapeList.remove(['test','test'])

def sysMenu(device):
	alist=['go', '[empty]','[empty]']
	mlist=['wireless','poweroff','nest test','load firmware','progress test','delete synth','test7','asdf','asdfg','more tests']

	listMenuScroll(device,mlist,alist,'MAIN>SYS')

def nestMenu(device):
	alist=['[empty]', '[empty]','[empty]']
	mlist=['nest test!','test5d','test6','test7','asdf','asdfg','more tests']

	listMenuScroll(device,mlist,alist,'MAIN>SYS>NEST')


# FILE OPERATIONS
def backupTape(device):

	if is_connected():
		forcedir(MOUNT_DIR)
		mountpath = getmountpath()
		print(' > OP-1 device path: %s', mountpath)
		mountdevice(mountpath, MOUNT_DIR, 'ext4', 'rw')
		print(' > Device mounted at %s' % MOUNT_DIR)
	print(is_connected())

	if os.path.exists(OP1_PATH)==1:

		drawText(device,['op1 connected','backup tape?',' 1-back',' 2-yup'])
		print('op1 connect success\n Backup Track?\n   1-back\n   2-continue\n ')

		#response loop
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
                                
				drawProgress(device,'backing up tape...',0)
                                for iFile, fileName in enumerate(copyList):
				        sh.copy(fileName,dpath)
				        print('%s copied' % trackNames[iFile])
                                        drawProgress(device, ('backed up %s' % trackNames[iFile]), (iFile+1)*0.20)

				print(' > Unmounting OP-1')
				unmountdevice(MOUNT_DIR)
				print(' > Done.')
				drawProgress(device,'back up done!',1)
				time.sleep(.5)
				return

			elif GPIO.event_detected(key['key1']):
				return
	else:
		print('no op1 detected')
		print('Is your device connected and in disk mode?')
		print('  1-Return to Menu')
		drawText(device,['no op1 found','1-return'])
		wait(keys,'key1')
		return

def loadTape(device,source):
	keys={}
	time.sleep(1)

	if is_connected():
		forcedir(MOUNT_DIR)
		mountpath = getmountpath()
		print(' > OP-1 device path: %s' % mountpath)
		mountdevice(mountpath, MOUNT_DIR, 'ext4', 'rw')
		print(' > Device mounted at %s' % MOUNT_DIR)
	print(is_connected())


	if os.path.exists(OP1_PATH)==1:
		
		print('op1 connected\n Download tape?\n (this overwrites!)\n   1-back\n    2-yes\n')
		drawText(device,['op1 connected','load tape?',' 1- back','2-yes'])

		#response loop
		while True:
			if GPIO.event_detected(key['key2']):
				print('downloading to op1')
				dpath=OP1_PATH+'/tape'

                                copyList = [str(source)+str(trackList[i]) for i in range(len(trackList))]
                                rmList = [str(dpath)+str(trackList[i]) for i in range(len(trackList))]
                                for rmFile in rmList:
                                        os.remove(rmFile)

                                drawProgress(device,'copying tape...',0)
                                for iFile, fileName in enumerate(copyList):
				        sh.copy(fileName,dpath)
				        print('%s copied' % trackNames[iFile])
                                        drawProgress(device,('copying %s' % trackNames[iFile]), (iFile+1)*0.20)

				print(' > Unmounting OP-1')
				unmountdevice(MOUNT_DIR)
				print(' > Done.')
				drawProgress(device,'finished copying!',1)
				time.sleep(.5)
				return

			elif GPIO.event_detected(key['key1']):
				return
	else:
		print('no op1 detected')
		print('Is your device connected and in disk mode?')
		print('  1-Return to Menu')

		drawText(device,['no op1 found','1-return to menu'])
		wait(keys,'key1')
		return

def loadUnloadSample(device,spath,dpath,name,op):
	keys={}
	time.sleep(1)

	if is_connected():
		forcedir(MOUNT_DIR)
		mountpath = getmountpath()
		print(' > OP-1 device path: %s' % mountpath)
		mountdevice(mountpath, MOUNT_DIR, 'ext4', 'rw')
		print(' > Device mounted at %s' % MOUNT_DIR)

	if os.path.exists(OP1_PATH)==1:
		
		print('op1 connected')
		drawText(device,['op1 connected success','you sure?','1-back','2-yes'])

		while True:
			if GPIO.event_detected(key['key2']):
				print('copying')

				print('%s >%s' % (dpath,spath))
						
				if op=='load':
					print('copying')
					copytree(spath,dpath)
					print(' > Unmounting OP-1')
					unmountdevice(MOUNT_DIR)
					print(' > Done.')
					return
					
				elif op=='delete':
					#sampleLoadMenu(term,keys)
					sh.rmtree(dpath)
					print('%s pack deleted' %  name)
					print(' > Unmounting OP-1')
					unmountdevice(MOUNT_DIR)
					print(' > Done.')
					return

			elif GPIO.event_detected(key['key1']):
				return
	else:
		print('no op1 detected\n Is your device connected and in disk mode?\n  1-Return to Menu\n')
		drawText(device,['no op1 found','1-return to menu'])
		wait(keys,'key1')
                return

def loadFirmware(device):
	if os.path.exists('/media/pi/OP-1')==1:
		drawText(device,['op1 connected','load firmware?','  1-back','  2-yup'])
		while True:
			if GPIO.event_detected(key['key2']):
				print('copying firmware')
				drawText(device,['copying firmware...'])
				spath=STORAGE_DIR+'misc/op1_225.op1'
				dpath='/media/pi/OP-1/'
				sh.copy(spath,dpath)
				return

			elif GPIO.event_detected(key['key1']):
				return

	else:
		drawText(device,['op1 not detected','','returning to menu...'])
		time.sleep(1)
		return

def scanTapes(device):
	directory=STORAGE_DIR+PROJECT_DIR+'/op1-tapebackups/'
	print('updating tape index')
	
        lst = sorted([f for f in os.listdir(directory) if not f.startswith('.')], key=str.lower)

	for filename in lst:
		fullPath = directory + filename
		tapeList.append([filename,fullPath])

        if ['test', 'test'] in tapeList: 
		sampleListSynth.remove(['test','test'])
	tapeList.sort()

	print('[TAPES]\n')
	print(tapeList)

def copytree(src, dst, symlinks=False, ignore=None):
	ct=0
	print('%s files to move' % str(len(os.listdir(src))))

	try:
		for item in os.listdir(src):
			s = os.path.join(src, item)
			print('source file: %s' % s)
			
			d = os.path.join(dst, item)
			if os.path.isdir(dst)==0:
				print('destination doesn\'t exist. creating...')
				os.mkdir(dst)
			if os.path.isdir(s):
				print('recurse!')
				sh.copytree(s, d, symlinks, ignore)
			else:
				sh.copy(s, d)
				ct+=1
				print('file %s moved' % str(ct)) 
	except:
		print('must be an error. file full or smt')

def scanSamples(directory):
	#scans sample packs in a path and updates sample lists
	print('Scanning for samplepacks')

	directory=STORAGE_DIR+'rpi_rp1/samplepacks/'
	for file in os.listdir(directory):
		fullPath = directory + file
		if os.path.isdir(fullPath):

			containsAif=0
			#each folder in parent directory
			for subfile in os.listdir(fullPath):
				subfullPath=fullPath+'/'+subfile

				if os.path.isdir(subfullPath):
					if subfile=='synth' or 'drum':
						pack=readAifDir(subfile,subfullPath)
						pack[2]['_types']=subfile #if in synth or drum folder, override type
						pack[0]=file

						if pack[2]['_types']=='synth':
							sampleListSynth.append(pack)
						elif pack[2]['_types']=='drum':
							sampleListDrum.append(pack)

				elif subfile.endswith('.aif') or subfile.endswith('.aiff'):
					containsAif=1
				elif subfile.endswith('.DS_Store'):
					continue
				else:
					print('what\'s going on here. name your folders or hold it with the nesting')
					print('SUBFILE: %s' % subfile)
			if containsAif==1:
				pack=readAifDir(file,fullPath)
				if pack[2]['_types']=='synth':
					sampleListSynth.append(pack)
				elif pack[2]['_types']=='drum':
					sampleListDrum.append(pack)

	if ['test', 'test'] in sampleListSynth: 
		sampleListSynth.remove(['test','test'])
	if ['test', 'test'] in sampleListDrum: 
		sampleListDrum.remove(['test','test'])

	print('[SYNTH PACKS]')
	print(sampleListSynth)
	print('[DRUM PACKS]')
	print(sampleListDrum)

def readAifDir(name,path):

	#should return amount of .aif's found in dir
	aifsampleList=[['a','a']]
	pack=[name,path+'/',dict([('_types','mixed')])]

	for file in os.listdir(path):
		fullPath=path+'/'+file
		if file.endswith('.aif')or file.endswith('.aiff'):
			#print('aif found at file: ',fullPath)
			atts=readAif(fullPath)
			aifsampleList.append([file,fullPath,atts['type']])
			#print atts['type']

		elif file.endswith('.DS_Store'):
			#ignore .DS_Store mac files
			continue
		else:
			print('%s is not a aif. what gives?' %  fullPath)
	if ['a','a'] in aifsampleList:
			aifsampleList.remove(['a','a'])

	for sample in aifsampleList:
	 	#print sample[1] #fullpath
	 	#print sample[2]
	 	sampleType=sample[2]
	 	if sampleType in pack[2]:
	 		pack[2][sampleType]=pack[2][sampleType]+1
	 	else:
	 		pack[2][sampleType]=1
	 	
	if ('cluster' in pack[2]) or ('sampler' in pack[2]) or ('drwave' in pack[2]) or ('string' in pack[2]) or ('pulse' in pack[2]) or ('phase' in pack[2]) or ('voltage' in pack[2]) or ('digital' in pack[2]) or ('dsynth' in pack[2]) or ('fm' in pack[2]):
		pack[2]['_types']='synth'

	if 'drum' in pack[2]:
		if pack[2]['_types']=='synth':
			pack[2]['_types']='mixed'
		else:
			pack[2]['_types']='drum'

	return pack

def readAif(path):

	attdata={}

	with open(path,'rb') as fp:
		line=fp.readline()

		if 'op-1' in line:
			data    = line.split('{', 1)[1].split('}')[0] #data is everything in brackets
 			data    = switchBrack(data,',','|')
			attlist = data.split(',')

			for i,line in enumerate(attlist):

				linesplit = line.split(':')
				attname   = linesplit[0]
				attname   = attname[1:-1]
				attvalue  = linesplit[1]
                                            
				valtype=''

				if isInt(attvalue):
					valtype='int'

				if isfloat(attvalue):
					valtype='float'

				if attvalue=='false' or attvalue=='true':
					valtype='bool'

				for j, char in enumerate(list(attvalue)):
					if valtype=="":
						if char=="'":
							valtype='string'
						elif char=='[':
							valtype='list'

				if valtype=='':
					valtype='no type detected'
				elif valtype=='string':
					attvalue=attvalue[1:-1]
				elif valtype=='list':
					attvalue=attvalue[1:-1]
					attvalue=attvalue.split('|')

				attdata.update({attname:attvalue})
				
		if 'type' in attdata:
			True
		else:
			attdata.update({'type':'not specified'})

		return attdata

def isInt(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False

def isfloat(s):
    try: 
        float(s)
        return True
    except ValueError:
        return False
					
def switchBrack(data,fromdelim,todelim):
			datalist=list(data)
			inbrack=0
			for i,char in enumerate(datalist):
				if char=='[':
					inbrack=1
				if char==']':
					inbrack=0
				if inbrack ==1:
					if char==fromdelim:
						if data[i-1].isdigit():
							datalist[i]=todelim
			newdata=''.join(datalist)
			return newdata
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

        # actual device operation, start on main menu here
        device=init()
        mlist=['tape deck', 'backup tape','sample packs','system info','shutdown']
        alist=['synth', 'drum',' ']
        listMenuScroll(device,mlist,alist,'MAIN',None,True,False) #no exit

if __name__ == '__main__':
        main()
