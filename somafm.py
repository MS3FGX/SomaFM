#!/usr/bin/env python3
# Python frontend for playing SomaFM with MPlayer
# Written by Tom Nardi (MS3FGX@gmail.com)
# Licensed under the GPLv3, see "COPYING"
version = "1.1"

import re
import os
import sys
import pickle
import shutil
import signal
import requests
import argparse
import colorama
import subprocess
from datetime import datetime
from colorama import Fore, Style
from collections import OrderedDict

# Default quality (0 is highest available)
quality_num = 0

# Default channel to play
default_chan = "Groove Salad"

# Enable/Disable experimental desktop notifications
desktop_notifications = False

# Following variables should probably be left alone
#-----------------------------------------------------------------------

# SomaFM channel list
url = "https://somafm.com/channels.json"

# Directory for cache
cache_dir = "/tmp/soma_cache"

# Directory for channel icons
icon_dir = cache_dir + "/icons"

# Default image size for icons
image_size = "xlimage"

# File name for channel cache
channel_file = cache_dir + "/channel_list"

# Define functions
#-----------------------------------------------------------------------#
# Catch ctrl-c
def signal_handler(sig, frame):
    print(Fore.RED + "Force closing...")
    # Try this
    playstream.terminate()
    # But also this
    os.system('killall mplayer')
    sys.exit(0)

# Download master list of channels
def downloadChannels():
    # Make global so other functions can acess it
    global channel_list

    # Let user know we're downloading
    print("Downloading channel list...", end='')
    sys.stdout.flush()

    # Pull down JSON file
    try:
        channel_raw = requests.get(url, timeout=15)
    except requests.exceptions.Timeout:
        print("Timeout!")
        exit()
    except requests.exceptions.ConnectionError:
        print("Network Error!")
        exit()
    except requests.exceptions.RequestException as e:
        print("Unknown Error!")
        exit()

    # Put channels in list
    channel_list = channel_raw.json()['channels']

    # Write to file
    with open(channel_file, 'wb') as fp:
        pickle.dump(channel_list, fp)

    print("OK")

# Download channel icons
def downloadIcons():
    # Create icon directory if don't exist
    if not os.path.exists(icon_dir):
        os.mkdir(icon_dir)

    # If there are already icons, return
    if os.listdir(icon_dir):
        return

    # Let user know we're downloading
    print("Downloading channel icons", end='')
    sys.stdout.flush()

    for channel in channel_list:
        # Download current icon
        current_icon = requests.get(channel[image_size])

        # Construct path
        icon_path = icon_dir + "/" + os.path.basename(channel[image_size])

        # Save it to file
        with open(icon_path, 'wb') as saved_icon:
            saved_icon.write(current_icon.content)

        # Print a dot so user knows we're moving
        print(".", end='')
        sys.stdout.flush()

    # If we get here, all done
    print("OK")

# Loop through channels and print their descriptions
def listChannels():
    # Loop through channels
    print(Fore.RED + "------------------------------")
    for channel in channel_list:
        print(Fore.BLUE + '{:>22}'.format(channel['title']) + Fore.WHITE, end=' : ')
        print(Fore.GREEN + channel['description'] + Fore.RESET)

# Show sorted list of listeners
def showStats():
    # To count total listeners
    listeners = 0

    # Dictionary for sorting
    channel_dict = {}

    # Put channels and listener counts into dictionary
    for channel in channel_list:
        channel_dict[channel['title']] = int(channel['listeners'])

    # Sort and print results
    sorted_list = OrderedDict(sorted(channel_dict.items(), key=lambda x: x[1], reverse=True))
    print(Fore.RED + "------------------------------")
    for key, val in sorted_list.items():
        # Total up listeners
        listeners = listeners + val
        print(Fore.GREEN + '{:>4}'.format(val) + Fore.BLUE, end=' : ')
        print(Fore.BLUE + key + Fore.RESET)

    # Print total line
    print(Fore.YELLOW + '{:>4}'.format(listeners) + Fore.BLUE, end=' : ')
    print(Fore.CYAN + "Total Listeners" + Fore.RESET)

# Make sure the channel is in the local channel list
def checkChannel(channel_name):
    for channel in channel_list:
        if channel_name == channel['title']:
            # We're good
            return()

    # If we get here, no match
    print(Fore.RED + "Channel not found!")
    print(Fore.WHITE + "Double check the name of the channel and try again.")
    print("Channel names must be entered EXACTLY as they are seen in the list.")
    exit()

# IMPORTANT: Verify channel exists before running the following functions
# Return playlist URL for given channel name
def getPLS(channel_name):
    for channel in channel_list:
        if channel_name == channel['title']:
            return(channel['playlists'][quality_num]['url'])

# Return icon filename for given channel
def getIcon(channel_name):
    for channel in channel_list:
        if channel_name == channel['title']:
            return(icon_dir + "/" + os.path.basename(channel[image_size]))

# Execution below this line
#-----------------------------------------------------------------------#
# Load signal handler
signal.signal(signal.SIGINT, signal_handler)

# Handle arguments
parser = argparse.ArgumentParser(description='Simple Python 3 player for SomaFM, version ' + version)
parser.add_argument('-l', '--list', action='store_true', help='Download and display list of channels')
parser.add_argument('-s', '--stats', action='store_true', help='Display current listener stats')
parser.add_argument('-n', '--notify', action='store_true', help='Enable experimental desktop notifications for this session')
parser.add_argument("channel", nargs='?', const=1, default=default_chan, help="Channel to stream. Default is Groove Salad")
args = parser.parse_args()

# Enable desktop notifications
if args.notify:
    desktop_notifications = True

# Get screen ready
colorama.init()
os.system('clear')
print(Style.BRIGHT, end='')

# Create cache directory if doesn't exist
if not os.path.exists(cache_dir):
    os.mkdir(cache_dir)

if args.list:
    # Always download, this allows manual update
    downloadChannels()
    listChannels()
    exit()

if args.stats:
    downloadChannels()
    showStats()
    exit()

# If we get here, we are playing
# Check for MPlayer before we get too comfortable
if shutil.which("mplayer") == None:
    print(Fore.RED + "MPlayer not found!")
    print(Fore.WHITE + "MPlayer is required for this script to function.")
    exit()

# See if we already have a channel list
if os.path.isfile(channel_file) == False:
    downloadChannels()

# Load local channel list
with open (channel_file, 'rb') as fp:
    channel_list = pickle.load(fp)

# Sanity check for desktop notifications
if desktop_notifications:
    # See if we have notify-send
    if shutil.which("notify-send") == None:
        # If we don't, turn off notifications and warn user
        desktop_notifications = False
        print(Fore.RED + "Desktop notifications not supported on this system!" + Fore.WHITE)
    else:
        # Otherwise, get icons
        downloadIcons()

# See if given channel exists before we go any farther
checkChannel(args.channel)

# Find playlist for given channel
stream_url = getPLS(args.channel)

# Record the start time
start_time = datetime.now()

# Open stream
print("Loading stream...", end='')
playstream = subprocess.Popen(['mplayer', '-playlist', stream_url], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=False)
print("OK")
print(Fore.RED + "--------------------------")
print(Fore.WHITE, end='')
# Parse output
for line in playstream.stdout:
    if line.startswith(b'Name'):
        print(Fore.CYAN + "Channel: " + Fore.WHITE + line.decode().split(':', 2)[1].strip())
    if line.startswith(b'Genre'):
        print(Fore.CYAN + "Genre: " + Fore.WHITE + line.decode().split(':', 1)[1].strip())
    if line.startswith(b'Bitrate'):
        print(Fore.CYAN + "Bitrate: " + Fore.WHITE + line.decode().split(':', 1)[1].strip())
        print(Fore.RED + "--------------------------")
    if line.startswith(b'ICY Info:'):
        info = line.decode().split(':', 1)[1].strip()
        attrs = dict(re.findall("(\w+)='([^']*)'", info))
        print(Fore.BLUE + datetime.now().strftime("%H:%M:%S"), end=' | ')
        print(Fore.GREEN + attrs.get('StreamTitle', '(none)'))

        # Send desktop notification
        if desktop_notifications:
            subprocess.Popen(['notify-send', '-i', getIcon(args.channel), attrs.get('StreamTitle', '(none)')])

# Calculate how long we were playing
time_elapsed = datetime.now() - start_time
hours, remainder = divmod(int(time_elapsed.total_seconds()), 3600)
minutes, seconds = divmod(remainder, 60)

# Print exit message
print(Fore.RESET + "Playback stopped after {:02}:{:02}:{:02}".format(int(hours), int(minutes), int(seconds)))
# EOF
