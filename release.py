import uuid

class Release:
    def __init__(self,id_):
        self.valid = True
        try:
            uuid.UUID(id_)
        except ValueError:
            print "Corrupt UUID given."
            self.valid = False
        else:
            self.id = id_

    def fetch(self):
        if not self.valid:
            return

        #Do fetching here

