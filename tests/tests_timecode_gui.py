from PySide6 import QtCore, QtWidgets, QtGui
import typing, random
from posttools.timecode import Timecode

class TimecodeModel(QtCore.QAbstractItemModel):

	def __init__(self):
		super().__init__()
		self._timecodes = []
		self._titles  = {"timecode":"Timecode","rate":"Rate","mode":"Mode", "hours":"Hours","minutes":"Minutes", "seconds":"Seconds","frames":"Frames","framenumber":"Frame Number"}
		self._headers = list(self._titles.keys())
	
	def index(self, row:int, col:int, parent:QtCore.QModelIndex=QtCore.QModelIndex()) -> QtCore.QModelIndex:
		"""Return an internal index to the cell"""
		if parent.isValid():
			return QtCore.QModelIndex()
		else:
			data = self._timecodes[row]
			return self.createIndex(row, col, data)

	def parent(self, child:QtCore.QModelIndex) -> QtCore.QModelIndex:
		"""Return an index to the parent"""
		if child.isValid():
			return QtCore.QModelIndex()
		else:
			print("Interesting")

	def rowCount(self, parent=QtCore.QModelIndex()) -> int:
		"""Return the number of child rows"""
		if parent.isValid():
			return 0
		else:
			return len(self._timecodes)
		
	def columnCount(self, parent:QtCore.QModelIndex=QtCore.QModelIndex()) -> int:
		"""Return the number of columns for each child row"""
		if parent.isValid():
			return 0
		else:
			return len(self._headers)
		
	def data(self, index:QtCore.QModelIndex, role:int=QtCore.Qt.DisplayRole) -> typing.Any:
		"""Return the active data for a cell"""
		
		# Display role
		if role == QtCore.Qt.DisplayRole:
			tc  = index.internalPointer()
			col = self._headers[index.column()]
			if col == "timecode":
				return str(tc)
			elif col == "rate":
				return tc.rate
			elif col == "mode":
				return str(tc.mode.name)
			elif col == "hours":
				return tc.hours
			elif col == "minutes":
				return tc.minutes
			elif col == "seconds":
				return tc.seconds
			elif col == "frames":
				return tc.frames
			elif col == "framenumber":
				return tc.framenumber
		
		#if role == QtCore.Qt.SortOrder

		# Get raw item
		elif role == QtCore.Qt.UserRole:
			return index.internalPointer()
	
	def sort(self, column:int, order:int=QtCore.Qt.AscendingOrder) -> None:
		self.beginResetModel()
		self._timecodes.sort(reverse=order==QtCore.Qt.DescendingOrder)
		self.endResetModel()

	def headerData(self, section, orientation, role:int=QtCore.Qt.DisplayRole) -> typing.Any:
		"""Return the active data for a header"""
		if role == QtCore.Qt.DisplayRole:
			return self._titles.get(self._headers[section])
	
	def addTimecode(self, timecode:Timecode):
		"""Non-Qt Method"""
		self.beginInsertRows(QtCore.QModelIndex(), len(self._timecodes), len(self._timecodes))
		self._timecodes.append(timecode)
		self.endInsertRows()
	
	def populateTimecodes(self, count=500, start:int=0, end:int=86400, rates:typing.List=None, modes:typing.List=None, continuous:bool=True):
		"""Non-Qt Method"""
		frame_start = min([start,end])
		frame_end   = max([start, end])
		rates = rates or [24, 30, 48, 60]
		modes = modes or [Timecode.Mode.NDF, Timecode.Mode.DF]

		self.beginResetModel()
		
		self._timecodes = []
		
		if not continuous:
			for _ in range(count):
				frame = random.randint(frame_start, frame_end)
				rate  = random.choice(rates)
				mode  = random.choice(modes) if rate%30==0 else Timecode.Mode.NDF

				self._timecodes.append(Timecode(frame, rate, mode))
		
		else:
			for rate in rates:
				for mode in modes:
					if rate % 30 and mode == Timecode.Mode.DF: continue
					for frame in range(frame_start, frame_end):
						self._timecodes.append(Timecode(frame, rate, mode))
		
		self.endResetModel()

class TimecodeTester(QtWidgets.QWidget):

	def __init__(self):
		super().__init__()
		self.setLayout(QtWidgets.QVBoxLayout())
		self.setupWidgets()
	
	def setupWidgets(self):
		grp_settings = QtWidgets.QGroupBox(title="Options")
		grp_settings.setLayout(QtWidgets.QHBoxLayout())

		self.txt_frame_from = QtWidgets.QLineEdit()
		self.txt_frame_from.setValidator(QtGui.QIntValidator())
		self.txt_frame_from.setText(str(0))
		self.txt_frame_from.setMaximumWidth(50)
		
		self.txt_frame_to   = QtWidgets.QLineEdit()
		self.txt_frame_to.setValidator(QtGui.QIntValidator())
		self.txt_frame_to.setText(str(86400))
		self.txt_frame_to.setMaximumWidth(50)

		self.rad_continuous = QtWidgets.QRadioButton(text="Continuous")
		self.rad_random     = QtWidgets.QRadioButton(text="Random Count:")
		grp_range = QtWidgets.QButtonGroup(self)
		grp_range.addButton(self.rad_continuous)
		grp_range.addButton(self.rad_random)

		self.txt_count		= QtWidgets.QLineEdit()
		self.txt_count.setValidator(QtGui.QIntValidator(bottom=1))
		self.txt_count.setText(str(20))
		self.txt_count.setMaximumWidth(35)
		grp_range.buttonToggled.connect(lambda: self.txt_count.setEnabled(self.rad_random.isChecked()))
		self.rad_continuous.setChecked(True)

		self.chk_rate_24	= QtWidgets.QCheckBox(text="24")
		self.chk_rate_24.setChecked(True)

		self.chk_rate_30	= QtWidgets.QCheckBox(text="30")
		self.chk_rate_48	= QtWidgets.QCheckBox(text="48")
		self.chk_rate_60	= QtWidgets.QCheckBox(text="60")

		self.chk_mode_ndf	= QtWidgets.QCheckBox(text="NDF")
		self.chk_mode_df	= QtWidgets.QCheckBox(text="DF")
		self.chk_mode_ndf.setChecked(True)

		self.btn_generate   = QtWidgets.QPushButton(text="Generate", clicked=self.populateModel)
		
		grp_settings.layout().addWidget(QtWidgets.QLabel(text="Frame Range:"))
		grp_settings.layout().addWidget(self.txt_frame_from)
		grp_settings.layout().addWidget(QtWidgets.QLabel(text="to"))
		grp_settings.layout().addWidget(self.txt_frame_to)

		grp_settings.layout().addStretch()
		grp_settings.layout().addWidget(self.rad_continuous)
		grp_settings.layout().addWidget(self.rad_random)
		grp_settings.layout().addWidget(self.txt_count)
		
		grp_settings.layout().addStretch()
		grp_settings.layout().addWidget(QtWidgets.QLabel(text="Rates:"))
		grp_settings.layout().addWidget(self.chk_rate_24)
		grp_settings.layout().addWidget(self.chk_rate_30)
		grp_settings.layout().addWidget(self.chk_rate_48)
		grp_settings.layout().addWidget(self.chk_rate_60)

		grp_settings.layout().addStretch()
		grp_settings.layout().addWidget(QtWidgets.QLabel(text="Modes:"))
		grp_settings.layout().addWidget(self.chk_mode_ndf)
		grp_settings.layout().addWidget(self.chk_mode_df)


		grp_settings.layout().addStretch()
		grp_settings.layout().addWidget(self.btn_generate)

		self.layout().addWidget(grp_settings)

		self.tree_timecodes = QtWidgets.QTreeView()
		self.tree_timecodes.setSortingEnabled(True)
		self.tree_timecodes.setAlternatingRowColors(True)
		self.tree_timecodes.setIndentation(0)
		self.tree_timecodes.setUniformRowHeights(True)
		self.tree_timecodes.sortByColumn(0, QtCore.Qt.AscendingOrder)
		self.layout().addWidget(self.tree_timecodes)

		creds = QtWidgets.QHBoxLayout()
		creds.addWidget(QtWidgets.QLabel("Timecode Tester by Michael Jordan"))
		creds.addStretch()
		creds.addWidget(QtWidgets.QLabel("<a href=\"https://github.com/mjiggidy/posttools/\">https://github.com/mjiggidy/posttools/</a>"))
		self.layout().addLayout(creds)
	
	def setTimecodeModel(self, model:QtCore.QAbstractItemModel):
		self.tree_timecodes.setModel(model)
		self.populateModel()
	
	def populateModel(self):
		range_start = int(self.txt_frame_from.text()) if self.txt_frame_from.text() else 0
		range_end = int(self.txt_frame_to.text()) if self.txt_frame_to.text() else max(range_start, 86400)
		count = int(self.txt_count.text()) if self.txt_count.text() and int(self.txt_count.text()) != 0 else 1

		rates = []
		if self.chk_rate_24.isChecked(): rates.append(24)
		if self.chk_rate_30.isChecked(): rates.append(30)
		if self.chk_rate_48.isChecked(): rates.append(48)
		if self.chk_rate_60.isChecked(): rates.append(60)

		modes = []
		if self.chk_mode_df.isChecked(): modes.append(Timecode.Mode.DF)
		if self.chk_mode_ndf.isChecked(): modes.append(Timecode.Mode.NDF)

		random = self.rad_continuous.isChecked()

		self.tree_timecodes.model().populateTimecodes(count=count, start=range_start, end=range_end, rates=rates, modes=modes, continuous=random)
		self.tree_timecodes.sortByColumn(0, QtCore.Qt.AscendingOrder)
		

class TimecodeWindow(QtWidgets.QMainWindow):

	def __init__(self):
		super().__init__()
		self.setWindowTitle("Timecode Tester")
		
		model_tc = TimecodeModel()
		
		widget_tcteser = TimecodeTester()
		widget_tcteser.setTimecodeModel(model_tc)
		
		self.setCentralWidget(widget_tcteser)







if __name__ == "__main__":

	app = QtWidgets.QApplication()
	win = TimecodeWindow()
	win.show()
	app.exec()