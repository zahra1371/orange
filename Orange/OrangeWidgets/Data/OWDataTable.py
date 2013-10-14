"""
<name>Data Table</name>
<description>Shows data in a spreadsheet.</description>
<icon>icons/DataTable.svg</icon>
<priority>100</priority>
<contact>Peter Juvan (peter.juvan@fri.uni-lj.si)</contact>
"""

import sys
from xml.sax.saxutils import escape
from functools import wraps

import sip

import Orange

from OWWidget import *
import OWGUI
import math
from orngDataCaching import *
import OWColorPalette

NAME = "Data Table"

DESCRIPTION = "Displays data in a spreadsheet."

LONG_DESCRIPTION = """Data Table widget takes one or more data sets
on its input and presents them in a spreadsheet format.
"""

ICON = "icons/DataTable.svg"

PRIORITY = 100

AUTHOR = "Peter Juvan"

AUTHOR_EMAIL = "peter.juvan(@at@)fri.uni-lj.si"

INPUTS = [("Data", ExampleTable, "dataset", Multiple + Default)]

OUTPUTS = [("Selected Data", ExampleTable, Default),
           ("Other Data", ExampleTable)]


def header_text(feature, labels=None):
    """
    Return an header text for an `Orange.feature.Descriptor` instance
    `feature`. If labels is not none it should be a sequence of keys into
    `feature.attributes` to include in the header (one per line). If the
    `feature.attribures` does not contain a value for the key the returned
    text will include an empty line for it.

    """
    lines = [feature.name]
    if labels is not None:
        lines += [str(feature.attributes.get(label, ""))
                  for label in labels]
    return "\n".join(lines)


def header_tooltip(feature, labels=None):
    """
    Return an header tooltip text for an `Orange.feature.Decriptor` instance.
    """

    if labels is None:
        labels = feature.attributes.keys()

    pairs = [(escape(key), escape(str(feature.attributes[key])))
             for key in labels if key in feature.attributes]
    tip = "<b>%s</b>" % escape(feature.name)
    tip = "<br/>".join([tip] + ["%s = %s" % pair for pair in pairs])
    return tip


def api_qvariant(func):
    @wraps(func)
    def data_get(*args, **kwargs):
        return QVariant(func(*args, **kwargs))
    return data_get

if hasattr(sip, "getapi") and sip.getapi("QVariant") > 1:
    def api_qvariant(func):
        return func


class ExampleTableModel(QAbstractItemModel):
    Attribute, ClassVar, ClassVars, Meta = range(4)

    def __init__(self, examples, dist, *args):
        QAbstractItemModel.__init__(self, *args)
        self.examples = examples
        self.domain = examples.domain
        self.dist = dist
        self.attributes = list(examples.domain.attributes)
        self.class_var = self.examples.domain.class_var
        self.class_vars = list(self.examples.domain.class_vars)
        self.metas = self.examples.domain.getmetas().values()
        # Attributes/features for all table columns
        self.all_attrs = (self.attributes +
                          ([self.class_var] if self.class_var else []) +
                          self.class_vars + self.metas)
        # Table roles for all table columns
        self.table_roles = \
            (([ExampleTableModel.Attribute] * len(self.attributes)) +
             ([ExampleTableModel.ClassVar] if self.class_var else []) +
             ([ExampleTableModel.ClassVars] * len(self.class_vars)) +
             ([ExampleTableModel.Meta] * len(self.metas)))

        # True if an feature at column i is continuous
        self._continuous_mask = [isinstance(attr, Orange.feature.Continuous)
                                 for attr in self.all_attrs]

        self._meta_mask = [role == ExampleTableModel.Meta
                           for role in self.table_roles]

        self.cls_color = QColor(160, 160, 160)
        self.meta_color = QColor(220, 220, 200)

        role_to_color = {ExampleTableModel.Attribute: None,
                         ExampleTableModel.ClassVar: self.cls_color,
                         ExampleTableModel.ClassVars: self.cls_color,
                         ExampleTableModel.Meta: self.meta_color}

        self.background_colors = map(role_to_color.get, self.table_roles)

        # all attribute labels (annotation) keys
        self.attr_labels = sorted(
            reduce(set.union,
                   [attr.attributes for attr in self.all_attrs],
                   set())
        )

        # text for all header items (no attr labels by default)
        self.header_labels = [header_text(feature)
                              for feature in self.all_attrs]

        self.sorted_map = range(len(self.examples))

        self._show_attr_labels = False
        self._other_data = {}

    def get_show_attr_labels(self):
        return self._show_attr_labels

    def set_show_attr_labels(self, val):
        if self._show_attr_labels != val:
            self.emit(SIGNAL("layoutAboutToBeChanged()"))
            self._show_attr_labels = val
            if val:
                labels = self.attr_labels
            else:
                labels = None
            self.header_labels = [header_text(feature, labels)
                                  for feature in self.all_attrs]

            self.emit(SIGNAL("headerDataChanged(Qt::Orientation, int, int)"),
                      Qt.Horizontal,
                      0,
                      len(self.all_attrs) - 1)

            self.emit(SIGNAL("layoutChanged()"))

            self.emit(SIGNAL("dataChanged(QModelIndex, QModelIndex)"),
                      self.index(0, 0),
                      self.index(len(self.examples) - 1,
                                 len(self.all_attrs) - 1)
                      )

    show_attr_labels = pyqtProperty("bool",
                                    fget=get_show_attr_labels,
                                    fset=set_show_attr_labels)

    @api_qvariant
    def data(self, index, role,
             # For optimizing out LOAD_GLOBAL byte code instructions in
             # the item role tests (goes from 14 us to 9 us average).
             _str=str,
             _Qt_DisplayRole=Qt.DisplayRole,
             _Qt_BackgroundRole=Qt.BackgroundRole,
             _OWGUI_TableBarItem_BarRole=OWGUI.TableBarItem.BarRole,
             _OWGUI_TableValueRole=OWGUI.TableValueRole,
             _OWGUI_TableClassValueRole=OWGUI.TableClassValueRole,
             _OWGUI_TableVariable=OWGUI.TableVariable,
             # Some cached local precomputed values.
             # All of the above roles we respond to
             _recognizedRoles=set([Qt.DisplayRole,
                                   Qt.BackgroundRole,
                                   OWGUI.TableBarItem.BarRole,
                                   OWGUI.TableValueRole,
                                   OWGUI.TableClassValueRole,
                                   OWGUI.TableVariable]),
             ):
        """
        Return the data for `role` for an value at `index`.
        """
        if role not in _recognizedRoles:
            return self._other_data.get((index.row(), index.column(), role),
                                        None)

        row, col = self.sorted_map[index.row()], index.column()
        example, attr = self.examples[row], self.all_attrs[col]

        val = example[attr]

        if role == _Qt_DisplayRole:
            return _str(val)
        elif role == _Qt_BackgroundRole:
            return self.background_colors[col]
        elif role == _OWGUI_TableBarItem_BarRole and \
                self._continuous_mask[col] and not val.isSpecial() and \
                col < len(self.dist):
            dist = self.dist[col]
            return (float(val) - dist.min) / (dist.max - dist.min or 1)
        elif role == _OWGUI_TableValueRole:
            # The actual value instance (should it be EditRole?)
            return val
        elif role == _OWGUI_TableClassValueRole and self.class_var is not None:
            # The class value for the row's example
            return example.get_class()
        elif role == _OWGUI_TableVariable:
            # The variable descriptor for column
            return attr

        return None

    def setData(self, index, variant, role):
        self._other_data[index.row(), index.column(), role] = variant
        self.emit(SIGNAL("dataChanged(QModelIndex, QModelIndex)"), index, index)
        
    def index(self, row, col, parent=QModelIndex()):
        return self.createIndex(row, col, 0)
    
    def parent(self, index):
        return QModelIndex()
    
    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        else:
            return len(self.examples)

    def columnCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        else:
            return len(self.all_attrs)

    @api_qvariant
    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal:
            attr = self.all_attrs[section]
            if role == Qt.DisplayRole:
                return self.header_labels[section]
            if role == Qt.ToolTipRole:
                return header_tooltip(attr, self.attr_labels)
        else:
            if role == Qt.DisplayRole:
                return QVariant(section + 1)
        return QVariant()

    def sort(self, column, order=Qt.AscendingOrder):
        self.emit(SIGNAL("layoutAboutToBeChanged()"))
        attr = self.all_attrs[column] 
        values = [(ex[attr], i) for i, ex in enumerate(self.examples)]
        values = sorted(values, key=lambda t: t[0] if not t[0].isSpecial() else sys.maxint, reverse=(order!=Qt.AscendingOrder))
        self.sorted_map = [v[1] for v in values]
        self.emit(SIGNAL("layoutChanged()"))
        self.emit(SIGNAL("dataChanged(QModelIndex, QModelIndex)"),
                  self.index(0,0),
                  self.index(len(self.examples) - 1, len(self.all_attrs) - 1)
                  )


class TableViewWithCopy(QTableView):
    def keyPressEvent(self, event):
        if event == QKeySequence.Copy:
            sel_model = self.selectionModel()
            try:
                self.copy_selection_to_clipboard(sel_model)
            except Exception:
                import traceback
                traceback.print_exc(file=sys.stderr)
        else:
            return QTableView.keyPressEvent(self, event)
            
    def copy_selection_to_clipboard(self, selection_model):
        """Copy table selection to the clipboard.
        """
        # TODO: html/rtf table
        import csv
        from StringIO import StringIO
        rows = selection_model.selectedRows(0)
        lines = []
        csv_str = StringIO()
        csv_writer = csv.writer(csv_str, dialect="excel")
        tsv_str = StringIO()
        tsv_writer = csv.writer(tsv_str, dialect="excel-tab")
        for row in rows:
            line = []
            for i in range(self.model().columnCount()):
                index = self.model().index(row.row(), i)
                val = index.data(Qt.DisplayRole)
                line.append(unicode(val.toString()))

            csv_writer.writerow(line)
            tsv_writer.writerow(line)

        csv_lines = csv_str.getvalue()
        tsv_lines = tsv_str.getvalue()

        mime = QMimeData()
        mime.setData("text/csv", QByteArray(csv_lines))
        mime.setData("text/tab-separated-values", QByteArray(tsv_lines))
        mime.setData("text/plain", QByteArray(tsv_lines))
        QApplication.clipboard().setMimeData(mime, QClipboard.Clipboard)


class OWDataTable(OWWidget):
    settingsList = ["showDistributions", "showMeta", "distColorRgb", "showAttributeLabels", "autoCommit", "selectedSchemaIndex", "colorByClass"]

    def __init__(self, parent=None, signalManager = None):
        OWWidget.__init__(self, parent, signalManager, "Data Table")

        self.inputs = [("Data", ExampleTable, self.dataset, Multiple + Default)]
        self.outputs = [("Selected Data", ExampleTable, Default), ("Other Data", ExampleTable)]

        self.data = {}          # key: id, value: ExampleTable
        self.showMetas = {}     # key: id, value: (True/False, columnList)
        self.showMeta = 1
        self.showAttributeLabels = 1
        self.showDistributions = 1
        self.distColorRgb = (220,220,220, 255)
        self.distColor = QColor(*self.distColorRgb)
        self.locale = QLocale()
        self.autoCommit = False
        self.colorSettings = None
        self.selectedSchemaIndex = 0
        self.colorByClass = True
        
        self.loadSettings()

        # info box
        infoBox = OWGUI.widgetBox(self.controlArea, "Info")
        self.infoEx = OWGUI.widgetLabel(infoBox, 'No data on input.')
        self.infoMiss = OWGUI.widgetLabel(infoBox, ' ')
        OWGUI.widgetLabel(infoBox, ' ')
        self.infoAttr = OWGUI.widgetLabel(infoBox, ' ')
        self.infoMeta = OWGUI.widgetLabel(infoBox, ' ')
        OWGUI.widgetLabel(infoBox, ' ')
        self.infoClass = OWGUI.widgetLabel(infoBox, ' ')
        infoBox.setMinimumWidth(200)
        OWGUI.separator(self.controlArea)

        # settings box
        boxSettings = OWGUI.widgetBox(self.controlArea, "Settings", addSpace=True)
        self.cbShowMeta = OWGUI.checkBox(boxSettings, self, "showMeta", 'Show meta attributes', callback = self.cbShowMetaClicked)
        self.cbShowMeta.setEnabled(False)
        self.cbShowAttLbls = OWGUI.checkBox(boxSettings, self, "showAttributeLabels", 'Show attribute labels (if any)', callback = self.cbShowAttLabelsClicked)
        self.cbShowAttLbls.setEnabled(True)

        box = OWGUI.widgetBox(self.controlArea, "Colors")
        OWGUI.checkBox(box, self, "showDistributions", 'Visualize continuous values', callback = self.cbShowDistributions)
        OWGUI.checkBox(box, self, "colorByClass", 'Color by class value', callback = self.cbShowDistributions)
        OWGUI.button(box, self, "Set colors", self.setColors, tooltip = "Set the canvas background color and color palette for coloring continuous variables", debuggingEnabled = 0)

        resizeColsBox = OWGUI.widgetBox(boxSettings, 0, "horizontal", 0)
        OWGUI.label(resizeColsBox, self, "Resize columns: ")
        OWGUI.toolButton(resizeColsBox, self, "+", self.increaseColWidth, tooltip = "Increase the width of the columns", width=20, height=20)
        OWGUI.toolButton(resizeColsBox, self, "-", self.decreaseColWidth, tooltip = "Decrease the width of the columns", width=20, height=20)
        OWGUI.rubber(resizeColsBox)

        self.btnResetSort = OWGUI.button(boxSettings, self, "Restore Order of Examples", callback = self.btnResetSortClicked, tooltip = "Show examples in the same order as they appear in the file")
        
        OWGUI.separator(self.controlArea)
        selectionBox = OWGUI.widgetBox(self.controlArea, "Selection")
        self.sendButton = OWGUI.button(selectionBox, self, "Send selections", self.commit, default=True)
        cb = OWGUI.checkBox(selectionBox, self, "autoCommit", "Commit on any change", callback=self.commitIf)
        OWGUI.setStopper(self, self.sendButton, cb, "selectionChangedFlag", self.commit)

        OWGUI.rubber(self.controlArea)

        dlg = self.createColorDialog()
        self.discPalette = dlg.getDiscretePalette("discPalette")

        # GUI with tabs
        self.tabs = OWGUI.tabWidget(self.mainArea)
        self.id2table = {}  # key: widget id, value: table
        self.table2id = {}  # key: table, value: widget id
        self.connect(self.tabs, SIGNAL("currentChanged(QWidget*)"), self.tabClicked)
        
        self.selectionChangedFlag = False
        

    def createColorDialog(self):
        c = OWColorPalette.ColorPaletteDlg(self, "Color Palette")
        c.createDiscretePalette("discPalette", "Discrete Palette")
        box = c.createBox("otherColors", "Other Colors")
        c.createColorButton(box, "Default", "Default color", QColor(Qt.white))
        c.setColorSchemas(self.colorSettings, self.selectedSchemaIndex)
        return c

    def setColors(self):
        dlg = self.createColorDialog()
        if dlg.exec_():
            self.colorSettings = dlg.getColorSchemas()
            self.selectedSchemaIndex = dlg.selectedSchemaIndex
            self.discPalette = dlg.getDiscretePalette("discPalette")
            self.distColor = color = dlg.getColor("Default")
            self.distColorRgb = (color.red(), color.green(), color.red())

            if self.showDistributions:
                # Update the views
                self.cbShowDistributions()

    def increaseColWidth(self):
        table = self.tabs.currentWidget()
        if table:
            for col in range(table.model().columnCount(QModelIndex())):
                w = table.columnWidth(col)
                table.setColumnWidth(col, w + 10)

    def decreaseColWidth(self):
        table = self.tabs.currentWidget()
        if table:
            for col in range(table.model().columnCount(QModelIndex())):
                w = table.columnWidth(col)
                minW = table.sizeHintForColumn(col)
                table.setColumnWidth(col, max(w - 10, minW))


    def dataset(self, data, id=None):
        """Generates a new table and adds it to a new tab when new data arrives;
        or hides the table and removes a tab when data==None;
        or replaces the table when new data arrives together with already existing id."""
        if data != None:  # can be an empty table!
            if self.data.has_key(id):
                # remove existing table
                self.data.pop(id)
                self.showMetas.pop(id)
                self.id2table[id].hide()
                self.tabs.removeTab(self.tabs.indexOf(self.id2table[id]))
                self.table2id.pop(self.id2table.pop(id))
            self.data[id] = data
            self.showMetas[id] = (True, [])

            table = TableViewWithCopy() #QTableView()
            table.setSelectionBehavior(QAbstractItemView.SelectRows)
            table.setSortingEnabled(True)
            table.setHorizontalScrollMode(QTableWidget.ScrollPerPixel)
            table.horizontalHeader().setMovable(True)
            table.horizontalHeader().setClickable(True)
            table.horizontalHeader().setSortIndicatorShown(False)
            
            option = table.viewOptions()
            size = table.style().sizeFromContents(QStyle.CT_ItemViewItem, option, QSize(20, 20), table) #QSize(20, QFontMetrics(option.font).lineSpacing()), table)
            
            table.verticalHeader().setDefaultSectionSize(size.height() + 2) #int(size.height() * 1.25) + 2)

            self.id2table[id] = table
            self.table2id[table] = id
            if data.name:
                tabName = "%s " % data.name
            else:
                tabName = ""
            tabName += "(" + str(id[1]) + ")"
            if id[2] != None:
                tabName += " [" + str(id[2]) + "]"
            self.tabs.addTab(table, tabName)

            self.progressBarInit()
            self.setTable(table, data)
            self.progressBarFinished()
            self.tabs.setCurrentIndex(self.tabs.indexOf(table))
            self.setInfo(data)
            self.sendButton.setEnabled(not self.autoCommit)

        elif self.data.has_key(id):
            table = self.id2table[id]
            self.data.pop(id)
            self.showMetas.pop(id)
            table.hide()
            self.tabs.removeTab(self.tabs.indexOf(table))
            self.table2id.pop(self.id2table.pop(id))
            self.setInfo(self.data.get(self.table2id.get(self.tabs.currentWidget(),None),None))

        if len(self.data) == 0:
            self.sendButton.setEnabled(False)

        self.setCbShowMeta()

    def setCbShowMeta(self):
        for ti in range(self.tabs.count()):
            if len(self.tabs.widget(ti).model().metas)>0:
                self.cbShowMeta.setEnabled(True)
                break
        else:
            self.cbShowMeta.setEnabled(False)
            
    def sendReport(self):
        qTableInstance = self.tabs.currentWidget()
        id = self.table2id.get(qTableInstance, None)
        data = self.data.get(id, None)
        self.reportData(data)
        table = self.id2table[id]
        import OWReport
        self.reportRaw(OWReport.reportTable(table))
        
        
    # Writes data into table, adjusts the column width.
    def setTable(self, table, data):
        if data==None:
            return
        qApp.setOverrideCursor(Qt.WaitCursor)
        vars = data.domain.variables
        m = data.domain.getmetas(False)
        ml = [(k, m[k]) for k in m]
        ml.sort(lambda x,y: cmp(y[0], x[0]))
        metas = [x[1] for x in ml]
        metaKeys = [x[0] for x in ml]

        mo = data.domain.getmetas(True).items()
        if mo:
            mo.sort(lambda x,y: cmp(x[1].name.lower(),y[1].name.lower()))
            metas.append(None)
            metaKeys.append(None)

        varsMetas = vars + metas

        numVars = len(data.domain.variables)
        numMetas = len(metas)
        numVarsMetas = numVars + numMetas
        numEx = len(data)
        numSpaces = int(math.log(max(numEx,1), 10))+1

#        table.clear()
        table.oldSortingIndex = -1
        table.oldSortingOrder = 1
#        table.setColumnCount(numVarsMetas)
#        table.setRowCount(numEx)

        dist = getCached(data, orange.DomainBasicAttrStat, (data,))
        
        datamodel = ExampleTableModel(data, dist, self)
        
#        proxy = QSortFilterProxyModel(self)
#        proxy.setSourceModel(datamodel)
        
        color_schema = self.discPalette if self.colorByClass else None
        table.setItemDelegate(OWGUI.TableBarItem(self, color=self.distColor, color_schema=color_schema) \
                              if self.showDistributions else QStyledItemDelegate(self)) #TableItemDelegate(self, table))
        
        table.setModel(datamodel)
        def p():
            try:
                table.updateGeometries()
                table.viewport().update()
            except RuntimeError:
                pass
        
        size = table.verticalHeader().sectionSizeHint(0)
        table.verticalHeader().setDefaultSectionSize(size)
        
        self.connect(datamodel, SIGNAL("layoutChanged()"), lambda *args: QTimer.singleShot(50, p))
        
        id = self.table2id.get(table, None)

        # set the header (attribute names)

        self.drawAttributeLabels(table)

        self.showMetas[id][1].extend([i for i, attr in enumerate(table.model().all_attrs) if attr in table.model().metas])
        self.connect(table.horizontalHeader(), SIGNAL("sectionClicked(int)"), self.sortByColumn)
        self.connect(table.selectionModel(), SIGNAL("selectionChanged(QItemSelection, QItemSelection)"), self.updateSelection)
        #table.verticalHeader().setMovable(False)

        qApp.restoreOverrideCursor() 

    def setCornerText(self, table, text):
        """
        Set table corner text. As this is an ugly hack, do everything in
        try - except blocks, as it may stop working in newer Qt.
        """

        if not hasattr(table, "btn") and not hasattr(table, "btnfailed"):
            try:
                btn = table.findChild(QAbstractButton)

                class efc(QObject):
                    def eventFilter(self, o, e):
                        if (e.type() == QEvent.Paint):
                            if isinstance(o, QAbstractButton):
                                btn = o
                                #paint by hand (borrowed from QTableCornerButton)
                                opt = QStyleOptionHeader()
                                opt.init(btn)
                                state = QStyle.State_None;
                                if (btn.isEnabled()):
                                    state |= QStyle.State_Enabled;
                                if (btn.isActiveWindow()):
                                    state |= QStyle.State_Active;
                                if (btn.isDown()):
                                    state |= QStyle.State_Sunken;
                                opt.state = state;
                                opt.rect = btn.rect();
                                opt.text = btn.text();
                                opt.position = QStyleOptionHeader.OnlyOneSection;
                                painter = QStylePainter(btn);
                                painter.drawControl(QStyle.CE_Header, opt);
                                return True # eat evebt
                        return False
                
                table.efc = efc()
                btn.installEventFilter(table.efc)

                if sys.platform == "darwin":
                    btn.setAttribute(Qt.WA_MacSmallSize)

                table.btn = btn
            except:
                table.btnfailed = True

        if hasattr(table, "btn"):
            try:
                btn = table.btn
                btn.setText(text)
                opt = QStyleOptionHeader()
                opt.text = btn.text()
                s = btn.style().sizeFromContents(QStyle.CT_HeaderSection, opt, QSize(), btn).expandedTo(QApplication.globalStrut())
                if s.isValid():
                    table.verticalHeader().setMinimumWidth(s.width())
                    
            except:
                pass

    def sortByColumn(self, index):
        table = self.tabs.currentWidget()
        table.horizontalHeader().setSortIndicatorShown(1)
        header = table.horizontalHeader()
        if index == table.oldSortingIndex:
            order = table.oldSortingOrder == Qt.AscendingOrder and Qt.DescendingOrder or Qt.AscendingOrder
        else:
            order = Qt.AscendingOrder
        table.sortByColumn(index, order)
        table.oldSortingIndex = index
        table.oldSortingOrder = order
        #header.setSortIndicator(index, order)

    def tabClicked(self, qTableInstance):
        """Updates the info box and showMetas checkbox when a tab is clicked.
        """
        id = self.table2id.get(qTableInstance,None)
        self.setInfo(self.data.get(id,None))
        show_col = self.showMetas.get(id,None)
        if show_col:
            self.cbShowMeta.setChecked(show_col[0])
            self.cbShowMeta.setEnabled(len(show_col[1])>0)
        self.updateSelection()

    def cbShowMetaClicked(self):
        table = self.tabs.currentWidget()
        id = self.table2id.get(table, None)
        if self.showMetas.has_key(id):
            show,col = self.showMetas[id]
            self.showMetas[id] = (not show,col)
        if show:
            for c in col:
                table.hideColumn(c)
        else:
            for c in col:
                table.showColumn(c)
                table.resizeColumnToContents(c)

    def drawAttributeLabels(self, table):
#        table.setHorizontalHeaderLabels(table.variableNames)
        table.model().show_attr_labels = bool(self.showAttributeLabels)
        if self.showAttributeLabels:
            labelnames = set()
            for a in table.model().examples.domain:
                labelnames.update(a.attributes.keys())
            labelnames = sorted(list(labelnames))
#            if len(labelnames):
#                table.setHorizontalHeaderLabels([table.variableNames[i] + "\n" + "\n".join(["%s" % a.attributes.get(lab, "") for lab in labelnames]) for (i, a) in enumerate(table.data.domain.attributes)])
            self.setCornerText(table, "\n".join([""] + labelnames))
        else:
            self.setCornerText(table, "")
        table.repaint()

    def cbShowAttLabelsClicked(self):
        for table in self.table2id.keys():
            self.drawAttributeLabels(table)

    def cbShowDistributions(self):
        for ti in range(self.tabs.count()):
            color_schema = self.discPalette if self.colorByClass else None
            delegate = OWGUI.TableBarItem(self, color=self.distColor,
                                          color_schema=color_schema) \
                       if self.showDistributions else QStyledItemDelegate(self)
            self.tabs.widget(ti).setItemDelegate(delegate)
        tab = self.tabs.currentWidget()
        if tab:
            tab.reset()

    # show data in the default order
    def btnResetSortClicked(self):
        table = self.tabs.currentWidget()
        if table:
            id = self.table2id[table]
            data = self.data[id]
            table.horizontalHeader().setSortIndicatorShown(False)
            self.progressBarInit()
            self.setTable(table, data)
            self.progressBarFinished()

    def setInfo(self, data):
        """Updates data info.
        """
        def sp(l, capitalize=False):
            n = len(l)
            if n == 0:
                if capitalize:
                    return "No", "s"
                else:
                    return "no", "s"
            elif n == 1:
                return str(n), ''
            else:
                return str(n), 's'

        if data == None:
            self.infoEx.setText('No data on input.')
            self.infoMiss.setText('')
            self.infoAttr.setText('')
            self.infoMeta.setText('')
            self.infoClass.setText('')
        else:
            self.infoEx.setText("%s example%s," % sp(data))
            missData = orange.Preprocessor_takeMissing(data)
            self.infoMiss.setText('%s (%.1f%s) with missing values.' % (len(missData), len(data) and 100.*len(missData)/len(data), "%"))
            self.infoAttr.setText("%s attribute%s," % sp(data.domain.attributes,True))
            self.infoMeta.setText("%s meta attribute%s." % sp(data.domain.getmetas()))
            if data.domain.classVar:
                if data.domain.classVar.varType == orange.VarTypes.Discrete:
                    self.infoClass.setText('Discrete class with %s value%s.' % sp(data.domain.classVar.values))
                elif data.domain.classVar.varType == orange.VarTypes.Continuous:
                    self.infoClass.setText('Continuous class.')
                else:
                    self.infoClass.setText("Class is neither discrete nor continuous.")
            else:
                self.infoClass.setText('Classless domain.')

    def updateSelection(self, *args):
        self.sendButton.setEnabled(bool(self.getCurrentSelection()) and not self.autoCommit)
        self.commitIf()
            
    def getCurrentSelection(self):
        table = self.tabs.currentWidget()
        if table and table.model():
            model = table.model()
            new = table.selectionModel().selectedIndexes()
            return sorted(set([model.sorted_map[ind.row()] for ind in new]))
        
    def commitIf(self):
        if self.autoCommit:
            self.commit()
        else:
            self.selectionChangedFlag = True
            
    def commit(self):
        table = self.tabs.currentWidget()
        if table and table.model():
            model = table.model()
            selected = self.getCurrentSelection()
            selection = [1 if i in selected else 0 for i in range(len(model.examples))]
            data = model.examples.select(selection)
            self.send("Selected Data", data if len(data) > 0 else None)
            data = model.examples.select(selection, 0)
            self.send("Other Data", data if len(data) > 0 else None)
        else:
            self.send("Selected Data", None)
            self.send("Other Data", None)
            
        self.selectionChangedFlag = False


def test():
    a = QApplication(sys.argv)
    ow = OWDataTable()

    d1 = orange.ExampleTable("auto-mpg")
    d2 = orange.ExampleTable("sponge.tab")
    d3 = orange.ExampleTable("wpbc.csv")
    d4 = orange.ExampleTable("adult_sample.tab")
    d5 = orange.ExampleTable("wine.tab")

    ow.show()
    ow.dataset(d1, "auto-mpg")
    ow.dataset(d2, "sponge")
    ow.dataset(d3, "wpbc")
    ow.dataset(d4, "adult_sample")
    ow.dataset(d5, "wine")
    a.exec_()
    ow.saveSettings()


if __name__ == "__main__":
    test()
