import os
from typing import List, Optional
from urllib.parse import urlparse, unquote

import requests
import shutil
import threading

from sadb import App

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, GLib, Adw

# Set cache location to ~/.cache/stillcenter
_CACHE_DIR = os.path.join(os.path.expanduser("~"), ".cache/stillcenter")
_ICON_DIR = os.path.join(_CACHE_DIR, "icons")
_SCREENSHOT_DIR = os.path.join(_CACHE_DIR, "screenshots")

for dir in [_CACHE_DIR, _ICON_DIR, _SCREENSHOT_DIR]:
    if not os.path.exists(dir):
        os.makedirs(dir)

# Clear out screenshot dir
shutil.rmtree(_SCREENSHOT_DIR)
os.makedirs(_SCREENSHOT_DIR)


queue = []


class UrlImage(Gtk.Stack):
    file_name: str
    url: str
    location: str

    def __init__(self, file_name: str, url: str):
        # Page 0 is a spinner
        super().__init__()
        self.file_name = file_name
        self.url = url

        self.image = Gtk.Image()
        self.add_child(self.image)
        self.spinner = Gtk.Spinner()
        self.spinner.set_size_request(64, 64)
        self.add_child(self.spinner)

        if self.file_name is not None:
            self.location = os.path.join(_CACHE_DIR, self.file_name)
        else:
            self.location = None

        self.connect("realize", self.on_show)
        self.connect("unrealize", self.on_hide)

    def on_show(self, _widget):
        if self.file_name is None:
            self.set_invalid()
            return
        if os.path.exists(self.location):
            self.set_image()
        else:
            self.set_spinner()
            queue.append(self)

    def on_hide(self, _widget):
        if self.location:
            if not os.path.exists(self.location):
                if self in queue:
                    queue.remove(self)

    def set_spinner(self):
        self.set_visible_child(self.spinner)
        self.spinner.start()

    def set_image(self):
        self.image.set_from_file(self.location)
        self.set_visible_child(self.image)
        self.spinner.stop()

    def download(self):
        """Downloads the image, should only be run from another thread"""
        if not url_exists(self.location):
            GLib.idle_add(self.set_invalid)
        try:
            response = requests.get(self.url)
            with open(self.location, "wb") as f:
                f.write(response.content)
            GLib.idle_add(self.set_image)
            queue.pop(0)
        except Exception:
            GLib.idle_add(self.set_invalid)

    def set_invalid(self):
        self.image.set_from_icon_name("image-missing-symbolic")
        self.set_visible_child(self.image)
        self.spinner.stop()


class UrlIcon(UrlImage):
    pixel_size: int

    def __init__(self, app: App, pixel_size: int):
        super().__init__(get_file_name_from_url(app.icon_url, app.app_id, _ICON_DIR), app.icon_url)
        if app.icon_url is None:
            app.icon_url = ""

        self.pixel_size = pixel_size
        self.image.set_pixel_size(pixel_size)
        self.image.set_size_request(self.pixel_size, self.pixel_size)
        self.spinner.set_size_request(self.pixel_size, self.pixel_size)


class UrlScreenshot(UrlImage):
    height: int

    def __init__(self, app_id: str, url: str, height):
        super().__init__(get_file_name_from_url(url, app_id, _SCREENSHOT_DIR), url)
        self.height = height
        self.image.set_size_request(self.height, self.height)
        self.spinner.set_size_request(64, 64)
        self.set_size_request(self.height, self.height)
        self.set_valign(Gtk.Align.START)
        self.set_halign(Gtk.Align.CENTER)
        self.set_hexpand(False)
        self.set_vexpand(False)

    def on_hide(self, _widget):
        super().on_hide(_widget)
        if os.path.exists(self.file_name):
            os.remove(self.file_name)


class ImageScroll(Gtk.Overlay):
    def __init__(self, screenshots: List[UrlScreenshot]):
        # Check that all the screenshots are the same height
        for i in range(1, len(screenshots) - 1):
            assert screenshots[i].height == screenshots[i - 1].height
        super().__init__(vexpand=False, valign=Gtk.Align.START)
        # NOTE:
        # For some reason using AdwCarousel.get_nth_page is super slow. Use len(self.screenshots) instead
        self.screenshots = screenshots
        self.carousel = Adw.Carousel(spacing=150)
        self.carousel.connect("page-changed", self.carousel_changed)
        for screenshot in screenshots:
            self.carousel.append(screenshot)
        self.set_child(self.carousel)

        self.back_revealer = Gtk.Revealer(transition_type=Gtk.RevealerTransitionType.CROSSFADE)
        self.back_revealer.set_transition_duration(100)
        self.back_revealer.set_margin_start(10)
        self.back_revealer.set_valign(Gtk.Align.CENTER)
        self.back_revealer.set_halign(Gtk.Align.START)

        self.back = Gtk.Button.new_from_icon_name("go-previous-symbolic")
        self.back.add_css_class("osd")
        self.back.add_css_class("circular")
        self.back.connect("clicked", self.btn_clicked, -1)

        self.forward_revealer = Gtk.Revealer(transition_type=Gtk.RevealerTransitionType.CROSSFADE)
        self.forward_revealer.set_transition_duration(100)
        self.forward_revealer.set_margin_end(10)
        self.forward_revealer.set_valign(Gtk.Align.CENTER)
        self.forward_revealer.set_halign(Gtk.Align.END)
        self.forward_revealer.set_reveal_child(True)

        self.forward = Gtk.Button.new_from_icon_name("go-next-symbolic")
        self.forward.add_css_class("osd")
        self.forward.add_css_class("circular")
        self.forward.connect("clicked", self.btn_clicked, 1)

        if len(self.screenshots) > 1:
            indicator = Adw.CarouselIndicatorDots()
            indicator.set_carousel(self.carousel)
            indicator.set_halign(Gtk.Align.CENTER)
            indicator.set_valign(Gtk.Align.END)
            self.add_overlay(indicator)

        self.back_revealer.set_child(self.back)
        self.forward_revealer.set_child(self.forward)
        self.add_overlay(self.back_revealer)
        self.add_overlay(self.forward_revealer)

    def btn_clicked(self, _button: Gtk.Button, changed_by: int):
        index = round(self.carousel.get_position())
        if 0 <= index + changed_by < len(self.screenshots):
            self.carousel.scroll_to(self.screenshots[index + changed_by], True)

    def carousel_changed(self, carousel: Adw.Carousel, index: int):
        if index > 0:
            self.back_revealer.set_reveal_child(True)
        else:
            self.back_revealer.set_reveal_child(False)

        if index + 1 >= carousel.get_n_pages():
            self.forward_revealer.set_reveal_child(False)
        else:
            self.forward_revealer.set_reveal_child(True)


def process_queue():
    while True:
        if len(queue) > 0:
            queue[0].download()


def get_file_name_from_url(url: Optional[str], app_id: str, base_dir: str) -> Optional[str]:
    """
    This function gets the filename from the end of a URL.

    :param url: The url from which to extract the filename.
    :param app_id: id of the app for the file name
    :param base_dir: directory the file is inside
    :return: The filename extracted from the url.
    """
    if url == "" or url is None:
        return "/usr/share/icons/AdwaitaLegacy/48x48/status/image-missing.png"
    if os.path.exists(url):
        return url


    # Parse the url to get the path
    path = urlparse(url).path

    # Get the file name from the path
    try:
        filename = unquote(path.split('/')[-1])
    except TypeError:
        return None

    return os.path.join(base_dir, f"{app_id}-{filename}")


def url_exists(url):
    try:
        response = requests.head(url)
        if response.status_code == 200:
            return True
        else:
            return False
    except requests.exceptions.RequestException as e:
        # Handle exceptions like network errors, invalid URLs, etc.
        print(f"Error: {e}")
        return False


thread = threading.Thread(target=process_queue)
thread.daemon = True
thread.start()
