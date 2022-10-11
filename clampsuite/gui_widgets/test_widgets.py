class ItemDelegate(QStyledItemDelegate):
    def __init__(self):
        super().__init__()

    def paint(self, painter, option, index):
        acq_components = index.model().data(index, Qt.ItemDataRole.DisplayRole)
        array = acq_components[2]
        width = option.rect.width()
        height = option.rect.height()
        norm_array = (array - np.max(array)) / np.min(array) * height + option.rect.y()
        x_array = np.linspace(width * 0.1, width, len(array)).tolist()
        zip_list = [QPointF(i, j) for i, j in zip(x_array, norm_array)]
        h = [QLineF(i, j) for i, j in zip(zip_list[:-1], zip_list[1:])]
        painter.setClipping(True)
        painter.setPen(Qt.GlobalColor.white)
        painter.drawLines(h)

    def sizeHint(self, option, index):
        return QSize(100, 200)


class ListModel2(QAbstractListModel):
    def __init__(self, acq_list=None, id_list=None, header_name="Acquisition(s)"):
        super().__init__()
        self.acq_list = acq_list or []
        self.id_list = id_list or []
        self.header_name = header_name

    def data(self, index, role):
        if role == Qt.ItemDataRole.DisplayRole:
            acq = self.acq_list[index.row()]
            return acq

    # def headerData(self, name, role):
    #     if role == Qt.ItemDataRole.DisplayRole:
    #         name = self.header_name
    # return name

    def rowCount(self, index):
        return len(self.acq_list)


class ListView2(QListView):
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setSelectionMode(self.MultiSelection)
        self.setDropIndicatorShown(True)

    def dragEnterEvent(self, e):
        """
        This function will detect the drag enter event from the mouse on the
        main window
        """
        if e.mimeData().hasUrls:
            e.accept()
        else:
            e.ignore()

    def dragMoveEvent(self, e):
        """
		This function will detect the drag move event on the main window
		"""
        if e.mimeData().hasUrls:
            e.accept()
        else:
            e.ignore()

    def dropEvent(self, e):
        """
		This function will enable the drop file directly on to the 
		main window. The file location will be stored in the self.filename
		"""
        if e.mimeData().hasUrls:
            e.setDropAction(Qt.CopyAction)
            e.accept()
            for url in e.mimeData().urls():
                fname = PurePath(str(url.toLocalFile()))
                print(fname.suffix)
                if fname.suffix == ".mat":
                    if fname.stem not in self.model().id_list:
                        self.model().acq_list += [load_scanimage_file(fname)]
                        self.model().id_list += [fname.stem]
            self.model().acq_list.sort(key=lambda x: int(x[0].split("_")[1]))
            self.model().layoutChanged.emit()
        else:
            e.ignore()


class ItemDelegate(QAbstractItemDelegate):
    def createEditor(self, parent, options, index):
        widget = CustomPlotWidget()
        return widget

    def setEditorData(self, editor, index):
        return editor.setDisplayData(index.data())

    def setModelData(self, editor, model, index):
        pass


class CustomPlotWidget(QWidget):
    def __init__(self):
        self.layout = QHBoxLayout()
        self.plot = pg.PlotWidget()
        self.plot.hideAxis("left")
        self.plot.hideAxis("bottom")
        self.label = QLabel()
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.plot)

    def setDisplayData(self, data_tuple):
        self.plot(data_tuple[2])
        self.label.setText(data_tuple[0])
