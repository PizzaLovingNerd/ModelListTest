import os
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
        self._author_visible = self._author is not None
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
        self.author_visible = self._author is not None

    @GObject.Property(type=bool, default=True)
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

        app_store = AppItem(app[0], app[1], app[2], app[3])

        for category in category_index.keys():
            if category in categories or category in keywords:
                category_index[category].append(app_store)
        category_index["all"].append(app_store)

try:
    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "appGridButton.ui"), "rb") as file:
        ui_bytes = file.read()
        GridItemFactory = Gtk.BuilderListItemFactory.new_from_bytes(None, GLib.Bytes.new(ui_bytes))
except IOError as e:
    print(f"Error reading UI file: {e}")


class AppView(Gtk.GridView):
    def __init__(self, category: str):
        category_index[category] = Gio.ListStore()
        super().__init__(model=Gtk.NoSelection.new(category_index[category]), factory=GridItemFactory)
        self.set_max_columns(5)


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
