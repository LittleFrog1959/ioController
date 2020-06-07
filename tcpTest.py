# Quick TCP server test program

import socket
import sys
import time
import os
import errno

# Before we start on the actual TCP stuff, work out the IP address
# of eth0 which we're going to use to connect to the other devices
# in the system
ipAddress = os.popen ('ip addr show eth0').read().split ("inet ")[1].split ("/")[0]

# Create a server which can handle just one client connection
# at a time
tcpServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the connection to a port
tcpServer.bind ((ipAddress, 10000))

# Allow for the port to be re-used immediately
tcpServer.setsockopt( socket.SOL_SOCKET, socket.SO_REUSEADDR, 1 )

# Make all operations with the socket non-blocking
tcpServer.setblocking (0)

# Start listening for an incoming connection
tcpServer.listen (1)

while True:
    print ("Listening")

    while True:
        clientSocket = None
        try:
            (clientSocket, address) = tcpServer.accept ()
        except:
            pass
        if (clientSocket != None):
            break

    print (clientSocket)
    print (address)

    clientSocket.setblocking (0)

    RxDBuffer = ""

    while True:
        try:
            RxD = clientSocket.recv (1024)
        except socket.error as e:
            err = e.args [0]
            if (err == errno.EAGAIN) or (err == errno.EWOULDBLOCK):
                pass
            else:
                # This is a real error while waiting for incoming
                # data
                print (e)
                sys.exit (1)
        else:
            if (len (RxD) == 0):
                break
            else:
                # Append the incoming bytes to the string (decode
                # converts the bytes to a string)
                RxDBuffer = RxDBuffer + RxD.decode ()
                print ("RxD Buffer contains " + RxDBuffer)
                EOLPosition = RxDBuffer.find ('\r\n')
                if (EOLPosition == -1):
                    print ('Input is not terminated correctly ' + RxDBuffer)
                else:
                    print ('Input is fine ' + RxDBuffer[0:EOLPosition + 1])
                    RxDBuffer = RxDBuffer[EOLPosition + 2:]

