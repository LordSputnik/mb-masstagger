import imp
import os

import Warp.plugins

def LoadPlugins():
    for directory, directories, filenames in os.walk("./Warp/plugins"):
        for filename in filenames:
            print filename
            file_minus_ext, ext = os.path.splitext(filename)
            if ext == ".py":
                print filename
                info = imp.find_module(file_minus_ext,["./Warp/plugins"])
                print "Found module {}".format(info)
                imp.load_module("Warp.plugins."+file_minus_ext, *info)
            