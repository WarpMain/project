import os
import sys

import requests
from PyQt5 import uic
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel

SCREEN_SIZE = [920, 520]
START_COORDS = [37.530887, 55.703118]
START_SPN = [0.015, 0.015]
API_SERVER = "http://static-maps.yandex.ru/1.x/"


class Example(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('main_menu.ui', self)
        self.getImage(START_COORDS, START_SPN)
        self.update_map()
        self.coords = START_COORDS

    def move_Image(self, changing_coords):
        self.coords[0] += changing_coords[0]
        self.coords[1] += changing_coords[1]
        self.getImage(self.coords, START_SPN)
        self.image.close()
        self.update_map()
        self.image.show()

    def getImage(self, coords, spn, style="map"):
        params = {"ll": ",".join(map(str, coords)),
                  "l": style,
                  "spn": ",".join(map(str, spn))}
        response = requests.get(API_SERVER, params=params)

        if not response:
            print("Ошибка выполнения запроса:")
            print("Http статус:", response.status_code, "(", response.reason, ")")
            sys.exit(1)

        self.map_file = "map.png"
        with open(self.map_file, "wb") as file:
            file.write(response.content)

    def update_map(self):
        self.pixmap = QPixmap(self.map_file)
        self.image = QLabel(self)
        self.image.move(280, 20)
        self.image.resize(630, 470)
        self.image.setPixmap(self.pixmap)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Right:
            self.move_Image([START_SPN[0] * 2, 0])
        if e.key() == Qt.Key_Left:
            self.move_Image([START_SPN[0] * -2, 0])
        if e.key() == Qt.Key_Up:
            self.move_Image([0, START_SPN[1] * 2])
        if e.key() == Qt.Key_Down:
            self.move_Image([0, START_SPN[1] * -2])

    def closeEvent(self, event):
        """При закрытии формы подчищаем за собой"""
        os.remove(self.map_file)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Example()
    ex.show()
    sys.exit(app.exec())
