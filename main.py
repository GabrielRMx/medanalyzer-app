import sys
from PySide6.QtWidgets import QApplication
from login import LoginWindow
from viewer import ViewerWindow

def main():
    app = QApplication(sys.argv)

    # Mostrar la ventana de login
    login_window = LoginWindow()
    if login_window.exec():
        user_id = login_window.username_input.text()
        # Si el login es exitoso, mostrar la ventana del visor
        viewer_window = ViewerWindow(user_id)
        viewer_window.show()
        sys.exit(app.exec())

if __name__ == "__main__":
    main()