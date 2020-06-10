a = 5

class xxx ():
    def test (self):
        print (dir ())

        exec ("exec ('a = 2')")

        print (dir ())
        print (a)

x = xxx()

x.test ()

exec ("print (dir ())")
