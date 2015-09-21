#!/usr/bin/python

import urwid
import config
import urllib.request
import tempfile
import collections

from imgview import W3MImageViewer
from twisted.internet import protocol, reactor
from twisted.protocols import basic
from twisted.test.proto_helpers import StringTransport


class StationNode(urwid.Text):
    _selectable = True

    def __init__(self, pancake, station, align=urwid.LEFT,
                 wrap=urwid.SPACE, layout=None):
        self.set_text(station.name)
        self.set_layout(align, wrap, layout)
        self.station = station
        self.pancake = pancake
        self.infobox = None

    def keypress(self, size, key):
        if key == 'enter':
            self.pancake.play_station(self.station)
        return key


class CommandNode(urwid.Text):
    _selectable = True

    def __init__(self, pancake, cmd, text, align=urwid.LEFT,
                 wrap=urwid.SPACE, layout=None):
        self.set_text("(" + cmd + ") " + text)
        self.set_layout(align, wrap, layout)
        self.pancake = pancake
        self.cmd = cmd

    def keypress(self, size, key):
        if key == 'enter':
            self.pancake.run_cmd(self.cmd)
        return key


class SongProgressBar(urwid.ProgressBar):

    def __init__(self, normal, complete, player, current=0, done=100,
                 satt=None):
        self.normal = normal
        self.complete = complete
        self._current = current
        self._done = done
        self.satt = satt
        self.player = player

    def get_text(self):
        time = self.player.get_time()
        try:
            sec_total = int(float(time[0]) + float(time[1]))
            sec_part = int(float(time[0]))
            m_total, s_total = divmod(sec_total, 60)
            m_part, s_part = divmod(sec_part, 60)
            return "%02d:%02d | %02d:%02d" % (m_part, s_part, m_total, s_total)
        except:
            return "0:00 | 0:00"


class PancakeLineReciever(basic.LineOnlyReceiver):

    def __init__(self, process):
        self.process = process

    delimiter = b'\n'

    def lineReceived(self, data):
        self.process.lineReceived(data)


class PancakeProcess(protocol.ProcessProtocol):

    def __init__(self, pancake):
        self.pancake = pancake
        self.lineparser = PancakeLineReciever(self)
        self.last_output = None
        pass

    def connectionMade(self):
        self.lineparser.makeConnection(StringTransport())

    def outReceived(self, data):
        self.lineparser.dataReceived(data)

    def lineReceived(self, data):
        if self._player_stopped(data):
            self.pancake.song_ended()

    def _player_stopped(self, data):
        data = data.decode().split()
        self.last_output = data
        return (str(data[0]) == "@P" and int(str(data[1])) == 0)
        # or (str(data[0]) == "@F" and int(str(data[2])) < 50)

    def _send_cmd(self, cmd):
        self.transport.write("{}\n".format(cmd).encode("utf-8"))

    def play(self, song):
        self._send_cmd("load {}".format(song.audio_url))

    def pause(self):
        self._send_cmd("pause")

    def stop(self):
        self._send_cmd("stop")

    def get_time(self):
        try:
            return self.last_output[3], self.last_output[4]
        except:
            return 0, 0


class Pancake(object):

    CMD_MAP = collections.OrderedDict([
        ('left', ("show_stations", None)),
        ('right', ("show_commands", None)),
        ('n', ("skip_song", "Skip")),
        ('p', ("pause", "Pause")),
        ('s', ("stop_station", "Stop Station")),
        ('r', ("update_player", None)),
        ('u', ("thumbs_up", "Thumbs Up")),
        ('d', ("thumbs_down", "Thumbs Down")),
        ('b', ("bookmark_song", "Bookmark Song")),
        ('a', ("bookmark_artist", "Bookmark Artist")),
        ('q', ("exit", "Exit"))
    ])

    def __init__(self):
        self.client = None
        self.loop = None
        self.song = None
        self.album_art = None
        self.playing = False
        self.image_viewer = W3MImageViewer()

    def get_client(self):

        builder = config.PancakeFileBuilder()
        if builder.file_exists:
            return builder.build()
        else:
            config.Configurator().configure()
            return self.get_client()

    def configure(self):
        config.Configurator().configure()

    def exit(self):
        raise urwid.ExitMainLoop()

    def song_ended(self):
        self.loop.remove_alarm(self.alarm)
        self.song = None
        self.album_art = None
        if self.playing:
            self.play_next()
        else:
            self.update_player()

    def play_next(self):
        self.song = next(self.station.get_playlist())
        self.process.play(self.song)
        self.update_callback()
        self.update_player()

    def update_callback(self):
        time = self.process.get_time()
        try:
            self.progress._current = (
                float(time[0]) / (float(time[1]) + float(time[0])))
        except:
            pass
        self.progress._invalidate()
        self.update_player()
        self.loop.draw_screen()
        self.alarm = self.event_loop.alarm(1, self.update_callback)

    def update_player(self):
        self.player_window.body = urwid.Pile([urwid.Text("No song playing",
                                                         align='center')])
        self.line_break = urwid.Divider()

        if self.song is not None and self.song.album_art_url is not '':
            player_window_contents = []
            for i in range(12):
                player_window_contents.append(self.line_break)

            player_window_contents.extend([
                urwid.Text(self.song.song_name, align='center'),
                self.line_break,
                urwid.Text(self.song.artist_name, align='center'),
                self.line_break,
                urwid.Text(self.song.album_name, align='center')
            ])

            self.player_window.body = urwid.Pile(player_window_contents)

            if self.album_art is None:
                self.album_art = tempfile.NamedTemporaryFile(
                    prefix='albumimg_',
                    suffix='.jpg',
                    dir='/tmp',
                    delete=True).name
                urllib.request.urlretrieve(
                    self.song.album_art_url,
                    self.album_art)

            width, height = self.image_viewer.get_console_size_px()
            album_size = int(height * (2/5))

            x = int(
                width * (
                    self.player_window_size / (self.player_window_size + 1)))
            x -= album_size // 2
            y = int(height / 2) - album_size
            self.image_viewer.draw(self.album_art, x, y, album_size, album_size)

        try:
            self.loop.draw_screen()
        except:
            pass

    def pause(self):
        self.process.pause()

    def skip_song(self):
        self.process.stop()

    def thumbs_up(self):
        if self.song is not None:
            self.song.thumbs_up()

    def thumbs_down(self):
        if self.song is not None:
            self.song.thumbs_down()
            self.skip_song()

    def bookmark_song(self):
        if self.song is not None:
            self.song.bookmark_song()

    def bookmark_artist(self):
        if self.song is not None:
            self.song.bookmark_artist()

    def stop_station(self):
        self.playing = False
        self.process.stop()

    def detect_input(self, key):
        try:
            cmd = getattr(self, self.CMD_MAP[key][0])
        except:
            return
        cmd()

    def play_station(self, station):
        self.playing = True
        self.station = station
        self.show_commands()
        self.play_next()

    def show_stations(self):
        self.body.contents[0] = (self.station_listbox, self.body.options())

    def show_commands(self):
        self.body.contents[0] = (self.command_listbox, self.body.options())

    def run_cmd(self, cmd):
        self.detect_input(cmd)

    def main(self):
        self.client = self.get_client()

        palette = [
            ("selected_station", "white", "black"),
            ("unselected_station", "black", "white"),
            ("progress_empty", "white", "black"),
            ("progress_full", "black", "light gray")
        ]

        station_listbox_content = []
        for station in self.client.get_station_list():
            station_listbox_content.append(
                urwid.AttrMap(
                    StationNode(self, station),
                    'unselected_station',
                    'selected_station')
            )
        self.station_listbox = urwid.ListBox(station_listbox_content)

        command_listbox_content = []
        for cmd in self.CMD_MAP:
            if self.CMD_MAP[cmd][1] is not None:
                command_listbox_content.append(
                    urwid.AttrMap(
                        CommandNode(self, cmd, self.CMD_MAP[cmd][1]),
                        'unselected_station',
                        'selected_station'))
        self.command_listbox = urwid.ListBox(command_listbox_content)

        self.player_window = urwid.Filler(
            urwid.Text(""))

        self.player_window_size = 2
        self.body = urwid.Columns([
            ('weight', 1, self.station_listbox),
            ('weight', self.player_window_size, self.player_window)],
            min_width=10)

        self.process = PancakeProcess(self)
        reactor.spawnProcess(
            self.process, 'mpg123', [
                'mpg123', '-q', '-R', '--no-gapless'])
        # reactor.run()

        self.progress = SongProgressBar("progress_empty", "progress_full",
                                        self.process, 0, 1)
        frame = urwid.Frame(self.body, footer=self.progress)
        self.update_player()

        self.event_loop = urwid.TwistedEventLoop()
        self.loop = urwid.MainLoop(
            frame,
            palette,
            unhandled_input=self.detect_input,
            event_loop=self.event_loop)
        self.loop.run()


def main():
    Pancake().main()

if __name__ == '__main__':
    main()
