import os
import re
import requests
import subprocess


def iterate_forever(func, *args, **kwargs):
    """Iterate over a finite iterator forever

    When the iterator is exhausted will call the function again to generate a
    new iterator and keep iterating.
    """
    output = func(*args, **kwargs)

    while True:
        try:
            yield next(output)
        except StopIteration:
            output = func(*args, **kwargs)


class SilentPopen(subprocess.Popen):
    """A Popen varient that dumps it's output and error
    """

    def __init__(self, *args, **kwargs):
        self._dev_null = open(os.devnull, "w")
        kwargs["stdin"] = subprocess.PIPE
        kwargs["stdout"] = subprocess.PIPE
        kwargs["stderr"] = self._dev_null
        super(SilentPopen, self).__init__(*args, **kwargs)

    def __del__(self):
        self._dev_null.close()
        super(SilentPopen, self).__del__()

class umask(object):
    """Set/Restore Umask Context Manager
    """

    def __init__(self, umask):
        self.umask = umask
        self.old_umask = None

    def __enter__(self):
        self.old_umask = os.umask(self.umask)

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.umask(self.old_umask)


class PandoraKeysConfigParser(object):
    """Parser for Pandora Keys Source Page
    This is an extremely naive restructured text parser designed only to parse
    the pandora API docs keys source file.
    """

    KEYS_URL = ("http://6xq.net/git/lars/pandora-apidoc.git/"
                "plain/json/partners.rst")

    FIELD_RE = re.compile(
            ":(?P<key>[^:]+): (?:`{2})?(?P<value>[^`\n]+)(?:`{2})?$")

    def _fixup_key(self, key):
        key = key.lower()

        if key.startswith("dec") and "password" in key:
            return "decryption_key"
        elif key.startswith("encrypt"):
            return "encryption_key"
        elif key == "deviceid":
            return "device"
        else:
            return key

    def _format_api_host(self, host):
        return "{}/services/json/".format(host)

    def _clean_device_name(self, name):
        return re.sub("[^a-z]+", "_", name, flags=re.I)

    def _fetch_config(self):
        return requests.get(self.KEYS_URL).text.split("\n")

    def _match_key(self, line):
        key_match = self.FIELD_RE.match(line)
        if key_match:
            match = key_match.groupdict()
            match["key"] = self._fixup_key(match["key"])
            return match
        else:
            return None

    def _is_host_terminator(self, line):
        return line.startswith("--")

    def _is_device_terminator(self, line):
        return line.startswith("^^")

    def load(self):
        buffer = []
        current_partner = {}
        api_host = None
        partners = {}

        for line in self._fetch_config():
            key_match = self._match_key(line)
            if key_match:
                current_partner[key_match["key"]] = key_match["value"]
            elif self._is_host_terminator(line):
                api_host = buffer.pop()
            elif self._is_device_terminator(line):
                key = self._clean_device_name(buffer.pop())
                current_partner = partners[key] = {
                        "api_host": self._format_api_host(api_host)
                        }

            buffer.append(line.strip().lower())

        return partners
