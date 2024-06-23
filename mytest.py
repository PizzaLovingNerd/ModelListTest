from typing import List

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GObject, Gio, Pango, GLib

import sadb, sadb.database, url_images


category_index = {"all": Gio.ListStore()}

from gi.repository import GObject

class AppItem(GObject.Object):
    __gtype_name__ = "AppItem"

    def __init__(self, app_id, name, author, icon):
        super().__init__()
        self._app_id = app_id
        self._name = name
        self._author = author
        self._author_visible = self._author != ""
        self._icon = icon

    @GObject.Property(type=str)
    def app_id(self):
        return self._app_id

    @app_id.setter
    def app_id(self, value):
        self._app_id = value

    @GObject.Property(type=str)
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @GObject.Property(type=str)
    def author(self):
        return self._author

    @author.setter
    def author(self, value):
        self._author = value
        self.author_visible = self._author != ""

    @GObject.Property(type=bool)
    def author_visible(self):
        return self._author_visible

    @author_visible.setter
    def author_visible(self, value):
        self._author_visible = value

    @GObject.Property(type=str)
    def icon(self):
        return self._icon

    @icon.setter
    def icon(self, value):
        self._icon = value

def stores_from_database():
    db = sadb.database.get_readable_db()
    db.c.execute("SELECT id, name, author, icon_url, categories, keywords FROM installed")
    apps_columns = db.c.fetchall()


    for app in apps_columns:
        categories = app[4]
        keywords = app[5]
        if not categories.endswith(","):
            categories += ","
        if not keywords.endswith(","):
            keywords += ","

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
            if category in categories or category in keywords:
                category_index[category].append(app_store)
        category_index["all"].append(app_store)


class AppView(Gtk.GridView):
    def __init__(self, category: str):
        category_index[category] = Gio.ListStore()
        super().__init__(model=Gtk.NoSelection.new(category_index[category]), factory=AppGridFactory())


# class AppGridFactory(Gtk.SignalListItemFactory):
#     image: Gtk.Image = None
#     name: Gtk.Label = None
#
#     def __init__(self):
#         super().__init__()
#
#         self.connect("setup", self.setup)
#         self.connect("bind", self.bind)
#         self.connect("unbind", self.unbind)
#         self.connect("teardown", self.teardown)
#
#     def setup(self, factory, list_item):
#         main_box = Gtk.Box(
#             orientation=Gtk.Orientation.HORIZONTAL,
#             spacing=15
#         )
#         main_box.add_css_class("card")
#
#         self.image = Gtk.Image(
#             halign=Gtk.Align.START,
#             icon_name="image-missing-symbolic",
#             pixel_size=32,
#             valign=Gtk.Align.CENTER,
#             margin_start=15
#         )
#         main_box.append(self.image)
#
#         label_box = Gtk.Box(
#             orientation=Gtk.Orientation.VERTICAL,
#             margin_top=15,
#             margin_bottom=15,
#             margin_end=15
#         )
#         self.name = Gtk.Label(
#             ellipsize=Pango.EllipsizeMode.END,
#             xalign=0
#         )
#         self.name.add_css_class("title-4")
#         label_box.append(self.name)
#         self.author = Gtk.Label(
#             ellipsize=Pango.EllipsizeMode.END,
#             xalign=0
#         )
#         self.author.add_css_class("dim-label")
#         label_box.append(self.author)
#         main_box.append(label_box)
#
#         list_item.set_child(main_box)
#
#     def bind(self, factory, list_item):
#         item = list_item.get_item()
#         self.name.set_label(item[1].get_string())
#
#         if item[2]:
#             self.author.set_label(item[2].get_string())
#         else:
#             self.author.set_visible(False)
#
#     def unbind(self, factory, list_item):
#         self.name.set_label("")
#         self.author.set_label("")
#         self.author.set_visible(True)
#
#     def teardown(self, factory, list_item):
#         pass
# Load the UI file content
try:
    with open("appGridButton.ui", "rb") as file:
        ui_bytes = file.read()
        GridItemFactory = Gtk.BuilderListItemFactory.new_from_bytes(None, GLib.Bytes.new(ui_bytes))
except IOError as e:
    print(f"Error reading UI file: {e}")


class Test(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)

        # Create a new Adw.TabView
        self.tab_view = Adw.TabView()
        self.append(self.tab_view)

        # Define the categories
        categories = ["AudioVideo", "Development", "Education", "Game", "Graphics", "all"]

        # Create an AppView for each category and add it to the tab view
        for category in categories:
            app_view = AppView(category)
            self.tab_view.append(app_view)

        # Create a new Adw.TabBar
        self.tab_bar = Adw.TabBar()
        self.tab_bar.set_view(self.tab_view)
        self.tab_bar.set_valign(Gtk.Align.START)
        self.tab_bar.set_vexpand(False)
        self.prepend(self.tab_bar)
        stores_from_database()

