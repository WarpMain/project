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
        self.spn = START_SPN
        self.map_type = 'map'

        self.map_type_map.toggled.connect(self.change_type_map_on_map)
        self.map_type_sat.toggled.connect(self.change_type_map_on_sat)
        self.map_type_hybrid.toggled.connect(self.change_type_map_on_hybrid)

        self.map_type_map.setFocusPolicy(Qt.NoFocus)
        self.map_type_sat.setFocusPolicy(Qt.NoFocus)
        self.map_type_hybrid.setFocusPolicy(Qt.NoFocus)

        self.SearchButton.clicked.connect(self.search)
        self.SearchButton.setFocusPolicy(Qt.NoFocus)
        self.address.setFocusPolicy(Qt.ClickFocus)

    def change_type_map_on_map(self):
        self.map_type = 'map'
        self.update_image()

    def change_type_map_on_sat(self):
        self.map_type = 'sat'
        self.update_image()

    def change_type_map_on_hybrid(self):
        self.map_type = 'sat,skl'
        self.update_image()

    def move_Image(self, changing_coords):
        self.coords[0] += changing_coords[0]
        self.coords[1] += changing_coords[1]
        self.update_image()

    def update_image(self):   # обновляет отображаемую карту
        self.getImage(self.coords, self.spn, self.map_type)
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

        if style == 'map':
            self.map_file = "map.png"
        else:
            self.map_file = "map.jpg"

        with open(self.map_file, "wb") as file:
            file.write(response.content)

    def update_map(self):
        self.pixmap = QPixmap(self.map_file)
        self.image = QLabel(self)
        self.image.move(280, 20)
        self.image.resize(630, 470)
        self.image.setPixmap(self.pixmap)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Right:
            self.move_Image([self.spn[0] * 2, 0])
        if event.key() == Qt.Key_Left:
            self.move_Image([self.spn[0] * -2, 0])
        if event.key() == Qt.Key_Up:
            self.move_Image([0, self.spn[1] * 2])
        if event.key() == Qt.Key_Down:
            self.move_Image([0, self.spn[1] * -2])

        if event.key() == Qt.Key_PageUp:
            self.zoom(True)
        elif event.key() == Qt.Key_PageDown:
            self.zoom(False)

    def mousePressEvent(self, event):   # для сбраса фокуса
        self.setFocus()

    def zoom(self, up):
        if up:
            self.spn[0] /= 2
            self.spn[1] /= 2
            if self.spn[0] < 0.00046875 and self.spn[1] < 0.00046875:
                self.spn[0], self.spn[1] = 0.00046875, 0.00046875
        else:
            self.spn[0] *= 2
            self.spn[1] *= 2
            if self.spn[0] > 30.72 and self.spn[1] > 30.72:
                self.spn[0], self.spn[1] = 30.72, 30.72
        self.getImage(self.coords, self.spn, self.map_type)
        self.image.close()
        self.update_map()
        self.image.show()

    def closeEvent(self, event):
        """При закрытии формы подчищаем за собой"""
        os.remove(self.map_file)

    def search(self):
        if self.address.text() != '':
            search_api_server = "https://search-maps.yandex.ru/v1/"
            api_key = "dda3ddba-c9ea-4ead-9010-f43fbc15c6e3"

            address_ll = "37.588392,55.734036"

            search_params = {
                "apikey": api_key,
                "text": self.address.text(),
                "lang": "ru_RU",
                "ll": address_ll,
                "type": "biz"
            }

            response = requests.get(search_api_server, params=search_params)
            if not response:
                print("Ошибка выполнения запроса:")
                print("Http статус:", response.status_code, "(", response.reason, ")")
                sys.exit(1)

            # Преобразуем ответ в json-объект
            json_response = response.json()

            # Получаем первую найденную организацию.
            organization = json_response["features"][0]
            # Название организации.
            org_name = organization["properties"]["CompanyMetaData"]["name"]
            # Адрес организации.
            org_address = organization["properties"]["CompanyMetaData"]["address"]

            # Получаем координаты ответа.
            point = organization["geometry"]["coordinates"]
            org_point = "{0},{1}".format(point[0], point[1])
            delta = "0.005"

            # Собираем параметры для запроса к StaticMapsAPI:
            map_params = {
                # позиционируем карту центром на наш исходный адрес
                "ll": org_point,
                "spn": ",".join([delta, delta]),
                "l": self.map_type,
                "pt": "{0},pm2dgl".format(org_point)
            }

            map_api_server = "http://static-maps.yandex.ru/1.x/"
            response = requests.get(map_api_server, params=map_params)

            self.coords = list(map(float, org_point.split(',')))
            self.spn = list(map(float, (delta, delta)))

            if self.map_type == 'map':
                self.map_file = "map.png"
            else:
                self.map_file = "map.jpg"

            with open(self.map_file, "wb") as file:
                file.write(response.content)
            self.image.close()
            self.update_map()
            self.image.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Example()
    ex.show()
    sys.exit(app.exec())
