import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw
import listtest

class MyWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Test Window")

        test = listtest.Test()
        self.set_child(test)

class MyApplication(Gtk.Application):
    def __init__(self):
        super().__init__()

    def do_activate(self):
        win = MyWindow(self)
        win.present()

app = MyApplication()
app.run([])