import imp
import os

import plugins
import utils

def LoadPlugins():
    for directory, directories, filenames in os.walk("./Warp/plugins"):
        for filename in filenames:
            file_minus_ext, ext = os.path.splitext(filename)
            if ext == ".py":
                info = imp.find_module(file_minus_ext,["./Warp/plugins"])
                utils.safeprint( u"Found module {}".format(info) )
                imp.load_module("plugins."+file_minus_ext, *info)
            