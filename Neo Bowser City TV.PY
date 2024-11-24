from PySide6.QtWidgets import (QApplication, QMainWindow, QScrollArea, 
                             QWidget, QVBoxLayout, QHBoxLayout, QFileDialog, 
                             QMessageBox, QTextEdit, QPushButton, QLabel,QSpinBox,QCheckBox)
from PySide6.QtGui import QPainter, QColor, QPixmap
from PySide6.QtCore import Qt, QRect
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
from PySide6.QtCore import QTimer
import sys
import yaml
import os

class TextureButtonWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(5)
        self.layout.setAlignment(Qt.AlignTop)
        self.buttons = []
        self.parent = parent

    def clear_buttons(self):
        for button in self.buttons:
            self.layout.removeWidget(button)
            button.deleteLater()
        self.buttons.clear()

    def add_texture_button(self, texture_path):
        button = QPushButton(os.path.basename(texture_path))
        button.setToolTip(texture_path)
        button.setStyleSheet("""
            QPushButton {
                padding: 5px;
                text-align: left;
                background-color: #000000;
                color: #ffffff;
                border: 1px solid #cccccc;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #303030;
            }
        """)
        # Verbinde den Button mit der Anzeigefunktion
        button.clicked.connect(lambda: self.parent.display_texture(texture_path))
        self.layout.addWidget(button)
        self.buttons.append(button)

class CheckeredWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(self.backgroundRole(), Qt.white)
        self.setPalette(palette)
        self.current_texture = None
        self.zoom_level = 1.0
        
    def set_texture(self, texture_path):
        if os.path.exists(texture_path):
            self.current_texture = QPixmap(texture_path)
            self.update()
        else:
            print(f"Texture not found: {texture_path}")
        
    def paintEvent(self, event):
        painter = QPainter(self)
        square_size = 16
        
        # Zeichne den karierten Hintergrund
        for i in range(0, self.width(), square_size):
            for j in range(0, self.height(), square_size):
                if (i // square_size + j // square_size) % 2 == 0:
                    painter.fillRect(i, j, square_size, square_size, QColor("#CCCCCC"))
        
        # Zeichne die Textur, wenn eine geladen ist
        if self.current_texture and not self.current_texture.isNull():
            # Berechne die Position zum Zentrieren der Textur
            scaled_width = self.current_texture.width() * self.zoom_level
            scaled_height = self.current_texture.height() * self.zoom_level
            x = (self.width() - scaled_width) / 2
            y = (self.height() - scaled_height) / 2
            
            # Zeichne die Textur
            target_rect = QRect(int(x), int(y), int(scaled_width), int(scaled_height))
            painter.drawPixmap(target_rect, self.current_texture)



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Neo Bowser City TV")
        self.resize(1200, 800)
        
        self.current_file = None
        self.yaml_content = None
        self.texture_paths = []
        self.yaml_directory = ""  # Neues Attribut für das YAML-Verzeichnis
        self.setup_ui()
        self.create_menu_bar()

    def setup_ui(self):
        self.main_widget = QWidget()
        main_layout = QHBoxLayout()
        
        # Linke Scroll Area mit Buttons
        left_scroll = QScrollArea()
        self.button_widget = TextureButtonWidget(self)
        left_scroll.setWidget(self.button_widget)
        left_scroll.setWidgetResizable(True)
        left_scroll.setMinimumWidth(200)
        left_scroll.setMaximumWidth(200)
        
        # Mittlerer Container
        self.middle_container = QWidget()
        self.middle_layout = QVBoxLayout()
        self.middle_layout.setSpacing(0)
        self.middle_layout.setContentsMargins(0, 0, 0, 0)
        
        # Kariertes Widget und Text Editor
        self.checkered_widget = CheckeredWidget()
        self.text_editor = QTextEdit()
        
        # Content Widget für die Mitte
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.addWidget(self.checkered_widget)
        
        # Untere Scroll Area
        self.animation_container = QWidget()
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(100)
        scroll_area.setMaximumHeight(200)
        
        # Create animation controls
        self.animation_controls = QWidget()
        controls_layout = QHBoxLayout()
        controls_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        
        # Play Button
        self.play_button = QPushButton()
        self.play_button.setIcon(QIcon("Data/icons/play.png"))
        self.play_button.setIconSize(QSize(20, 20))
        self.play_button.setFixedSize(30, 30)
        self.play_button.clicked.connect(self.toggle_animation)
        controls_layout.addWidget(self.play_button)
        
        # Stop Button
        self.stop_button = QPushButton()
        self.stop_button.setIcon(QIcon("Data/icons/stop.png"))
        self.stop_button.setIconSize(QSize(20, 20))
        self.stop_button.setFixedSize(30, 30)
        self.stop_button.clicked.connect(self.stop_animation)
        controls_layout.addWidget(self.stop_button)
        
        # FPS Controls
        fps_label = QLabel("FPS:")
        fps_label.setAlignment(Qt.AlignCenter)
        controls_layout.addWidget(fps_label)
        
        self.fps_input = QSpinBox()
        self.fps_input.setRange(1, 120)
        self.fps_input.setValue(30)
        self.fps_input.setAlignment(Qt.AlignCenter)
        self.fps_input.setFixedWidth(80)
        self.fps_input.valueChanged.connect(self.update_animation_speed)
        controls_layout.addWidget(self.fps_input)
        
        # Loops Checkbox
        self.loops_checkbox = QCheckBox("Loops")
        self.loops_checkbox.setChecked(False)
        self.loops_checkbox.stateChanged.connect(self.update_animation_loop)
        controls_layout.addWidget(self.loops_checkbox)
        
        self.animation_controls.setLayout(controls_layout)
        
        # Main layout for animation area
        animation_layout = QVBoxLayout(self.animation_container)
        animation_layout.addWidget(self.animation_controls)
        
        # Create timeline widget
        self.timeline_widget = QWidget()
        self.timeline_widget.setMinimumHeight(100)
        self.timeline_widget.setStyleSheet("""
            background-color: #333333;
            border: 2px solid #333333;
            border-radius: 10px;
            padding: 10px;
        """)
        animation_layout.addWidget(self.timeline_widget)
        
        scroll_area.setWidget(self.animation_container)
        
        # Initialize animation variables
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.next_frame)
        self.current_frame = 0
        self.animation_frames = []
        self.is_playing = False
        
        
        # Mittleres Layout zusammensetzen
        self.middle_layout.addWidget(self.content_widget)
        self.middle_layout.addWidget(scroll_area)
        self.middle_container.setLayout(self.middle_layout)
        
        # Hauptlayout zusammensetzen
        main_layout.addWidget(left_scroll)
        main_layout.addWidget(self.middle_container)
        
        self.main_widget.setLayout(main_layout)
        self.setCentralWidget(self.main_widget)

    def display_texture(self, relative_texture_path):
        # Prüfe verschiedene mögliche Dateierweiterungen
        possible_extensions = ['', '.png', '.jpg', '.jpeg']
        base_path = os.path.join(self.yaml_directory, relative_texture_path)
        
        for ext in possible_extensions:
            test_path = base_path + ext
            test_path = os.path.normpath(test_path)
            if os.path.exists(test_path):
                self.checkered_widget.set_texture(test_path)
                return
                
        # Wenn keine Datei gefunden wurde
        QMessageBox.warning(self, "Fehler", f"Textur nicht gefunden: {relative_texture_path}")

    def create_menu_bar(self):
        menubar = self.menuBar()
        
        # File Menu
        file_menu = menubar.addMenu("File")
        
        open_file_action = file_menu.addAction("Open File")
        open_file_action.triggered.connect(self.open_yaml_file)
        open_file_action.setShortcut('Ctrl+O')
        
        save_all_action = file_menu.addAction("Generate yaml File")
        save_all_action.triggered.connect(self.save_yaml_file)
        save_all_action.setShortcut('Ctrl+S')

        # Edit Menu
        Edit_menu = menubar.addMenu("Edit")
        
        self.toggle_editor_action = Edit_menu.addAction("Text Editor")
        self.toggle_editor_action.setShortcut('Ctrl+T')
        self.toggle_editor_action.setCheckable(True)
        self.toggle_editor_action.triggered.connect(self.toggle_editor)

    def toggle_editor(self, checked):
        current_widget = self.content_layout.itemAt(0).widget()
        self.content_layout.removeWidget(current_widget)
        current_widget.hide()
        
        if checked:
            self.content_layout.addWidget(self.text_editor)
            if self.yaml_content:
                self.text_editor.setText(self.yaml_content)
            self.text_editor.show()
            self.toggle_editor_action.setText("Show Checkered View")
        else:
            self.content_layout.addWidget(self.checkered_widget)
            self.checkered_widget.show()
            self.toggle_editor_action.setText("Text Editor")

    def parse_texture_paths(self, yaml_content):
        try:
            data = yaml.safe_load(yaml_content)
            texture_paths = []
            
            def extract_texture_paths(data_obj):
                if isinstance(data_obj, dict):
                    if 'MaterialAnimConfigs' in data_obj:
                        for material in data_obj['MaterialAnimConfigs']:
                            if isinstance(material, dict) and 'TexturePatternInfos' in material:
                                for texture_info in material['TexturePatternInfos']:
                                    if isinstance(texture_info, dict) and \
                                    'CurveData' in texture_info and \
                                    texture_info['CurveData'] and \
                                    'KeyFrames' in texture_info['CurveData']:
                                        key_frames = texture_info['CurveData']['KeyFrames']
                                        frames_dict = {str(k): v for k, v in key_frames.items()}
                                        for value in frames_dict.values():
                                            if isinstance(value, str):
                                                texture_paths.append(value)
                    
                    for key, value in data_obj.items():
                        if isinstance(key, str) and 'texture' in key.lower() and isinstance(value, str):
                            texture_paths.append(value)
                        elif isinstance(value, (dict, list)):
                            extract_texture_paths(value)
                            
                elif isinstance(data_obj, list):
                    for item in data_obj:
                        if isinstance(item, str):
                            texture_paths.append(item)
                        elif isinstance(item, (dict, list)):
                            extract_texture_paths(item)

            extract_texture_paths(data)
            return list(dict.fromkeys(texture_paths))  # Entferne Duplikate
                
        except Exception as e:
            print(f"Fehler beim Parsen der YAML-Datei: {str(e)}")
            return []

    def load_textures(self):
        self.button_widget.clear_buttons()
        if not self.texture_paths:
            return
        
        for texture_path in self.texture_paths:
            self.button_widget.add_texture_button(texture_path)

    def open_yaml_file(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Open YAML File",
            "",
            "YAML Files (*.yaml *.yml);;All Files (*)"
        )
        
        if file_name:
            try:
                # Speichere das Verzeichnis der YAML-Datei
                self.yaml_directory = os.path.dirname(os.path.abspath(file_name))
                
                with open(file_name, 'r', encoding='utf-8') as file:
                    self.yaml_content = file.read()
                    yaml.safe_load(self.yaml_content)
                    self.text_editor.setText(self.yaml_content)
                    self.current_file = file_name
                    
                    self.texture_paths = self.parse_texture_paths(self.yaml_content)
                    self.load_textures()

                    # Zeige den ersten Frame automatisch an
                    if self.texture_paths:
                        self.display_texture(self.texture_paths[0])
                    
                    self.setWindowTitle(f"Neo Bowser City TV - {file_name}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error opening file:\n{str(e)}")


    def save_yaml_file(self):
        if not self.current_file:
            self.current_file, _ = QFileDialog.getSaveFileName(
                self,
                "Save YAML File",
                "",
                "YAML Files (*.yaml *.yml);;All Files (*)"
            )
        
        if self.current_file:
            try:
                yaml_content = self.text_editor.toPlainText()
                yaml.safe_load(yaml_content)
                
                with open(self.current_file, 'w', encoding='utf-8') as file:
                    file.write(yaml_content)
                self.yaml_content = yaml_content
                
                self.texture_paths = self.parse_texture_paths(yaml_content)
                self.load_textures()
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error saving file:\n{str(e)}")

    def next_frame(self):
        if not self.animation_frames:
            return

        # Nächsten Frame anzeigen
        self.current_frame += 1
        if self.current_frame >= len(self.animation_frames):
            if self.loops_checkbox.isChecked():  # Nur loopen, wenn Checkbox aktiviert ist
                self.current_frame = 0  # Zurück zum ersten Frame
            else:
                self.stop_animation()  # Animation stoppen
                return

        # Zeige den aktuellen Frame
        self.display_texture(self.animation_frames[self.current_frame])

    def update_animation_loop(self):
        # Optional: Zeige an, ob Loops aktiviert oder deaktiviert wurden
        if self.loops_checkbox.isChecked():
            print("Loop aktiviert")
        else:
            print("Loop deaktiviert")



    def toggle_animation(self):
        if self.is_playing:  # Läuft -> Pausieren
            self.pause_animation()
            self.play_button.setIcon(QIcon("Data/icons/play.png"))
        else:  # Gestoppt oder pausiert -> Starten
            self.start_animation()
            self.play_button.setIcon(QIcon("Data/icons/pause.png"))


    def start_animation(self):
        if not self.texture_paths:
            QMessageBox.warning(self, "Fehler", "Keine Animationen verfügbar.")
            return

        # Extrahiere Frames aus der Texturpfad-Liste
        self.animation_frames = self.texture_paths  # Reihenfolge hier eventuell anpassen
        self.current_frame = 0  # Starte bei Frame 0

        # Timer für FPS-Einstellungen starten
        fps = self.fps_input.value()
        self.animation_timer.start(1000 // fps)
        self.is_playing = True

    def pause_animation(self):
        self.animation_timer.stop()
        self.is_playing = False

    def stop_animation(self):
        self.animation_timer.stop()
        self.is_playing = False
        self.current_frame = 0  # Zurück zum ersten Frame
        self.play_button.setIcon(QIcon("Data/icons/play.png"))

        if self.animation_frames:
            self.display_texture(self.animation_frames[0])  # Zeige den ersten Frame


    def update_animation_speed(self):
        if self.is_playing:  # Timer läuft
            fps = self.fps_input.value()  # Hole den aktuellen FPS-Wert
            self.animation_timer.start(1000 // fps)  # Aktualisiere den Timer

    def update_animation_speed(self):
        if self.is_playing:  # Timer läuft
            fps = self.fps_input.value()  # Hole den aktuellen FPS-Wert
            self.animation_timer.start(1000 // fps)  # Aktualisiere den Timer





if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())