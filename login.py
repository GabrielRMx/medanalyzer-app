import sys
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from register import RegisterWindow  # Importa la ventana de registro
import mysql.connector
import hashlib

class LoginWindow(QDialog):
    def __init__(self):
        super(LoginWindow, self).__init__()
        self.setWindowTitle("MedAnalyzer - Iniciar Sesión")

        self.layout = QVBoxLayout()
        self.resize(400, 350)

        # Añadir QLabel para mostrar la imagen
        self.image_label = QLabel(self)
        self.image_path = "./assets/background.png"  # Ruta de la imagen cargada
        self.pixmap = QPixmap(self.image_path)
        self.image_label.setPixmap(self.pixmap.scaled(150, 150))  # Ajustar tamaño de la imagen si es necesario
        self.image_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.image_label)

        self.text_title = QLabel(self)
        self.text_title.setText("MedAnalyzer")
        self.text_title.setStyleSheet("font-size: 28px; font-weight: bold;")
        self.text_title.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.text_title)

        self.text_title_2 = QLabel(self)
        self.text_title_2.setText("Ingreso Usuarios")
        self.text_title_2.setStyleSheet("font-size: 12px; font-weight: bold;")
        self.text_title_2.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.text_title_2)

        self.username_input = QLineEdit(self)
        self.username_input.setPlaceholderText("Cédula")
        self.layout.addWidget(self.username_input)

        self.password_input = QLineEdit(self)
        self.password_input.setPlaceholderText("Contraseña")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.layout.addWidget(self.password_input)

        self.login_button = QPushButton("Iniciar sesión")
        self.login_button.clicked.connect(self.check_credentials)
        self.layout.addWidget(self.login_button)

        self.error_label = QLabel("", self)
        self.error_label.setStyleSheet("color: red;")
        self.layout.addWidget(self.error_label)

        # Botón para abrir el diálogo de registro
        self.register_button = QPushButton("Registrar nuevo usuario")
        self.register_button.clicked.connect(self.open_register_window)  # Conecta al diálogo de registro
        self.layout.addWidget(self.register_button)

        self.footer = QLabel(self)
        self.footer.setText("Versión Preliminar")
        self.footer.setStyleSheet("font-size: 10px;")
        self.footer.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.footer)

        self.setLayout(self.layout)

    def connect_to_db(self):
        """Establece la conexión con la base de datos MySQL"""
        try:
            self.db = mysql.connector.connect(
                host="localhost",   # Cambiar por tu host de MySQL
                user="root",  # Cambiar por tu usuario de MySQL
                password="Gabriel12.",  # Cambiar por tu contraseña
                database="med_analyzer_3"  # Base de datos que creaste
            )
            self.cursor = self.db.cursor()
        except mysql.connector.Error as err:
            self.error_label.setText(f"Error al conectar con la base de datos: {err}")

    def check_credentials(self):
        """Validar las credenciales ingresadas con la base de datos"""
        username = self.username_input.text()
        password = self.password_input.text()

        hash_object = hashlib.sha256(password.encode('utf-8'))  
        password = hash_object.hexdigest()

        self.connect_to_db()  # Conectar a la base de datos

        query = "SELECT password FROM users WHERE username = %s"
        self.cursor.execute(query, (username,))
        result = self.cursor.fetchone()

        if result and result[0] == password:
            self.accept()  # Cierra el diálogo si las credenciales son correctas
        else:
            self.error_label.setText("Credenciales Incorrectas")

        self.cursor.close()
        self.db.close()

    def open_register_window(self):
        """Abrir el diálogo de registro"""
        register_window = RegisterWindow()
        register_window.exec()
