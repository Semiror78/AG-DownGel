import sys
import os
import re
import requests
import configparser
import json
from urllib.parse import urlparse

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, 
    QPushButton, QProgressBar, QHBoxLayout, QCheckBox, QComboBox
)
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QIcon

os.makedirs("downloads", exist_ok=True)
os.makedirs("locales", exist_ok=True)

class Worker(QThread):
    statusChanged = pyqtSignal(str)
    progressUpdated = pyqtSignal(int, int)

    def __init__(self, tags, user_id, api_key, download_dir, allowed_exts, translator):
        super().__init__()
        self.tags = tags
        self.user_id = user_id
        self.api_key = api_key
        self.download_dir = download_dir
        self.allowed_exts = allowed_exts
        self.tr = translator

    def run(self):
        try:
            base_url = "https://gelbooru.com/index.php"
            params_base = {
                "page": "dapi",
                "s": "post",
                "q": "index",
                "limit": 1000,
                "json": 1,
                "tags": self.tags,
            }
            if self.user_id:
                params_base["user_id"] = self.user_id
            if self.api_key:
                params_base["api_key"] = self.api_key

            posts = []
            total_count = 0
            has_total = False
            pid = 0
            self.statusChanged.emit(self.tr["getting_posts"])
            while True:
                params = params_base.copy()
                params["pid"] = pid
                response = requests.get(base_url, params=params)
                response_text = response.text.strip()[:200]
                if response.status_code != 200:
                    self.statusChanged.emit(self.tr["http_error"].format(response.status_code, response_text))
                    return
                if not response_text:
                    self.statusChanged.emit(self.tr["empty_response"].format(response.status_code))
                    return
                try:
                    data = response.json()
                except ValueError as e:
                    if "Missing authentication" in response_text or "login_required" in response_text.lower():
                        self.statusChanged.emit(self.tr["json_error_auth"].format(response_text))
                    else:
                        self.statusChanged.emit(self.tr["json_error"].format(str(e), response_text))
                    return
                
                # Handle both dict and list formats (GelBooru uses dict with "post")
                if isinstance(data, list):
                    new_posts = data
                    success = True  # Assume success if list
                elif isinstance(data, dict):
                    success = data.get("success", True)
                    if not success:
                        msg = data.get('message', 'Неизвестная ошибка API')
                        self.statusChanged.emit(self.tr["api_error"].format(msg))
                        return
                    new_posts = data.get("post", [])  # GelBooru uses "post", not "posts"
                    if total_count == 0:
                        attributes = data.get("@attributes", {})
                        total_count = attributes.get("count", len(new_posts))
                        has_total = True
                else:
                    self.statusChanged.emit(self.tr["unexpected_type"].format(type(data), response_text))
                    return

                posts.extend(new_posts)
                current_count = len(posts)
                if not has_total:
                    total_str = self.tr["pagination_note"]
                else:
                    total_str = f" / {total_count}"
                self.progressUpdated.emit(current_count, total_count if has_total else 0)
                self.statusChanged.emit(self.tr["received_posts"].format(current_count, total_str))
                if len(new_posts) < 1000:
                    break
                pid += 1

            if len(posts) == 0:
                self.statusChanged.emit(self.tr["no_posts"])
                return

            self.statusChanged.emit(self.tr["starting_download"])
            downloaded = 0
            processed = 0
            total_posts = len(posts)
            video_exts = {'.mp4', '.webm', '.avi', '.mov', '.swf'}
            gif_ext = '.gif'
            image_exts = {'.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tga'}
            
            for post in posts:
                processed += 1
                if not isinstance(post, dict):
                    self.progressUpdated.emit(processed, total_posts)
                    continue
                url = post.get("file_url")
                if not url:
                    self.progressUpdated.emit(processed, total_posts)
                    continue
                post_id = post.get("id", "")
                parsed_url = urlparse(url)
                filename = os.path.basename(parsed_url.path)
                if not filename or '.' not in filename:
                    ext = os.path.splitext(parsed_url.path)[1] or ".jpg"
                    filename = f"{post_id}{ext}"
                else:
                    # Clean filename
                    filename = re.sub(r'[<>:"/\\|?*]', '_', f"{post_id}_{filename}")
                ext = os.path.splitext(filename)[1].lower()
                
                if ext not in self.allowed_exts:
                    self.progressUpdated.emit(processed, total_posts)
                    continue
                
                # Determine subdir
                if ext == gif_ext:
                    subdir = "GIF"
                elif ext in video_exts:
                    subdir = "videos"
                else:
                    subdir = "images"
                
                subdir_path = os.path.join(self.download_dir, subdir)
                os.makedirs(subdir_path, exist_ok=True)
                filepath = os.path.join(subdir_path, filename)
                
                try:
                    dl_response = requests.get(url, stream=True)
                    dl_response.raise_for_status()
                    with open(filepath, 'wb') as f:
                        for chunk in dl_response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    downloaded += 1
                    if processed % 10 == 0:
                        self.statusChanged.emit(self.tr["processed_downloaded"].format(processed, total_posts, downloaded))
                except Exception as e:
                    self.statusChanged.emit(self.tr["download_error"].format(url, str(e)))
                self.progressUpdated.emit(processed, total_posts)
            
            skipped = total_posts - downloaded
            self.statusChanged.emit(self.tr["finished"].format(processed, total_posts, downloaded, skipped, self.download_dir))
        except Exception as e:
            self.statusChanged.emit(self.tr["unexpected_error"].format(str(e)))


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setGeometry(100, 100, 400, 350)  # Slightly taller for lang combo

        # Load languages
        self.languages = []
        if os.path.exists("locales"):
            for file in os.listdir("locales"):
                if file.endswith('.json'):
                    lang = file[:-5]
                    self.languages.append(lang)
        if not self.languages:
            self.languages = ["en"]  # Fallback

        self.current_lang = "en"  # Default
        self.translator = self.load_translator(self.current_lang)

        self.setWindowTitle(self.translator["title"])
        self.setWindowIcon(QIcon("icon.png"))

        # Load config
        self.config_file = 'config.ini'
        self.config = configparser.ConfigParser()
        if os.path.exists(self.config_file):
            self.config.read(self.config_file)

        layout = QVBoxLayout(self)

        # Language selector
        lang_layout = QHBoxLayout()
        lang_label = QLabel("Language / Язык / 语言 / 言語:")
        lang_layout.addWidget(lang_label)
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(self.languages)
        self.lang_combo.setCurrentText(self.current_lang)
        self.lang_combo.currentTextChanged.connect(self.change_language)
        lang_layout.addWidget(self.lang_combo)
        lang_layout.addStretch()
        layout.addLayout(lang_layout)

        # User ID
        self.user_id_label = QLabel()
        layout.addWidget(self.user_id_label)
        self.user_id_edit = QLineEdit()
        self.user_id_edit.setText(self.config.get('API', 'user_id', fallback=''))
        layout.addWidget(self.user_id_edit)

        # API Key
        self.api_key_label = QLabel()
        layout.addWidget(self.api_key_label)
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_edit.setText(self.config.get('API', 'api_key', fallback=''))
        layout.addWidget(self.api_key_edit)

        # Tags
        self.tags_label = QLabel()
        layout.addWidget(self.tags_label)
        tags_hbox = QHBoxLayout()
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText(self.translator["tags_placeholder"])
        tags_hbox.addWidget(self.tags_edit)
        self.no_ai_cb = QCheckBox()
        self.no_ai_cb.setToolTip(self.translator["no_ai_tooltip"])
        tags_hbox.addWidget(self.no_ai_cb)
        tags_hbox.addStretch()
        layout.addLayout(tags_hbox)

        # File types
        self.file_types_label = QLabel()
        layout.addWidget(self.file_types_label)
        types_hbox = QHBoxLayout()
        self.images_cb = QCheckBox()
        types_hbox.addWidget(self.images_cb)
        self.gif_cb = QCheckBox()
        types_hbox.addWidget(self.gif_cb)
        self.video_cb = QCheckBox()
        types_hbox.addWidget(self.video_cb)
        types_hbox.addStretch()
        layout.addLayout(types_hbox)

        # Button
        self.download_btn = QPushButton()
        self.download_btn.clicked.connect(self.start_download)
        layout.addWidget(self.download_btn)

        # Progress
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        # Status
        self.status_label = QLabel()
        layout.addWidget(self.status_label)

        self.update_ui()

    def load_translator(self, lang):
        path = f"locales/{lang}.json"
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return self.load_translator("en")  # Fallback to en

    def change_language(self, lang):
        self.current_lang = lang
        self.translator = self.load_translator(lang)
        self.update_ui()
        self.setWindowTitle(self.translator["title"])

    def update_ui(self):
        self.user_id_label.setText(self.translator["user_id_label"])
        self.api_key_label.setText(self.translator["api_key_label"])
        self.tags_label.setText(self.translator["tags_label"])
        self.no_ai_cb.setText(self.translator["no_ai_checkbox"])
        self.file_types_label.setText(self.translator["file_types_label"])
        self.images_cb.setText(self.translator["images_checkbox"])
        self.gif_cb.setText(self.translator["gif_checkbox"])
        self.video_cb.setText(self.translator["videos_checkbox"])
        self.download_btn.setText(self.translator["download_button"])
        self.status_label.setText(self.translator["status_initial"])

    def start_download(self):
        user_id = self.user_id_edit.text().strip()
        api_key = self.api_key_edit.text().strip()
        tags = self.tags_edit.text().strip()

        if not tags:
            self.status_label.setText(self.translator["enter_tags_error"])
            return

        # Save config
        self.config['API'] = {'user_id': user_id, 'api_key': api_key}
        with open(self.config_file, 'w') as f:
            self.config.write(f)

        # No AI
        original_tags = tags
        if self.no_ai_cb.isChecked():
            tags += " -ai-generated"

        self.status_label.setText(self.translator["searching_tags"].format(tags, original_tags.replace(' ', '_')[:50]))

        # Allowed exts
        allowed_exts = set()
        if self.images_cb.isChecked():
            allowed_exts.update({'.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tga'})
        if self.gif_cb.isChecked():
            allowed_exts.add('.gif')
        if self.video_cb.isChecked():
            allowed_exts.update({'.mp4', '.webm', '.avi', '.mov', '.swf'})
        if not allowed_exts:
            self.status_label.setText(self.translator["select_file_type_error"])
            return

        # Base downloads dir
        base_downloads = "downloads"
        os.makedirs(base_downloads, exist_ok=True)

        # Sanitize dir name: keep spaces, remove only invalid chars
        dir_name = re.sub(r'[^a-zA-Z0-9\s-]', '', original_tags).strip()[:50]
        if not dir_name:
            dir_name = "downloads"
        download_dir = os.path.join(base_downloads, dir_name)
        os.makedirs(download_dir, exist_ok=True)

        self.download_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setValue(0)

        self.worker = Worker(tags, user_id, api_key, download_dir, allowed_exts, self.translator)
        self.worker.statusChanged.connect(self.status_label.setText)
        self.worker.progressUpdated.connect(self.update_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()

    def update_progress(self, current, total):
        if total > 0:
            self.progress.setRange(0, total)
            self.progress.setValue(current)
        else:
            self.progress.setRange(0, 0)  # Indeterminate mode

    def on_finished(self):
        self.download_btn.setEnabled(True)
        self.progress.setVisible(False)
        self.progress.setRange(0, 100)  # Reset


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    dark_stylesheet = """
    QWidget {
        background-color: #03091c;
        color: #ffffff;
        font-family: Arial;
    }
    QLineEdit {
        background-color: #0a1a2e;
        border: 1px solid #1e3a5f;
        padding: 5px;
        border-radius: 3px;
        color: #ffffff;
    }
    QLineEdit:focus {
        border: 1px solid #0078d4;
    }
    QPushButton {
        background-color: #1e3a5f;
        border: 1px solid #2a4a6f;
        padding: 8px;
        border-radius: 3px;
        color: #ffffff;
    }
    QPushButton:hover {
        background-color: #2a4a6f;
    }
    QPushButton:pressed {
        background-color: #0f1e2f;
    }
    QCheckBox {
        color: #ffffff;
        spacing: 5px;
    }
    QCheckBox::indicator {
        width: 13px;
        height: 13px;
    }
    QCheckBox::indicator:unchecked {
        background-color: #0a1a2e;
        border: 1px solid #1e3a5f;
        border-radius: 3px;
    }
    QCheckBox::indicator:checked {
        background-color: #0078d4;
        border: 1px solid #0078d4;
        border-radius: 3px;
    }
    QComboBox {
        background-color: #0a1a2e;
        border: 1px solid #1e3a5f;
        padding: 5px;
        border-radius: 3px;
        color: #ffffff;
    }
    QComboBox::drop-down {
        border: 1px solid #1e3a5f;
    }
    QProgressBar {
        background-color: #0a1a2e;
        border: 1px solid #1e3a5f;
        border-radius: 3px;
        color: #ffffff;
        text-align: center;
    }
    QProgressBar::chunk {
        background-color: #0078d4;
        border-radius: 2px;
    }
    QLabel {
        color: #ffffff;
        padding: 2px;
    }
    """
    app.setStyleSheet(dark_stylesheet)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())