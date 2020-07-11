"""
A gedit plugin which adds a Label to the status bar with the active documents 
wordcount, where a word is definied as r"[a-zA-Z0-9]+[a-zA-Z0-9\-']*\s?"
"""

import re
from gi.repository import GObject, GLib, Gtk, Gedit # pylint: disable=E0611

WORD_RE = re.compile(r"[a-zA-Z0-9]+[a-zA-Z0-9\-']*\s?")

def get_text(doc):
    """Return the full text of the document"""
    start, end = doc.get_bounds()
    return doc.get_text(start, end, False)

def count_words(text):
    return len(WORD_RE.findall(text))

class WordcountPlugin(GObject.Object, Gedit.WindowActivatable):
    """
    Adds a Label to the status bar with the active documents wordcount, 
    where a word is definied as r"[a-zA-Z0-9]+[a-zA-Z0-9\-']*\s?"
    """
    __gtype_name__ = "wordcount"
    window = GObject.property(type=Gedit.Window)
    
    def __init__(self):
        GObject.Object.__init__(self)
        self._doc_changed_id = None
        self._label = Gtk.Label()
        self._selection_count = 0
        self._document_count = 0
    
    def do_activate(self):
        """called when plugin is activated"""
        self.window.get_statusbar().pack_end(self._label, False, False, 5)
        self._label.show()
    
    def do_deactivate(self):
        """called when plugin is deactivated, cleanup"""
        Gtk.Container.remove(self.window.get_statusbar(), self._label)
        if self._doc_changed_id:
            for signal_id in self._doc_changed_id[1]:
                self._doc_changed_id[0].disconnect(signal_id)
        del self._label
    
    def do_update_state(self):
        """state requires update"""
        if self._doc_changed_id:
            for signal_id in self._doc_changed_id[1]:
                self._doc_changed_id[0].disconnect(signal_id)
        doc = self.window.get_active_document()
        if doc:
            self._doc_changed_id = (doc, [
                doc.connect("changed", self.on_document_changed),
                doc.connect("notify::cursor-position", lambda doc, _prop: self.on_text_selection_changed(doc)),
                ])
            GLib.idle_add(self.on_document_changed, doc)
        else: # user closed all tabs
            self._label.set_text('')
    
    def on_document_changed(self, doc):
        """active documents content has changed"""
        text = get_text(doc)
        self._document_count = count_words(text)
        GLib.idle_add(self.on_text_selection_changed, doc)
        
    def on_text_selection_changed(self, doc):
        """highlighted text changed"""
        old_count = self._selection_count
        if doc.get_has_selection():
            (start, end) = doc.get_selection_bounds()
            text = start.get_text(end)
            self._selection_count = count_words(text)
        else:
            self._selection_count = 0
        if old_count != self._selection_count:
            GLib.idle_add(self.update_label)
    
    def update_label(self):
        """update the plugins status bar label"""
        self._label.set_text(f'total: {self._document_count}, selection: {self._selection_count}')
