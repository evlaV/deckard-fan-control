#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import glob
import argparse
import time
import subprocess

sensor_names = None

# EV2 Channels

# address 0x12
# CH 1 : Kryo APC1 Cores
# CH 2 : Kryo APC2 Cores
# CH 3 : Kryo APC0 Cores
# CH 4 : Tensor Processor – NSP1

ev2_channels_1 = ["APC1 Cores", "APC2 Cores", "APC0 Cores", "Tensor NSP1"]

# address 0x1a
# CH 1 : GFX Power
# CH 2 : Tensor Processor – NSP2
# CH 3 : VPH Power
# CH 4 : Unused

ev2_channels_2 = ["GFX", "Tensor NSP2", "VPH", "Unused"]

# address 0x10
# CH 1 : BOB 
# CH 2 : S6C ~1.9V Subregulation 
# CH 3 : S1C ~1.3V Subregulation
# CH 4 : S3C ~1V Subreulation 

ev2_channels_3 = ["BOB", "S6C", "S1C", "S3C"]

# EV3 Channels

# address 0x12
# CH 1 : Kryo APC0 Cores
# CH 2 : Kryo APC2 Cores
# CH 3 : Kryo APC1 Cores
# CH 4 : Tensor Processor – NSP1

ev3_channels_1 = ["APC0 Cores", "APC2 Cores", "APC1 Cores", "Tensor NSP1"]

# address 0x1a
# CH 1 : GFX Power
# CH 2 : Tensor Processor – NSP2
# CH 3 : Bob Power
# CH 4 : Unused

ev3_channels_2 = ["GFX", "Tensor NSP2", "BOB", "Unused"]

# address 0x10
# CH 1 : VPH
# CH 2 : S6C ~1.9V Subregulation 
# CH 3 : S3C ~1.3V Subregulation
# CH 4 : S1C ~1V Subreulation 

ev3_channels_3 = ["VPH", "S6C", "S3C", "S1C"]

default_sample_time_msec = 1000


def get_paths():
    folders = ['/sys/class/hwmon/hwmon']
    paths = []

    for f in folders:
        # Get every enumerated hwmon item
        t_folders = glob.glob(f + '*')

        for sf in t_folders:
            # Check if it has a name
            name_file = os.path.join(sf, 'name')
            if not os.path.exists(name_file):
                # Not a valid folder
                continue

            name = None
            with open(name_file, 'r') as fd:
                name = fd.read().strip()

            if name != 'max34417':
                # Not a valid power monitor 
                continue
            paths.append(sf)
    return paths

def enable_measurement():
    paths = get_paths()
    for sf in paths:
        # turn on single measurement mode 
        mode_file = os.path.join(sf, 'measurement_mode')
        with open(mode_file, 'w') as fd:
            fd.write("normal")

def get_powers():
    powers = []
    paths = get_paths()

    # Get the device model
    process = subprocess.run(['vrdevice_path', 'model'], capture_output=True, text=True)

    # determine which monitor we have found
    for sf in paths:
        node_file = os.path.join(sf, 'of_node/reg')
        with open(node_file, 'r') as fd:
            reg = fd.read()
            channels = []
            for c in reg:
                if ord(c) == 0x12:
                    if "EV1" in process.stdout or "EV2" in process.stdout:
                        channels = ev2_channels_1
                    else:
                        channels = ev3_channels_1
                elif ord(c) == 0x1a:
                    if "EV1" in process.stdout or "EV2" in process.stdout:
                        channels = ev2_channels_2
                    else:
                        channels = ev3_channels_2
                elif ord(c) == 0x10:
                    if "EV1" in process.stdout or "EV2" in process.stdout:
                        channels = ev2_channels_3
                    else:
                        channels = ev3_channels_3
            if channels == []: 
                print("Unknown power monitor reg {:s}".format(reg))
           
            # read power averages 
            for i in range(1,5):
                sensor_file = os.path.join(sf, 'power' + str(i) + '_average')
                # Read power 
                with open(sensor_file, 'r') as fd:
                    power = int(fd.read())
                    powers.append((channels[i-1], power))

    # Sort the Sensors by name
    #powers.sort(key=lambda x: x[0])

    return powers 

def get_voltages():
    voltages = []
    paths = get_paths()

    # Get the device model
    process = subprocess.run(['vrdevice_path', 'model'], capture_output=True, text=True)

    # determine which monitor we have found
    for sf in paths:
        node_file = os.path.join(sf, 'of_node/reg')
        with open(node_file, 'r') as fd:
            reg = fd.read()
            channels = []
            for c in reg:
                if ord(c) == 0x12:
                    if "EV1" in process.stdout or "EV2" in process.stdout:
                        channels = ev2_channels_1
                    else:
                        channels = ev3_channels_1
                elif ord(c) == 0x1a:
                    if "EV1" in process.stdout or "EV2" in process.stdout:
                        channels = ev2_channels_2
                    else:
                        channels = ev3_channels_2
                elif ord(c) == 0x10:
                    if "EV1" in process.stdout or "EV2" in process.stdout:
                        channels = ev2_channels_3
                    else:
                        channels = ev3_channels_3
            if channels == []: 
                print("Unknown power monitor reg {:s}".format(reg))
           
            # read voltages 
            for i in range(0,4):
                sensor_file = os.path.join(sf, 'in' + str(i) + '_input')
                # Read power 
                with open(sensor_file, 'r') as fd:
                    voltage = int(fd.read())
                    voltages.append((channels[i], voltage))

    # Sort the Sensors by name
    #powers.sort(key=lambda x: x[0])

    return voltages

def print_info(powers,voltages,sampletime,gpupower,gpuvoltage,cpupower):
    sum = 0
    cores = 0
    vph = 0
    gpu = 0
    for p in powers:
#       print('{: >20s}: {:0.04f}'.format(p[0], p[1]/1000000))
        if ( p[0] != "VPH"):
            sum += p[1]/1000000
        if "Cores" in p[0] or "Tensor" in p[0]:
            cores += p[1]/1000000
        if p[0] == "VPH":
            vph += p[1]/1000000
        if p[0] == "GFX":
            gpu += p[1]/1000000

    if gpupower == 1:
        print("gpupower: {:0.04f}".format(gpu))

    if cpupower == 1:
        print("cpupower: {:0.04f}".format(cores))

    if gpuvoltage == 1:
        for v in voltages:
            if v[0] == "GFX":
                print('gpuvoltage: {:0.04f}'.format(v[1]/1000))

    if (gpupower == 1) or (cpupower == 1) or (gpuvoltage == 1):
        return

    ''' MAX34417 Power and Voltage results '''
    print(f'MAX34417 Power and Voltage results [ {sampletime} ms ]')
    print('---- Power Monitor Rails (W) ----')


    for p in powers:
        print('{: >20s}: {:0.04f}'.format(p[0], p[1]/1000000))


    print('\n ---- Power Monitor Groups (W) ----')
    print("{: >20s}: {:0.04f}".format('VPH Total',vph))
    print("{: >20s}: {:0.04f}".format("Cores", cores))
    print("{: >20s}: {:0.04f}".format("GPU", gpu))
    print("{: >20s}: {:0.04f}".format("VPH Other",vph -sum))
    
    print('\n ---- Voltage Rails (V) ----')

    for v in voltages:
        print('{: >20s}: {:0.04f}'.format(v[0], v[1]/1000))

    print('\n ---- Measurement Location ----')
    print("{: >20s}: {}".format('VPH ', 'PM8550BHS VPH'))
    print("{: >20s}: {}".format('APC1', 'PM8550VS_E S1E,S2E,S3E'))
    print("{: >20s}: {}".format('APC2', 'PM8550VS_E S4E,S5E'))
    print("{: >20s}: {}".format('APC0', 'PM8550VS_E S6E'))
    print("{: >20s}: {}".format('GFX ', 'PM8550VS_D S1D,S2D,S5D,S6D'))
    print("{: >20s}: {}".format('NSP1', 'PM8550VE_I S6I,S7I'))
    print("{: >20s}: {}".format('NSP2', 'PM8550VS_G S1G,S2G'))
    print("{: >20s}: {}".format('BOB ', 'PM8550 INPUT (includes BOB1/BOB2)'))
    print("{: >20s}: {}".format('Misc', 'PM8550VS_C S1C,S3C,S6C'))

def main():
    ''' start power monitors, let them accumulate, and read results '''
    parser = argparse.ArgumentParser(
        description='Display POCF Power Monitor Data')
    parser.add_argument('-s', '--sample_time_msec', type=int, default=default_sample_time_msec,
                        help='time in msec to wait to read results ( 1kHz sample rate )')

    parser.add_argument('--cpupower', action='store_true')   

    parser.add_argument('--gpupower', action='store_true')   

    parser.add_argument('--gpuvoltage', action='store_true')

    args = parser.parse_args()

    if get_paths() == []:
        print("Error: Could not find MAX34417 HWMON")
        return -1

    enable_measurement()

    # allow measurements to accumulate
    # setting measurement mode resets accumulator
    # each read of a channel resets accumulator for the next one
    # sample rate is 1 kHz, so this defines number of samples before reading
    # defaulting to 2 seconds for default watch time
    time.sleep(args.sample_time_msec/1000)

    # get results
    powers = get_powers()
    voltages = get_voltages()
    gpupower=args.gpupower
    cpupower=args.cpupower
    gpuvoltage=args.gpuvoltage
    print_info(powers,voltages,args.sample_time_msec,gpupower,gpuvoltage,cpupower)

    return 0

if __name__ == "__main__":
    # Run Main
    sys.exit(main())
