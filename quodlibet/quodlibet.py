#!/usr/bin/env python

import pygtk
pygtk.require('2.0')
import gtk
import gtk.glade
import gobject
import sys
import parser
import library
import gc
import os

def escape(str):
    return str.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

class Widgets(object):
    def __init__(self, file):
        self.widgets = gtk.glade.XML("quodlibet.glade")
        self.widgets.signal_autoconnect(GladeHandlers.__dict__)

    def __getitem__(self, key):
        return self.widgets.get_widget(key)

class GladeHandlers(object):
    def gtk_main_quit(*args): gtk.main_quit()

    def select_song(tree, indices, col):
        iter = widgets.sorted.get_iter(indices)
        iter = widgets.sorted.convert_iter_to_child_iter(None, iter)
        iter = widgets.filter.convert_iter_to_child_iter(iter)
        song = widgets.songs.get_value(iter, 0)
        title = ", ".join(song.get("title", "Unknown").split("\n"))

        text = u'<span weight="bold" size="x-large">%s</span>' % escape(title)
        if "version" in song:
            text += u"\n         <small><b>%s</b></small>" % escape(
                song["version"])

        artist = ", ".join(song.get("artist", "Unknown").split("\n"))
        text += u"\n      <small>by %s</small>" % escape(artist)
        if "album" in song:
            album = u"\n   <b>%s</b>" % escape(song["album"])
            if "tracknumber" in song:
                album += u" - Track %s" % escape(song["tracknumber"])
            text += album
        label = widgets["currentsong"]

        cover_base = os.path.split(song["filename"])[0]
        for fn in ["cover", "Cover"]:
            for ext in ["png", "PNG", "jpg", "JPG"]:
                cover = os.path.join(cover_base, fn + "." + ext)
                if os.path.exists(cover):
                    pixbuf = gtk.gdk.pixbuf_new_from_file(cover)
                    scaled_buf = pixbuf.scale_simple(100, 100,
                                                     gtk.gdk.INTERP_BILINEAR)
                    widgets["albumcover"].set_from_pixbuf(scaled_buf)
                    break
            else: continue
            break
        else:
            widgets["albumcover"].set_from_stock(gtk.STOCK_CDROM,
                                                 gtk.ICON_SIZE_BUTTON)
        label.set_markup(text)

    def open_chooser(*args):
        chooser = gtk.FileChooserDialog(
            title = "Add Music",
            action = gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
            buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                       gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        chooser.set_select_multiple(True)
        resp = chooser.run()
        if resp == gtk.RESPONSE_OK:
            for song in library.load(chooser.get_filenames()):
                widgets.songs.append([song])
        chooser.destroy()

    def text_parse(*args):
        from parser import QueryParser, QueryLexer
        text = widgets["query"].get_text()
        if text.strip() == "":
            CURRENT_FILTER[0] = FILTER_ALL
            widgets.filter.refilter()
        else:
            try:
                q = QueryParser(QueryLexer(text)).Query()
            except: pass
            else:
                CURRENT_FILTER[0] = q.search
                widgets.filter.refilter()

widgets = Widgets("quodlibet.glade")

HEADERS = ["artist", "title", "album"]

FILTER_ALL = lambda x: True
CURRENT_FILTER = [ FILTER_ALL ]

def list_filter(model, it, qlist):
    song = model[it][0]
    query = qlist[0]
    return bool(song and query(song))

def list_transform(model, iter, col):
    citer = model.convert_iter_to_child_iter(iter)
    cmodel = model.get_model()
    song = cmodel.get_value(citer, 0)
    return song.get(HEADERS[col], "")

def main():
    sl = widgets["songlist"]
    widgets.songs = gtk.ListStore(object)
    widgets.filter = widgets.songs.filter_new()
    widgets.filter.set_modify_func([str]*len(HEADERS), list_transform)
    widgets.filter.set_visible_func(list_filter, CURRENT_FILTER)
    widgets.sorted = gtk.TreeModelSort(widgets.filter)

    for i, t in enumerate(HEADERS):
        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn(t.title(), renderer, text=i)
        column.set_resizable(True)
        column.set_sort_column_id(i)
        sl.append_column(column)

    for song in library.load(sys.argv[1:]):
        widgets.songs.append([song])
    sl.set_model(widgets.sorted)
    sl.set_reorderable(True)
    widgets.sorted.set_sort_column_id(0, gtk.SORT_ASCENDING)
    gc.collect()
    gtk.main()

if __name__ == "__main__": main()
