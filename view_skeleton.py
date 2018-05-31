# Copyright (c) 2015, Disney Research
# All rights reserved.
#
# Author(s): Sehoon Ha <sehoon.ha@disneyresearch.com>
# Disney Research Robotics Group
import sys
from pydart2.gui.pyqt5.window import PyQt5Window
from pydart2.gui.trackball import Trackball
import pydart2 as pydart
import argparse

def getViewer(sim, title=None):
	win = PyQt5Window(sim, title)
	win.scene.add_camera(Trackball(theta=0, phi = 0, zoom=1.2,trans=[0,0.0,-30]), 'Hopper_camera')
	win.scene.set_camera(win.scene.num_cameras()-1)
	#win.run()
	return win

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Views a skel file")

    parser.add_argument("--skel", dest="skel_path", default=False)

    args = parser.parse_args()

    pydart.init(verbose=True)
    print('pydart initialization OK')

    world = pydart.World(0.0002, args.skel_path)
    print('pydart create_world OK')

    window = getViewer(world)
    window.run()
