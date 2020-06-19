# This is a really simple demo of the Test Controller end of the TCP link

import socket
import sys
import time
import os
import errno
import curses
import datetime as dt

dump = open ("dump.txt", "w")

## Set up a couple of variables to hold IO Controller sizing
#global iBoards, oBoards
#iBoards = None
#oBoards = None

class globals ():
    iBoards = None
    oBoards = None
    iState = []
    iForce = []
    iName = []
    oState = []
    oForce = []
    oName = []

g = globals ()

# Tell this program where the server is
serverIPAddress = '192.168.1.106'
serverIPPort = 10001

# Learn our IP address
ipAddress = os.popen ('ip addr show eth0').read().split ("inet ")[1].split ("/")[0]

# Create a TCP client with a timeout on how long we wait
client = socket.socket (socket.AF_INET, socket.SOCK_STREAM)
client.settimeout (1)

def main (ui, *args):
    # Go into loop waiting for server to appear
    while True:
        try:
            client.connect ((serverIPAddress, serverIPPort))
        except:
            ui.addstr (0, 0, 'Server not found')
            ui.refresh ()
        else:
            # We've got a connect, wait for incoming messages and also wait until
            # we get the iBoards message which is basically the start of a packet
            # of information
            gotStart = False
            RxDBuffer = ""
            while True:
                try:
                    # Grab the incoming bytes and convert to a string using default
                    # encoding
                    RxD = client.recv (1024).decode ()
                    RxDBuffer = RxDBuffer + RxD
                except KeyboardInterrupt:
                    curses.echo ()
                    curses.nocbreak ()
                    curses.endwin ()
                    sys.exit ()
                except:
                    ui.addstr (0, 0, 'Error')
                    ui.refresh ()

                if gotStart == False:
                    # We don't have the start of the packet yet
                    if RxDBuffer.find ('g.iBoards') != -1:
                        # Delete everything upto the iBoards text
                        RxDBuffer = RxDBuffer[RxDBuffer.find ('g.iBoards'):]
                        gotStart = True
                        row = 1
                else:
                    row, RxDBuffer = printLine (row, RxDBuffer)

def printLine (r, m):
    # This function could end up printing many lines of text...
    while (m.find ("\n")) != -1:
        # Slice off the string to print without the \r\n
        lineOfText = m[0:m.find ("\n") - 1]
        if (lineOfText.find ('g.iBoards') == 0) and (g.iBoards == None):
            # Create the lists needed to hold input information
            dump.write  ("******" + lineOfText + "*******\n")
            exec (lineOfText)     # populate iBoard
            dump.write ("xxxxx" + str (g.iBoards) + "xxxxx")
            for p in range (0, g.iBoards):
                g.iState.append ([])
                g.iForce.append ([])
                g.iName.append ([])
        if (lineOfText.find ('g.oBoards') == 0) and (g.oBoards == None):
            # Create the lists needed to hold input information
            exec (lineOfText)           # populate oBoard
            for p in range (0, g.oBoards):
                g.oState.append ([])
                g.oForce.append ([])
                g.oName.append ([])

        # It should be safe to exec anything now
        exec (lineOfText)
        if lineOfText.find ('g.iBoards') == 0:
            r = 1

        outputLine = str (dt.datetime.now ())[17:] + " " + str (r) + " " + lineOfText
        ui.addstr (r, 0, outputLine)
        ui.clrtoeol ()
        ui.refresh ()
        r += 1
        # Now trim off what we just printed remembering that it's \r\n at the
        # end of the line
        m = m[m.find ("\n") + 1:]
    return r, m

if __name__ == "__main__":
    # Create a screen device which does not echo keypresses to the screen
    # or wait for ENTER before returning keystrokes then call our application
    # in a way that makes the terminal recover if the program crashes
    ui = curses.initscr ()
    curses.noecho ()
    curses.cbreak ()
    curses.wrapper (main)
