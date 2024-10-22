from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QFileDialog
from PySide6.QtCore import Qt, QTimer, QTime, QRect
from PySide6.QtGui import QPixmap, QTransform, QMouseEvent, QImage, QPainter, QPen
from viewer_ui import Ui_MedAnalyzer  # Importamos la clase generada por pyside6-uic
import mysql.connector
import cv2
import numpy as np
import pydicom
from datetime import datetime

class ViewerWindow(QDialog):
    def __init__(self, user_id):
        super(ViewerWindow, self).__init__()

        self.user_id = user_id  # Guardar el ID del usuario autenticado
        self.ui = Ui_MedAnalyzer()  # Crea una instancia de la interfaz generada
        self.ui.setupUi(self)   # Configura el diseño en la ventana actual

        # Conectar botones a las funciones correspondientes
        self.ui.zoom_in.clicked.connect(self.zoom_in)
        self.ui.zoom_out.clicked.connect(self.zoom_out)
        self.ui.zoom_reset.clicked.connect(self.reset_zoom)
        self.ui.open_image.clicked.connect(self.load_image)
        self.ui.close_image.clicked.connect(self.close_image)
        self.ui.rotate_left.clicked.connect(self.rotate_left)
        self.ui.rotate_right.clicked.connect(self.rotate_right)
        self.ui.rotation_reset.clicked.connect(self.reset_rotation)

        self.scale_factor = 1.0
        self.max_scale = 3.0  # Límite superior para el zoom
        self.min_scale = 0.5  # Límite inferior para el zoom
        self.rotation_angle = 0  # Ángulo de rotación en grados

        self.ui.image_label.setMouseTracking(True)

        # Cargar la información del usuario desde la base de datos
        self.load_user_info()

        # Configurar el temporizador para actualizar la hora cada segundo
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)

        self.setMouseTracking(True)

        self.pixmap = None  # Mantiene la imagen cargada para aplicar el zoom

        self.selection_start = None  # Coordenada de inicio de la selección
        self.selection_end = None  # Coordenada final de la selección
        self.is_selecting = False  # Bandera para saber si está seleccionando

    def connect_to_db(self):
        """Establece la conexión con la base de datos MySQL"""
        try:
            self.db = mysql.connector.connect(
                host="localhost",
                user="root",
                password="Gabriel12.",
                database="med_analyzer_3"
            )
            self.cursor = self.db.cursor()
        except mysql.connector.Error as err:
            self.ui.user_info_label.setText(f"Error al conectar con la base de datos: {err}")

    def load_user_info(self):
        """Obtiene el nombre y apellido del usuario de la base de datos y los muestra"""
        self.connect_to_db()

        query = "SELECT name, last_name FROM users WHERE username = %s"
        self.cursor.execute(query, (self.user_id,))
        print(self.user_id)
        result = self.cursor.fetchone()

        if result:
            name, last_name = result
            self.ui.user_info_label.setText(f"Bienvenido: {name} {last_name}")
        else:
            self.ui.user_info_label.setText("Usuario no encontrado.")

        self.cursor.close()
        self.db.close()

    def update_time(self):
        """Actualiza la hora actual en la etiqueta"""
        current_time = QTime.currentTime().toString("hh:mm:ss")
        text = self.ui.user_info_label.text().split("\n")[0]  # Mantener el nombre actual
        self.ui.user_info_label.setText(f"{text}\nHora actual: {current_time}")

    # Funciones de zoom y rotación (sin cambios)
    # def load_image(self):
    #     image_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar imagen", "", "Images (*.png *.jpg *.bmp)")
    #     if image_path:
    #         self.pixmap = QPixmap(image_path)
    #         self.ui.image_label.setPixmap(self.pixmap.scaled(self.ui.image_label.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation))
    #         self.scale_factor = 1.0  # Reiniciar factor de escala al cargar una nueva imagen

    def load_image(self):
        # Abrir un diálogo para seleccionar una imagen o archivo DICOM
        image_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar imagen o archivo DICOM", "", "Images (*.png *.jpg *.bmp);;DICOM Files (*.dcm)")

        if image_path.endswith('.dcm'):
            # Si es un archivo DICOM, procesarlo y mostrarlo
            self.load_dicom_image(image_path)
        else:
            # Si es una imagen estándar (JPG, PNG, BMP), mostrarla normalmente
            self.load_standard_image(image_path)

    def load_standard_image(self, image_path):
        # Cargar y mostrar una imagen estándar
        self.pixmap = QPixmap(image_path)
        self.ui.image_label.setPixmap(self.pixmap.scaled(self.ui.image_label.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation))

    def load_dicom_image(self, dicom_path):
        # Leer el archivo DICOM
        dicom = pydicom.dcmread(dicom_path)

        # Extraer las fechas (manejar errores si algún campo no existe)
        dicom_image = dicom.pixel_array

        # Función auxiliar para formatear fechas
        def format_date(dicom_date):
            if dicom_date:
                try:
                    return datetime.strptime(dicom_date, "%Y%m%d").strftime("%d-%m-%Y")
                except ValueError:
                    return "N/A"
            return "N/A"

        # Extraer las fechas con manejo de errores
        study_date = format_date(getattr(dicom, 'StudyDate', None))
        series_date = format_date(getattr(dicom, 'SeriesDate', None))
        acquisition_date = format_date(getattr(dicom, 'AcquisitionDate', None))
        patient_birth_date = format_date(getattr(dicom, 'PatientBirthDate', None))

        # Crear un string con la información
        dicom_info = (f"Fecha de Estudio: {study_date}\n"
                        f"Fecha de Serie: {series_date}\n"
                        f"Fecha de Adquisición: {acquisition_date}\n"
                        f"Fecha de Nacimiento del Paciente: {patient_birth_date}")

        # Mostrar la información en el QLabel
        self.ui.dicom_info_label.setText(dicom_info)

        # Normalizar los valores de píxeles entre 0 y 255 para convertir a formato de imagen
        dicom_image_normalized = cv2.normalize(dicom_image, None, 0, 255, cv2.NORM_MINMAX)
        dicom_image_normalized = dicom_image_normalized.astype(np.uint8)

        # Convertir la imagen a formato RGB para ser compatible con QPixmap
        if len(dicom_image_normalized.shape) == 2:  # Imagen en escala de grises
            qimage = cv2.cvtColor(dicom_image_normalized, cv2.COLOR_GRAY2RGB)
        else:
            qimage = cv2.cvtColor(dicom_image_normalized, cv2.COLOR_BGR2RGB)

        # Convertir el array de OpenCV a formato QImage
        height, width, channel = qimage.shape
        bytes_per_line = 3 * width
        self.pixmap = QPixmap(QImage(qimage.data, width, height, bytes_per_line, QImage.Format_RGB888))

        # Mostrar la imagen en el QLabel
        self.ui.image_label.setPixmap(self.pixmap.scaled(self.ui.image_label.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation))
    
    def zoom_in(self):
        if self.scale_factor < self.max_scale:
            self.scale_factor += 0.1
            self.apply_zoom()

    def zoom_out(self):
        if self.scale_factor > self.min_scale:
            self.scale_factor -= 0.1
            self.apply_zoom()

    def apply_zoom(self):
        if self.pixmap is not None:
            label_width = self.ui.image_label.width()
            label_height = self.ui.image_label.height()
            pixmap_width = self.pixmap.width()
            pixmap_height = self.pixmap.height()
            scaled_pixmap = self.pixmap.scaled(pixmap_width * self.scale_factor, pixmap_height * self.scale_factor, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
            self.ui.image_label.setPixmap(scaled_pixmap)
            self.ui.image_label.setAlignment(Qt.AlignCenter)
    
    def reset_zoom(self):
        if self.pixmap is not None:
            self.scale_factor = 1.0
            self.ui.image_label.setPixmap(self.pixmap.scaled(self.ui.image_label.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation))

    def rotate_left(self):
        self.rotation_angle -= 90
        if self.rotation_angle <= -360:
            self.rotation_angle = 0
        self.apply_transformations()

    def rotate_right(self):
        self.rotation_angle += 90
        if self.rotation_angle >= 360:
            self.rotation_angle = 0
        self.apply_transformations()

    def apply_transformations(self):
        if self.pixmap is not None:
            scaled_pixmap = self.pixmap.scaled(self.ui.image_label.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
            transform = QTransform()
            transform.rotate(self.rotation_angle)
            rotated_pixmap = scaled_pixmap.transformed(transform, Qt.SmoothTransformation)
            self.ui.image_label.setPixmap(rotated_pixmap)
            self.ui.image_label.setAlignment(Qt.AlignCenter)

    def reset_rotation(self):
        self.rotation_angle = 0
        self.apply_transformations()

    def mouseMoveEvent(self, event: QMouseEvent):
        # Obtener las coordenadas del cursor en la ventana principal
        pos = event.pos()

        if self.is_selecting:
            self.selection_end = pos
            self.update()  # Redibujar la interfaz

        # Verificar si el cursor está dentro del área de image_label
        if self.ui.image_label.geometry().contains(pos):
            # Convertir las coordenadas a locales dentro del QLabel
            local_pos = self.ui.image_label.mapFromParent(pos)
            self.ui.mouse_position_label.setText(f"X: {local_pos.x()} Y: {local_pos.y()}")
        else:
            self.ui.mouse_position_label.setText("X: 0 Y: 0")

    def mousePressEvent(self, event):
        """Captura la posición inicial cuando el mouse es presionado."""
        pos = event.pos()
        if self.ui.image_label.geometry().contains(pos):
            if event.button() == Qt.LeftButton:
                self.selection_start = event.pos()
                self.is_selecting = True

    def mouseReleaseEvent(self, event):
        """Aplica el zoom cuando el mouse es soltado."""
        pos = event.pos()
        if self.ui.image_label.geometry().contains(pos):
            if event.button() == Qt.LeftButton:
                self.selection_end = event.pos()
                self.is_selecting = False
                self.zoom_to_selected_region()

    def paintEvent(self, event):
        """Dibuja el rectángulo de selección en la imagen."""
        super(ViewerWindow, self).paintEvent(event)
        if self.is_selecting and self.selection_start and self.selection_end:
            painter = QPainter(self)
            pen = QPen(Qt.red, 2, Qt.DashLine)
            painter.setPen(pen)

            # Dibujar el rectángulo de selección
            rect = QRect(self.selection_start, self.selection_end)
            painter.drawRect(rect)

    def zoom_to_selected_region(self):
        """Realiza un zoom en la región seleccionada."""
        if self.pixmap and self.selection_start and self.selection_end:
            # Coordenadas del área seleccionada
            rect = QRect(self.selection_start, self.selection_end).normalized()

            # Escalar las coordenadas de la selección para que correspondan al tamaño real de la imagen
            scaled_rect = QRect(
                rect.x() * self.pixmap.width() / self.ui.image_label.width(),
                rect.y() * self.pixmap.height() / self.ui.image_label.height(),
                rect.width() * self.pixmap.width() / self.ui.image_label.width(),
                rect.height() * self.pixmap.height() / self.ui.image_label.height()
            )

            # Recortar la imagen en la región seleccionada
            cropped_pixmap = self.pixmap.copy(scaled_rect)

            # Establecer la imagen recortada en el QLabel
            self.ui.image_label.setPixmap(cropped_pixmap.scaled(
                self.ui.image_label.size(),
                Qt.IgnoreAspectRatio,
                Qt.SmoothTransformation
            ))

            # Resetear la selección
            self.selection_start = None
            self.selection_end = None

    def close_image(self):
        # Limpiar el contenido del QLabel (cerrar la imagen)
        self.ui.image_label.clear()
        self.ui.image_label.setText("Imagen cerrada. Cargue otra imagen para visualizar.")
        self.pixmap = None