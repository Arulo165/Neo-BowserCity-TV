from PySide6.QtWidgets import (QApplication, QMainWindow, QScrollArea, 
                             QWidget, QVBoxLayout, QHBoxLayout, QFileDialog, 
                             QMessageBox, QTextEdit, QPushButton, QLabel, QSpinBox, QCheckBox,
                             QDialog, QLineEdit, QDialogButtonBox, QFormLayout,QListWidgetItem,QListWidget,QGroupBox)
from PySide6.QtGui import QPainter, QColor, QPixmap, QDrag, QIcon
from PySide6.QtCore import Qt, QRect, QMimeData, QPoint, QSize, QTimer
from PySide6.QtWidgets import QFormLayout
from PySide6.QtGui import QIcon
import sys
import yaml
import os
from PIL import Image
import io

class AddFrameDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Frame")
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        # Erklärungstext
        info_label = QLabel("Enter the texture path for the new frame:")
        layout.addWidget(info_label)
        
        # Textfeld für den Texturpfad
        self.path_input = QLineEdit()
        layout.addWidget(self.path_input)
        
        # Standard Dialog-Buttons (OK & Cancel)
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

class DraggableButton(QPushButton):
    def __init__(self, text, frame_index, texture_path, parent=None):
        super().__init__(text, parent)
        self.frame_index = frame_index
        self.texture_path = texture_path
        self.setAcceptDrops(True)
        
        # Erstelle Layout für Button mit Delete-Icon
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(5, 0, 5, 0)
        self.layout.setSpacing(5)
        
        # Label für den Frame-Text
        self.text_label = QLabel(text)
        self.text_label.setStyleSheet("color: white;")
        self.layout.addWidget(self.text_label)
        
        # Stretch zwischen Text und Delete-Button
        self.layout.addStretch()
        
        self.delete_button = QPushButton()
        self.delete_button.setFixedSize(20, 20)
        self.delete_button.setIcon(QIcon("Data/Icons/remove.png"))
        self.delete_button.setIconSize(QSize(20, 20))
        self.delete_button.setStyleSheet("border: none; background-color: transparent;")
        self.delete_button.clicked.connect(self.delete_frame)
        self.layout.addWidget(self.delete_button)
        
        self.setLayout(self.layout)
        
        self.setStyleSheet("""
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

    def delete_frame(self):
        self.parent().delete_frame(self.frame_index)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            drag = QDrag(self)
            mime_data = QMimeData()
            mime_data.setText(str(self.frame_index))
            drag.setMimeData(mime_data)
            
            pixmap = QPixmap(self.size())
            self.render(pixmap)
            drag.setPixmap(pixmap)
            
            drag.exec(Qt.MoveAction)
        else:
            super().mousePressEvent(event)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        source_index = int(event.mimeData().text())
        target_index = self.frame_index
        self.parent().handle_frame_reorder(source_index, target_index)
        event.acceptProposedAction()

class TextureButtonWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(5)
        self.layout.setAlignment(Qt.AlignTop)
        self.buttons = []
        self.parent = parent

        # Füge "Add Frame" Button hinzu
        self.add_frame_button = QPushButton("+ Add Frame")
        self.add_frame_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 5px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.add_frame_button.clicked.connect(self.show_add_frame_dialog)
        self.layout.addWidget(self.add_frame_button)

    def show_add_frame_dialog(self):
        dialog = AddFrameDialog(self)
        if dialog.exec() == QDialog.Accepted:
            new_texture_path = dialog.path_input.text().strip()
            if new_texture_path:
                self.parent.add_new_frame(new_texture_path)

    def clear_buttons(self):
        for button in self.buttons:
            self.layout.removeWidget(button)
            button.deleteLater()
        self.buttons.clear()

    def add_texture_button(self, texture_path, frame_index):
        button_text = f"Frame {frame_index}: {os.path.basename(texture_path)}"
        button = DraggableButton(button_text, frame_index, texture_path, self)
        button.setToolTip(texture_path)
        button.clicked.connect(lambda: self.parent.display_texture(texture_path))
        # Füge den Button vor dem "Add Frame" Button ein
        self.layout.insertWidget(self.layout.count() - 1, button)
        self.buttons.append(button)

    def handle_frame_reorder(self, source_index, target_index):
        self.parent.reorder_animation_frames(source_index, target_index)

    def delete_frame(self, frame_index):
        self.parent.delete_animation_frame(frame_index)

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

        self.yaml_property_editor = YAMLPropertyEditor(self)
        
        self.current_file = None
        self.yaml_content = None
        self.texture_paths = []  # Liste der ursprünglichen Texturpfade
        self.animation_frames = []  # Neue separate Liste für Animationsframes
        self.yaml_directory = ""
        self.property_editor = None 
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
        
        self.property_editor = YAMLPropertyEditor(self)

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

        # Rechte YAML Property Editor Area hinzufügen
        self.yaml_editor = YAMLPropertyEditor(self)
        right_scroll = QScrollArea()
        right_scroll.setWidget(self.yaml_editor)
        right_scroll.setWidgetResizable(True)
        right_scroll.setMinimumWidth(250)
        right_scroll.setMaximumWidth(300)
        
        # Hauptlayout zusammensetzen
        main_layout.addWidget(left_scroll)
        main_layout.addWidget(self.middle_container)
        main_layout.addWidget(right_scroll)
        
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
        
        save_all_action = file_menu.addAction("save yaml File")
        save_all_action.triggered.connect(self.save_yaml_file)
        save_all_action.setShortcut('Ctrl+S')

        # Füge einen Separator hinzu
        file_menu.addSeparator()

        # Füge Export Animation Option hinzu
        export_action = file_menu.addAction("Export Animation as GIF...")
        export_action.triggered.connect(self.export_animation)
        export_action.setShortcut('Ctrl+E')  # Optional: Füge einen Shortcut hinzu

        # Edit Menu
        Edit_menu = menubar.addMenu("Edit")
        
        self.toggle_editor_action = Edit_menu.addAction("Text Editor")
        self.toggle_editor_action.setShortcut('Ctrl+T')
        self.toggle_editor_action.setCheckable(True)
        self.toggle_editor_action.triggered.connect(self.toggle_editor)


    def export_animation(self):
        if not self.animation_frames:
            QMessageBox.warning(self, "Error", "No animation frames available to export.\nPlease load a YAML file with texture animations first.")
            return

        # Dialog zum Speichern der GIF-Datei
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Animation as GIF",
            "",
            "GIF Files (*.gif)"
        )

        if not file_path:
            return

        try:
            frames = []
            frame_duration = int(1000 / self.fps_input.value())  # Berechne die Frame-Dauer in Millisekunden

            # Zeige einen Fortschrittsdialog
            progress = QMessageBox(QMessageBox.Information, "Exporting...", "Creating GIF animation...", QMessageBox.Cancel)
            progress.setStandardButtons(QMessageBox.NoButton)  # Entferne alle Buttons
            progress.show()
            QApplication.processEvents()  # Aktualisiere die UI

            # Sammle alle Frames
            for texture_path in self.animation_frames:
                # Konstruiere den vollständigen Pfad
                full_path = os.path.join(self.yaml_directory, texture_path)
                
                # Prüfe verschiedene mögliche Dateierweiterungen
                possible_extensions = ['', '.png', '.jpg', '.jpeg']
                for ext in possible_extensions:
                    test_path = full_path + ext
                    test_path = os.path.normpath(test_path)
                    if os.path.exists(test_path):
                        # Öffne das Bild mit PIL
                        img = Image.open(test_path)
                        # Konvertiere zu RGB falls notwendig
                        if img.mode != 'RGB':
                            img = img.convert('RGB')
                        frames.append(img)
                        break

            if not frames:
                progress.close()
                raise Exception("No valid frames found")

            # Speichere die Animation als GIF
            frames[0].save(
                file_path,
                save_all=True,
                append_images=frames[1:],
                duration=frame_duration,
                loop=0 if self.loops_checkbox.isChecked() else 1
            )

            # Schließe den Fortschrittsdialog
            progress.close()

            QMessageBox.information(self, "Success", "Animation successfully exported as GIF!")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error exporting animation:\n{str(e)}")

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
            animation_frames = []  # Store frames in order
            unique_textures = set()  # Collect unique textures
            
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
                                                animation_frames.append(value)
                                                unique_textures.add(value)
                    
                    for key, value in data_obj.items():
                        if isinstance(key, str) and 'texture' in key.lower() and isinstance(value, str):
                            animation_frames.append(value)
                            unique_textures.add(value)
                        elif isinstance(value, (dict, list)):
                            extract_texture_paths(value)
                            
                elif isinstance(data_obj, list):
                    for item in data_obj:
                        if isinstance(item, str):
                            animation_frames.append(item)
                            unique_textures.add(item)
                        elif isinstance(item, (dict, list)):
                            extract_texture_paths(item)

            extract_texture_paths(data)
            
            # Update frame count and name in data and yaml content
            if animation_frames:
                data['FrameCount'] = len(animation_frames)
                # Set name from file path if not present
                if not data.get('Name'):
                    data['Name'] = os.path.splitext(os.path.basename(self.current_file))[0]
                self.yaml_content = yaml.dump(data, sort_keys=False, allow_unicode=True)
                
            return list(unique_textures), animation_frames

        except Exception as e:
            
            return [], []


    def load_textures(self):
        self.button_widget.clear_buttons()
        if not self.animation_frames:
            return
        
        for i, texture_path in enumerate(self.animation_frames):
            self.button_widget.add_texture_button(texture_path, i)

    def open_yaml_file(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Open YAML File",
            "",
            "YAML Files (*.yaml *.yml);;All Files (*)"
        )
        
        if file_name:
            try:
                self.yaml_directory = os.path.dirname(os.path.abspath(file_name))
                
                with open(file_name, 'r', encoding='utf-8') as file:
                    self.yaml_content = file.read()
                    yaml.safe_load(self.yaml_content)  
                    self.text_editor.setText(self.yaml_content)
                    self.current_file = file_name
                    
                    # Load properties in editor
                    self.yaml_editor.load_yaml_content(self.yaml_content)
                    
                    # Load textures and animation frames
                    self.texture_paths, self.animation_frames = self.parse_texture_paths(self.yaml_content)
                    self.load_textures()

                    if self.animation_frames:
                        self.display_texture(self.animation_frames[0])
                    
                    self.setWindowTitle(f"Neo Bowser City TV - {file_name}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error opening file:\n{str(e)}")

    def update_yaml(self):
        if not self.yaml_content:
            return
        
        
            
        # Update basic properties
        self.yaml_content['Name'] = self.name_edit.text()
        self.yaml_content['Path'] = None if not self.path_edit.text() else self.path_edit.text()
        self.yaml_content['Loop'] = self.loop_checkbox.isChecked()
        self.yaml_content['FrameCount'] = self.frame_count_spin.value()
        
        # Update material configs
        if self.yaml_content.get('MaterialAnimConfigs'):
            for material in self.yaml_content['MaterialAnimConfigs']:
                if material.get('TexturePatternInfos'):
                    material['TexturePatternInfos'][0]['IsConstant'] = self.is_constant_checkbox.isChecked()
        
        # Generate YAML content
        yaml_content = yaml.dump(self.yaml_content, sort_keys=False, allow_unicode=True)
        
        # Update text editor
        if hasattr(self.parent(), 'text_editor'):
            self.parent().text_editor.setText(yaml_content)
            
        # Save to file if exists
        if hasattr(self.parent(), 'current_file') and self.parent().current_file:
            try:
                with open(self.parent().current_file, 'w', encoding='utf-8') as file:
                    file.write(yaml_content)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error saving file:\n{str(e)}")


    def next_frame(self):
        if not self.animation_frames:
            return

        # Nächsten Frame anzeigen
        self.current_frame += 1
        if self.current_frame >= len(self.animation_frames):
            if self.loops_checkbox.isChecked():
                self.current_frame = 0
            else:
                self.stop_animation()
                return

        # Zeige den aktuellen Frame
        self.display_texture(self.animation_frames[self.current_frame])


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
                QMessageBox.information(None, "Message", "yaml saved succesfully")

                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error saving file:\n{str(e)}")

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
        if not self.animation_frames:  # Prüfe animation_frames statt texture_paths
            QMessageBox.warning(self, "Fehler", "Keine Animationen verfügbar.")
            return

        self.current_frame = 0  # Starte bei Frame 0
        
        # Timer für FPS-Einstellungen starten
        fps = self.fps_input.value()
        self.animation_timer.start(1000 // fps)
        self.is_playing = True
        
        # Zeige den ersten Frame
        self.display_texture(self.animation_frames[0])


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
        if self.is_playing:  # Wenn die Animation läuft
            fps = self.fps_input.value()
            self.animation_timer.start(1000 // fps)  # Timer-Intervall basierend auf FPS aktualisieren

    def update_animation_speed(self):
        if self.is_playing:  # Timer läuft
            fps = self.fps_input.value()  # Hole den aktuellen FPS-Wert
            self.animation_timer.start(1000 // fps)  # Aktualisiere den Timer

    def reorder_animation_frames(self, source_index, target_index):
        if 0 <= source_index < len(self.animation_frames) and 0 <= target_index < len(self.animation_frames):
            # Verschiebe Frame in der Liste
            frame = self.animation_frames.pop(source_index)
            self.animation_frames.insert(target_index, frame)
            
            # Aktualisiere die Buttons
            self.load_textures()
            
            # Aktualisiere die YAML-Datei
            self.update_yaml_with_new_order()
            
            # Aktualisiere den Text Editor
            if self.yaml_content:
                self.text_editor.setText(self.yaml_content)

    def update_yaml_with_new_order(self):
        try:
            data = yaml.safe_load(self.yaml_content)
            
            def update_frames_in_data(data_obj):
                if isinstance(data_obj, dict):
                    if 'MaterialAnimConfigs' in data_obj:
                        for material in data_obj['MaterialAnimConfigs']:
                            if isinstance(material, dict) and 'TexturePatternInfos' in material:
                                for texture_info in material['TexturePatternInfos']:
                                    if isinstance(texture_info, dict) and \
                                    'CurveData' in texture_info and \
                                    texture_info['CurveData'] and \
                                    'KeyFrames' in texture_info['CurveData']:
                                        # Erstelle neue KeyFrames basierend auf der neuen Reihenfolge
                                        new_frames = {}
                                        for i, frame in enumerate(self.animation_frames):
                                            new_frames[str(i)] = frame
                                        texture_info['CurveData']['KeyFrames'] = new_frames
                    
                    for key, value in data_obj.items():
                        if isinstance(value, (dict, list)):
                            update_frames_in_data(value)
                
                elif isinstance(data_obj, list):
                    for item in data_obj:
                        if isinstance(item, (dict, list)):
                            update_frames_in_data(item)

            update_frames_in_data(data)
            self.yaml_content = yaml.dump(data, sort_keys=False, allow_unicode=True)
            
            # Aktualisiere Text Editor
            self.text_editor.setText(self.yaml_content)
            
            # Speichere die Änderungen sofort in die Datei
            if self.current_file:
                with open(self.current_file, 'w', encoding='utf-8') as file:
                    file.write(self.yaml_content)
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error updating YAML file:\n{str(e)}")

    def add_new_frame(self, texture_path):
        self.animation_frames.append(texture_path)
        self.load_textures()
        self.update_yaml_with_new_order()
        
    def delete_animation_frame(self, frame_index):
        if 0 <= frame_index < len(self.animation_frames):
            self.animation_frames.pop(frame_index)
            self.load_textures()
            self.update_yaml_with_new_order()

    def update_yaml_with_property_changes(self):
        try:
            if not self.yaml_content:
                return

            # Aktualisierte YAML-Daten generieren
            updated_yaml_content = yaml.dump(self.yaml_content, sort_keys=False, allow_unicode=True)

            # Änderungen in die Datei schreiben
            if self.current_file:
                with open(self.current_file, 'w', encoding='utf-8') as file:
                    file.write(updated_yaml_content)
                
                # YAML-Inhalt aktualisieren
                self.yaml_content = updated_yaml_content
                self.text_editor.setText(updated_yaml_content)

               
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Aktualisieren der YAML-Datei:\n{str(e)}")

    def update_yaml(self):
        try:
            # Validate core objects exist
            if not self.yaml_property_editor:
                print("Error: Property editor not initialized")
                return
            
            # Safe text retrieval
            current_name = (self.yaml_property_editor.name_edit.text() or '').strip()
            current_path = (self.yaml_property_editor.path_edit.text() or '').strip()
            
            # Ensure YAML content is a dictionary
            if not isinstance(self.yaml_content, dict):
                try:
                    # Convert to dict if not already
                    self.yaml_content = yaml.safe_load(str(self.yaml_content)) or {}
                except Exception as parse_error:
                    print(f"YAML parsing error: {parse_error}")
                    self.yaml_content = {}
            
            # Safe updates with null checks
            if current_name:
                self.yaml_content['Name'] = current_name
            
            self.yaml_content['Path'] = current_path or None
            self.yaml_content['Loop'] = self.yaml_property_editor.loop_checkbox.isChecked()
            self.yaml_content['FrameCount'] = self.yaml_property_editor.frame_count_spin.value()
            
            # Safe material config update
            if self.yaml_content.get('MaterialAnimConfigs'):
                for material in self.yaml_content['MaterialAnimConfigs']:
                    if material and material.get('TexturePatternInfos'):
                        material['TexturePatternInfos'][0]['IsConstant'] = \
                            self.yaml_property_editor.is_constant_checkbox.isChecked()
            
            # Convert to YAML string
            yaml_content = yaml.dump(self.yaml_content, sort_keys=False, allow_unicode=True)
            
            # Trigger update
            if hasattr(self.yaml_property_editor, 'trigger_yaml_update'):
                self.yaml_property_editor.trigger_yaml_update()
        
        except Exception as e:
            print(f"Unexpected error in update_yaml: {e}")



# Property editor

class YAMLPropertyEditor(QWidget):
    def __init__(self, parent: 'MainWindow' = None):  # Type-Annotation in Anführungszeichen
        super().__init__(parent)
        self._main_window: 'MainWindow' = parent  # Explizite Typ-Annotation 
        self.yaml_content = None
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Basic properties group
        basic_group = QGroupBox("Basic Properties")
        basic_layout = QFormLayout()
        
        self.name_edit = QLineEdit()
        self.name_edit.textChanged.connect(self.update_yaml)
        basic_layout.addRow("Name:", self.name_edit)
        
        self.path_edit = QLineEdit()
        self.path_edit.textChanged.connect(self.update_yaml)
        basic_layout.addRow("Path:", self.path_edit)
        
        self.loop_checkbox = QCheckBox()
        self.loop_checkbox.stateChanged.connect(self.update_yaml)
        basic_layout.addRow("Loop:", self.loop_checkbox)
        
        self.frame_count_spin = QSpinBox()
        self.frame_count_spin.setRange(1, 9999)
        self.frame_count_spin.valueChanged.connect(self.update_yaml)
        basic_layout.addRow("Frame Count:", self.frame_count_spin)
        
        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)
        
        # Materials group
        materials_group = QGroupBox("Material Configs")
        materials_layout = QVBoxLayout()
        
        self.materials_list = QListWidget()
        self.materials_list.currentItemChanged.connect(self.on_material_selected)
        materials_layout.addWidget(self.materials_list)
        
        # Material properties
        material_form = QFormLayout()
        self.material_name_edit = QLineEdit()
        self.material_name_edit.setEnabled(False)
        self.material_name_edit.textChanged.connect(self.update_material_property)
        material_form.addRow("Material Name:", self.material_name_edit)
        
        # TexturePatternInfo properties
        self.is_constant_checkbox = QCheckBox()
        self.is_constant_checkbox.stateChanged.connect(self.update_yaml)
        material_form.addRow("Is Constant:", self.is_constant_checkbox)
        
        materials_layout.addLayout(material_form)
        materials_group.setLayout(materials_layout)
        layout.addWidget(materials_group)
        
        self.setLayout(layout)

    def load_yaml_content(self, yaml_content):
        try:
            self.yaml_content = yaml.safe_load(yaml_content) if yaml_content else {
                'Name': '',  # Change default to empty string
                'Path': None,
                'Loop': False,
                'FrameCount': 1,
                'MaterialAnimConfigs': [
                    {
                        'Name': '',
                        'TexturePatternInfos': [
                            {
                                'Name': '_a0',
                                'IsConstant': False,
                                'ConstantValue': None,
                                'CurveData': {'KeyFrames': {}}
                            }
                        ],
                        'ParamInfos': []
                    }
                ]
            }
            self.update_ui_from_yaml()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading YAML data:\n{str(e)}")

            
    def update_ui_from_yaml(self):
        if not self.yaml_content:
            return
        
        # Use get() with empty string as default to ensure any parsed name is used
        self.name_edit.setText(self.yaml_content.get('Name', ''))

            
        # Calculate frame count from animation frames if available
        if 'MaterialAnimConfigs' in self.yaml_content and self.yaml_content['MaterialAnimConfigs']:
            for material in self.yaml_content['MaterialAnimConfigs']:
                if material.get('TexturePatternInfos'):
                    for texture_info in material['TexturePatternInfos']:
                        if texture_info.get('CurveData') and texture_info['CurveData'].get('KeyFrames'):
                            frame_count = len(texture_info['CurveData']['KeyFrames'])
                            self.frame_count_spin.setValue(frame_count)
                            self.yaml_content['FrameCount'] = frame_count
                            break
        
        self.name_edit.setText(self.yaml_content.get('Name', 'walk'))
        self.path_edit.setText(str(self.yaml_content.get('Path', '')))
        self.loop_checkbox.setChecked(self.yaml_content.get('Loop', False))
        
        self.materials_list.clear()
        materials = self.yaml_content.get('MaterialAnimConfigs', [])
        for material in materials:
            item = QListWidgetItem(material.get('Name', ''))
            item.setData(Qt.UserRole, material)
            self.materials_list.addItem(item)
            
        if materials and materials[0].get('TexturePatternInfos'):
            texture_info = materials[0]['TexturePatternInfos'][0]
            self.is_constant_checkbox.setChecked(texture_info.get('IsConstant', False))
            
    def update_yaml(self):

        if hasattr(self._main_window, 'update_yaml'):
            self._main_window.update_yaml()
            
    def update_material_property(self):
        current_item = self.materials_list.currentItem()
        if not current_item:
            return
            
        material_data = current_item.data(Qt.UserRole)
        material_data['Name'] = self.material_name_edit.text()
        current_item.setText(material_data['Name'])
        self.update_yaml()
        
    def on_material_selected(self, current, previous):
        if not current:
            self.material_name_edit.setEnabled(False)
            return
        
        material_data = current.data(Qt.UserRole)
        self.material_name_edit.setText(material_data.get('Name', ''))
        self.material_name_edit.setEnabled(True)

    def trigger_yaml_update(self):
        parent = self.parent()
        if hasattr(parent, 'update_yaml_with_property_changes'):
            self._main_window.update_yaml_with_property_changes()

    def update_material_property(self):
        current_item = self.materials_list.currentItem()
        if not current_item:
            return
        
        # Existing update logic...
        
        # Call the new trigger method
        self.trigger_yaml_update()



if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())