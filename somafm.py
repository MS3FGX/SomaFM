#!/usr/bin/env python3
# Python frontend for playing SomaFM with MPlayer
# Written by Tom Nardi (MS3FGX@gmail.com)
# Licensed under the GPLv3, see "COPYING"
version = "1.5"

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
from random import randrange
from datetime import datetime
from colorama import Fore, Style
from collections import OrderedDict

# Optional Chromecast support, don't error if can't import
try:
    import pychromecast
    chromecast_support = True
except ImportError:
    chromecast_support = False

# Basic config options:
#-----------------------------------------------------------------------

# Default quality (0 is highest available)
quality_num = 0

# Default channel to play
default_chan = "Groove Salad"

# Name of Chromecast device
chromecast_name = "The Office"

# Highlight station IDs in yellow
station_highlights = True

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

# Known station IDs
station_ids = ["SomaFM", "Big Url"]

# Define functions
#-----------------------------------------------------------------------#
# Catch ctrl-c
def signal_handler(sig, frame):
    print(Fore.RED + "Force closing...")
    # Kill any sneaky mplayers
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

# Return information for given channel
def channelGet(request, channel_name):
    for channel in channel_list:
        if channel_name.capitalize() in channel['title'].capitalize():
            # Channel exists, now what?
            if request == "VERIFY":
                return()
            elif request == "PLS":
                return(channel['playlists'][quality_num]['url'])
            elif request == "NAME":
                return(channel['title'])
            elif request == "DESC":
                return(channel['description'])
            elif request == "ICON":
                return(icon_dir + "/" + os.path.basename(channel[image_size]))
            elif request == "ICON_URL":
                return(channel[image_size])
            elif request == "URL":
                # Download PLS
                pls_file = requests.get(channel['playlists'][quality_num]['url'])

                # Split out MP3 URL
                for line in pls_file.text.splitlines():
                    if "File1" in line:
                        return(line.split('=')[1])
            else:
                print(Fore.RED + "Unknown channel operation!")
                exit()

    # If we get here, no match
    print(Fore.RED + "Channel not found!")
    print(Fore.WHITE + "Double check the name of the channel and try again.")
    exit()

# Stream channel with media player
def startStream(channel_name):
    # Find playlist for given channel
    stream_url = channelGet('PLS', args.channel)

    # Open stream
    print("Loading stream...", end='')
    try:
        playstream = subprocess.Popen(['mplayer', '-playlist', stream_url], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=False)
    except:
        print(Fore.RED + "FAILED")
        print("")
        print(Fore.WHITE + "Playback encountered an unknown error.")
        exit()
    print("OK")

    # Hand off to info display
    streamInfo(playstream)

# Stream channel on Chromecast
def startCast(channel_name):
    # Populate stream variables
    stream_name = channelGet('NAME', channel_name)
    stream_url = channelGet('URL', channel_name)

    # Now try to communicate with CC
    print("Connecting to", chromecast_name, end='...')
    sys.stdout.flush()
    try:
        chromecasts = pychromecast.get_chromecasts()
        cast = next(cc for cc in chromecasts if cc.device.friendly_name == chromecast_name)
    except:
        print(Fore.RED + "FAILED")
        print("")
        print(Fore.WHITE + "Double check the device name and try again.")
        exit()

    # Attempt to start stream
    try:
        cast.wait()
        stream = cast.media_controller
        stream.play_media(stream_url, 'audio/mp3', stream_name, channelGet('ICON_URL', channel_name))
        stream.block_until_active()
    except:
        print(Fore.RED + "FAILED")
        print("")
        print(Fore.WHITE + "Stream failed to start on Chromecast.")
        exit()
    print("OK")

    # Start mplayer with no audio to get track info
    try:
        playstream = subprocess.Popen(['mplayer', '-ao', 'null', stream_url], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=False)
    except:
        print(Fore.RED + "Track Sync Failed!")
        exit()

    # Hand off to info display
    streamInfo(playstream)

    # If we get here, then mplayer has stopped and so should Cast
    #cast.media_controller.stop()
    cast.quit_app()

# Print stream and track information
def streamInfo(playstream):
    InfoPrinted = False
    print(Fore.RED + "--------------------------")
    # Parse output
    for line in playstream.stdout:
        if InfoPrinted is False:
            if line.startswith(b'Name'):
                print(Fore.CYAN + "Channel: " + Fore.WHITE + line.decode().split(':', 2)[1].strip())
            if line.startswith(b'Genre'):
                print(Fore.CYAN + "Genre: " + Fore.WHITE + line.decode().split(':', 1)[1].strip())
            if line.startswith(b'Bitrate'):
                print(Fore.CYAN + "Bitrate: " + Fore.WHITE + line.decode().split(':', 1)[1].strip())
                print(Fore.RED + "--------------------------")
                InfoPrinted = True

        # Updates on every new track
        if line.startswith(b'ICY Info:'):
            # Break out artist - track data
            info = line.decode().split(':', 1)[1].strip()
            match = re.search(r"StreamTitle='(.*)';StreamUrl=", info)
            track = match.group(1)

            # Print date before track
            print(Fore.BLUE + datetime.now().strftime("%H:%M:%S"), end=' | ')

            # Highlight station IDs in yellow
            if station_highlights:
                stationHighlight(track)
            else:
                print(Fore.GREEN + track)

            # Send desktop notification if enabled
            if desktop_notifications:
                subprocess.Popen(['notify-send', '-i', channelGet('ICON', args.channel), attrs.get('StreamTitle', '(none)')])

# Highlight known station IDs
def stationHighlight(track):
    # Loop through known IDs, return on match
    for station in station_ids:
        if station.capitalize() in track.capitalize():
            print(Fore.YELLOW + track)
            return()

    # If we get here, no match was found
    print(Fore.GREEN + track)

# Execution below this line
#-----------------------------------------------------------------------#
# Load signal handler
signal.signal(signal.SIGINT, signal_handler)

# Handle arguments
parser = argparse.ArgumentParser(description='Simple Python 3 player for SomaFM, version ' + version)
parser.add_argument('-l', '--list', action='store_true', help='Download and display list of channels')
parser.add_argument('-s', '--stats', action='store_true', help='Display current listener stats')
parser.add_argument('-a', '--about', action='store_true', help='Show information about SomaFM')
parser.add_argument('-c', '--cast', action='store_true', help='Start playback on Chromecast')
parser.add_argument('-n', '--notify', action='store_true', help='Enable experimental desktop notifications for this session')
parser.add_argument('-p', '--purge', action='store_true', help='Delete cache files')
parser.add_argument("channel", nargs='?', const=1, default=default_chan, help="Channel to stream. Default is Groove Salad")
args = parser.parse_args()

# Enable desktop notifications
if args.notify:
    desktop_notifications = True

# Delete cache directory, exit
if args.purge:
    try:
        shutil.rmtree(cache_dir)
    except:
        print("Error while clearing cache!")
        exit()

    # If we get here, sucess
    print("Cache cleared.")
    exit()

# Get screen ready
colorama.init()
os.system('clear')
print(Style.BRIGHT, end='')

if args.about:
    # I can't decide which one I like best, so let's use them all!
    randlogo = randrange(3)
    if randlogo == 0:
        print(Fore.BLUE + "   _____                  " + Fore.GREEN + "     ________  ___")
        print(Fore.BLUE + "  / ___/____  ____ ___  ____ _" + Fore.GREEN + "/ ____/  |/  /")
        print(Fore.BLUE + "  \__ \/ __ \/ __ `__ \/ __ `" + Fore.GREEN + "/ /_  / /|_/ / ")
        print(Fore.BLUE + " ___/ / /_/ / / / / / / /_/ " + Fore.GREEN + "/ __/ / /  / /  ")
        print(Fore.BLUE + "/____/\____/_/ /_/ /_/\__,_" + Fore.GREEN + "/_/   /_/  /_/   ")
    elif randlogo == 1:
        print(Fore.BLUE + " __" + Fore.GREEN + "                         ___")
        print(Fore.BLUE + "/ _\ ___  _ __ ___   __ _  " + Fore.GREEN + "/ __\/\/\   ")
        print(Fore.BLUE + "\ \ / _ \| '_ ` _ \ / _` |" + Fore.GREEN + "/ _\ /    \  ")
        print(Fore.BLUE + "_\ \ (_) | | | | | | (_| " + Fore.GREEN + "/ /  / /\/\ \ ")
        print(Fore.BLUE + "\__/\___/|_| |_| |_|\__,_" + Fore.GREEN + "\/   \/    \/ ")
    elif randlogo == 2:
        print(Fore.BLUE + " ______     ______     __    __     ______  " + Fore.GREEN + "   ______   __    __    ")
        print(Fore.BLUE + "/\  ___\   /\  __ \   /\ '-./  \   /\  __ \ " + Fore.GREEN + "  /\  ___\ /\ '-./  \   ")
        print(Fore.BLUE + "\ \___  \  \ \ \/\ \  \ \ \-./\ \  \ \  __ \ " + Fore.GREEN + " \ \  __\ \ \ \-./\ \  ")
        print(Fore.BLUE + " \/\_____\  \ \_____\  \ \_\ \ \_\  \ \_\ \_\ " + Fore.GREEN + " \ \_\    \ \_\ \ \_\ ")
        print(Fore.BLUE + "  \/_____/   \/_____/   \/_/  \/_/   \/_/\/_/ " + Fore.GREEN + "  \/_/     \/_/  \/_/ ")

    print(Fore.WHITE + "")
    print("SomaFM is a listener-supported Internet-only radio station.")
    print("")
    print("That means no advertising or annoying commercial interruptions. SomaFM's")
    print("mission is to search for and expose great new music which people may")
    print("otherwise never encounter.")
    print("")
    print("If you like what you hear on SomaFM and want to help, please consider")
    print("visiting their site and making a donation.")
    print("")
    print(Fore.BLUE + "https://somafm.com/support/")
    print("")
    exit()

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

# Record the start time
start_time = datetime.now()

# If Chromecast support is enabled, break off here
if args.cast:
    if chromecast_support:
        startCast(args.channel)
    else:
        print(Fore.RED + "Chromecast Support Disabled!")
        print(Fore.WHITE + "Please install the pychromecast library.")
        exit()
else:
    # Else, start stream
    startStream(args.channel)

# Calculate how long we were playing
time_elapsed = datetime.now() - start_time
hours, remainder = divmod(int(time_elapsed.total_seconds()), 3600)
minutes, seconds = divmod(remainder, 60)

# Print exit message
print(Fore.RESET + "Playback stopped after {:02}:{:02}:{:02}".format(int(hours), int(minutes), int(seconds)))
# EOF
