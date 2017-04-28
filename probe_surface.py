#!/usr/bin/env python
#probing uneven surfaces with robots
#by Mike Erickstad using libraries developed by A J Mendez PhD

from numpy import arange
from lib import argv
from lib.grbl_status import GRBL_status
from lib.communicate import Communicate
from clint.textui import puts, colored
import time, readline
import numpy as np


args = argv.arg(description='Simple python grbl surface probe pattern')

DEBUG_VERBOSE = False

X_MAX = 2.5
Y_MAX = 2.0
X_STEP = 0.5
Y_STEP = 0.5
HIGH_Z = 0.020
LOW_Z = -0.030
PROBE_FEED_RATE = 0.2
DESCENT_SPEED = 2.0/60.0
DESCENT_TIME = HIGH_Z/DESCENT_SPEED

Surface_Data = np.empty([len(arange(0, X_MAX+X_STEP/2.0, X_STEP)),len(arange(0, Y_MAX+Y_STEP/2.0, Y_STEP))])

Z=HIGH_Z
converged = False

# get a serial device and wake up the grbl, by sending it some enters
with Communicate(args.device, args.speed, timeout=args.timeout, debug=args.debug, quiet=args.quiet) as serial:
    # wait for the arduino to be setup
    time.sleep(10)
    # set absolut coords
    command = "G90"
    try:
        serial.run(command)
    except KeyboardInterrupt:
        puts(colored.red('Emergency Feed Hold.  Enter "~" to continue'))
        serial.run('!\n?')
    # set standard units
    command = "G20"
    try:
        serial.run(command)
    except KeyboardInterrupt:
        puts(colored.red('Emergency Feed Hold.  Enter "~" to continue'))
        serial.run('!\n?')
    # get an index couter for storing the data
    num_x = -1
    # loop over X postions
    for X in arange(0, X_MAX+X_STEP/2.0, X_STEP):
        # increment the x axis index couter
        num_x=num_x+1
        # get an increment counter for the y axis also
        num_y=-1
        # loop over Y positions
        for Y in arange(0, Y_MAX+Y_STEP/2.0, Y_STEP):
            # increment the y axis counter
            num_y=num_y+1
            # inform the user of the surrent move
            puts(colored.yellow("going to x:{:.4f} and y:{:.4f}".format(X,Y)))
            # make  command to go to the next coordinate
            command = "G0 X{:.4f} Y{:.4f} Z{:.4f}".format(X,Y,HIGH_Z)
            if DEBUG_VERBOSE:
                print command
            # try to run the command
            try:
                serial.run(command)
            # allow for keyboard interupts
            except KeyboardInterrupt:
                puts(colored.red('Emergency Feed Hold.  Enter "~" to continue'))
                serial.run('!\n?')
            # construct a probe command string
            command = "G38.2 Z{:.4f} F{:.4f}".format(LOW_Z,PROBE_FEED_RATE)
            # try to run this prob command
            try:
                serial.run(command)
            # allow for keyboard interrupts
            except KeyboardInterrupt:
                puts(colored.red('Emergency Feed Hold.  Enter "~" to continue'))
                serial.run('!\n?')

            ##################################
            ### DETERMINE CONVERGANCE OF PROBE
            ##################################

            # converged boolean defaults to false during the begining of each probe cycle
            converged = False
            # lock into a while loop waiting for the convergence condition to be met
            while not converged:
                # check for convergenceevery 2 seconds
                time.sleep(2)
                # qurey GRBL for a atatus update
                status_report_string = serial.run('?',singleLine=True)
                # parse the string from GRBL
                current_status = GRBL_status().parse_grbl_status(status_report_string)
                print ''
                puts(colored.yellow(''.join('Z=' + '{:.4f}'.format((float(current_status.get_z()))))))
                #print 'z position :'
                #print float(current_status.get_z())
                if current_status.is_idle():
                    converged = True
                    Z=current_status.get_z()
                    Surface_Data[num_x,num_y] = Z
                if current_status.is_alarmed():
                    print 'PyGRBL: did not detect surface in specified z range, alarm tripped'
                    serial.run('$X')
                    serial.run("G0 X{:.4f} Y{:.4f} Z{:.4f}".format(X,Y,HIGH_Z))
                    break

            command = "G0 X{:.4f} Y{:.4f} Z{:.4f}".format(X,Y,HIGH_Z)
            if DEBUG_VERBOSE:
                print command
            try:
                serial.run(command)
            except KeyboardInterrupt:
                puts(colored.red('Emergency Feed Hold.  Enter "~" to continue'))
                serial.run('!\n?')

    command = "G0 X{:.4f} Y{:.4f} Z{:.4f}".format(0.0,0.0,HIGH_Z)
    if DEBUG_VERBOSE:
        print command
    try:
        serial.run(command)
    except KeyboardInterrupt:
        puts(colored.red('Emergency Feed Hold.  Enter "~" to continue'))
        serial.run('!\n?')

    command = "G0 X{:.4f} Y{:.4f} Z{:.4f}".format(0.0,0.0,0.0)
    if DEBUG_VERBOSE:
        print command
    try:
        serial.run(command)
    except KeyboardInterrupt:
        puts(colored.red('Emergency Feed Hold.  Enter "~" to continue'))
        serial.run('!\n?')


print Surface_Data
np.savetxt('probe_test.out', Surface_Data, delimiter=',',header='X_STEP:,{:.4f}, Y_STEP:,{:.4f},'.format(X_STEP,Y_STEP))

puts(
colored.green('''
gCode finished streaming!''') +
colored.red('''
!!! WARNING: Please make sure that the buffer clears before finishing...'''))
try:
  raw_input('<Press any key to finish>')
  raw_input('   Are you sure? Any key to REALLY exit.')
except KeyboardInterrupt as e:
  serial.run('!\n?')
  puts(colored.red('Emergency Stop! Enter "~" to continue. You can enter gCode to run here as well.'))
  while True:
      x = raw_input('GRBL> ').strip()
      serial.run(x)
      if '~' in x: break
