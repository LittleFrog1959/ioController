import datetime as dt
import os

import constants
c = constants.constants ()

import globals
g = globals.ioGlobals ()

# Logging system for ioController and testController

class log ():
    # Very simple logging system.  Just formats the supplied message with a timestamp
    # and a level (which defaults to "debug").  Outputs the message to a TCP data client
    # if it's connected

    def __init__ (self):
        # Open a file on the local drive to which we're going to send all the logging
        # messages.  Note that errors here are printed (rather than logged) because
        # the log file is not set up until we exit so printing is the least-worst
        # thing to do

        # First we need to create a log directory if there's not one already
        try:
            os.mkdir (c.logDirectory)
            print ('Created log directory: ' + c.logDirectory)

        except FileExistsError:
            # We got an error because the logs directory already exists.  Now we need
            # to delete all the old log files.  Work out the cut off for deleting them
            cutOff = dt.datetime.now () - dt.timedelta (minutes = c.logAge)

            try:
                # Work through ALL of the files in the logs directory.  This might be
                # an error (maybe we should only look for old .log files)

                for filename in os.listdir (c.logDirectory):
                    fullFilename = c.logDirectory + filename
                    # Get the last modified date/time
                    fileTime = dt.datetime.fromtimestamp (os.stat (fullFilename).st_mtime)
                    # Delete the file if we should do

                    if cutOff > fileTime:
                        os.remove (fullFilename)
                        print ('Removed log file: ' + fullFilename)
            except Exception as ex:
                template = 'An exception of type {0} occurred. Arguments:\n{1!r}'
                message = template.format(type(ex).__name__, ex.args)
                print ('Trying to delete old log files')
                print (message)

        except Exception as ex:
            template = 'An exception of type {0} occurred. Arguments:\n{1!r}'
            message = template.format(type(ex).__name__, ex.args)
            print ('Trying to make a log file directory')
            print (message)
        # Construct the file name from the D-M-Y H:M:S part of the datetime and remove
        # any spaces because it makes working with the resulting file name easier
        f = str (dt.datetime.now ())[0:19].replace (' ', '_')

        # Return the file handle while opening the log file
        self.logFileHandle = open (c.logDirectory + f + c.logExtension, 'w')

        # Create a symbolic link to this file so that it's easy to refer to the current
        # log file for external programs (like tail -F) but first delete the existing
        # symlink if we find it
        try:
            os.unlink (c.symbolicLogFilename)
        except FileNotFoundError:
            # Ignore this error as it's just that the program has never been run before
            # and so there's no link file to unlink from
            pass
        except Exception as ex:
            template = 'An exception of type {0} occurred. Arguments:\n{1!r}'
            message = template.format(type(ex).__name__, ex.args)
            print ('Unknown error while unlinking symbolic log file')
            print (message)

        # Create the new link
        os.symlink (c.logDirectory + f + c.logExtension, c.symbolicLogFilename)

        self.logDiskMsg ('')
        self.logDiskMsg ('Starting disk log')
        self.logDiskMsg ('')

    def logDiskMsg (self, message, level = 'debug'):
        # Print the supplied message to the disk and pre-pend it with the date/time
        # and level (if supplied)
        # I don't bother to wrap the message to the disk in any kind of nice way
        # but it does get wrapped when being presented on the messagePage

        # Grab the current time
        t = str (dt.datetime.now ())

        # And form the message with the level padded to 10 chars
        m = t + ' ' + '{:<10}'.format (level) + message

        # Now send the message to the log file
        self.logFileHandle.write (m + '\r\n')

        # Simple flush every time I write  to the disk.  I might put this in a timer
        # later on
        self.logDiskFlush ()

        # And finally return the message so it can be sent elsewhere if required
        return m

    def logDiskClose (self):
        self.logFileHandle.close ()

    def logDiskFlush (self):
        self.logFileHandle.flush ()

