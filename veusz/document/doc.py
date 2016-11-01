# document.py
# A module to handle documents

#    Copyright (C) 2004 Jeremy S. Sanders
#    Email: Jeremy Sanders <jeremy@jeremysanders.net>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program; if not, write to the Free Software Foundation, Inc.,
#    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
##############################################################################

"""A class to represent OpenReliability documents, with dataset classes."""

from __future__ import division
import codecs
import os.path
import traceback
import datetime
from collections import defaultdict

import numpy as N

try:
    import h5py
except ImportError:
    h5py = None

from ..compat import citems, cvalues, cstr, CStringIO, cexecfile
from .. import qtall as qt4

from . import widgetfactory
from . import painthelper
from . import evaluate

from .. import datasets
from .. import utils
from .. import setting

def _(text, disambiguation=None, context="Document"):
    """Translate text."""
    return qt4.QCoreApplication.translate(context, text, disambiguation)

def getSuitableParent(widgettype, initialwidget):
    """Find the nearest relevant parent for the widgettype given."""

    # find the parent to add the child to, we go up the tree looking
    # for possible parents
    parent = initialwidget
    wc = widgetfactory.thefactory.getWidgetClass(widgettype)
    while parent is not None and not wc.willAllowParent(parent):
        parent = parent.parent
    return parent

class DocSuspend(object):
    """Handle document updates/suspensions."""
    def __init__(self, doc):
        self.doc = doc
    def __enter__(self):
        self.doc.suspendUpdates()
        return self
    def __exit__(self, type, value, traceback):
        self.doc.enableUpdates()

class Document(qt4.QObject):
    """Document class for holding the graph data.
    """

    pluginsloaded = False

    # this is emitted when the document is modified
    signalModified = qt4.pyqtSignal(int)
    # emited to log a message
    sigLog = qt4.pyqtSignal(cstr)
    # emitted when document wiped
    sigWiped = qt4.pyqtSignal()
    # to ask whether the import is allowed (module name and symbol list)
    sigAllowedImports = qt4.pyqtSignal(cstr, list)

    def __init__(self):
        """Initialise the document."""
        qt4.QObject.__init__( self )

        if not Document.pluginsloaded:
            Document.loadPlugins()
            Document.pluginsloaded = True

        # change tracking of document as a whole
        self.changeset = 0            # increased when the document changes

        # map tags to dataset names
        self.datasettags = defaultdict(list)

        # if set, do not notify listeners of updates
        # wait under enableUpdates
        self.suspendupdates = []

        # default document locale
        self.locale = qt4.QLocale()

        # evaluation context
        self.evaluate = evaluate.Evaluate(self)

        self.clearHistory()
        self.wipe()

    def wipe(self):
        """Wipe out any stored data."""
        self.data = {}
        self.basewidget = widgetfactory.thefactory.makeWidget(
            'document', None, None)
        self.basewidget.document = self
        self.setModified(False)
        self.filename = ""
        self.sigWiped.emit()

    def clearHistory(self):
        """Clear any history."""
        self.historybatch = []
        self.historyundo = []
        self.historyredo = []

    def suspendUpdates(self):
        """Holds sending update messages.
        This speeds up modification of the document and prevents the document
        from being updated on the screen."""
        self.suspendupdates.append(self.changeset)

    def enableUpdates(self):
        """Reenables document updates."""
        changeset = self.suspendupdates.pop()
        if not self.suspendupdates and changeset != self.changeset:
            # bump this up as some watchers might ignore this otherwise
            self.changeset += 1
            self.setModified()

    def suspend(self):
        """Return context manager for suspending updates."""
        return DocSuspend(self)

    def makeDefaultDoc(self):
        """Add default widgets to create document."""
        page = widgetfactory.thefactory.makeWidget('page', self.basewidget)
        widgetfactory.thefactory.makeWidget('graph', page)
        self.setModified()
        self.setModified(False)
        self.changeset = 0

    def log(self, message):
        """Log a message - this is emitted as a signal."""
        self.sigLog.emit(message)

    def applyOperation(self, operation):
        """Apply operation to the document.

        Operations represent atomic actions which can be done to the document
        and undone.

        Updates are suspended during the operation.
        """

        with DocSuspend(self):
            retn = operation.do(self)
            self.changeset += 1

        if self.historybatch:
            # in batch mode, create an OperationMultiple for all changes
            self.historybatch[-1].addOperation(operation)
        else:
            # standard mode
            self.historyundo = self.historyundo[-9:] + [operation]
        self.historyredo = []

        return retn

    def batchHistory(self, batch):
        """Enable/disable batch history mode.

        In this mode further operations are added to the OperationMultiple specified,
        until batchHistory is called with None.

        The objects are pushed into a list and popped off

        This allows multiple operations to be batched up for simple undo.
        """
        if batch:
            self.historybatch.append(batch)
        else:
            self.historybatch.pop()

    def undoOperation(self):
        """Undo the previous operation."""

        operation = self.historyundo.pop()
        with DocSuspend(self):
            operation.undo(self)
            self.changeset += 1
        self.historyredo.append(operation)

    def canUndo(self):
        """Returns True if previous operation can be removed."""
        return len(self.historyundo) != 0

    def redoOperation(self):
        """Redo undone operations."""
        operation = self.historyredo.pop()
        return self.applyOperation(operation)

    def canRedo(self):
        """Returns True if previous operation can be redone."""
        return len(self.historyredo) != 0

    def resolveFullWidgetPath(self, path):
        """Translate the widget path given into the widget."""

        widget = self.basewidget
        for p in [i for i in path.split('/') if i != '']:
            for child in widget.children:
                if p == child.name:
                    widget = child
                    break
            else:
                # break wasn't called
                assert False
        return widget

    def resolveFullSettingPath(self, path):
        """Translate setting path into setting object."""

        # find appropriate widget
        widget = self.basewidget
        parts = [i for i in path.split('/') if i != '']
        while len(parts) > 0:
            for child in widget.children:
                if parts[0] == child.name:
                    widget = child
                    del parts[0]
                    break
            else:
                # no child with name
                break

        # get Setting object
        s = widget.settings
        while isinstance(s, setting.Settings) and parts[0] in s.setdict:
            s = s.get(parts[0])
            del parts[0]

        assert isinstance(s, setting.Setting)
        return s

    def isBlank(self):
        """Does the document contain widgets and no data"""
        return self.changeset == 0

    def setData(self, name, dataset):
        """Set data to val, with symmetric or negative and positive errors."""
        self.data[name] = dataset
        dataset.document = self
        dataset.username = name

        # update the change tracking
        self.setModified()

    def deleteData(self, name):
        """Remove a dataset"""
        if name in self.data:
            del self.data[name]
            self.setModified()

    def modifiedData(self, dataset):
        """The named dataset was modified"""
        if dataset in self.data.values():
            self.setModified()

    def getLinkedFiles(self, filenames=None):
        """Get a list of LinkedFile objects used by the document.
        if filenames is a set, only get the objects with filenames given
        """
        links = set()
        for ds in cvalues(self.data):
            if ds.linked and (filenames is None or
                              ds.linked.filename in filenames):
                links.add(ds.linked)
        return list(links)

    def reloadLinkedDatasets(self, filenames=None):
        """Reload linked datasets from their files.
        If filenames is a set(), only reload from these filenames

        Returns a tuple of
        - List of datasets read
        - Dict of tuples containing dataset names and number of errors
        """

        links = self.getLinkedFiles(filenames=filenames)

        read = []
        errors = {}

        # load in the files, merging the vars read and errors
        if links:
            with self.suspend():
                for lf in links:
                    nread, nerrors = lf.reloadLinks(self)
                    read += nread
                    errors.update(nerrors)
                self.setModified()

        read.sort()
        return (read, errors)

    def datasetName(self, dataset):
        """Find name for given dataset, raising ValueError if missing."""
        for name, ds in citems(self.data):
            if ds is dataset:
                return name
        raise ValueError("Cannot find dataset")

    def renameDataset(self, oldname, newname):
        """Rename the dataset."""
        d = self.data[oldname]
        del self.data[oldname]
        self.data[newname] = d
        d.username = newname

        self.setModified()

    def getData(self, name):
        """Get data with name"""
        return self.data[name]

    def setModified(self, ismodified=True):
        """Set the modified flag on the data, and inform views."""

        # useful for tracking back modifications
        # import traceback
        # traceback.print_stack()

        self.modified = ismodified
        self.changeset += 1

        if len(self.suspendupdates) == 0:
            self.signalModified.emit(ismodified)

    def isModified(self):
        """Return whether modified flag set."""
        return self.modified

    @classmethod
    def loadPlugins(kls, pluginlist=None):
        """Load plugins and catch exceptions."""
        if pluginlist is None:
            pluginlist = setting.settingdb.get('plugins', [])

        for plugin in pluginlist:
            try:
                cexecfile(plugin, {})
            except Exception:
                err = _('Error loading plugin %s\n\n%s') % (
                    plugin, traceback.format_exc())
                qt4.QMessageBox.critical(None, _("Error loading plugin"), err)

    def printTo(self, printer, pages, scaling=1., antialias=False):
        """Print onto printing device.
        Returns list of page sizes
        """

        painter = painthelper.DirectPainter(printer)
        dpi = (printer.logicalDpiX(), printer.logicalDpiY())
        if antialias:
            painter.setRenderHint(qt4.QPainter.Antialiasing, True)
            painter.setRenderHint(qt4.QPainter.TextAntialiasing, True)

        sizes = []

        # This all assumes that only pages can go into the root widget
        for count, page in enumerate(pages):
            painter.save()
            size = self.pageSize(page, dpi=dpi)
            sizes.append(size)
            painter.setClipRect(qt4.QRectF(
                qt4.QPointF(0,0), qt4.QPointF(*size)))
            helper = painthelper.PaintHelper(
                size, dpi=dpi, directpaint=painter)
            self.paintTo(helper, page)
            painter.restore()

            # start new pages between each page
            if count < len(pages)-1:
                printer.newPage()
        painter.end()

        return sizes

    def paintTo(self, painthelper, page):
        """Paint page specified to the paint helper."""
        self.basewidget.draw(painthelper, page)

    def getNumberPages(self):
        """Return the number of pages in the document."""
        return len(self.basewidget.children)

    def getPage(self, pagenumber):
        """Return widget for page."""
        return self.basewidget.children[pagenumber]

    def datasetTags(self):
        """Get list of all tags in datasets."""
        tags = set()
        for dataset in cvalues(self.data):
            tags.update(dataset.tags)
        return sorted(tags)

    def _writeFileHeader(self, fileobj, type):
        """Write a header to a saved file of type."""

        fileobj.write('# OpenReliability %s (version %s)\n' % (type, utils.version()))
        fileobj.write('# Saved at %s\n\n' %
                      datetime.datetime.utcnow().isoformat())

    def saveDatasetTags(self, fileobj):
        """Write dataset tags to output file"""

        # get a list of all tags and which datasets have them
        bytag = defaultdict(list)
        for name, dataset in sorted(self.data.items()):
            for t in dataset.tags:
                bytag[t].append(name)

        # write out tags
        for tag, val in sorted(bytag.items()):
            fileobj.write('TagDatasets(%s, %s)\n' %
                          (repr(tag), repr(val)))

    def saveToFile(self, fileobj):
        """Save the text representing a document to a file.

        The ordering can be important, as some things override
        previous steps:

         - Tagging doesn't work if the dataset isn't
           already defined.
         - Loading from files may bring in new datasets which
           override defined datasets, so save links first
        """

        self._writeFileHeader(fileobj, 'saved document')

        # add file directory to import path if we know it
        reldirname = None
        if getattr(fileobj, 'name', False):
            reldirname = os.path.dirname( os.path.abspath(fileobj.name) )
            fileobj.write('AddImportPath(%s)\n' % repr(reldirname))

        # add custom definitions
        self.evaluate.saveCustomDefinitions(fileobj)

        # save those datasets which are linked
        # we do this first in case the datasets are overridden below
        savedlinks = {}
        for name, dataset in sorted(self.data.items()):
            dataset.saveLinksToSavedDoc(fileobj, savedlinks,
                                        relpath=reldirname)

        # save the remaining datasets
        for name, dataset in sorted(self.data.items()):
            dataset.saveToFile(fileobj, name)

        # save tags of datasets
        self.saveDatasetTags(fileobj)

        # save the actual tree structure
        fileobj.write(self.basewidget.getSaveText())

        self.setModified(False)

    def saveToHDF5File(self, fileobj):
        """Save to HDF5 (h5py) output file given."""

        # groups in output hdf5
        vszgrp = fileobj.create_group('Veusz')
        vszgrp.attrs['vsz_version'] = utils.version()
        vszgrp.attrs['vsz_saved_at'] = datetime.datetime.utcnow().isoformat()
        vszgrp.attrs['vsz_format'] = 1  # version number (currently unused)
        datagrp = vszgrp.create_group('Data')
        docgrp = vszgrp.create_group('Document')

        textstream = CStringIO()

        self._writeFileHeader(textstream, 'saved document')

        # add file directory to import path if we know it
        reldirname = None
        if getattr(fileobj, 'filename', False):
            reldirname = os.path.dirname( os.path.abspath(fileobj.filename) )
            textstream.write('AddImportPath(%s)\n' % repr(reldirname))

        # add custom definitions
        self.evaluate.saveCustomDefinitions(textstream)

        # save those datasets which are linked
        # we do this first in case the datasets are overridden below
        savedlinks = {}
        for name, dataset in sorted(self.data.items()):
            dataset.saveLinksToSavedDoc(textstream, savedlinks,
                                        relpath=reldirname)

        # save the remaining datasets
        for name, dataset in sorted(self.data.items()):
            dataset.saveToFile(textstream, name, mode='hdf5', hdfgroup=datagrp)

        # handle tagging
        # get a list of all tags and which datasets have them
        bytag = defaultdict(list)
        for name, dataset in sorted(self.data.items()):
            for t in dataset.tags:
                bytag[t].append(name)

        # write out tags as datasets
        tagsgrp = docgrp.create_group('Tags')
        for tag, dsnames in sorted(bytag.items()):
            tagsgrp[tag] = [v.encode('utf-8') for v in sorted(dsnames)]

        # save the actual tree structure
        textstream.write(self.basewidget.getSaveText())

        # create single dataset contains document
        docgrp['document'] = [ textstream.getvalue().encode('utf-8') ]

        self.setModified(False)

    def save(self, filename, mode='vsz'):
        """Save to output file.

        mode is 'vsz' or 'hdf5'
        """
        if mode == 'vsz':
            with codecs.open(filename, 'w', 'utf-8') as f:
                self.saveToFile(f)
        elif mode == 'hdf5':
            if h5py is None:
                raise RuntimeError('Missing h5py module')
            with h5py.File(filename, 'w') as f:
                self.saveToHDF5File(f)
        else:
            raise RuntimeError('Invalid save mode')

        self.filename = filename

    def load(self, filename, mode='vsz', callbackunsafe=None):
        """Load document from file.

        mode is 'vsz' or 'hdf5'
        """
        from . import loader
        loader.loadDocument(self, filename, mode=mode,
                            callbackunsafe=callbackunsafe)

        self.filename = filename

    def exportStyleSheet(self, fileobj):
        """Export the StyleSheet to a file."""

        self._writeFileHeader(fileobj, 'exported stylesheet')
        stylesheet = self.basewidget.settings.StyleSheet

        fileobj.write( stylesheet.saveText(True, rootname='') )

    def _pagedocsize(self, widget, dpi, scaling, integer):
        """Helper for page or doc size."""
        if dpi is None:
            p = qt4.QPixmap(1, 1)
            dpi = (p.logicalDpiX(), p.logicalDpiY())
        helper = painthelper.PaintHelper( (1,1), dpi=dpi, scaling=scaling )
        w = widget.settings.get('width').convert(helper)
        h = widget.settings.get('height').convert(helper)
        if integer:
            return int(w), int(h)
        else:
            return w, h

    def pageSize(self, pagenum, dpi=None, scaling=1., integer=True):
        """Get the size of a particular page in pixels.

        If dpi is None, use the default Qt screen dpi
        Use dpi if given."""

        page = self.basewidget.getPage(pagenum)
        if page is None:
            return self.docSize(dpi=dpi, scaling=scaling, integer=integer)
        return self._pagedocsize(
            page, dpi=dpi, scaling=scaling, integer=integer)

    def docSize(self, dpi=None, scaling=1., integer=True):
        """Get size for document."""
        return self._pagedocsize(
            self.basewidget,
            dpi=dpi, scaling=scaling, integer=integer)

    def resolveItem(self, fromwidget, where):
        """Resolve item relative to fromwidget.
        Returns a widget, setting or settings as appropriate.
        """
        parts = where.split('/')

        if where[:1] == '/':
            # relative to base directory
            obj = self.basewidget
        else:
            # relative to here
            obj = fromwidget

        # iterate over parts in string
        for p in parts:
            if p == '..':
                p = obj.parent
                if p is None:
                    raise ValueError("Base graph has no parent")
                obj = p
            elif p == '.' or len(p) == 0:
                pass
            else:
                if obj.isWidget():
                    child = obj.getChild(p)
                    if child is not None:
                        obj = child
                    else:
                        if p in obj.settings:
                            obj = obj.settings[p]
                        else:
                            raise ValueError("Widget has no child %s" % p)
                else:
                    if isinstance(obj, setting.Settings):
                        try:
                            obj = obj.get(p)
                        except KeyError:
                            raise ValueError("Settings has no child %s" % p)
                    else:
                        raise ValueError("Item has no children")

        # return widget
        return obj

    def resolve(self, fromwidget, where):
        """Resolve graph relative to the widget fromwidget

        Allows unix-style specifiers, e.g. /graph1/x
        Returns widget
        """

        parts = where.split('/')

        if where[:1] == '/':
            # relative to base directory
            obj = self.basewidget
        else:
            # relative to here
            obj = fromwidget

        # iterate over parts in string
        for p in parts:
            if p == '..':
                # relative to parent object
                p = obj.parent
                if p is None:
                    raise ValueError("Base graph has no parent")
                obj = p
            elif p == '.' or len(p) == 0:
                # relative to here
                pass
            else:
                # child specified
                obj = obj.getChild( p )
                if obj is None:
                    raise ValueError("Child '%s' does not exist" % p)

        # return widget
        return obj

    def walkNodes(self, tocall, root=None,
                  nodetypes=('widget', 'setting', 'settings'),
                  _path=None):
        """Walk the widget/settings/setting nodes in the document.
        For each one call tocall(path, node).
        nodetypes is tuple of possible node types
        """

        if root is None:
            root = self.basewidget
        if _path is None:
            _path = root.path

        if root.nodetype in nodetypes:
            tocall(_path, root)

        if root.nodetype == 'widget':
            # get rid of // at start of path
            if _path == '/':
                _path = ''

            # do the widget's children
            for w in root.children:
                self.walkNodes(tocall, root=w, nodetypes=nodetypes,
                               _path = _path + '/' + w.name)
            # then do the widget's settings
            self.walkNodes(tocall, root=root.settings,
                           nodetypes=nodetypes, _path=_path)
        elif root.nodetype == 'settings':
            # do the settings of the settings
            for name, s in sorted(root.setdict.items()):
                self.walkNodes(tocall, root=s, nodetypes=nodetypes,
                               _path = _path + '/' + s.name)
        # elif root.nodetype == 'setting': pass

    def formatValsWithDatatypeToText(self, vals, displaydatatype):
        """Given a set of values, datatype, return a list of strings
        corresponding to these data."""

        if displaydatatype == 'text':
            return vals
        elif displaydatatype == 'numeric':
            return [ utils.formatNumber(val, '%Vg', locale=self.locale)
                     for val in vals ]
        elif displaydatatype == 'date':
            return [ utils.dateFloatToString(val) for val in vals ]
        else:
            raise RuntimeError('Invalid data type')
