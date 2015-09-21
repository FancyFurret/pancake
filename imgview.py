import subprocess

from subprocess import Popen, PIPE


class W3MImageViewer:

    def __init__(self):
        self.w3m_path = "/usr/lib/w3m/w3mimgdisplay"
        self.process = Popen([self.w3m_path],
                             stdin=PIPE,
                             stdout=PIPE,
                             universal_newlines=True)

    def draw(self, image_path, x, y, width, height):
        self.process.stdin.write(self._generate_w3m_cmd(
            image_path,
            x,
            y,
            width,
            height))
        self.process.stdin.flush()
        self.process.stdout.readline()

    def _generate_w3m_cmd(self, image_path, x, y, width, height):
        return "0;1;{x};{y};{w};{h};;;;;{image_path}\n4;\n3;\n".format(
            x=x,
            y=y,
            w=width,
            h=height,
            image_path=image_path)

    def _get_font_dimensions(self):
        xpixels, ypixels = self.get_console_size_px()
        rows, cols = self.get_console_size()

        return (xpixels // int(cols)), (ypixels // int(rows))

    def get_console_size(self):
        return subprocess.check_output(["stty", "size"]).split()

    def get_console_size_px(self):
        process = Popen([self.w3m_path, "-test"],
        stdout=PIPE,
        universal_newlines=True)
        output, _ = process.communicate()
        output = output.split()
        return int(output[0]), int(output[1])
