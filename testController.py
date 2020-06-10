# This is a really simple demo of the Test Controller end of the TCP link

import socket
import sys
import time
import os
import errno
import curses

import datetime as dt

dump = open ("dump.txt", "w")

# Set up a couple of variables to hold IO Controller sizing
global iBoards, oBoards
iBoards = None
oBoards = None


# Tell this program where the server is
serverIPAddress = '192.168.1.101'
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
                    dump.write ("\r\nGot the following from the port\r\n")
                    dump.write (RxD)
                    dump.write ("\r\nThat was the port input\r\n")
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
                    if RxDBuffer.find ('iBoards') != -1:
                        # Delete everything upto the iBoards text
                        RxDBuffer = RxDBuffer[RxDBuffer.find ('iBoards'):]
                        gotStart = True
                        dump.write ("\r\nSet gotStart True\r\n")
                        row = 1
                        row, RxDBuffer = printLine (row, RxDBuffer)
                else:
                    # We have already detected the start of packet so
                    # just print out what comes in UNLESS we find another start
                    # of packet in which case reset the row pointer
                    if RxDBuffer.find ('iBoards') != -1:
                        dump.write ("\r\nReset row counter\r\n")
                        row = 1
                    row, RxDBuffer = printLine (row, RxDBuffer)

def printLine (r, m):
    dump.write ('\r\nEntered printLine with \r\n')
    dump.write (m)
    dump.write ('\r\nThat was what we entered printLine with\r\n')

    # This function could end up printing many lines of text...
    while (m.find ("\n")) != -1:
        # Slice off the string to print without the \r\n
        lineOfText = m[0:m.find ("\n") - 1]

        # Process the line we've just received

        if (lineOfText.find ('iBoards') == 0) and (iBoards == None):
            # Create the lists needed to hold input information
            print ("£" + lineOfText)
            exec (lineOfText)     # populate iBoard
            print (str (iBoards))
            time.sleep (10)
            dump.write (lineOfText + "\r\n")
            for p in range (0, iBoards):
                iState.append ([])
                iForce.append ([])
                iName.append ([])
        if (lineOfText.find ('oBoards') == 0) and (oBoards == None):
            # Create the lists needed to hold input information
            exec (lineOfText)           # populate oBoard
            dump.write (lineOfText + "\r\n")
            for p in range (0, oBoards):
                oState.append ([])
                oForce.append ([])
                oName.append ([])

        # It should be safe to exec anything now
        exec (lineOfText)

        dump.write ("\r\nhere's what we printed\r\n")
        dump.write (lineOfText)
        dump.write ("\r\nThat's what we printed\r\n")
        ui.addstr (r, 0, str (dt.datetime.now ())[17:] + " " + str (r) + " " + lineOfText)
        ui.clrtoeol ()
        ui.refresh ()
        r += 1
        # Now trim off what we just printed remembering that it's \r\n at the
        # end of the line
        m = m[m.find ("\n") + 1:]
    dump.write ('\r\nLeft printLine with \r\n')
    dump.write (m)
    dump.write ("\r\nThats what we left printLine with\r\n")
    return r, m

if __name__ == "__main__":
    # Create a screen device which does not echo keypresses to the screen
    # or wait for ENTER before returning keystrokes then call our application
    # in a way that makes the terminal recover if the program crashes
    ui = curses.initscr ()
    curses.noecho ()
    curses.cbreak ()
    curses.wrapper (main)
