f = open ("log.txt", "w")
f.write ("Hello")
f.write ("Goodbye")
f.close ()


def initLog ():
    return open ("log.txt", "w")

def addLog (m):
    h.write (m)

h = initLog ()
# h.write ("lobster\n")

addLog ("June")

h.close ()

