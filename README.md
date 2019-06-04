![feat_img](screenshots/playing.png)
# Python SomaFM Player
This simple player for SomaFM keeps the distractions, and system resource utilization, to an absolute minimum. The look of this player was inspired equally by the excellent SomaFM terminal interfaces which were already available, and the 90's hacker aesthetic that I seem to find myself nostalgic for when listening to a Shoutcast stream at 2AM.

The only testing done so far has been on Linux, though presumably it can work on other operating systems with some tweaks. If you've got a PR to make it work on your OS of choice, I'd be happy to take a look at it.

## Dependencies
This interface is written for Python 3.x, and playback is done with [MPlayer](http://www.mplayerhq.hu/design7/news.html). You'll also need to have the following libraries installed:

* [colorama](https://pypi.org/project/colorama/)
* [requests](https://3.python-requests.org/)

## Usage
Simply running `somafm.py` with no options will start streaming "Groove Salad." In the somewhat unlikely event you wanted to listen to something else, simply give it the channel name like so:

```console
./somafm.py "DEF CON Radio"
```
In addition, the following options are available:

#### --list
Download the latest master list of SomaFM channels and display their descriptions.

![channel_img](screenshots/channel_list.png)

#### --stats
This option shows the number of listeners for each currently online SomaFM channel, along with a total listener count.

## Future Development
As of this initial release I've accomplished essentially everything I set out to do originally, but there are a couple things which might be interesting to look into:

* Support other players (mpv/VLC)
* Display keyboard controls during playback
* Desktop notifications on new track

## License
This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License version 3 as published by the Free Software Foundation.

![](https://www.gnu.org/graphics/gplv3-127x51.png)

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

For details, see the file "COPYING" in the source directory.
