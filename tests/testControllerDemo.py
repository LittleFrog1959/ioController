# This is a really simple demo of the Test Controller end of the TCP link
# Prints nicely formatted raw input from the IO Controller and then prints
# nicely formated lists that should have been loaded
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
                        # Tell the rest of the program that we're in sync
                        gotStart = True
                        row = 1
                # Print the lines of text we've received updating the current
                # row and trimming the contents of the receive buffer
                row, RxDBuffer = printLine (row, RxDBuffer)

def printLine (r, m):
    # This function could end up printing many lines of text...
    while (m.find ("\n")) != -1:
        # Slice off the string to print without the \r\n
        lineOfText = m[0:m.find ("\n") - 1]

        if (lineOfText.find ('g.iBoards') == 0) & (g.iBoards == None):
            # Create the lists needed to hold input information
            dump.write ('Loading up iBoards\n')
            exec (lineOfText)     # populate iBoard
            for p in range (0, g.iBoards):
                g.iState.append ([])
                g.iForce.append ([])
                g.iName.append ([])

        elif (lineOfText.find ('g.oBoards') == 0) & (g.oBoards == None):
            # Create the lists needed to hold input information
            dump.write ('Loading oBoards\n')
            exec (lineOfText)           # populate oBoard
            for p in range (0, g.oBoards):
                g.oState.append ([])
                g.oForce.append ([])
                g.oName.append ([])

        elif (g.iBoards != None) & (g.oBoards != None):
            # It is only safe to exec general lines of output once iBoards and oBoards
            # are populated
            # Under these circumstances, don't keep exec-ing the i/oBoard statements
            if (lineOfText.find ('g.iBoards = ') == -1) & (lineOfText.find ('g.oBoards = ') == -1):
                dump.write ('exec the following  ' + lineOfText + '\n')
                exec (lineOfText)
            else:
                dump.write ('Passing over i/oBoards exec\n')
        else:
            # We have to dump the lineOfText because it did not satify one
            # of the above conditions
            dump.write ('Throwing away ' + lineOfText + '\n')

        # Reset the row pointer every time we get iBoards
        if lineOfText.find ('g.iBoards') == 0:
            r = 1
            # And becuase we're at the start of the process, print out the lists
            if (g.iBoards != None) & (g.oBoards != None):
                printLists ()

        # Form the line to be printed from the time part of datetime, the row number
        # and the actual line of text
        outputLine = str (dt.datetime.now ())[17:] + " " + str (r) + " " + lineOfText
        ui.addstr (r, 0, outputLine)
        ui.clrtoeol ()
        ui.refresh ()
        r += 1
        # Now trim off what we just printed remembering that it's \r\n at the
        # end of the line
        m = m[m.find ("\n") + 1:]
    return r, m

def printLists ():
    # Print nicely formated lists that should have been loaded by the exec command in printLine
    # Start of the table to get out of the way of the raw text printout
    baseRow = 28
    lRow = 0
    ui.addstr (baseRow + lRow, 0, 'g,iBoards      ' + str (g.iBoards))
    ui.clrtoeol ()
    lRow += 1
    ui.addstr (baseRow + lRow, 0, 'g,oBoards      ' + str (g.oBoards))
    ui.clrtoeol ()
    lRow += 1
    # Single loop to print all the input information
    for pointer in range (0, g.iBoards):
        printRow (baseRow + lRow + 0, g.iState[pointer])
        printRow (baseRow + lRow + 1, g.iForce[pointer])
        printRow (baseRow + lRow + 2, g.iName[pointer])
        lRow += 3

    lRow += 1

    # And now the output  information
    for pointer in range (0, g.oBoards):
        printRow (baseRow + lRow + 0, g.oState[pointer])
        printRow (baseRow + lRow + 1, g.oForce[pointer])
        printRow (baseRow + lRow + 2, g.oName[pointer])
        lRow += 3

    ui.refresh ()

def printRow (pr, rowList):
    # Print the list of items on the supplied row
    for pointer in range (0, len (rowList)):
        ui.addstr (pr, pointer * 8, rowList [pointer]) 
        ui.clrtoeol ()

if __name__ == "__main__":
    # Create a screen device which does not echo keypresses to the screen
    # or wait for ENTER before returning keystrokes then call our application
    # in a way that makes the terminal recover if the program crashes
    ui = curses.initscr ()
    curses.noecho ()
    curses.cbreak ()
    curses.wrapper (main)
