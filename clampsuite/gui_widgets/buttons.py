from PyQt5.QtWidgets import QButtonGroup, QPushButton, QVBoxLayout

from .qtwidgets import WorkerSignals


class AnalysisButtonsWidget(QVBoxLayout):

    button_map = {1: "analyze_acqs", 2: "calculate_parameters", 3: "reset"}

    def __init__(self, parent=None):
        super(AnalysisButtonsWidget, self).__init__(parent)

        self.signals = WorkerSignals()

        self.button_group = QButtonGroup()

        self.analyze_acq_button = QPushButton("Analyze acquisition(s)")
        self.addWidget(self.analyze_acq_button)
        self.button_group.addButton(self.analyze_acq_button, 1)
        self.analyze_acq_button.setObjectName("analyze_acq_button")

        self.calculate_parameters = QPushButton("Final analysis")
        self.addWidget(self.calculate_parameters)
        self.button_group.addButton(self.calculate_parameters, 2)
        self.calculate_parameters.setObjectName("calculate_parameters")

        self.reset_button = QPushButton("Reset analysis")
        self.addWidget(self.reset_button)
        self.button_group.addButton(self.reset_button, 3)

        self.button_group.buttonClicked.connect(self.clicked)

    def clicked(self, object):
        button_id = self.button_group.id(object)
        print(self.button_map[button_id])
        self.signals.finished.emit(self.button_map[button_id])
