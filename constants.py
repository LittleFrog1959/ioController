# Constants used by the testController and ioController programs

class constants ():
    # The number of pins on an ABE PIO board port
    pinsPerBoard = 16

    # A pair lists describing the I2C ports used by the I/O boards
    oBoard = [0x20, 0x22, 0x24, 0x26]
    iBoard = [0x21, 0x23, 0x25, 0x27]

    # The directory into which we put run time log files
    logDirectory = 'logs/'

    # The file extenion used by run time logs (the filename is the
    # date/time)
    logExtension = '.log'

    # The symbolic filename we create at program start so that you
    # can always go to a fixed place when looking for the latest log
    symbolicLogFilename = 'log.log'

    # Max age of log files in minutes.  Anything older than this is
    # deleted when the program starts.  This purge does NOT happen
    # when the program's running
    logAge = 10

    # The max number of messages we can have in the message text box
    # before we loose some off the bottom of the screen.
    messageRowMax = 20

    # Resolution of the touch screen
    touchScreenResolution = '1280x800'

    # TCP/IP ports
    tcpControlPort = 10000
    tcpDataPort = 10001

    #tkInter colours and other bits and bobs
    normalGrey = '#d9d9d9'
    brightGrey = "#e9e9e9"
