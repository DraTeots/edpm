import click


# A list of known text names of colors
known_colors = ["black",        # (might be a gray)
                "red",
                "green",
                "yellow",       # (might be an orange)
                "blue",
                "magenta",
                "cyan",
                "white",        # (might be light gray)
                "bright_black",
                "bright_red",
                "bright_green",
                "bright_yellow",
                "bright_blue",
                "bright_magenta",
                "bright_cyan",
                "bright_white",
                "reset"]


def color_echo(title, text, color, title_bold=False, text_bold=False, nl=True):
    """
    Prints colorful title and then text in one line

    :param title:      text in color
    :param text:       later text without color
    :param color:      color of the title
    :param title_bold: title is bold
    :param text_bold:  text is bold
    :param nl:         new line after the text
    """
    click.secho(title, fg=color, bold=title_bold, nl=False)
    click.secho(text, bold=text_bold, nl=nl)


# noinspection PyBroadException
try:
    # noinspection PyUnresolvedReferences
    from HTMLParser import HTMLParser
except:
    from html.parser import HTMLParser


class ColorMarkupClickPrinter(HTMLParser, object):

    def error(self, message):
        pass

    is_bold = False       # the next printed text will be bold
    is_underline = False  # the next printed text will be underlined
    color = ""            # color of the next printed text

    def handle_starttag(self, tag, attrs):

        # make in case independent
        tag = tag.lower()

        # do we know this tag?
        if tag == 'b':
            self.is_bold = True
        elif tag == 'u':
            self.is_underline = True
        elif tag in known_colors:
            self.color = tag
        else:
            click.secho('<{}>'.format(tag), fg=self.color, bold=self.is_bold, underline=self.is_underline, nl=False)


    def handle_endtag(self, tag):
        # make in case independent
        tag = tag.lower()

        # do we know this tag?
        if tag == 'b':
            self.is_bold = False
        elif tag == 'u':
            self.is_underline = False
        elif tag in known_colors:
            self.color = "reset"
        else:
            click.secho('</{}>'.format(tag), fg=self.color, bold=self.is_bold, underline=self.is_underline, nl=False)

    def handle_data(self, data):
        click.secho(data, fg=self.color, bold=self.is_bold, underline=self.is_underline, nl=False)


def markup_print(text, *args, **kwargs):
    """markdown print
    <red> </red>
    <green> <green>
    <blue><blue>
    """
    if args or kwargs:
        text = text.format(*args, **kwargs)
    parser = ColorMarkupClickPrinter()
    parser.feed(text)
    print("")     # new line in the end


if __name__ == "__main__":
    markup_print("One two <b> df <red> my red red red </red> </b>")