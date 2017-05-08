#!/usr/bin/env python2
#  -*- coding: utf-8 -*-

import sys
from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QTimer

NUM_ROWS = 40
NUM_COLS = 60
CELL_SIZE = 17
TIME_INTERVAL = 400
SPEED_SLIDER_MAX = 4


class CellButton(QtGui.QPushButton):

    def __init__(self, parent=None):

        super(CellButton, self).__init__(parent)
        self._alive = False
        self.next_state = None
        self.resize(CELL_SIZE, CELL_SIZE)

    def mousePressEvent(self, *args, **kwargs):
        world = self.parentWidget()
        if world.edit_mode:
            if self.is_alive():
                self.died()
            else:
                self.set_alive()

    def is_alive(self):
        return self._alive

    def set_alive(self):
        self._alive = True
        self.setStyleSheet("background-color: green;")

    def died(self):
        self._alive = False
        self.setStyleSheet(self.parentWidget().styleSheet())

    def compute_next_state(self):
        world = self.parentWidget()
        environment = world.environment(self.x, self.y)
        alive_neighbours = len([el for el in environment if el.is_alive()])
        if self.is_alive():
            if alive_neighbours < 2 or alive_neighbours > 3:
                self.next_state = False
            else:
                self.next_state = True
        else:
            if alive_neighbours == 3:
                self.next_state = True
            else:
                self.next_state = False

    def set_next_state(self):
        if self.next_state:
            self.set_alive()
        else:
            self.died()


class PlayButton(QtGui.QPushButton):

    def __init__(self, parent=None):

        super(PlayButton, self).__init__(parent)
        self.setText('Play')

    def mousePressEvent(self, *args, **kwargs):
        world = self.parentWidget()
        if world.is_playing():
            world.stop()
            self.setText('Play')
        else:
            world.play()
            self.setText('Stop')


class EditButton(QtGui.QPushButton):

    def __init__(self, parent=None):

        super(EditButton, self).__init__(parent)
        self.setText('Edit')

    def mousePressEvent(self, *args, **kwargs):
        world = self.parentWidget()
        if not world.editing():
            world.start_edit()
            self.setText('OK')
        else:
            world.finish_edit()
            self.setText('Edit')


class ClearButton(QtGui.QPushButton):

    def __init__(self, parent=None):

        super(ClearButton, self).__init__(parent)
        self.setText('Clear')

    def mousePressEvent(self, *args, **kwargs):
        world = self.parentWidget()
        for row in world.world_matrix:
            for cell in row:
                cell.died()


class LoadButton(QtGui.QPushButton):

    def __init__(self, parent=None):

        super(LoadButton, self).__init__(parent)
        self.setText('Load from file')

    def mousePressEvent(self, *args, **kwargs):
        world = self.parentWidget()
        filename = QtGui.QFileDialog.getOpenFileNameAndFilter(self,
                                                              'Open file',
                                                              '',
                                                              'Text files (*.txt)')[0]
        filename = str(filename)
        loaded = world.load_from_file(filename)
        if not loaded:
            msg = QtGui.QMessageBox(self)
            msg.setText("File loading error\nSee 'About' for correct file format")
            msg.setWindowTitle('Error')
            msg.setStandardButtons(QtGui.QMessageBox.Ok)
            msg.show()


class SaveButton(QtGui.QPushButton):

    def __init__(self, parent=None):

        super(SaveButton, self).__init__(parent)
        self.setText('Save to file')

    def mousePressEvent(self, *args, **kwargs):
        world = self.parentWidget()
        filename = QtGui.QFileDialog.getSaveFileNameAndFilter(self,
                                                              'Save file',
                                                              '',
                                                              'Text files (*.txt)')[0]
        filename = str(filename)
        saved = world.save_to_file(filename)
        if not saved:
            msg = QtGui.QMessageBox(self)
            msg.setText("File saving error")
            msg.setWindowTitle('Error')
            msg.setStandardButtons(QtGui.QMessageBox.Ok)
            msg.show()


class SpeedSlider(QtGui.QSlider):

    def __init__(self, parent=None):
        super(SpeedSlider, self).__init__(parent)
        self.setRange(1, SPEED_SLIDER_MAX)
        self.setTickInterval(1)
        self.setTickPosition(QtGui.QSlider.TicksBelow)
        self.setOrientation(Qt.Horizontal)
        self.setValue(1)

    def sliderChange(self, *args, **kwargs):
        world = self.parentWidget()
        if self.value() != 0:
            world.timer.setInterval(TIME_INTERVAL / self.value())


class InfoButton(QtGui.QPushButton):

    def __init__(self, parent=None):

        super(InfoButton, self).__init__(parent)
        self.setText('About')

    def mousePressEvent(self, *args, **kwargs):
        msg = QtGui.QMessageBox(self)
        msg.setText("Supported file can contain only zeros "
                    "(for empty cells) and ones (for alive cells) "
                    "without any spaces.\nIt may contain not more than 40 rows "
                    "with not more 60 symbols in each one.")
        msg.setWindowTitle('About')
        msg.setStandardButtons(QtGui.QMessageBox.Ok)
        msg.show()


class Main(QtGui.QMainWindow):

    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Background, Qt.white)
        self.setPalette(palette)
        left_margin = 10
        top_margin = 10
        bottom_margin = 10
        right_margin = 140
        self.resize(left_margin + NUM_COLS * CELL_SIZE + right_margin,
                    top_margin + NUM_ROWS * CELL_SIZE + bottom_margin)
        self.setWindowTitle("Conway's Game of Life")

        self.world_matrix = []
        self.edit_mode = False
        self.playing = False

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.timer_tick)
        self.timer.setInterval(TIME_INTERVAL)

        button_margin = left_margin + NUM_COLS * CELL_SIZE + 20
        self.play_button = PlayButton(self)
        self.play_button.move(button_margin, top_margin)

        self.label = QtGui.QLabel(self)
        self.label.setText('Speed')
        self.label.move(button_margin, top_margin + 25)
        self.slider = SpeedSlider(self)
        self.slider.move(button_margin, top_margin + 50)

        self.edit_button = EditButton(self)
        self.edit_button.move(button_margin, top_margin + 100)
        self.clear_button = ClearButton(self)
        self.clear_button.move(button_margin, top_margin + 130)
        self.load_button = LoadButton(self)
        self.load_button.move(button_margin, top_margin + 160)
        self.save_button = SaveButton(self)
        self.save_button.move(button_margin, top_margin + 200)
        self.info_button = InfoButton(self)
        self.info_button.move(button_margin, top_margin + 250)

        left = left_margin
        top = top_margin

        for x in range(NUM_ROWS):
            cell_line = []
            for y in range(NUM_COLS):
                cell = CellButton(self)
                cell.move(left, top)
                cell.x = x
                cell.y = y
                cell_line.append(cell)
                left += CELL_SIZE
            self.world_matrix.append(cell_line)
            top += CELL_SIZE
            left = left_margin

        self.load_from_file('Gosper.txt')

        self.show()

    def timer_tick(self):
        for row in self.world_matrix:
            for cell in row:
                cell.compute_next_state()
        for row in self.world_matrix:
            for cell in row:
                cell.set_next_state()

    def play(self):
        self.timer.start()
        self.playing = True
        self.edit_button.setDisabled(True)
        self.clear_button.setDisabled(True)
        self.load_button.setDisabled(True)
        self.save_button.setDisabled(True)

    def stop(self):
        self.timer.stop()
        self.playing = False
        self.edit_button.setEnabled(True)
        self.clear_button.setEnabled(True)
        self.load_button.setEnabled(True)
        self.save_button.setEnabled(True)

    def is_playing(self):
        return self.playing

    def editing(self):
        return self.edit_mode

    def start_edit(self):
        self.edit_mode = True
        self.play_button.setDisabled(True)
        self.save_button.setDisabled(True)

    def finish_edit(self):
        self.edit_mode = False
        self.play_button.setEnabled(True)
        self.save_button.setEnabled(True)

    def environment(self, x, y):
        environment = []
        for i in range(x - 1, x + 2):
            for j in range(y - 1, y + 2):
                if not (x == i and y == j):
                    environment.append(self.world_matrix[self.check_x(i)][self.check_y(j)])
        return environment

    def check_x(self, x):
        result = x % NUM_ROWS
        return result

    def check_y(self, y):
        result = y % NUM_COLS
        return result

    def load_from_file(self, filename):
        try:
            with open(filename, 'r') as f:
                for i, row in enumerate(f):
                    for j, cell in enumerate(row[:-1]):
                        if cell == '1':
                            self.world_matrix[i][j].set_alive()
                        elif cell == '0':
                            self.world_matrix[i][j].died()
                        else:
                            raise TypeError
            loaded = True
        except:
            loaded = False

        return loaded

    def save_to_file(self, filename):

        try:
            with open(filename, 'w') as f:
                for cell in self.world_matrix[0]:
                    if cell.is_alive():
                        f.write('1')
                    else:
                        f.write('0')
                for row in self.world_matrix[1:]:
                    f.write('\n')
                    for cell in row:
                        if cell.is_alive():
                            f.write('1')
                        else:
                            f.write('0')
            saved = True
        except:
            saved = False

        return saved


def main():
    app = QtGui.QApplication(sys.argv)
    main = Main()
    main.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
