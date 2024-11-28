from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFileDialog,
    QWidget,
    QTextEdit,
    QProgressBar,
    QListWidget,
    QLineEdit,
    QMessageBox,
    QListWidgetItem
)
from PyQt5.QtGui import QFont, QColor, QPalette
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import os
import sys
import subprocess


class FindVenvsThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(list)
    log = pyqtSignal(str)

    def __init__(self, search_path, max_depth=3):
        super().__init__()
        self.search_path = search_path
        self.max_depth = max_depth

    def run(self):
        """尋找所有虛擬環境"""
        venvs = []
        total_dirs = 0
        found_dirs = 0

        def search_directory(path, depth):
            nonlocal total_dirs, found_dirs
            if depth > self.max_depth:
                return
            try:
                for entry in os.scandir(path):
                    if entry.is_dir():
                        total_dirs += 1
                        self.log.emit(f"正在搜尋: {entry.path}")
                        pyvenv_path = os.path.join(entry.path, "pyvenv.cfg")
                        if os.path.isfile(pyvenv_path):
                            project_name = os.path.basename(os.path.dirname(entry.path))
                            venvs.append((project_name, entry.path))
                            self.log.emit(f"找到虛擬環境: {project_name} ({entry.path})")
                            return  # 找到虛擬環境後結束搜尋
                        else:
                            search_directory(entry.path, depth + 1)
                        found_dirs += 1
                        self.progress.emit(int((found_dirs / total_dirs) * 100))
            except PermissionError:
                self.log.emit(f"無法訪問: {path}")

        self.log.emit(f"正在搜尋: {self.search_path}")
        search_directory(self.search_path, 0)
        self.finished.emit(venvs)


class CreateVenvThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str, str)

    def __init__(self, parent_folder, project_name):
        super().__init__()
        self.parent_folder = parent_folder
        self.project_name = project_name
        self.venv_name = "myenv"
        self.python_version = "python3" if os.name != 'nt' else "python"

    def run(self):
        """建立虛擬環境"""
        try:
            project_path = os.path.join(self.parent_folder, self.project_name)
            os.makedirs(project_path, exist_ok=True)
            # 建立虛擬環境
            subprocess.run([self.python_version, "-m", "venv", self.venv_name], cwd=project_path, check=True)
            self.progress.emit(100)
            venv_path = os.path.join(project_path, self.venv_name)
            self.finished.emit(f"虛擬環境已在 {venv_path} 建立成功！", project_path)
        except subprocess.CalledProcessError as e:
            self.finished.emit(f"建立虛擬環境失敗：{e}", "")


class VenvManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Python 虛擬環境管理工具")
        self.setGeometry(300, 300, 900, 700)
        self.init_ui()
        self.thread = None  # 初始化搜尋執行緒

    def init_ui(self):
        """初始化界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 设置字体大小为20px
        font = QFont("微軟正黑體", 10)
        mono_font = QFont("Cascadia Mono", 10)

        # 标题
        self.title_label = QLabel("Python 虛擬環境管理工具")
        self.title_label.setFont(QFont("微軟正黑體", 20, QFont.Bold))
        self.title_label.setAlignment(Qt.AlignCenter)

        # 列表框
        self.venv_list = QListWidget()
        self.venv_list.setFont(font)
        self.venv_list.setSelectionMode(QListWidget.SingleSelection)
        self.venv_list.setStyleSheet("""
            QListWidget {
                background-color: #1e1e1e; 
                color: #ffffff;
            }
            QListWidget::item:hover {
                background-color: #3e3e42;
            }
        """)
        self.venv_list.itemClicked.connect(self.on_venv_item_clicked)

        # 文字区
        self.output_area = QTextEdit()
        self.output_area.setFont(mono_font)
        self.output_area.setReadOnly(True)
        self.output_area.setStyleSheet("background-color: #1e1e1e; color: #ffffff; border: none;")
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setFont(font)
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("QProgressBar { background-color: #1e1e1e; color: #ffffff; }")

        # 搜尋選項
        self.select_folder_button = QPushButton("選擇資料夾")
        self.select_folder_button.setFont(font)
        self.select_folder_button.setStyleSheet("background-color: #1e1e1e; color: #ffffff;")
        self.select_folder_button.clicked.connect(self.select_folder)

        # 虛擬環境名稱輸入框
        self.venv_name_input = QLineEdit()
        self.venv_name_input.setFont(font)
        self.venv_name_input.setPlaceholderText("輸入專案名稱")
        self.venv_name_input.setStyleSheet("background-color: #1e1e1e; color: #ffffff;")

        # 按鈕區域
        self.exit_button = QPushButton("退出")
        self.exit_button.setFont(font)
        self.exit_button.setFixedHeight(50)
        self.exit_button.setStyleSheet(self.apply_hover_effect("""
            QPushButton {
                background-color: #0078d7; 
                color: white; 
                border: none; 
                border-radius: 15px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #005a9e;
                color: white;
            }
        """))
        self.exit_button.clicked.connect(self.close)

        self.search_button = QPushButton("搜尋虛擬專案")
        self.search_button.setFont(font)
        self.search_button.setFixedHeight(50)
        self.search_button.setStyleSheet(self.apply_hover_effect("""
            QPushButton {
                background-color: #107c10; 
                color: white; 
                border: none; 
                border-radius: 15px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #0b6a0b;
                color: white;
            }
        """))
        self.search_button.clicked.connect(self.find_venvs)

        # 建立虛擬環境按鈕
        self.create_venv_button = QPushButton("建立虛擬環境")
        self.create_venv_button.setFont(font)
        self.create_venv_button.setFixedHeight(50)
        self.create_venv_button.setStyleSheet(self.apply_hover_effect("""
            QPushButton {
                background-color: #d83b01; 
                color: white; 
                border: none; 
                border-radius: 15px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #a52600;
                color: white;
            }
        """))
        self.create_venv_button.clicked.connect(self.create_venv)

        # 按鈕布局
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.search_button)
        button_layout.addWidget(self.create_venv_button)
        button_layout.addWidget(self.exit_button)

        # 主布局
        layout = QVBoxLayout()
        layout.addWidget(self.title_label)
        layout.addWidget(self.output_area)
        layout.addWidget(self.venv_list)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.select_folder_button)
        layout.addLayout(button_layout)  # 將按鈕布局添加到主布局
        layout.addWidget(self.venv_name_input)

        central_widget.setLayout(layout)

        # 設定主題顏色
        self.set_theme_colors()

    def apply_hover_effect(self, style: str) -> str:
        """為按鈕添加 hover 效果"""
        hover_style = """
            QPushButton:hover {
                background-color: #005a9e;
                color: white;
            }
        """
        return style + hover_style

    def set_theme_colors(self):
        """設定主題顏色"""
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(30, 30, 30))
        palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
        palette.setColor(QPalette.Base, QColor(30, 30, 30))
        palette.setColor(QPalette.AlternateBase, QColor(30, 30, 30))
        palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
        palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
        palette.setColor(QPalette.Text, QColor(255, 255, 255))
        palette.setColor(QPalette.Button, QColor(30, 30, 30))
        palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
        palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
        palette.setColor(QPalette.Highlight, QColor(0, 120, 215))
        palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
        self.setPalette(palette)

    def select_folder(self):
        """選擇特定資料夾"""
        folder = QFileDialog.getExistingDirectory(self, "選擇資料夾")
        if folder:
            self.search_path = folder

    def find_venvs(self):
        """查找虛擬環境並顯示"""
        if self.thread and self.thread.isRunning():
            self.thread.terminate()  # 停止之前的搜尋執行緒

        self.progress_bar.setValue(0)
        self.output_area.clear()
        self.output_area.append("⏳ 正在搜尋虛擬環境...\n")

        if hasattr(self, 'search_path'):
            search_path = self.search_path
        else:
            self.output_area.append("請選擇資料夾。")
            return

        self.thread = FindVenvsThread(search_path)
        self.thread.progress.connect(self.update_progress)
        self.thread.log.connect(self.output_area.append)
        self.thread.finished.connect(self.on_venvs_found)
        self.thread.start()

    def create_venv(self):
        """建立新的虛擬環境"""
        parent_folder = QFileDialog.getExistingDirectory(self, "選擇父資料夾")
        project_name = self.venv_name_input.text().strip()
        if parent_folder and project_name:
            self.progress_bar.setValue(0)
            self.output_area.append(f"正在建立虛擬環境，請稍候...\n{parent_folder}")
            self.create_thread = CreateVenvThread(parent_folder, project_name)
            self.create_thread.progress.connect(self.update_progress)
            self.create_thread.finished.connect(self.on_venv_created)
            self.create_thread.start()
        else:
            self.output_area.append("請選擇父資料夾並輸入專案名稱。")

    def update_progress(self, value):
        """更新進度條"""
        self.progress_bar.setValue(value)

    def on_venvs_found(self, venvs):
        """顯示所有虛擬環境"""
        self.venv_list.clear()
        self.output_area.clear()
        if venvs:
            for project_name, path in venvs:
                item_text = f"{project_name} ({path})"
                item = QListWidgetItem(item_text)
                self.venv_list.addItem(item)
                self.output_area.append(f"找到虛擬環境: {item_text}\n")
        else:
            self.output_area.append("未找到虛擬環境。")
        self.output_area.append("完成搜尋。")

    def on_venv_created(self, message, project_path):
        """當虛擬環境建立完成後顯示訊息並詢問是否啟動"""
        self.output_area.append(message)
        self.progress_bar.setValue(0)
        if project_path:
            reply = QMessageBox.question(self, '啟動虛擬環境', f'虛擬環境已建立成功！是否要啟動虛擬環境？\n{project_path}',
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.activate_venv(os.path.join(project_path, 'myenv'))
            open_vscode_reply = QMessageBox.question(self, '開啟 VSCode', f'是否要以 VSCode 開啟專案？\n{project_path}',
                                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if open_vscode_reply == QMessageBox.Yes:
                self.open_vscode(project_path)

    def activate_venv(self, venv_path):
        """啟動虛擬環境"""
        if os.name == 'nt':
            activate_script = os.path.join(venv_path, 'Scripts', 'activate.bat')
        else:
            activate_script = os.path.join(venv_path, 'bin', 'activate')
        self.output_area.append(f"啟動虛擬環境: {activate_script}")
        subprocess.run(activate_script, shell=True)

    def on_venv_item_clicked(self, item):
        """當虛擬環境項目被點擊時顯示按鈕"""
        item_text = item.text()
        project_name, path = item_text.split(" (")
        path = path.rstrip(")")

        # 清除之前的按鈕
        for i in range(self.venv_list.count()):
            widget = self.venv_list.itemWidget(self.venv_list.item(i))
            if widget:
                self.venv_list.removeItemWidget(self.venv_list.item(i))

        # 添加按鈕
        open_explorer_button = QPushButton("在檔案總管開啟")
        open_explorer_button.setFixedHeight(30)
        open_explorer_button.setFixedWidth(150)
        open_explorer_button.setFont(QFont("微軟正黑體", 16))
        open_explorer_button.clicked.connect(lambda: self.open_in_explorer(path))
    
        open_vscode_button = QPushButton("以 VSCode 開啟")
        open_vscode_button.setFixedHeight(30)
        open_vscode_button.setFixedWidth(150)
        open_vscode_button.setFont(QFont("微軟正黑體", 16))
        open_vscode_button.clicked.connect(lambda: self.open_vscode(path))

        button_layout = QHBoxLayout()
        button_layout.addWidget(open_explorer_button)
        button_layout.addWidget(open_vscode_button)

        button_widget = QWidget()
        button_widget.setLayout(button_layout)

        self.venv_list.setItemWidget(item, button_widget)

    def open_in_explorer(self, path):
        """在檔案總管中開啟"""
        parent_path = os.path.dirname(path)
        if os.name == 'nt':
            subprocess.run(["explorer", os.path.realpath(parent_path)], shell=True)
        else:
            subprocess.run(["xdg-open", parent_path], shell=True)

    def open_vscode(self, path):
        """以 VSCode 開啟專案"""
        parent_path = os.path.dirname(path)
        subprocess.run(["code", os.path.realpath(parent_path)], shell=True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VenvManager()
    window.show()
    sys.exit(app.exec_())