# This program has two functions;
# 1.    Connect to the Data Port on the IO Controller and suck in the incoming stream
#       which is printed as a nicely formatted lists that should have been loaded
#       from the IO Controller and then exec'ed into the global variable space of this
#       program.
# 2.    Connect to the Control Port on the IO Controller and send out commands to
#       change variables in its global variable space.  This is effectivly a test bed
#       for making the incoming side of the Control Port more robust (actually so
#       it looks more like the incoming side of this program).

import socket
import sys
import os
import curses
import datetime as dt

# Debug file
dump = open ("dump.txt", "w")

## Set up a couple of variables to hold IO Controller sizing

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

# Tell this program where the servers are
dataIPAddress = '192.168.1.106'
dataIPPort = 10001
controlIPAddress = '192.168.1.106'
controlIPPort = 10000

# Learn our IP address.  Actually we don't need this right now
ipAddress = os.popen ('ip addr show eth0').read().split ("inet ")[1].split ("/")[0]

# Create a TCP client for the Data Port and Control Port with a timeout on how long we wait
dataClient = socket.socket (socket.AF_INET, socket.SOCK_STREAM)
dataClient.settimeout (1)
controlClient = socket.socket (socket.AF_INET, socket.SOCK_STREAM)
controlClient.settimeout (1)

def main (ui, *args):
    # Go into loop waiting for the Data Port to appear
    while True:
        try:
            dataClient.connect ((dataIPAddress, dataIPPort))
            logMsg ('Data Port connected')
        except:
            ui.addstr (0, 0, str (dt.datetime.now ()) + ' Data Port not found')
            logMsg ('Data Port not found')
            ui.refresh ()
        else:
            try:
                # Now try to get the Control Port to connect
                controlClient.connect ((controlIPAddress, controlIPPort))
                logMsg ('Control Port connected')
            except:
                ui.addstr (0, 40, str (dt.datetime.now ()) + ' Control Port not found')
                logMsg ('Control Port not found')
                ui.refresh ()
            else:
                # We've got a connect on both the Data and Control ports.  Wait for incoming
                # messages and also wait until we get the iBoards message which is basically
                # the start of a packet of information
                gotStart = False
                dataRxDBuffer = ''
                controlRxDBuffer = ''
                while True:
                    try:
                        # Grab the incoming bytes and convert to a string using default
                        # encoding
                        dataRxD = dataClient.recv (1024).decode ()
                        dataRxDBuffer = dataRxDBuffer + dataRxD
                    except KeyboardInterrupt:
                        curses.echo ()
                        curses.nocbreak ()
                        curses.endwin ()
                        sys.exit ()
                    except:
                        ui.addstr (0, 0, str (dt.datetime.now ()) + ' Data Port Error')
                        logMsg ('Data Port Error')
                        ui.refresh ()

                    if gotStart == False:
                        # We don't have the start of the packet yet
                        if dataRxDBuffer.find ('g.iBoards') != -1:
                            # Delete everything upto the iBoards text
                            dataRxDBuffer = dataRxDBuffer[dataRxDBuffer.find ('g.iBoards'):]
                            # Tell the rest of the program that we're in sync
                            gotStart = True
                    # row and trimming the contents of the receive buffer
                    dataRxDBuffer = execLinesOfText (dataRxDBuffer)

                    # Now have a look at the Control Port
                    try:
                        controlRxD = controlClient.recv (1024).decode ()
                        controlRxDBuffer = controlRxDBuffer + controlRxD
                    except KeyboardInterrupt:
                        curses.echo ()
                        curses.nocbreak ()
                        curses.endwin ()
                        sys.exit ()
                    except:
                        ui.addstr (0, 40, str (dt.datetime.now ()) + ' Control Port Error')
                        logMsg ('Control Port Error')
                        ui.refresh ()
                    else:
                        controlRxDBuffer = processControlRxD (controlRxDBuffer)

def processControlRxD (m):
    # Simply send income messages from the control port to the dump file for now
    dLine = 1
    while (m.find ('\n') != -1):
        lineOfText = m[0:m.find ('\n') - 1]
        logMsg ('From the control port ' + str (dLine) + ' ' + lineOfText)
        dLine += 1
        m = m[m.find ("\n") + 1:]

def execLinesOfText (m):
    # This function could end up processing many lines of text...
    while (m.find ("\n")) != -1:
        # Slice off the string to print without the \r\n
        lineOfText = m[0:m.find ("\n") - 1]

        if (lineOfText.find ('g.iBoards') == 0) & (g.iBoards == None):
            # Create the lists needed to hold input information
            logMsg ('Loading up iBoards')
            exec (lineOfText)     # populate iBoard
            for p in range (0, g.iBoards):
                g.iState.append ([])
                g.iForce.append ([])
                g.iName.append ([])

        elif (lineOfText.find ('g.oBoards') == 0) & (g.oBoards == None):
            # Create the lists needed to hold input information
            logMsg ('Loading oBoards')
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
#                logMsg ('exec the following  ' + lineOfText)
                exec (lineOfText)
            else:
                logMsg ('Passing over i/oBoards exec because they are already loaded')
        else:
            # We have to dump the lineOfText because it did not satify one
            # of the above conditions
            logMsg ('g.iBoards and/or g.oBoards are not valid.  Throwing away ' + lineOfText)

        # Reset the row pointer every time we get iBoards
        if lineOfText.find ('g.iBoards') == 0:
            # When we're printing the first row then print out the lists
            # if they've been populated
            if (g.iBoards != None) & (g.oBoards != None):
                printLists ()

        # Now trim off what we just printed remembering that it's \r\n at the
        # end of the line
        m = m[m.find ("\n") + 1:]
    return m

def printLists ():
    # Print nicely formated lists that should have been loaded by the exec command in execLinesOfText
    # Start of the table to get out of the way of the raw text printout
    lRow = 1
    ui.addstr (lRow, 0, 'g,iBoards      ' + str (g.iBoards))
    ui.clrtoeol ()
    lRow += 1
    ui.addstr (lRow, 0, 'g,oBoards      ' + str (g.oBoards))
    ui.clrtoeol ()
    lRow += 1
    # Single loop to print all the input information
    for pointer in range (0, g.iBoards):
        printRow (lRow + 0, g.iState[pointer])
        printRow (lRow + 1, g.iForce[pointer])
        printRow (lRow + 2, g.iName[pointer])
        lRow += 3

    lRow += 1

    # And now the output  information
    for pointer in range (0, g.oBoards):
        printRow (lRow + 0, g.oState[pointer])
        printRow (lRow + 1, g.oForce[pointer])
        printRow (lRow + 2, g.oName[pointer])
        lRow += 3

    ui.refresh ()

def printRow (pr, rowList):
    # Print the list of items on the supplied row
    for pointer in range (0, len (rowList)):
        ui.addstr (pr, pointer * 10, rowList [pointer])
        ui.clrtoeol ()

def logMsg (m):
    # Print a nicely formatted message to the program dump file
    dump.write (str (dt.datetime.now ())[17:] + ' ' + m + '\n')
    dump.flush ()

if __name__ == "__main__":
    # Create a screen device which does not echo keypresses to the screen
    # or wait for ENTER before returning keystrokes then call our application
    # in a way that makes the terminal recover if the program crashes
    ui = curses.initscr ()
    curses.noecho ()
    curses.cbreak ()
    curses.wrapper (main)
