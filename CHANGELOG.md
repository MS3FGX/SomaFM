# Version History

## January 5th, 2024
- Fix station ID matching
- Add Nerd Show to list of station IDs

## November 16th, 2023
- Add experimental track saving (press C during playback)

## November 10th, 2023
- Add random channel option (Thanks blutack)

### January 8th, 2022
- Release as v1.71

### December 11th, 2021
- Dynamically space channel name column when using -l

### November 26th, 2021
- Strip HTTPS from all playlist links
- Remove player/OS specific HTTPS fixes (now redundant)

### December 10th, 2020
- Fix unclean exit when channel not found

### December 5th, 2020
- Add ability to select Chromecast device from command line
- Use tempfile to find safe temporary directory on each OS
- Use HTTP link for MPlayer on Windows/Mac OS
- Use cls on Windows
- Update README
- Release as v1.7

### September 1st, 2020
- Make sure PID is deleted in fringe cases

### July 27th, 2020 (HOPE 2020 Release)
- Update README
- Update PyPi README
- Bump version to 1.61

### July 4th, 2020
- Add option to log played tracks to file
- Add PID file creation/detection

### July 1st, 2020
- Fix for MPlayer HTTPS links not working on Mac OS

### June 30th, 2020
- Starting script with -v will display backend player output for debug

### May 17th, 2020
- Update README
- Update PyPi README
- Release as v1.6

### May 7th, 2020
- Modular approach to supporting alternate players
- Experimental support for custom notification commands

### May 3rd, 2020
- Don't show desktop notifications for station IDs

### May 1st, 2020
- Fix notifications
- Initial support for mpv
- Add optional player name display
- Chromecast track sync now optional

### April 30th, 2020
- Initial support for mpg123
- Restructuring for PyPi upload

### December 3rd, 2019
- Fix for track titles with apostrophes

### August 8th, 2019 (DEF CON 27 Release)
- Update README
- Bump version to 1.5
- Fix for duplicate stream info display

### August 7th, 2019
- Modularize stream playback
- Highlight known Station IDs (optional)
- Get time elapsed for Chromecast stream
- Show track info for Chromecast steam in terminal

### August 6th, 2019
- Initial Chromecast support

### August 5th, 2019
- Fuzzy channel matching

### July 27th, 2019
- Add about screen with donation link

### June 26th, 2019
- Add cache purge option
- Improve channel matching

### June 23rd, 2019
- Release as v1.1

### June 20th, 2019
- Add CHANGELOG.md
- Add name/email to source file
- Display time elapsed when playback ended
- Add experimental desktop notifications with libnotify

### June 4th, 2019
- First Release, v1.0
