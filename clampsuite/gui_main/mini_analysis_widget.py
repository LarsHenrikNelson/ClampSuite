import logging

import numpy as np
import pyqtgraph as pg
from pyqtgraph.dockarea.Dock import Dock
from pyqtgraph.dockarea.DockArea import DockArea
from PySide6.QtCore import Qt, QThreadPool
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ..functions.kde import create_kde
from ..functions.utilities import round_sig
from ..gui_widgets import (
    AnalysisButtonsWidget,
    BaselineWidget,
    DragDropWidget,
    FilterWidget,
    LoadAcqWidget,
    mini,
    RCCheckWidget,
    ThreadWorker,
    WorkerSignals,
)
from ..manager import ExpManager

logger = logging.getLogger(__name__)


class MiniAnalysisWidget(DragDropWidget):
    def __init__(self, parent=None):
        super(DragDropWidget, self).__init__(parent)
        self.initUI()

    def initUI(self):
        self.signals = WorkerSignals()
        self.need_to_save = False

        logger.info("Creating Mini analysis GUI")
        # Create tabs for part of the analysis program
        self.signals.file.connect(self.loadPreferences)
        self.signals.file_path.connect(self.loadExperiment)
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget)

        self.tab1_scroll = QScrollArea()
        self.tab1_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.tab1_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.tab1_scroll.setWidgetResizable(True)
        self.tab1 = QWidget()
        self.tab1_scroll.setWidget(self.tab1)

        self.analysis_widget = mini.AnalysisWidget()

        self.tab3_scroll = QScrollArea()
        self.tab3_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.tab3_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.tab3_scroll.setWidgetResizable(True)
        self.dock_area3 = DockArea()

        self.tab_widget.addTab(self.tab1_scroll, "Setup")
        self.tab_widget.addTab(self.analysis_widget, "Analysis")
        self.tab_widget.addTab(self.dock_area3, "Final data")

        self.setStyleSheet(
            """QTabWidget::tab-bar
                                          {alignment: left;}"""
        )

        self.pbar = QProgressBar(self)
        self.pbar.setValue(0)
        self.main_layout.addWidget(self.pbar)

        self.dlg = QMessageBox(self)

        # Tab 1 layouts
        self.setup_layout = QHBoxLayout()

        self.tab1.setLayout(self.setup_layout)

        self.input_layout = QVBoxLayout()
        self.setup_layout.addLayout(self.input_layout, 0)

        self.baseline_widget = BaselineWidget()
        self.input_layout.addWidget(self.baseline_widget)

        self.rc_widget = RCCheckWidget()
        self.input_layout.addWidget(self.rc_widget)

        self.filter_widget = FilterWidget()
        self.input_layout.addWidget(self.filter_widget)

        self.analysis_buttons = AnalysisButtonsWidget()
        self.input_layout.addLayout(self.analysis_buttons)
        self.input_layout.addStretch()

        self.mini_settings = mini.MiniWidget()
        self.setup_layout.addLayout(self.mini_settings)

        # Setup for the drag and drop load layout
        self.analysis_type = "mini"
        self.load_widget = LoadAcqWidget(analysis_type=self.analysis_type)
        self.load_widget.signals.progress.connect(self.updateProgress)
        self.load_widget.signals.dir_path.connect(self.setWorkingDirectory)

        self.setup_layout.addLayout(self.load_widget, 0)

        self.setup_layout.addStretch(1)

        # Tab 3 layouts and setup
        self.table_dock = Dock("Data (table)")
        self.ave_event_dock = Dock("Average Event")
        self.data_dock = Dock("Data (visualization)")
        self.dock_area3.addDock(self.table_dock, position="left")
        self.dock_area3.addDock(self.ave_event_dock, position="right")
        self.dock_area3.addDock(self.data_dock, position="bottom")
        self.ave_event_plot = pg.PlotWidget(
            labels={"left": "Amplitude (pA)", "bottom": "Time (ms)"}, useOpenGL=True
        )
        self.ave_event_plot.setLabel(
            "bottom",
            text="Time (ms)",
            **{"color": "#C9CDD0", "font-size": "10pt"},
        )
        self.ave_event_plot.setLabel(
            "left",
            text="Amplitude (pA)",
            **{"color": "#C9CDD0", "font-size": "10pt"},
        )
        self.ave_event_dock.addWidget(self.ave_event_plot)
        self.ave_event_plot.setObjectName("Ave event plot")
        self.final_tab_widget = QTabWidget()
        self.final_tab_widget.setMinimumHeight(300)
        self.table_dock.addWidget(self.final_tab_widget)
        self.stem_plot = pg.PlotWidget(labels={"bottom": "Time (ms)"}, useOpenGL=True)
        self.amp_dist = pg.PlotWidget(useOpenGL=True)
        self.plot_selector = QComboBox()
        self.plot_selector.setMaximumWidth(100)
        self.plot_selector.currentTextChanged.connect(self.plotRawData)
        self.data_dock.addWidget(self.plot_selector, 0, 0)
        self.data_dock.addWidget(self.stem_plot, 0, 1)
        self.data_dock.addWidget(self.amp_dist, 0, 2)

        self.exp_manager = ExpManager()
        self.exp_manager.set_callback(self.updateProgress)
        self.load_widget.setData(self.exp_manager)
        self.setWidth()

    def clearTables(self):
        if self.table_dict:
            for i in self.table_dict.values():
                i.clear()
                i.hide()
                i.deleteLater()
            self.table_dict = {}

    # This needs to be fixed because it changes the lineedits that
    # are part of the spinboxes which is not ideal. Need to create
    # a dict to hold the lineedits.
    def setWidth(self):
        line_edits = self.findChildren(QLineEdit)
        for i in line_edits:
            if not isinstance(i.parentWidget(), QSpinBox):
                i.setMinimumWidth(70)

        push_buttons = self.findChildren(QPushButton)
        for i in push_buttons:
            i.setMinimumWidth(80)

        combo_boxes = self.findChildren(QComboBox)
        for i in combo_boxes:
            i.setSizeAdjustPolicy(QComboBox.AdjustToContents)
            i.adjustSize()

    def analyze(self):
        """
        This function creates each MiniAnalysis object and puts
        it into a dictionary. The events are create within the
        EventAnalysis objection. Note that the created
        EventAnalysis object needs to have analyze run. This was
        chosen because it made the initial debugging easier.
        """
        if not self.exp_manager.acqs_exist("mini"):
            logger.info("No acquisitions, analysis ended.")
            self.errorDialog("No acquisitions, analysis ended.")
            self.analyze_acq_button.setEnabled(True)
            return None

        logger.info("Analysis started.")
        self.pbar.setFormat("Analyzing...")
        self.pbar.setValue(0)

        self.inspectionPlot.clear()
        self.scrollPlot.clear()
        self.inspectionPlot.setAutoVisible(y=True)
        self.scrollPlot.enableAutoRange()
        self.event_view_plot.clear()

        self.need_to_save = True

        self.analyze_acq_button.setEnabled(False)
        self.calculate_parameters.setEnabled(False)
        self.calculate_parameters_2.setEnabled(False)

        # The for loop creates each EventAnalysis object. Enumerate returns
        # count which is used to adjust the progress bar and acq_components
        # comes from the load_widget
        if (
            self.window_edit.currentText() == "gaussian"
            or self.window_edit.currentText() == "kaiser"
        ):
            window = (self.window_edit.currentText(), self.beta_sigma.value())
        else:
            window = self.window_edit.currentText()
        # I need to just put all the settings into a dictionary,
        # so the functions are not called for every acquisition
        worker = ThreadWorker(self.exp_manager)
        worker.addAnalysis(
            "analyze",
            exp=self.analysis_type,
            filter_args={
                "baseline_start": self.b_start_edit.toInt(),
                "baseline_end": self.b_end_edit.toInt(),
                "filter_type": self.filter_selection.currentText(),
                "order": self.order_edit.toInt(),
                "high_pass": self.high_pass_edit.toFloat(),
                "high_width": self.high_width_edit.toFloat(),
                "low_pass": self.low_pass_edit.toFloat(),
                "low_width": self.low_width_edit.toFloat(),
                "window": window,
                "polyorder": self.polyorder_edit.toInt(),
            },
            analysis_args={
                "sensitivity": self.sensitivity_edit.toFloat(),
                "amp_threshold": self.amp_thresh_edit.toFloat(),
                "mini_spacing": self.event_spacing_edit.toFloat(),
                "min_rise_time": self.min_rise_time.toFloat(),
                "max_rise_time": self.max_rise_time.toFloat(),
                "min_decay_time": self.min_decay.toFloat(),
                "event_length": self.event_length.toInt(),
                "decay_rise": self.decay_rise.isChecked(),
                "invert": self.invert_checkbox.isChecked(),
                "decon_type": self.decon_type_edit.currentText(),
                "curve_fit_decay": self.curve_fit_decay.isChecked(),
                "curve_fit_type": self.curve_fit_edit.currentText(),
                "baseline_corr": self.baseline_corr_choice.isChecked(),
                "rc_check": self.rc_checkbox.isChecked(),
                "rc_check_start": self.rc_check_start_edit.toFloat(),
                "rc_check_end": self.rc_check_end_edit.toFloat(),
            },
            template_args={
                "tmp_amplitude": self.amplitude_edit.toFloat(),
                "tmp_tau_1": self.tau_1_edit.toFloat(),
                "tmp_tau_2": self.tau_2_edit.toFloat(),
                "tmp_risepower": self.risepower_edit.toFloat(),
                "tmp_length": self.temp_length_edit.toFloat(),
                "tmp_spacer": self.spacer_edit.toFloat(),
            },
        )
        worker.signals.progress.connect(self.updateProgress)
        worker.signals.finished.connect(self.setAcquisition)
        logger.info("Starting analysis thread.")
        QThreadPool.globalInstance().start(worker)

    def setAcquisition(self):
        self.acquisition_number.setMaximum(self.exp_manager.end_acq)
        self.acquisition_number.setMinimum(self.exp_manager.start_acq)
        self.acquisition_number.setValue(self.exp_manager.start_acq)

        # Events always start from 0 since list indexing in python starts
        # at zero. I choose this because it is easier to reference events
        # when adding or removing events and python list indexing starts at 0.
        self.event_number.setMinimum(0)
        # self.eventSpinbox(0)

        # Enabling the buttons since they were temporarily disabled while
        # The acquisitions were analyzed.
        self.analyze_acq_button.setEnabled(True)
        self.calculate_parameters.setEnabled(True)
        self.calculate_parameters_2.setEnabled(True)
        self.tab_widget.setCurrentIndex(1)
        logger.info("Analysis finished.")
        self.pbar.setFormat("Analysis finished")
        logger.info("First acquisition set.")

    def acqSpinbox(self, h):
        """This function plots each acquisition and each of its events."""

        if not self.exp_manager.analyzed:
            logger.info(
                "No acquisitions analyzed,"
                f" acquisition {self.acquisition_number.value()} not set."
            )
            self.errorDialog(
                f"No acquisitions analyzed, acquisition {self.acquisition_number.value()} not set."
            )
            return None

        # Plots are cleared first otherwise new data is just appended to
        # the plot.
        logger.info("Preparing UI for plotting.")
        self.need_to_save = True
        self.inspectionPlot.clear()
        self.scrollPlot.clear()
        self.inspectionPlot.setAutoVisible(y=True)
        self.scrollPlot.enableAutoRange()
        self.event_view_plot.clear()

        # Reset the clicked points since we do not want to accidentally
        # adjust plot items on the new acquisition
        self.last_acq_point_clicked = None
        self.last_event_clicked_global = None
        self.last_event_clicked_local = None
        self.last_event_point_clicked = None

        # sort_index and event_spinbox_list are used to reference the correct
        # event when using the eventSpinbox. This was choosen because you cannot
        # sort GUI objects when they are presented on the screen.
        self.sort_index = []
        self.event_spinbox_list = []

        # I choose to just show
        acq_dict = self.exp_manager.exp_dict["mini"]
        if self.acquisition_number.value() in acq_dict:
            logger.info(f"Plotting acquisition {self.acquisition_number.value()}.")

            # Temporarily disable the acquisition number to prevent some weird behavior
            # where the the box will skip every other acquisition.
            self.acquisition_number.setEnabled(False)

            # Creates a reference to the acquisition object so that the
            # acquisition object does not have to be referenced from
            # acquisition dictionary. Makes it more readable.
            acq_object = acq_dict.get(self.acquisition_number.value())

            # Set the epoch
            self.epoch_edit.setText(acq_object.epoch)

            # Set baseline mean or voltage offset
            self.voltage_offset_edit.setText(str(round_sig(acq_object.offset, 4)))

            # Set Rs from Rc check
            self.rs_edit.setText(str(round_sig(acq_object.rs, 4)))

            # Create the acquisitions plot item for the main acquisition plot
            acq_plot = pg.PlotDataItem(
                x=acq_object.plot_acq_x(),
                y=acq_object.plot_acq_y(),
                name=str(self.acquisition_number.text()),
                pen=pg.mkPen("#C9CDD0"),
                symbol="o",
                symbolSize=8,
                symbolBrush=(0, 0, 0, 0),
                symbolPen=(0, 0, 0, 0),
            )

            # Creates the ability to click on specific points in the main
            # acquisition plot window. The function acqPlotClicked stores
            # the point clicked for later use and is used when creating a
            # new event.
            acq_plot.sigPointsClicked.connect(self.acqPlotClicked)

            # Add the plot item to the plot. Need to do it this way since
            # the ability to the click on specific points is need.
            self.inspectionPlot.addItem(acq_plot)
            self.inspectionPlot.setYRange(
                min(acq_object.final_array),
                max(acq_object.final_array),
                padding=0.1,
            )

            # Add the draggable region to scrollPlot.
            self.scrollPlot.addItem(self.region, ignoreBounds=True)

            # Create the plot with the draggable region. Since there is
            # no interactivity with this plot there is no need to create
            # a plot item.
            self.scrollPlot.plot(
                x=acq_object.plot_acq_x(),
                y=acq_object.plot_acq_y(),
                pen=pg.mkPen("#C9CDD0"),
            )

            # Enabled the acquisition number since it was disabled earlier.
            self.acquisition_number.setEnabled(True)
            logger.info(f"Acquisition {self.acquisition_number.value()} plotted.")

            # Plot the postsynaptic events.
            if acq_object.postsynaptic_events:
                logger.info(
                    f"Plotting acquisition {self.acquisition_number.value()} events."
                )

                # Create the event list and the true index of each event.
                # Since the plot items on a pyqtgraph plot cannot be sorted
                # I had to create a way to correctly reference the position
                # of events when adding new events because I ended up just
                # adding the new events to postsynaptic events list.
                self.sort_index = self.exp_manager.exp_dict["mini"][
                    self.acquisition_number.value()
                ].sort_index()
                self.event_spinbox_list = self.exp_manager.exp_dict["mini"][
                    self.acquisition_number.value()
                ].list_of_events()

                # Plot each event. Since the postsynaptic events are stored in
                # a list you can iterate through the list even if there is just
                # one event because lists are iterable in python.

                for i in self.event_spinbox_list:
                    # Create the event plot item that is added to the p1 plot.
                    event_plot = pg.PlotCurveItem(
                        x=acq_object.postsynaptic_events[i].event_x_comp()[:2],
                        y=acq_object.postsynaptic_events[i].event_y_comp()[:2],
                        pen=pg.mkPen("#34E44B", width=3),
                        name=i,
                        clickable=True,
                    )
                    # Adds the clicked functionality to the event plot item.
                    event_plot.sigClicked.connect(self.eventClicked)
                    self.inspectionPlot.addItem(event_plot)

                    # Events plotted on scrollPlot do not need any interactivity. You have
                    # create new event plot items for each plot because one graphic
                    # item cannot be used in multiple parts of a GUI in Qt.
                    self.scrollPlot.plot(
                        x=acq_object.postsynaptic_events[i].event_x_comp()[:2],
                        y=acq_object.postsynaptic_events[i].event_y_comp()[:2],
                        pen=pg.mkPen("#34E44B", width=3),
                    )

                # Set the event spinbox to the first event and sets the min
                # an max value. I choose to start the events at 0 because it
                # is easier to work with event referenceing
                self.event_number.setMinimum(0)
                self.event_number.setMaximum(self.event_spinbox_list[-1])
                self.event_number.setValue(0)
                self.eventSpinbox(0)
                logger.info(
                    f"Acquisition {self.acquisition_number.value()} has no events to plot."
                )
            else:
                logger.info(
                    f"Acquisition {self.acquisition_number.value()}: Events plotted."
                )
            self.acq_point_clicked = pg.PlotDataItem(
                x=[],
                y=[],
                pen=None,
                symbol="o",
                symbolPen=pg.mkPen({"color": "#34E44B", "width": 2}),
            )

            self.inspectionPlot.addItem(self.acq_point_clicked)
        else:
            logger.info(f"No acquisition {self.acquisition_number.value()}.")
            text = pg.TextItem(text="No acquisition", anchor=(0.5, 0.5))
            text.setFont(QFont("Helvetica", 20))
            self.scrollPlot.setRange(xRange=(-30, 30), yRange=(-30, 30))
            self.scrollPlot.addItem(text)
            self.acquisition_number.setEnabled(True)

    def reset(self):
        logger.info("Resetting UI.")
        """
        This function resets all the variables and clears all the plots.
        It takes a while to run.
        """
        self.inspectionPlot.clear()
        self.scrollPlot.clear()
        self.template_plot.clear()
        self.load_widget.clearData()
        self.calc_param_clicked = False
        self.event_view_plot.clear()
        self.last_event_point_clicked = None
        self.last_acq_point_clicked = None
        self.last_event_clicked_global = None
        self.last_event_clicked_local = None
        self.event_spinbox_list = []
        self.sort_index = []
        self.stem_plot.clear()
        self.amp_dist.clear()
        self.ave_event_plot.clear()
        self.inspection_widget.clearData()
        self.calc_param_clicked = False
        self.need_to_save = False
        self.analyze_acq_button.setEnabled(True)
        self.calculate_parameters.setEnabled(True)
        self.plot_selector.clear()
        self.pbar.setValue(0)
        self.exp_manager = ExpManager()
        self.load_widget.setData(self.exp_manager)
        self.clearTables()
        self.pbar.setFormat("Ready to analyze")
        logger.info("UI Reset. Ready to analyze.")

    def update(self):
        """
        This functions is used for the draggable region.
        See PyQtGraphs documentation for more information.
        """
        self.region.setZValue(10)
        minX, maxX = self.region.getRegion()
        self.inspectionPlot.setXRange(minX, maxX, padding=0)

    def updateRegion(self, window, viewRange):
        """
        This functions is used for the draggable region.
        See PyQtGraphs documentation for more information
        """
        rgn = viewRange[0]
        self.region.setRegion(rgn)

    def slider_value(self, value):
        self.modify = value

    def leftbutton(self):
        if self.left_button.isDown():
            minX, maxX = self.region.getRegion()
            self.region.setRegion([minX - self.modify, maxX - self.modify])

    def rightbutton(self):
        if self.right_button.isDown():
            minX, maxX = self.region.getRegion()
            self.region.setRegion([minX + self.modify, maxX + self.modify])

    def acqPlotClicked(self, item, points):
        """
        Returns the points clicked in the acquisition plot window.
        """
        if len(points) > 0:
            logger.info(f"Acquisition {self.acquisition_number.value()} point clicked.")
        if self.acq_point_clicked is None:
            self.acq_point_clicked = pg.PlotDataItem(
                x=[points[0].pos()[0]],
                y=[points[0].pos()[1]],
                pen=None,
                symbol="o",
                symbolPen=pg.mkPen({"color": "#34E44B", "width": 2}),
            )
            self.inspectionPlot.addItem(self.acq_point_clicked)
            self.last_acq_point_clicked = points[0].pos()

            logger.info(f"Point {self.last_acq_point_clicked} set as point clicked.")
        else:
            self.acq_point_clicked.setData(
                x=[points[0].pos()[0]],
                y=[points[0].pos()[1]],
                pen=None,
                symbol="o",
                symbolPen=pg.mkPen({"color": "#34E44B", "width": 2}),
            )
            self.last_acq_point_clicked = points[0].pos()

            logger.info(f"Point {self.last_acq_point_clicked} set as point clicked.")

    def eventClicked(self, item):
        """
        Set the event spinbox to the event that was clicked in the acquisition
        window.
        """
        logger.info("Event clicked.")
        index = self.sort_index.index(int(item.name()))
        self.event_number.setValue(index)
        self.eventSpinbox(index)
        logger.info(f"Event {index} set as current event.")

    def eventSpinbox(self, h):
        """
        Function to plot a event in the event plot.
        """
        if not self.exp_manager.acqs_exist("mini"):
            logger.info(
                "Event was not plotted, acquisition"
                f" {self.acquisition_number.value()} does not exist."
            )
            self.errorDialog(
                f"Event was not plotted, {self.acquisition_number.value()} does not exist."
            )
            return None

        # Return the correct index of the event. This is needed because of
        # how new events are created
        event_index = self.sort_index[h]

        logger.info(
            f"Plotting event {event_index} on acquisition {self.acquisition_number.value()}."
        )

        self.need_to_save = True

        # if h in self.event_spinbox_list:
        # Clear the last event_point_clicked
        self.last_event_point_clicked = None

        # Resets the color of the events on p1 and scrollPlot. In python
        # when you create an object it is given a position in the memory
        # you can create new "pointers" to the object. This makes it
        # easy to modify Qt graphics objects without having to find them
        # under their original parent.
        if self.last_event_clicked_global is not None:
            self.last_event_clicked_global.setPen("#34E44B", width=3)
            self.last_event_clicked_local.setPen("#34E44B", width=3)

        # Clear the event plot
        self.event_view_plot.clear()

        # Reference the event.
        acq = self.exp_manager.exp_dict["mini"][self.acquisition_number.value()]
        event = acq.postsynaptic_events[event_index]

        # This allows the window on p1 to follow each event when using
        # the event spinbox. The window will only adjust if any part of
        # the event array falls outside of the current viewable region.
        minX, maxX = self.region.getRegion()
        width = maxX - minX
        if event.plot_event_x()[0] < minX or event.plot_event_x()[-1] > maxX:
            self.region.setRegion(
                [
                    int(event.plot_event_x()[0] - 100),
                    int(event.plot_event_x()[0] + width - 100),
                ]
            )

        # Create the event plot item. The x_array is a method call
        # because it needs to be corrected for sample rate and
        # displayed as milliseconds.
        event_item = pg.PlotDataItem(
            x=event.plot_event_x(),
            y=event.plot_event_y(),
            symbol="o",
            symbolPen=None,
            symbolBrush="#C9CDD0",
            symbolSize=6,
        )

        # Add clickable functionality to the event plot item.
        event_item.sigPointsClicked.connect(self.eventPlotClicked)

        self.event_view_plot.addItem(event_item)

        # Plot item for the baseline, peak and estimated tau.
        event_plot_items = pg.PlotDataItem(
            x=event.event_x_comp(),
            y=event.event_y_comp(),
            pen=None,
            symbol="o",
            symbolBrush=[
                pg.mkBrush("#34E44B"),
                pg.mkBrush("#E867E8"),
                pg.mkBrush("#2A82DA"),
            ],
            symbolSize=12,
        )

        # Add the plot items to the event view widget.
        self.event_view_plot.addItem(event_plot_items)

        # Plot the fit taus if curve fit was selected.
        if event.fit_tau is not np.nan and self.curve_fit_decay.isChecked():
            event_decay_items = pg.PlotDataItem(
                x=event.fit_decay_x,
                y=event.fit_decay_y,
                pen=pg.mkPen((255, 0, 255, 175), width=3),
            )
            self.event_view_plot.addItem(event_decay_items)

        # Creating a reference to the clicked events.
        self.last_event_clicked_global = self.scrollPlot.listDataItems()[
            event_index + 1
        ]
        self.last_event_clicked_local = self.inspectionPlot.listDataItems()[
            event_index + 1
        ]

        # Sets the color of the events on p1 and scrollPlot so that the event
        # selected with the spinbox or the event that was clicked is shown.
        self.last_event_clicked_global.setPen("#E867E8", width=3)
        self.last_event_clicked_local.setPen("#E867E8", width=3)

        # Set the attributes of the event on the GUI.
        self.event_amplitude.setText(str(round_sig(event.amplitude, sig=4)))
        self.event_tau.setText(str(round_sig(event.final_tau_x, sig=4)))
        self.event_rise_time.setText(str(round_sig(event.rise_time, sig=4)))
        self.event_rise_rate.setText(str(round_sig(event.rise_rate, sig=4)))
        self.event_baseline.setText(str(round_sig(event.event_start_y, sig=4)))

        logger.info("Event plotted.")

    def eventPlotClicked(self, item, points):
        """
        Function to make the event in the event view widget
        clickable.

        Returns
        -------
        None
        """
        # Resets the color of the previously clicked event point.
        event_index = self.sort_index[int(self.event_number.text())]

        logger.info(f"Point clicked on event {event_index}.")
        if self.last_event_point_clicked:
            # self.last_event_point_clicked.resetPen()
            # self.last_event_point_clicked = None
            self.event_view_plot.removeItem(self.last_event_point_clicked[0])

        # Set the color and size of the new event point that
        # was clicked.
        event_point_clicked = pg.PlotDataItem(
            x=[points[0].pos()[0]],
            y=[points[0].pos()[1]],
            pen=None,
            symbol="o",
            symbolPen=pg.mkPen("#E867E8", width=3),
        )
        self.event_view_plot.addItem(event_point_clicked)
        self.last_event_point_clicked = (event_point_clicked, points[0].pos())

        logger.info(f"Point {self.last_event_point_clicked[1][0]} clicked.")

    def setPointAsPeak(self):
        """
        This will set the event peak as the point selected on the event plot and
        update the other two acquisition plots.

        Returns
        -------
        None.

        """
        if not self.exp_manager.acq_exists("mini", self.acquisition_number.value()):
            logger.info(
                "Event peak was not set, acquisition"
                f" {self.acquisition_number.value()} does not exist."
            )
            self.errorDialog(
                f"Event peak was not set, acquisition {self.acquisition_number.value()} does not exist."
            )

        elif self.last_event_point_clicked is None:
            logger.info("No event peak was selected, peak not set.")
            self.errorDialog("No event peak was selected, peak not set.")

        elif self.last_event_point_clicked is not None:
            self.need_to_save = True

            # Find the index of the event so that the correct event is
            # modified.
            event_index = self.sort_index[int(self.event_number.text())]
            acq = self.exp_manager.exp_dict["mini"][self.acquisition_number.value()]
            event = acq.postsynaptic_events[event_index]

            logger.info(
                f"Setting peak on event {event_index} on acquisition {self.acquisition_number.value()}."
            )

            # if len(self.last_event_point_clicked) > 0:
            # X and Y point of the event point that was clicked. The
            # x point needs to be adjusted back to samples for the
            # change amplitude function in the postsynaptic event
            # object.
            x = self.last_event_point_clicked[1][0]
            y = self.last_event_point_clicked[1][1]

            # Pass the x and y points to the change amplitude function
            # for the postsynaptic event.
            event.set_amplitude(x, y)

            # Redraw the events on p1 and scrollPlot plots. Note that the last
            # event clicked provides a "pointed" to the correct plot
            # object on p1 and scrollPlot so that it does not have to be
            # referenced again.
            self.last_event_clicked_global.setData(
                x=event.event_x_comp()[:2],
                y=event.event_y_comp()[:2],
                pen=pg.mkPen("#E867E8", width=3),
            )
            self.last_event_clicked_local.setData(
                x=event.event_x_comp()[:2],
                y=event.event_y_comp()[:2],
                pen=pg.mkPen("#E867E8", width=3),
            )

            # This is need to redraw the event in the event view.
            self.eventSpinbox(int(self.event_number.text()))

            # Reset the last point clicked.
            self.event_view_plot.removeItem(self.last_event_point_clicked)

            logger.info(
                f"Peak set on event {event_index} on acquisition {self.acquisition_number.value()}."
            )

    def setPointAsBaseline(self):
        """
        This will set the baseline as the point selected on the event plot and
        update the other two acquisition plots.

        Returns
        -------
        None.

        """
        # Reset the last point clicked.
        self.event_view_plot.removeItem(self.last_event_point_clicked)

        if not self.exp_manager.acq_exists("mini", self.acquisition_number.value()):
            logger.info(
                f"Event baseline was not set, acquisition {self.acquisition_number.value()} does not exist."
            )
            self.errorDialog(
                f"Event baseline was not set, acquisition {self.acquisition_number.value()} does not exist."
            )

        elif self.last_event_point_clicked is None:
            logger.info("No event baseline was selected, baseline not set.")
            self.errorDialog("No event baseline was selected, baseline not set.")

        elif self.last_event_point_clicked is not None:
            self.need_to_save = True

            # Find the index of the event so that the correct event is
            # modified.
            event_index = self.sort_index[int(self.event_number.text())]

            acq = self.exp_manager.exp_dict["mini"][self.acquisition_number.value()]
            event = acq.postsynaptic_events[event_index]

            logger.info(
                f"Setting point as peak on event {event_index} on acquisition {self.acquisition_number.value()}."
            )
            # X and Y point of the event point that was clicked. The
            # x point needs to be adjusted back to samples for the
            # change amplitude function in the postsynaptic event
            # object.
            x = self.last_event_point_clicked[1][0]
            y = self.last_event_point_clicked[1][1]

            # Pass the x and y points to the change baseline function
            # for the postsynaptic event.
            event.set_baseline(x, y)

            # Redraw the events on p1 and scrollPlot plots. Note that the last
            # event clicked provides a "pointed" to the correct plot
            # object on p1 and scrollPlot so that it does not have to be
            # referenced again.
            self.last_event_clicked_global.setData(
                x=event.event_x_comp()[:2],
                y=event.event_y_comp()[:2],
                pen=pg.mkPen("#E867E8", width=3),
            )
            self.last_event_clicked_local.setData(
                x=event.event_x_comp()[:2],
                y=event.event_y_comp()[:2],
                pen=pg.mkPen("#E867E8", width=3),
            )

            # This is need to redraw the event in the event view.
            self.eventSpinbox(int(self.event_number.text()))

            logger.info(
                f"Baseline set on event {event_index} on acquisition {self.acquisition_number.value()}."
            )

    def deleteEvent(self):
        """
        This function deletes a event from the acquisition and removes it from the
        GUI.

        Returns
        -------
        None
        """
        if not self.exp_manager.acq_exists("mini", self.acquisition_number.value()):
            logger.info(
                f"No event deleted, acquisition {self.acquisition_number.value()}"
                "does not exist."
            )
            self.errorDialog(
                f"No event deleted, acquisition {self.acquisition_number.value()} does not exist."
            )
            return None
        self.need_to_save = True

        # Find the correct event.
        event_index = self.sort_index[int(self.event_number.text())]

        logger.info(
            f"Deleting event {event_index} on acquisition \
                  {self.acquisition_number.value()}."
        )

        # self.last_event_deleted = \
        #     self.acq_object.postsynaptic_events[int(self.event_number.text())]
        self.last_event_deleted_number = self.event_number.text()

        # Clear the event view plot.
        self.event_view_plot.clear()

        # Remove the event from the plots. +1 is added because the first plot
        # item is the acquisition.
        self.inspectionPlot.removeItem(self.last_event_clicked_local)
        self.scrollPlot.removeItem(self.last_event_clicked_global)

        # Deleted the event from the postsynaptic events and final events.
        acq = self.exp_manager.exp_dict["mini"][self.acquisition_number.value()]
        acq.del_postsynaptic_event(event_index)

        # Recreate the sort_index and event_spinbox_list
        self.sort_index = self.exp_manager.exp_dict["mini"][
            self.acquisition_number.value()
        ].sort_index()
        self.event_spinbox_list = self.exp_manager.exp_dict["mini"][
            self.acquisition_number.value()
        ].list_of_events()

        # Rename the plotted event's
        for num, i, j in zip(
            self.event_spinbox_list,
            self.inspectionPlot.listDataItems()[1:],
            self.scrollPlot.listDataItems()[1:],
        ):
            i.opts["name"] = num
            j.opts["name"] = num

        # Clear the last_event_clicked_global to prevent errors
        self.last_event_clicked_global = None
        self.last_event_clicked_local = None

        # Reset the maximum spinbox value
        if len(self.event_spinbox_list) > 0:
            self.event_number.setMaximum(self.event_spinbox_list[-1])

        # Plot the next event in the list
        self.eventSpinbox(int(self.event_number.text()))
        self.events_deleted += 1

        logger.info(
            f"Deleted event {event_index} on acquisition \
                {self.acquisition_number.value()}."
        )

    def createEvent(self):
        """
        This function is used to create new event events. By clicking
        on the main acquisition and clicking create new event's button
        will run this function.
        """
        # Reset the clicked point so a new point is not accidentally created.
        if not self.exp_manager.acq_exists("mini", self.acquisition_number.value()):
            logger.info(
                f"No event created, acquisition {self.acquisition_number.value()} does not exist."
            )
            self.errorDialog(
                f"No event created, acquisition {self.acquisition_number.value()} does not exist."
            )

        # Make sure that the last acq point that was clicked exists.
        elif self.last_acq_point_clicked is not None:
            self.inspectionPlot.removeItem(self.acq_point_clicked)
            self.need_to_save = True
            logger.info(
                f"Creating event on acquisition {self.acquisition_number.value()}."
            )
            x = self.last_acq_point_clicked[0]

            # The event needs a baseline of at least 2 milliseconds long.
            acq = self.exp_manager.exp_dict["mini"][self.acquisition_number.value()]

            if x > 2:
                # Create the new event.
                created = acq.create_new_event(x)

                if not created:
                    self.errorDialog(
                        f"Could not create event at {x}\n"
                        f" on acquisition {self.acquisition_number.value()}"
                    )
                    self.logger.info(
                        f"Could not create event at {x}"
                        f" on acquisition {self.acquisition_number.value()}"
                    )
                    return None

                # Reset the event_spinbox_list and sort index.
                self.sort_index = acq.sort_index()
                self.event_spinbox_list = acq.list_of_events()

                # Return the correct position of the event
                id_value = self.event_spinbox_list[-1]
                event = acq.postsynaptic_events[id_value]

                # Add the event item to the plot and make it clickable for p1.
                event_plot = pg.PlotCurveItem(
                    x=event.event_x_comp()[:2],
                    y=event.event_y_comp()[:2],
                    pen=pg.mkPen("#34E44B", width=3),
                    name=id_value,
                    clickable=True,
                )
                event_plot.sigClicked.connect(self.eventClicked)
                self.inspectionPlot.addItem(event_plot)
                self.scrollPlot.plot(
                    x=event.event_x_comp()[:2],
                    y=event.event_y_comp()[:2],
                    pen=pg.mkPen("#34E44B", width=3),
                    name=id_value,
                )

                # Set the spinbox maximum and current value.
                self.event_number.setMaximum(self.event_spinbox_list[-1])
                self.event_number.setValue(self.sort_index.index(id_value))
                self.eventSpinbox(self.sort_index.index(id_value))

                logger.info(
                    f"Event created on acquisition {self.acquisition_number.value()}."
                )
            else:
                # Raise error if the point is too close to the beginning.
                self.errorDialog(
                    "The selected point is too close\n"
                    "to the beginning of the acquisition"
                )
                logger.info("No event created, selected point to close to beginning.")
        self.last_acq_point_clicked = None
        self.acq_point_clicked = None

    def deleteAcq(self):
        """
        Deletes the current acquisition when the delete acquisition
        button is clicked.
        """

        if not self.exp_manager.acqs_exist("mini"):
            logger.info(
                f"Acquisition {self.acquisition_number.value()} was not"
                " deleted, no acquisitions exist."
            )
            self.errorDialog(
                f"Acquisition {self.acquisition_number.value()} was not\n"
                " deleted, no acquisitions exist."
            )
            return None

        logger.info(f"Deleting aquisition {self.acquisition_number.value()}.")
        self.need_to_save = True

        self.recent_reject_acq = {}

        # Add acquisition to be deleted to the deleted acquisitions
        # and the recent deleted acquistion dictionary.
        self.exp_manager.delete_acq("mini", self.acquisition_number.value())

        # Clear plots
        self.inspectionPlot.clear()
        self.scrollPlot.clear()
        self.event_view_plot.clear()

        # Reset the analysis list and change the acquisition to the next
        # acquisition.
        self.acquisition_number.setValue(self.acquisition_number.value() + 1)
        logger.info(f"Aquisition {self.acquisition_number.value()} deleted.")

    def resetRejectedAcqs(self):
        if not self.exp_manager.acqs_exist("mini"):
            logger.info("Did not reset acquistions, no acquisitions exist.")
            self.errorDialog("Did not reset acquistions, no acquisitions exist.")
        else:
            self.need_to_save = True
            logger.info("Resetting deleted acquisitions.")
            self.exp_manager.reset_deleted_acqs("mini")
            logger.info("Deleted acquisitions reset.")
            self.pbar.setFormat("Reset deleted acquisitions.")

    def resetRecentRejectedAcq(self):
        if not self.exp_manager.acqs_exist("mini"):
            logger.info("Did not reset recent acquistion, no acquisitions exist.")
            self.errorDialog("Did not reset recent acquistion, no acquisitions exist.")
        else:
            self.need_to_save = True
            logger.info("Resetting most recent deleted acquisition.")
            number = self.exp_manager.reset_recent_deleted_acq("mini")
            if number != 0:
                self.acquisition_number.setValue(number)
                logger.info(f"Acquisition {number} reset.")
                self.pbar.setFormat(f"Reset acquisition {number}.")
            else:
                logger.info("No acquisition to reset.")
                self.pbar.setFormat("No acquisition to reset.")

    def runFinalAnalysis(self):
        if not self.exp_manager.acqs_exist("mini"):
            logger.info("Did not run final analysis, no acquisitions analyzed.")
            self.errorDialog("Did not run final analysis, no acquisitions analyzed.")
            return None
        logger.info("Beginning final analysis.")
        self.calculate_parameters.setEnabled(False)
        self.calculate_parameters_2.setEnabled(False)
        self.calc_param_clicked = True
        if self.exp_manager.final_analysis is not None:
            logger.info("Clearing previous analysis.")
            self.final_tab_widget.clear()
            self.clearTables()
            self.table_dict = {}
        self.need_to_save = True

        self.pbar.setFormat("Analyzing...")
        logger.info("Experiment manager started final analysis")
        self.exp_manager.run_final_analysis(acqs_deleted=self.exp_manager.acqs_deleted)
        logger.info("Experiment manager finished final analysis.")
        fa = self.exp_manager.final_analysis
        self.plotAveEvent(
            fa.average_event_x(),
            fa.average_event_y(),
            fa.fit_decay_x(),
            fa.fit_decay_y(),
        )
        logger.info("Plotted average event")
        for key, df in fa.df_dict.items():
            data_table = pg.TableWidget(sortable=False)
            self.table_dict[key] = data_table
            data_table.setData(df.T.to_dict("dict"))
            self.final_tab_widget.addTab(data_table, key)
        logger.info("Set final data into tables.")
        plots = [
            "Amplitude (pA)",
            "Est tau (ms)",
            "Rise time (ms)",
            "Rise rate (pA/ms)",
            "IEI (ms)",
        ]
        self.plot_selector.clear()
        self.plot_selector.addItems(plots)
        self.plot_selector.setMinimumContentsLength(len(max(plots, key=len)))
        if self.plot_selector.currentText() != "IEI (ms)":
            self.plotRawData(self.plot_selector.currentText())
        self.pbar.setFormat("Finished analysis")
        self.calculate_parameters.setEnabled(True)
        self.calculate_parameters_2.setEnabled(True)
        self.tab_widget.setCurrentIndex(2)
        logger.info("Plotted final data.")
        logger.info("Finished analyzing.")
        self.pbar.setFormat("Final analysis finished")

    def plotAveEvent(self, x, y, decay_x, decay_y):
        self.ave_event_plot.clear()
        self.ave_event_plot.plot(x=x, y=y, pen=pg.mkPen(width=3))
        self.ave_event_plot.plot(
            x=decay_x, y=decay_y, pen=pg.mkPen({"color": "#34E44B", "width": 2})
        )

    def plotRawData(self, y: str):
        if self.exp_manager.final_analysis is not None and y != "":
            if y != "IEI (ms)":
                self.plotStemData(y)
            else:
                self.stem_plot.clear()
            self.plotAmpDist(y)

    def plotStemData(self, column: str):
        self.stem_plot.clear()
        fa = self.exp_manager.final_analysis
        x_values = fa.timestamp_array()
        y_values = fa.get_raw_data(column)
        y_stems = np.insert(y_values, np.arange(y_values.size), 0)
        x_stems = np.repeat(x_values, 2)
        stem_item = pg.PlotDataItem(x=x_stems, y=y_stems, connect="pairs")
        head_item = pg.PlotDataItem(
            x=x_values,
            y=y_values,
            pen=None,
            symbol="o",
            symbolSize=2,
            symbolPen=None,
            symbolBrush="w",
        )
        self.stem_plot.addItem(stem_item)
        self.stem_plot.addItem(head_item)
        self.stem_plot.setLabel(axis="left", text=f"{column}")

    def plotAmpDist(self, column: str):
        self.amp_dist.clear()
        fa = self.exp_manager.final_analysis
        log_y, x = create_kde(
            fa.df_dict["Raw data"],
            self.plot_selector.currentText(),
        )
        y = fa.get_raw_data(self.plot_selector.currentText())
        dist_item = pg.PlotDataItem(
            x=x,
            y=log_y,
            fillLevel=0,
            fillOutline=True,
            fillBrush=pg.mkBrush("#bf00bf50"),
        )
        self.amp_dist.addItem(dist_item)
        self.amp_dist.setXRange(np.nanmin(y), np.nanmax(y))
        y_values = np.full(y.shape, max(log_y) * 0.05)
        y_stems = np.insert(y_values, np.arange(y_values.size), 0)
        x_stems = np.repeat(y, 2)
        stem_item = pg.PlotDataItem(x=x_stems, y=y_stems, connect="pairs")
        self.amp_dist.addItem(stem_item)

    def errorDialog(self, text):
        self.dlg.setWindowTitle("Error")
        self.dlg.setText(text)
        self.dlg.exec()

    def eventNotCreated(self):
        self.dlg.setWindowTitle("Information")
        self.dlg.setText("Event could not be created")
        self.dlg.exec()

    def loadExperiment(self, directory):
        logger.info(f"Loading experiment from {directory}.")
        self.reset()
        self.pbar.setFormat("Loading...")
        self.exp_manger = ExpManager()
        self.worker = ThreadWorker(self.exp_manager)
        self.worker.addAnalysis("load", analysis="mini", file_path=directory)
        self.worker.signals.progress.connect(self.updateProgress)
        self.worker.signals.finished.connect(self.setLoadData)
        QThreadPool.globalInstance().start(self.worker)

    def setLoadData(self):
        if self.exp_manager.final_analysis is not None:
            logger.info("Setting previously analyzed data.")
            self.pbar.setFormat("Setting previously analyzed data.")
            fa = self.exp_manager.final_analysis
            self.plotAveEvent(
                fa.average_event_x(),
                fa.average_event_y(),
                fa.fit_decay_x(),
                fa.fit_decay_y(),
            )
            for key, df in fa.df_dict.items():
                data_table = pg.TableWidget()
                self.table_dict[key] = data_table
                data_table.setData(df.T.to_dict("dict"))
                self.final_tab_widget.addTab(data_table, key)
            plots = [
                "Amplitude (pA)",
                "Est tau (ms)",
                "Rise time (ms)",
                "Rise rate (pA/ms)",
                "IEI (ms)",
            ]
            self.plot_selector.addItems(plots)
        self.calculate_parameters_2.setEnabled(True)
        self.calculate_parameters.setEnabled(True)
        self.pbar.setFormat("Loaded")
        self.acquisition_number.setMaximum(self.exp_manager.end_acq)
        self.acquisition_number.setMinimum(self.exp_manager.start_acq)
        self.acquisition_number.setValue(self.exp_manager.ui_prefs["Acq_number"])
        logger.info("Experiment successfully loaded.")
        self.pbar.setFormat("Experiment successfully loaded")

    def saveAs(self, save_filename):
        if not self.exp_manager.acqs_exist("mini"):
            logger.info("There is no data to save")
            self.errorDialog("There is no data to save")
        else:
            logger.info("Saving experiment.")
            self.reset_button.setEnabled(False)
            self.pbar.setFormat("Saving...")
            self.pbar.setValue(0)
            pref_dict = self.createPrefDict()
            pref_dict["Final Analysis"] = self.calc_param_clicked
            pref_dict["Acq_number"] = self.acquisition_number.value()
            self.exp_manager.set_ui_prefs(pref_dict)
            self.worker = ThreadWorker(self.exp_manager)
            self.worker.addAnalysis("save", file_path=save_filename)
            self.worker.signals.progress.connect(self.updateProgress)
            self.worker.signals.finished.connect(self.finishedSaving)
            QThreadPool.globalInstance().start(self.worker)
            self.reset_button.setEnabled(True)
            self.need_to_save = False

    def finishedSaving(self):
        self.pbar.setFormat("Finished saving")
        logger.info("Finished saving.")

    def createExperiment(self, urls):
        self.pbar("Creating experiment")
        self.load_widget.addData(urls)
        self.pbar("Experiment created")

    def createPrefDict(self):
        logger.info("Creating preferences dictionary.")
        pref_dict = {}
        pref_dict["baseline"] = self.baseline_widget.getSettings()
        pref_dict["filter"] = self.filter_widget.getSettings()
        pref_dict["rc_check"] = self.rc_widget.getSettings()
        pref_dict["mini"] = self.mini_settings.getSettings()
        return pref_dict

    def setPreferences(self, pref_dict: dict[dict[str, int | float | str]]):
        logger.info("Setting MiniAnalysis preferences.")

        self.baseline_widget.setSettings(pref_dict["baseline"])
        self.filter_widget.getSettings(pref_dict["filter"])
        self.rc_widget.getSettings(pref_dict["rc_check"])
        self.mini_settings.getSettings(pref_dict["mini"])

        logger.info("Preferences set.")
        self.pbar.setFormat("Preferences set")

    def loadPreferences(self, file_name):
        pref_dict = self.exp_manager.load_ui_prefs(file_name)
        self.setPreferences(pref_dict)

    def savePreferences(self, save_filename):
        pref_dict = self.createPrefDict()
        if pref_dict:
            self.exp_manager.save_ui_prefs(save_filename, pref_dict)

    def updateProgress(self, value):
        if isinstance(value, (int, float)):
            self.pbar.setFormat(f"Acquisition {value} analyzed")
        elif isinstance(value, str):
            self.pbar.setFormat(value)

    def setAppearancePreferences(self, pref_dict):
        self.inspectionPlot.setBackground(pref_dict[0])
        self.inspectionPlot.getAxis("left").setPen(pref_dict[1])
        self.inspectionPlot.getAxis("left").setTextPen(pref_dict[1])
        self.inspectionPlot.getAxis("bottom").setPen(pref_dict[1])
        self.inspectionPlot.getAxis("bottom").setTextPen(pref_dict[1])
        self.scrollPlot.setBackground(pref_dict[2])
        self.scrollPlot.getAxis("left").setPen(pref_dict[3])
        self.scrollPlot.getAxis("left").setTextPen(pref_dict[3])
        self.scrollPlot.getAxis("bottom").setPen(pref_dict[3])
        self.scrollPlot.getAxis("bottom").setTextPen(pref_dict[3])
        self.event_view_plot.setBackground(pref_dict[4])
        self.event_view_plot.getAxis("left").setPen(pref_dict[5])
        self.event_view_plot.getAxis("left").setTextPen(pref_dict[5])
        self.event_view_plot.getAxis("bottom").setPen(pref_dict[5])
        self.event_view_plot.getAxis("bottom").setTextPen(pref_dict[5])

    def setWorkingDirectory(self, path):
        self.signals.dir_path.emit(path)
