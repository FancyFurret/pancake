# pancake
Pancake is a cli pandora client built with urwid for linux.

### Features

---

* Beautiful, interactive cli interface build with urwid
* Album art shows as an actual image
* Thumbs up, thumbs down, or even bookmark your favorite songs and artists

### Installation

---

*links provided are for arch linux, but as long as you can get them installed on your distro, it should run*

Make sure you have the following installed:

* [Python 3](https://www.archlinux.org/packages/?name=python)
* [Urwid](https://www.archlinux.org/packages/?name=python-urwid)
* [Twisted](https://www.archlinux.org/packages/?name=python-twisted)
* [W3M](https://www.archlinux.org/packages/?name=w3m)
* [mpg123](https://www.archlinux.org/packages/?name=mpg123)

### Usage

---

1. Run pancake.py
2. Enter your account information (will be saved to ~/.config/pancake/config)
3. Use up/down to scroll through your stations, use enter to pick one.
4. Use left/right to switch between the station and command windows.

### Commands

---

* left: Show stations
* right: Show commands
* n: Skip song
* p: Pause
* s: Stop station
* u: Thumbs up :)
* d: Thumbs down :(
* b: Bookmark song
* a: Bookmark artist
* q: Quit

### FAQ

---

* No stations show up!
*First, make sure you actually have some stations on your account. You'll have to go to [pandora.com](http://pandora.com) to add stations for now. Second, check ~/.config/pancake/config and make sure you've entered your email and password correctly*

* No album art!
*Double check that you have w3m installed, and that w3mimgdisplay resides in /usr/lib/w3m/. Also make sure that you are using an up-to-date terminal running in an x session. If your terminal doesn't display them, let me know.*

* No sound!
*Is your computer muted...*

### Known bugs

---

* Album art doesn't display correctly in tmux
* Occasionally crashes when a song finishes, just hit q and start it up again to fix it.

### Credits

---

I could not have made all this myself! Huge thanks to the following:

* mcrute, for [his awesome pandora api and example player](https://github.com/mcrute/pydora)
* [habnabit](https://github.com/habnabit), from #python on freenode, giving me tons of great advice and guidance