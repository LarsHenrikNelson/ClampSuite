from PySide6 import QtGui

black2white = [
    "#000000",
    "#101010",
    "#202020",
    "#404040",
    "#606060",
    "#808080",
    "#c0c0c0",
    "#e0e0e0",
    "#f0f0f0",
    "#ffffff",
]


class DarkPalette(QtGui.QPalette):
    """Class that inherits from pyqtgraph.QtGui.QPalette and renders dark colours for the application."""

    def __init__(self):
        QtGui.QPalette.__init__(self)
        self.setup()

    def setup(self):
        self.setColor(QtGui.QPalette.Window, QtGui.QColor(black2white[2]))
        self.setColor(QtGui.QPalette.WindowText, QtGui.QColor(black2white[-1]))
        self.setColor(QtGui.QPalette.Base, QtGui.QColor(black2white[3]))
        self.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(black2white[2]))
        self.setColor(QtGui.QPalette.ToolTipBase, QtGui.QColor(black2white[-1]))
        self.setColor(QtGui.QPalette.ToolTipText, QtGui.QColor(black2white[-1]))
        self.setColor(QtGui.QPalette.Text, QtGui.QColor(black2white[-1]))
        self.setColor(QtGui.QPalette.Button, QtGui.QColor(black2white[2]))
        self.setColor(QtGui.QPalette.ButtonText, QtGui.QColor(black2white[-1]))
        self.setColor(QtGui.QPalette.BrightText, QtGui.QColor(255, 0, 0))
        self.setColor(QtGui.QPalette.Link, QtGui.QColor(42, 130, 218))
        self.setColor(QtGui.QPalette.Highlight, QtGui.QColor(42, 130, 218))
        self.setColor(QtGui.QPalette.HighlightedText, QtGui.QColor(0, 0, 0))
        self.setColor(
            QtGui.QPalette.Disabled, QtGui.QPalette.Text, QtGui.QColor(128, 128, 128)
        )
        self.setColor(
            QtGui.QPalette.Disabled,
            QtGui.QPalette.ButtonText,
            QtGui.QColor(128, 128, 128),
        )
        self.setColor(
            QtGui.QPalette.Disabled,
            QtGui.QPalette.WindowText,
            QtGui.QColor(128, 128, 128),
        )


class LightPalette(QtGui.QPalette):
    """Class that inherits from pyqtgraph.QtGui.QPalette and renders dark colours for the application."""

    def __init__(self):
        QtGui.QPalette.__init__(self)
        self.setup()

    def setup(self):
        self.setColor(QtGui.QPalette.Window, QtGui.QColor(black2white[7]))
        self.setColor(QtGui.QPalette.WindowText, QtGui.QColor(black2white[0]))
        self.setColor(QtGui.QPalette.Base, QtGui.QColor(black2white[8]))
        self.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(black2white[7]))
        self.setColor(QtGui.QPalette.ToolTipBase, QtGui.QColor(black2white[0]))
        self.setColor(QtGui.QPalette.ToolTipText, QtGui.QColor(black2white[0]))
        self.setColor(QtGui.QPalette.Text, QtGui.QColor(black2white[0]))
        self.setColor(QtGui.QPalette.Button, QtGui.QColor(black2white[7]))
        self.setColor(QtGui.QPalette.ButtonText, QtGui.QColor(black2white[0]))
        self.setColor(QtGui.QPalette.BrightText, QtGui.QColor(255, 0, 0))
        self.setColor(QtGui.QPalette.Link, QtGui.QColor(42, 130, 218))
        self.setColor(QtGui.QPalette.Highlight, QtGui.QColor(42, 130, 218))
        self.setColor(QtGui.QPalette.HighlightedText, QtGui.QColor(0, 0, 0))
        self.setColor(
            QtGui.QPalette.Disabled, QtGui.QPalette.Text, QtGui.QColor(128, 128, 128)
        )
        self.setColor(
            QtGui.QPalette.Disabled,
            QtGui.QPalette.ButtonText,
            QtGui.QColor(128, 128, 128),
        )
        self.setColor(
            QtGui.QPalette.Disabled,
            QtGui.QPalette.WindowText,
            QtGui.QColor(128, 128, 128),
        )
