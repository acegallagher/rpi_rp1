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
# 1: menu    -- entries that get displayed as menu lists
# 2: actions -- entries that have 'actions' that run (i.e. functions... such as backing up tape)

# A Menu consists of one or more sub-Menu objects that a user can choose
# to run or subroutines that the user can call.
class Menu:

    # Constructor
    def __init__(self, name):
        self.entries = {} 
        self.heading = name

    # Adds an option to this Menu. An option consists of a number,
    # name, and the actual object it corresponds to (submenu or procedure).
    # The last value in each key-value pair denotes whether the given option
    # should trigger an exit from the current Menu after it is called.
    def addAction(self, entryNumber, actionName, action, TriggersExit):
        self.entries[entryNumber] = [actionName, action, TriggersExit]

    def addSubMenu(self, entryNumber, optionName, menu):
        self.entries[entryNumber] = [optionName, menu, False]

    # Returns the number of options in this Menu
    def size(self):
        return len(self.options)

    # Displays this Menu's error text
    def displayError(self):
        print("\n{}\n".format(self.errorText))

    # Prints the Menu in its entirety
    def display(self):
        print(self.prompt)
        for i in range(1, self.size()+1):
            print("{} - {}".format( i, self.options[i][0] ))
        print()

    # Runs this Menu
    def run(self):
        userInput = ""
        self.display()
        while True:
            userInput = input("Your selection: ")
            try:
                userInput = int(userInput)
                if userInput <= 0 or userInput > self.size():
                    self.displayError()
                else:
                    # If the menu option is a function, call it
                    if callable(self.options[userInput][1]):
                        self.options[userInput][1]()
                        # And if it's an option that triggers a return/exit, then return after it's called
                        if self.options[userInput][2]:
                            return
                        # Otherwise, redisplay the menu options
                        else:
                            self.display()
                    # But if the menu option is a submenu, run it
                    else:
                        self.options[userInput][1].run()
                        # And display the calling menu's options again upon return from the submenu
                        self.display()
            except ValueError:
                self.displayError()

class Action: 

    # Constructor
    def __init__(self, name, function):
        self.title  = name
        self.action = function

    def name(self):
        return self.name


def Exit():
    print("\n\tThanks for using my program!\n")

def Return():
    return

def Option1():
    values = input("\n\tEnter some values: ")
    print("\n\tYou entered these values:", end=" ")
    for i in range(0, len(values)):
        print(values[i], end=" ")
    print()

def MyLife():
    print("\n\tLife's hard.\n")

def GettingHelp():
    print("\n\tRecursion jokes suck\n")

def Placeholder():
    print("functions haven't been implemented yet")

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
        # device=init()
        # mlist=['tape deck', 'backup tape','sample packs','system info','shutdown']
        # alist=['synth', 'drum',' ']
        # listMenuScroll(device,mlist,alist,'MAIN',None,True,False) #no exit

        # there will be the main menu 
        mainMenu = Menu("MAIN")

        # and these will be entries in the menu
        tapeDownMenu = Menu("MAIN>TAPES") # a menu that lists the tapes on the rpi, available for upload to the OP1
        

['tape deck', 'backup tape','sample packs','system info','shutdown']
    
        menu1 = Menu()
        menu1.addOption(1, "Option1", Option1, False)
        menu1.addOption(2, "Return", Return, True)
    
        menu2 = Menu()
        menu2.setPrompt("\nWhat would you like help with?")
        menu2.addOption(1, "My life", MyLife, False)
        menu2.addOption(2, "Getting help", GettingHelp, False)
        menu2.addOption(3, "Return", Return, True)
    
        mainMenu.addOption(1, "Enter new values", menu1, False)
        mainMenu.addOption(2, "Help", menu2, False)
        mainMenu.addOption(3, "Exit", Exit, True)
        mainMenu.run()  


if __name__ == '__main__':
        main()


