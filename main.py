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
        self.coords = START_COORDS
        self.spn = START_SPN
        self.map_type = 'map'
        self.full_address = ''
        self.org_point = ''
        self.getImage(START_COORDS, START_SPN)
        self.update_map()

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
        if self.org_point != '':
            params = {"ll": ",".join(map(str, coords)),
                      "l": style,
                      "spn": ",".join(map(str, spn)),
                      "pt": "{0},pm2dgl".format(self.org_point)}
        else:
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

    def change_full_address(self, text):
        text = text.split(', ')
        end_text = ['']
        for t in text:
            if len(end_text[-1]) + len(t) + 2 <= 33:
                if text.index(t) != 0:
                    end_text[-1] += ', ' + t
                else:
                    end_text[-1] = t
            else:
                end_text[-1] += ','
                end_text.append(t)
        text = '\n'.join(end_text)

        self.text_address.setText(text)
        self.full_address = text

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
            self.org_point = "{0},{1}".format(point[0], point[1])
            self.spn = [0.005, 0.005]
            self.coords = list(map(float, self.org_point.split(',')))
            self.update_image()

            search_api_server = "https://geocode-maps.yandex.ru/1.x/"
            api_key = "40d1649f-0493-4b70-98ba-98533de7710b"

            search_params = {
                "apikey": api_key,
                "geocode": self.org_point,
                "format": 'json'}

            response = requests.get(search_api_server, params=search_params)
            json_response = response.json()
            postal_code = json_response['response']['GeoObjectCollection'][
                'featureMember'][0]['GeoObject']['metaDataProperty'][
                'GeocoderMetaData']['Address']['postal_code']

            if self.checkBoxIndex.isChecked():
                text = org_address + '\n' + f'почтовый индекс: {postal_code}'
            else:
                text = org_address
            self.change_full_address(text)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Example()
    ex.show()
    sys.exit(app.exec())
