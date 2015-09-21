import getpass
import os

from pandora.clientbuilder import FileBasedClientBuilder, SettingsDict
from pandora.client import APIClient
from pandora.py2compat import ConfigParser

from utils import PandoraKeysConfigParser
from utils import umask


class Configurator(object):

    """Interactive Configuration Builder
    Allows a user to configure pydora interactively. Ultimately writes the
    pydora config file.
    """

    def __init__(self):
        self.builder = PancakeFileBuilder()

        self.cfg = ConfigParser()
        self.cfg.add_section("user")
        self.cfg.add_section("api")

    def get_partner_config(self):
        try:
            return PandoraKeysConfigParser().load()["ios"]
        except:
            self.fail("Error loading config file. Unable to continue.")

    def get_value(self, section, key, prompt):
        self.cfg.set(section, key, input(prompt))

    def get_password(self, section, key, prompt):
        self.cfg.set(section, key, getpass.getpass(prompt))

    def set_static_value(self, section, key, value):
        self.cfg.set(section, key, value)

    def add_partner_config(self, config):
        for key, value in config.items():
            self.cfg.set("api", key, value)

    def write_config(self):
        if not os.path.exists(os.path.dirname(self.builder.path)):
            os.makedirs(os.path.dirname(self.builder.path))

        with umask(0o077), open(self.builder.path, "w") as fp:
            self.cfg.write(fp)

    def configure(self):
        if self.builder.file_exists:
            print("You already have a pancake config!")
        else:
            print("Hey there new pancake user! Give me your personal info!")
            print("Sorry this part looks so lame, i'm too lazy to make a nice "
                  "fancy login screen :P")
            self.add_partner_config(self.get_partner_config())
            self.get_value("user", "username", "Pandora E-Mail: ")
            self.get_password("user", "password", "Pandora Password: ")
            self.set_static_value(
                "api", "default_audio_quality",
                APIClient.HIGH_AUDIO_QUALITY
                )
            self.write_config()


class PancakeFileBuilder(FileBasedClientBuilder):

    DEFAULT_CONFIG_FILE = "~/.config/pancake/config"

    @staticmethod
    def cfg_to_dict(cfg, key, kind=SettingsDict):
        return kind((k.strip().upper(), v.strip())
                    for k, v in cfg.items(key, raw=True))

    def parse_config(self):
        cfg = ConfigParser()

        with open(self.path) as fp:
            cfg.read_file(fp)

        settings = PancakeFileBuilder.cfg_to_dict(cfg, "api")
        settings["user"] = PancakeFileBuilder.cfg_to_dict(
            cfg, "user", dict)

        return settings
