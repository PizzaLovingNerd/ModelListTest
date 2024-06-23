import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw
import mytest

class MyWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Test Window")

        self.scroll = Gtk.ScrolledWindow()
        self.scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.set_child(self.scroll)

        test = mytest.Test()
        self.scroll.set_child(test)

class MyApplication(Gtk.Application):
    def __init__(self):
        super().__init__()

    def do_activate(self):
        win = MyWindow(self)
        win.present()

app = MyApplication()
app.run([])