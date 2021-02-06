import sys
import logging
import colorsys

from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import Qt, pyqtSignal, QPoint
from PyQt5.QtGui import QColor, QPixmap, QPainter

from ui.main_window import Ui_MainWindow

logging.basicConfig(filemode='application.log', level=logging.ERROR)
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)


class MyWindow(QtWidgets.QMainWindow):
    # Сигнал выбора цвета
    select_color = pyqtSignal(tuple)
    # Сигнал выбора насышенности цвета
    select_hue = pyqtSignal(tuple)
    # Сигнал обновления цвета (отдает кортеж rgb)
    color_changed = pyqtSignal(tuple)

    def __init__(self, *args, **kwargs):
        super(MyWindow, self).__init__(*args, **kwargs)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowTitle("ColorPicker")
        self.color_dict = {}
        self.start_hsv = None
        self.start_rgb = None
        # Названия виджетов для заданных цветов
        self.fixed_colors = {"lbl_c1": (255, 0, 0), "lbl_c2": (255, 255, 0), "lbl_c3": (255, 255, 255),
                             "lbl_c4": (0, 0, 0), "lbl_c5": (255, 0, 255), "lbl_c6": (0, 255, 0),
                             "lbl_c7": (0, 255, 255), "lbl_c8": (0, 0, 255), "lbl_c9": (255, 100, 0)}
        # Названия виджетов для сохраненных цветов
        self.saved_colors = {"lbl_s_c1": None, "lbl_s_c2": None, "lbl_s_c3": None, "lbl_s_c4": None, "lbl_s_c5": None,
                             "lbl_s_c6": None, "lbl_s_c7": None, "lbl_s_c8": None, "lbl_s_c9": None, "lbl_s_c10": None,
                             "lbl_s_c11": None, "lbl_s_c12": None}

        self.fill_color_scale()
        self.fill_discrete_colors()

        self.select_color[tuple].connect(self.fill_color_view)
        self.select_color[tuple].emit((255, 0, 0))

        self.ui.pb_save_color.clicked.connect(self.save_color)
        self.color_changed[tuple].connect(self.change_color_handler)
        self.color_changed[tuple].emit((255, 0, 0))

        self.ui.sb_r.valueChanged.connect(self.rgb_value_changed)
        self.ui.sb_g.valueChanged.connect(self.rgb_value_changed)
        self.ui.sb_b.valueChanged.connect(self.rgb_value_changed)
        self.ui.sb_h.valueChanged.connect(self.hsv_value_changed)
        self.ui.sb_s.valueChanged.connect(self.hsv_value_changed)
        self.ui.sb_v.valueChanged.connect(self.hsv_value_changed)

        self.ui.le_hex.textChanged.connect(self.hex_value_changed)

    def rgb_value_changed(self):
        logger.info(f"rgb_value_changed")
        r = self.ui.sb_r.value()
        g = self.ui.sb_g.value()
        b = self.ui.sb_b.value()
        self.color_changed[tuple].emit((r, g, b))

    def hsv_value_changed(self):
        logger.info(f"hsv_value_changed")
        h = self.ui.sb_h.value() / 360
        s = self.ui.sb_s.value() / 100
        v = self.ui.sb_v.value() / 100
        r, g, b = self.ordinary_rgb(colorsys.hsv_to_rgb(h, s, v))
        self.color_changed[tuple].emit((r, g, b))

    def hex_value_changed(self):
        logger.info(f"hex_value_changed")
        hex_str = self.ui.le_hex.text()
        if len(hex_str) != 1 + 2 * 3:
            return
        r, g, b = self.hex_to_rgb(hex_str)
        self.color_changed[tuple].emit((r, g, b))

    def change_color_handler(self, color):
        """Обработчик изменения цвета"""
        logger.info(f"change_color_handler {color}")
        self.change_color_scale(color)
        self.fill_show_color(color)

    def change_color_scale(self, color):
        """Обновить значения цвета в спин-бокс-ах"""
        logger.info(f"change_color_scale {color}")
        hsv = colorsys.rgb_to_hsv(*self.normalize_rgb(color))
        hex_ = self.rgb_to_hex(color)
        self.set_rgb_value(color)
        self.set_hsv_value(hsv)
        self.set_hex_value(hex_)

    def fill_discrete_colors(self):
        """Заполнить цветовую палитру"""
        for lbl, c in dict(**self.fixed_colors, **self.saved_colors).items():
            if c is None:
                c = (255, 255, 255)
            widget = getattr(self.ui, lbl)
            pixmap = QPixmap(widget.width(), widget.height())
            pixmap.fill(QColor(*c))
            widget.setPixmap(pixmap)

    def fill_preview(self, color):
        logger.info(f"fill_preview {color}")
        pixmap = QPixmap(self.ui.lbl_cur_color.width(), self.ui.lbl_cur_color.height())
        pixmap.fill(QColor(*color))
        self.ui.lbl_cur_color.setPixmap(pixmap)

    def save_color(self):
        """Сохранить цвет в палитру"""
        r = self.ui.sb_r.value()
        g = self.ui.sb_g.value()
        b = self.ui.sb_b.value()
        for w in self.saved_colors:
            if self.saved_colors[w] is None:
                self.saved_colors[w] = (r, g, b)
                break
        self.fill_discrete_colors()

    def mousePressEvent(self, e: QtGui.QMouseEvent) -> None:
        logger.info(f"Click on {e.pos()}")
        if e.button() != Qt.LeftButton:
            for w in self.saved_colors:
                if self.on_widget(getattr(self.ui, w), e.pos()):
                    self.saved_colors[w] = None
                    self.fill_discrete_colors()
                    break
            return

        for w, val in dict(**self.fixed_colors, **self.saved_colors).items():
            if val and self.on_widget(getattr(self.ui, w), e.pos()):
                self.color_changed[tuple].emit(val)
                break
        if self.on_widget(self.ui.lbl_color, e.pos()):
            # Выбор насышенности
            pos = self.coord_in_widget(self.ui.lbl_color, e.pos())
            w, h = self.ui.lbl_color.width(), self.ui.lbl_color.height()
            s, v = pos.x() / w, 1 - pos.y() / h
            rgb = self.ordinary_rgb(colorsys.hsv_to_rgb(self.start_hsv[0], s, v))
            self.color_changed[tuple].emit(rgb)
        elif self.on_widget(self.ui.lbl_colors, e.pos()):
            # Выбор цвета
            pos = self.coord_in_widget(self.ui.lbl_colors, e.pos())
            rgb = self.color_dict[pos.y()]
            self.start_rgb = rgb
            self.select_color[tuple].emit(rgb)
            self.color_changed[tuple].emit(rgb)

    def generate_color_dict(self):
        """Заполнить словарь с цветами. Oy -> (r, g, b)"""
        hue = [(255, 0, 0), (255, 0, 255), (0, 0, 255), (0, 255, 255), (0, 255, 0), (255, 255, 0), (255, 0, 0)]
        s = 255 * 6 / self.ui.lbl_colors.height()
        p = 0
        for f, t in zip(hue[:-1], hue[1:]):
            for c in self.gen_color(f, t, s):
                self.color_dict[p] = c
                p += 1

    def fill_color_scale(self):
        """Заполнить цветовую шкалу"""
        if not self.color_dict:
            self.generate_color_dict()
        pixmap = QPixmap(self.ui.lbl_colors.width(), self.ui.lbl_colors.height())
        qp = QPainter()
        qp.begin(pixmap)
        for p, c in self.color_dict.items():
            qp.setPen(QColor(*c))
            qp.drawLine(0, p, self.ui.lbl_colors.width(), p)
        qp.end()

        self.ui.lbl_colors.setPixmap(pixmap)

    def fill_color_view(self, color):
        """Заполнить цветовое поле"""
        logger.debug(f"Call of select color callback. Color {color}")
        w, h = self.ui.lbl_color.width(), self.ui.lbl_color.height()
        pixmap = QPixmap(w, h)
        qp = QPainter()
        qp.begin(pixmap)
        self.start_hsv = colorsys.rgb_to_hsv(*self.normalize_rgb(color))
        sh = self.start_hsv[0]
        for x in range(self.ui.lbl_color.width() + 1):
            for y in range(self.ui.lbl_color.height() + 1):
                s, v = x / w, 1 - y / h
                c = self.ordinary_rgb(colorsys.hsv_to_rgb(sh, s, v))
                qp.setPen(QColor(*c))
                qp.drawPoint(x, y)
        qp.end()

        self.ui.lbl_color.setPixmap(pixmap)

    def fill_show_color(self, color):
        """Установить цвет в области просмотра"""
        logger.debug(f"fill_show_color {color}")
        pixmap = QPixmap(self.ui.lbl_cur_color.width(), self.ui.lbl_cur_color.height())
        pixmap.fill(QColor(*color))
        self.ui.lbl_cur_color.setPixmap(pixmap)

    def set_rgb_value(self, rgb):
        logger.debug(f"set_rgb_value {rgb}")
        self.ui.sb_r.blockSignals(True)
        self.ui.sb_g.blockSignals(True)
        self.ui.sb_b.blockSignals(True)
        self.ui.sb_r.setValue(rgb[0])
        self.ui.sb_g.setValue(rgb[1])
        self.ui.sb_b.setValue(rgb[2])
        self.ui.sb_r.blockSignals(False)
        self.ui.sb_g.blockSignals(False)
        self.ui.sb_b.blockSignals(False)

    def set_hsv_value(self, hsv):
        logger.debug(f"set_hsv_value {hsv}")
        self.ui.sb_h.blockSignals(True)
        self.ui.sb_s.blockSignals(True)
        self.ui.sb_v.blockSignals(True)
        self.ui.sb_h.setValue(int(hsv[0] * 360 + 0.5))
        self.ui.sb_s.setValue(int(hsv[1] * 100 + 0.5))
        self.ui.sb_v.setValue(int(hsv[2] * 100 + 0.5))
        self.ui.sb_h.blockSignals(False)
        self.ui.sb_s.blockSignals(False)
        self.ui.sb_v.blockSignals(False)

    def set_hex_value(self, hex_):
        logger.debug(f"set_hex_value {hex_}")
        self.ui.le_hex.blockSignals(True)
        self.ui.le_hex.setText(hex_)
        self.ui.le_hex.blockSignals(False)

    @staticmethod
    def gen_color(f, t, s):
        r = -(f[0] - t[0]) // 255
        g = -(f[1] - t[1]) // 255
        b = -(f[2] - t[2]) // 255
        c = int(255 / s + 0.5)
        while c:
            yield f
            c -= 1
            f = (f[0] + r * s, f[1] + g * s, f[2] + b * s)

    @staticmethod
    def on_widget(widget, point):
        """Проверит что точка ледит внутри виджета"""
        g = widget.geometry()
        return g.x() <= point.x() <= g.x() + g.width() and \
               g.y() <= point.y() <= g.y() + g.height()

    @staticmethod
    def coord_in_widget(widget, point):
        """Вернет положение точки относительно виджета"""
        g = widget.geometry()
        return QPoint(point.x() - g.x(), point.y() - g.y())

    @staticmethod
    def ordinary_rgb(norm_rgb):
        """Перевести значения нормализованног цвета в значения 0-255"""
        return tuple(map(lambda c: 255 * c, norm_rgb))

    @staticmethod
    def normalize_rgb(rgb):
        """Перевести значения нормализованног цвета в значения 0-255"""
        return tuple(map(lambda c: c / 255, rgb))

    @staticmethod
    def rgb_to_hex(rgb):
        return "#{:02x}{:02x}{:02x}".format(*map(int, rgb))

    @staticmethod
    def hex_to_rgb(hex_):
        hex_ = hex_.lstrip("#")
        return tuple(int(hex_[i:i + 2], 16) for i in range(0, 6, 2))


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    application = MyWindow()
    application.show()

    sys.exit(app.exec())
