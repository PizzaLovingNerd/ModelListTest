from typing import List

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GObject, Gio, Pango

import sadb, sadb.database, url_images


category_index = {}


def stores_from_database():
    db = sadb.database.get_readable_db()
    db.c.execute("SELECT id, name, author, icon_url, categories, keywords FROM installed")
    apps_columns = db.c.fetchall()

    return_store = Gio.ListStore()
    for app in apps_columns:
        if not app[4].endswith(","):
            app[4] += ","
        if not app[5].endswith(","):
            app[5] += ","

        app_store = Gio.ListStore()
        app_store.append(Gtk.StringObject.new(app[0]))
        app_store.append(Gtk.StringObject.new(app[1]))

        if app[2] is None:
            app_store.append(Gtk.StringObject.new(""))
        else:
            app_store.append(Gtk.StringObject.new(app[2]))

        if app[3] is None:
            app_store.append(Gtk.StringObject.new(""))
        else:
            app_store.append(Gtk.StringObject.new(app[3]))

        for category in category_index.keys():
            if category in app[4] or category in app[5]:
                category_index[category].append(app_store)


class AppView(Gtk.GridView):
    def __init__(self, category: str):
        category_index[category] = Gio.ListStore()
        super().__init__(model=category_index[category], factory=AppFactory())


class AppGridFactory(Gtk.SignalListItemFactory):
    image: Gtk.Image = None
    name: Gtk.Label = None

    def __init__(self):
        super().__init__()

        self.connect("setup", self.setup)
        self.connect("bind", self.bind)
        self.connect("unbind", self.unbind)
        self.connect("teardown", self.teardown)

    def setup(self, factory, list_item):
        main_box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            margin_top=5,
            margin_bottom=5,
            margin_start=5,
            margin_end=15,
            spacing=15
        )
        self.image = Gtk.Image(
            halign=Gtk.Alignment.START,
            icon_name="image-missing-symbolic",
            pixel_size=32,
            valign=Gtk.Alignment.CENTER
        )
        main_box.append(self.image)

        label_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.name = Gtk.Label(
            ellipsize=Pango.EllipsizeMode.END,
            xalign=0
        )
        self.name.add_style_class("title-4")
        self.author = Gtk.Label(
            ellipsize=Pango.EllipsizeMode.END,
            xalign=0
        )
        self.author.add_style_class("dim-label")



    def bind(self, factory, list_item):
        list_item.get_child().bind(list_item.get_item())

    def unbind(self, factory, list_item):
        list_item.get_child().unbind()

    def teardown(self, factory, list_item):
        pass


class Test(Gtk.Box):
    def __init__(self):
        super().__init__()
        factory = Factory()
        list_view = Gtk.GridView.new(Gtk.SingleSelection.new(store), factory)
        self.append(list_view)
