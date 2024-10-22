from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PySide6.QtCore import Qt
import mysql.connector
import hashlib
import re

class RegisterWindow(QDialog):
    def __init__(self):
        super(RegisterWindow, self).__init__()
        self.setWindowTitle("MedAnalyzer - Registro de Usuario")

        self.layout = QVBoxLayout()
        self.resize(400, 300)

        self.text_title = QLabel(self)
        self.text_title.setText("Registrar Nuevo Usuario")
        self.text_title.setStyleSheet("font-size: 20px; font-weight: bold;")
        self.text_title.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.text_title)

        self.name_input = QLineEdit(self)
        self.name_input.setPlaceholderText("Nombre")
        self.layout.addWidget(self.name_input)

        self.last_name_input = QLineEdit(self)
        self.last_name_input.setPlaceholderText("Apellido")
        self.layout.addWidget(self.last_name_input)

        self.email_input = QLineEdit(self)
        self.email_input.setPlaceholderText("Correo Electrónico")
        self.layout.addWidget(self.email_input)

        self.username_input = QLineEdit(self)
        self.username_input.setPlaceholderText("Cédula")
        self.layout.addWidget(self.username_input)

        self.password_input = QLineEdit(self)
        self.password_input.setPlaceholderText("Contraseña")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.layout.addWidget(self.password_input)

        self.confirm_password_input = QLineEdit(self)
        self.confirm_password_input.setPlaceholderText("Confirmar Contraseña")
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        self.layout.addWidget(self.confirm_password_input)

        self.register_button = QPushButton("Registrar")
        self.register_button.clicked.connect(self.register_user)
        self.layout.addWidget(self.register_button)

        self.error_label = QLabel("", self)
        self.error_label.setStyleSheet("color: red;")
        self.layout.addWidget(self.error_label)

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

    def register_user(self):
        """Registrar al usuario en la base de datos"""
        email = self.email_input.text()
        nombre = self.name_input.text()
        apellido = self.last_name_input.text()
        username = self.username_input.text()
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()

        if not username or not password:
            self.error_label.setText("Por favor, ingrese todos los campos.")
            return

        if confirm_password != password:
            self.error_label.setText("Las contraseñas no coinciden.")
            return
        
        # Validar email
        if not self.validate_email(email):
            self.error_label.setText("Correo electrónico inválido.")
            return

        # Validar contraseña
        valid_password, message = self.validate_password(password)
        if not valid_password:
            self.error_label.setText(message)
            return

        self.connect_to_db()

        # Verificar si el usuario ya existe
        query_check = "SELECT username FROM users WHERE username = %s"
        self.cursor.execute(query_check, (username,))
        result = self.cursor.fetchone()

        if result:
            self.error_label.setText("El usuario ya existe.")
        else:

            hash_object = hashlib.sha256(password.encode('utf-8'))  
            password_hash = hash_object.hexdigest()
            # Insertar nuevo usuario
            query_insert = "INSERT INTO users (name, last_name, username, password, email) VALUES (%s, %s, %s, %s, %s)"
            self.cursor.execute(query_insert, (nombre, apellido, username, password_hash, email))
            self.db.commit()

            self.cursor.close()
            self.db.close()

            # Mostrar mensaje de éxito
            QMessageBox.information(self, "Registro Exitoso", "Usuario registrado exitosamente.")
            self.accept()  # Cierra el diálogo después de registrar

        self.cursor.close()
        self.db.close()

    def validate_email(self, email):
        """Verifica si el email tiene un formato válido"""
        regex = r"^\S+@\S+\.\S+$"
        if re.match(regex, email):
            return True
        else:
            return False

    def validate_password(self, password):
        """Verifica si la contraseña cumple con los requisitos de seguridad"""
        if len(password) < 8:
            return False, "La contraseña debe tener al menos 8 caracteres."
        if not re.search(r'[A-Z]', password):
            return False, "La contraseña debe contener al menos una letra mayúscula."
        if not re.search(r'[a-z]', password):
            return False, "La contraseña debe contener al menos una letra minúscula."
        if not re.search(r'[0-9]', password):
            return False, "La contraseña debe contener al menos un número."
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "La contraseña debe contener al menos un carácter especial."
        return True, ""