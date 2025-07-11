import os
import numpy as np
import tempfile
from datetime import datetime
from PyQt5.QtWidgets import (
    QDialog, QPushButton, QHBoxLayout, QVBoxLayout, QFileDialog, QLabel,
    QWidget, QGridLayout, QSizePolicy, QMessageBox, QProgressBar,
    QTextEdit, QFrame, QScrollArea, QStackedWidget, QListWidget,
    QRadioButton, QSpinBox, QColorDialog, QApplication
)
from PyQt5.QtCore import Qt, QSize, QEvent, QTranslator
from PyQt5.QtGui import QFontMetrics, QIcon, QColor, QFont

from OCC.Extend.DataExchange import read_step_file_with_names_colors
from OCC.Display.backend import load_backend

load_backend("pyqt5")
from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB
from OCC.Display import qtDisplay
from OCC.Core.Graphic3d import Graphic3d_BufferType

from similarity_calculator import process_query
from gui_widgets import CustomLabel, ClassLabel
from gui_report import ReportGenerator
from gui_utils import ButtonStyles, MessageUtils


class CADRetrievalApp(QDialog):
    def __init__(self):
        super().__init__()
        self.translator = QTranslator()
        self.current_language = 'zh'  # 默认中文
        self.title = "CAD检索平台"
        screen = QApplication.primaryScreen()
        screen_rect = screen.availableGeometry()
        self.width = int(screen_rect.width() * 0.80)
        self.height = int(screen_rect.height() * 0.95)
        self.left = int(screen_rect.width() * 0.10)
        self.top = int(screen_rect.height() * 0.05)

        self.initializeAttributes()
        self.initUI()

    def switchLanguage(self, language):
        """切换应用程序语言"""
        self.current_language = language
        QApplication.instance().removeTranslator(self.translator)

        if language == 'en':
            if self.translator.load(':/translations/english.qm'):
                QApplication.instance().installTranslator(self.translator)
            self.title = "CAD Retrieval Platform"
        else:
            self.title = "CAD检索平台"

        self.setWindowTitle(self.title)
        self.retranslateUI()

    def retranslateUI(self):
        """更新所有UI元素的文本"""
        # 更新按钮文本
        button_texts = {
            'zh': {
                "上传模型": "上传模型",
                "上传特征文件": "上传特征文件",
                "上传数据库特征": "上传数据库特征",
                "设置检索路径": "设置检索路径",
                "执行检索": "执行检索",
                "设置颜色": "设置颜色",
                "切换显示模式": "切换显示模式",
                "保存结果": "保存结果",
                "生成报告": "生成报告",
                "清除显示": "清除显示",
                "帮助": "帮助"
            },
            'en': {
                "上传模型": "Upload Model",
                "上传特征文件": "Upload Feature",
                "上传数据库特征": "Upload Database",
                "设置检索路径": "Set Search Path",
                "执行检索": "Execute Search",
                "设置颜色": "Set Colors",
                "切换显示模式": "Toggle Display",
                "保存结果": "Save Results",
                "生成报告": "Generate Report",
                "清除显示": "Clear Display",
                "帮助": "Help"
            }
        }

        for text, btn in self.button_refs.items():
            btn.setText(button_texts[self.current_language].get(text, text))

        # 更新其他UI元素
        if self.current_language == 'en':
            self.uploaded_class_label.setText("Uploaded Class: None")
            self.history_button.setText("Search History")
            self.single_file_rb.setText("Single Database File")
            self.multiple_files_rb.setText("Multiple Feature Files")
            self.prevButton.setText("◀ Previous")
            self.nextButton.setText("Next ▶")
            self.resultNumSpin.setSuffix(" results")
            self.pageLabel.setText(f"Page {self.current_page + 1} / {self.total_pages}")
            for label in self.labels:
                label.setText("Similarity: 0.0")
            for class_label in self.class_labels:
                class_label.setText("Class: None")
        else:
            self.uploaded_class_label.setText("上传类别: 无")
            self.history_button.setText("检索历史")
            self.single_file_rb.setText("单个数据库文件")
            self.multiple_files_rb.setText("多个特征文件")
            self.prevButton.setText("◀ 上一页")
            self.nextButton.setText("下一页 ▶")
            self.resultNumSpin.setSuffix(" 个结果")
            self.pageLabel.setText(f"第 {self.current_page + 1} 页 / 共 {self.total_pages} 页")
            for label in self.labels:
                label.setText("相似度: 0.0")
            for class_label in self.class_labels:
                class_label.setText("类别: 无")

    def initializeAttributes(self):
        self.ais_list = []
        self.labels = []
        self.class_labels = []
        self.canvases = []
        self.current_class = None
        self.feature_file = None
        self.database_file = None
        self.database_folder = None
        self.search_path = ""
        self.result_paths = []
        self.result_scores = []
        self.result_classes = []
        self.current_page = 0
        self.total_pages = 0
        self.show_3d_models = True
        self.text_results = ""
        self.max_results = 8
        self.step_file_path = None
        self.search_history = []
        self.max_history_items = 20
        self.history_panel_height = 80
        self.correct_color = Quantity_Color(0.0, 1.0, 0.0, Quantity_TOC_RGB)
        self.incorrect_color = Quantity_Color(1.0, 0.0, 0.0, Quantity_TOC_RGB)
        self.button_refs = {}
        self.setupTempDir()
        self.report_generator = ReportGenerator(self)

    def setupTempDir(self):
        self.temp_dir = os.path.normpath(os.path.join(os.path.expanduser("~"), "cad_temp"))
        try:
            os.makedirs(self.temp_dir, exist_ok=True)
            os.chmod(self.temp_dir, 0o755)
        except Exception as e:
            self.temp_dir = tempfile.mkdtemp()
            self.logMessage(f"无法创建自定义临时目录，使用系统临时目录: {self.temp_dir}" if self.current_language == 'zh'
                            else f"Failed to create temp dir, using system temp: {self.temp_dir}")

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.setWindowIcon(QIcon('1.ico'))
        self.createMainLayout()
        self.show()

    def createMainLayout(self):
        mainLayout = QHBoxLayout()
        mainLayout.setSpacing(10)
        mainLayout.setContentsMargins(5, 5, 5, 5)
        self.setLayout(mainLayout)

        # 左侧面板
        leftPanel = self.createLeftPanel()

        # 右侧面板
        rightPanel = self.createRightPanel()

        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)

        # 创建一个容器来包装右侧面板和语言按钮
        rightContainer = QWidget()
        rightContainerLayout = QVBoxLayout(rightContainer)
        rightContainerLayout.setContentsMargins(0, 0, 0, 0)
        rightContainerLayout.setSpacing(0)

        # 添加语言切换按钮到右上角
        lang_btn = QPushButton("EN/中文")
        lang_btn.setFixedSize(80, 30)  # 设置固定大小确保显示完整
        lang_btn.setStyleSheet("""
            QPushButton {
                font-size: 10pt;
                padding: 2px;
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        lang_btn.clicked.connect(lambda: self.switchLanguage('en' if self.current_language == 'zh' else 'zh'))

        # 创建一个水平布局来右对齐按钮
        buttonLayout = QHBoxLayout()
        buttonLayout.addStretch()  # 添加伸缩项
        buttonLayout.addWidget(lang_btn)
        buttonLayout.setContentsMargins(0, 0, 5, 5)  # 设置右边距和下边距

        rightContainerLayout.addLayout(buttonLayout)  # 添加按钮布局
        rightContainerLayout.addWidget(rightPanel, 1)  # 添加右侧面板内容

        # 将各部分添加到主布局
        mainLayout.addWidget(leftPanel)
        mainLayout.addWidget(separator)
        mainLayout.addWidget(rightContainer, 1)  # 使用容器替代直接添加rightPanel

        self.setToolTips()

    def createLeftPanel(self):
        leftPanel = QWidget()
        leftPanel.setMaximumWidth(int(self.width * 0.42))
        leftLayout = QVBoxLayout(leftPanel)
        leftLayout.setSpacing(8)
        leftLayout.setContentsMargins(0, 0, 0, 0)

        self.uploaded_class_label = QLabel("上传类别: 无" if self.current_language == 'zh' else "Uploaded Class: None")
        self.uploaded_class_label.setAlignment(Qt.AlignCenter)
        self.uploaded_class_label.setStyleSheet("""
            QLabel {
                font-size: 12pt;
                font-weight: bold;
                color: #2c3e50;
                padding: 5px;
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                background-color: #ecf0f1;
            }
        """)
        self.uploaded_class_label.setWordWrap(True)
        leftLayout.addWidget(self.uploaded_class_label)

        self.history_button = QPushButton("检索历史" if self.current_language == 'zh' else "Search History")
        self.history_button.setStyleSheet("""
            QPushButton {
                font-size: 11pt;
                padding: 5px;
                background-color: #e3f2fd;
                border: 1px solid #bbdefb;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #bbdefb;
            }
        """)
        leftLayout.addWidget(self.history_button)

        self.history_panel = QWidget()
        self.history_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.history_panel.setMaximumHeight(self.history_panel_height)

        history_layout = QVBoxLayout(self.history_panel)
        history_layout.setContentsMargins(0, 0, 0, 0)
        history_layout.setSpacing(0)

        self.history_list = QListWidget()
        self.history_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.history_list.itemClicked.connect(self.replaySearch)
        history_layout.addWidget(self.history_list)

        leftLayout.addWidget(self.history_panel)

        self.db_format_group = QWidget()
        db_format_layout = QHBoxLayout(self.db_format_group)
        self.single_file_rb = QRadioButton("单个数据库文件" if self.current_language == 'zh' else "Single Database File")
        self.multiple_files_rb = QRadioButton("多个特征文件" if self.current_language == 'zh' else "Multiple Feature Files")
        self.single_file_rb.setChecked(True)
        db_format_layout.addWidget(self.single_file_rb)
        db_format_layout.addWidget(self.multiple_files_rb)
        leftLayout.addWidget(self.db_format_group)

        controlGrid = self.createControlGrid()
        leftLayout.addLayout(controlGrid)

        self.progressBar = QProgressBar()
        self.progressBar.setMaximum(100)
        self.progressBar.setValue(0)
        self.progressBar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ccc;
                border-radius: 5px;
                height: 12px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
            }
        """)
        leftLayout.addWidget(self.progressBar)

        self.logArea = QTextEdit()
        self.logArea.setReadOnly(True)
        self.logArea.setMaximumHeight(60)
        self.logArea.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ccc;
                border-radius: 5px;
                font-size: 10pt;
            }
        """)
        leftLayout.addWidget(self.logArea)

        self.mainCanvas = qtDisplay.qtViewer3d(self)
        self.mainCanvas.setMinimumHeight(150)
        leftLayout.addWidget(self.mainCanvas, 1)

        return leftPanel

    def createControlGrid(self):
        controlGrid = QGridLayout()
        controlGrid.setSpacing(10)
        controlGrid.setContentsMargins(5, 5, 5, 5)

        main_buttons = [
            ("上传模型", self.loadSTEP),
            ("上传特征文件", self.loadFeatureFile),
            ("上传数据库特征", self.loadDatabaseFile),
            ("设置检索路径", self.setSearchPath),
            ("执行检索", self.performSearch)
        ]

        for i, (text, callback) in enumerate(main_buttons[:4]):
            btn = QPushButton(text)
            btn.setMinimumHeight(36)
            ButtonStyles.setDefaultStyle(btn)
            btn.clicked.connect(callback)
            row = i // 2
            col = i % 2
            controlGrid.addWidget(btn, row, col, 1, 1)
            self.button_refs[text] = btn

        execute_btn = QPushButton(main_buttons[4][0])
        execute_btn.setMinimumHeight(42)
        ButtonStyles.setExecuteStyle(execute_btn)
        execute_btn.clicked.connect(main_buttons[4][1])
        controlGrid.addWidget(execute_btn, 2, 0, 1, 2)
        self.button_refs[main_buttons[4][0]] = execute_btn

        separator1 = QFrame()
        separator1.setFrameShape(QFrame.HLine)
        separator1.setFrameShadow(QFrame.Sunken)
        controlGrid.addWidget(separator1, 3, 0, 1, 2)

        utility_buttons = [
            ("设置颜色", self.showColorSettings),
            ("切换显示模式", self.toggleDisplayMode),
            ("保存结果", self.saveResults),
            ("生成报告", self.generateReport)
        ]

        auxiliary_buttons = [
            ("清除显示", self.clearDisplay),
            ("帮助", self.showHelp)
        ]

        for i, (text, callback) in enumerate(utility_buttons):
            btn = QPushButton(text)
            btn.setMinimumHeight(32)
            ButtonStyles.setUtilityStyle(btn)
            btn.clicked.connect(callback)
            row = 4 + i // 2
            col = i % 2
            controlGrid.addWidget(btn, row, col)
            self.button_refs[text] = btn

        separator2 = QFrame()
        separator2.setFrameShape(QFrame.HLine)
        separator2.setFrameShadow(QFrame.Sunken)
        controlGrid.addWidget(separator2, 6, 0, 1, 2)

        for i, (text, callback) in enumerate(auxiliary_buttons):
            btn = QPushButton(text)
            btn.setMinimumHeight(32)
            ButtonStyles.setHelpStyle(btn)
            btn.clicked.connect(callback)
            row = 7 + i // 2
            col = i % 2
            controlGrid.addWidget(btn, row, col)
            self.button_refs[text] = btn

        self.resultNumSpin = QSpinBox()
        self.resultNumSpin.setRange(1, 100)
        self.resultNumSpin.setValue(8)
        self.resultNumSpin.setSuffix(" 个结果" if self.current_language == 'zh' else " results")
        self.resultNumSpin.setStyleSheet("""
            QSpinBox {
                font-size: 11pt;
                padding: 3px;
            }
        """)
        controlGrid.addWidget(QLabel("返回结果数:" if self.current_language == 'zh' else "Results count:"), 9, 0)
        controlGrid.addWidget(self.resultNumSpin, 9, 1)

        return controlGrid

    def createRightPanel(self):
        rightPanel = QWidget()
        rightLayout = QVBoxLayout(rightPanel)
        rightLayout.setSpacing(8)
        rightLayout.setContentsMargins(0, 0, 0, 0)

        self.resultStack = QStackedWidget()

        modelWidget = QWidget()
        modelLayout = QVBoxLayout(modelWidget)
        modelLayout.setContentsMargins(0, 0, 0, 0)

        resultsGrid = QGridLayout()
        resultsGrid.setSpacing(8)
        resultsGrid.setContentsMargins(3, 3, 3, 3)

        for i in range(8):
            row, col = divmod(i, 4)
            canvas = qtDisplay.qtViewer3d(self)
            canvas.setMinimumHeight(140)

            label_layout = QVBoxLayout()
            label_layout.setSpacing(2)
            label_layout.setContentsMargins(2, 2, 2, 2)

            similarity_label = CustomLabel("相似度: 0.0" if self.current_language == 'zh' else "Similarity: 0.0")
            class_label = ClassLabel("类别: 无" if self.current_language == 'zh' else "Class: None")

            label_layout.addWidget(similarity_label)
            label_layout.addWidget(class_label)

            frame = QWidget()
            frame.setStyleSheet("""
                QWidget {
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    background-color: #f9f9f9;
                }
            """)
            frameLayout = QVBoxLayout(frame)
            frameLayout.setContentsMargins(2, 2, 2, 2)
            frameLayout.setSpacing(3)
            frameLayout.addWidget(canvas, 1)
            frameLayout.addLayout(label_layout)

            self.canvases.append(canvas)
            self.labels.append(similarity_label)
            self.class_labels.append(class_label)
            resultsGrid.addWidget(frame, row, col)

        scrollArea = QScrollArea()
        scrollArea.setWidgetResizable(True)
        scrollContent = QWidget()
        scrollContent.setLayout(resultsGrid)
        scrollArea.setWidget(scrollContent)
        modelLayout.addWidget(scrollArea, 1)

        pageControl = QHBoxLayout()
        pageControl.setContentsMargins(0, 3, 0, 0)

        self.prevButton = QPushButton("◀ 上一页" if self.current_language == 'zh' else "◀ Previous")
        self.prevButton.setFixedSize(90, 28)
        self.prevButton.setEnabled(False)
        self.prevButton.clicked.connect(self.showPreviousPage)

        self.pageLabel = QLabel(f"第 0 页 / 共 0 页" if self.current_language == 'zh' else "Page 0 / 0")
        self.pageLabel.setAlignment(Qt.AlignCenter)

        self.nextButton = QPushButton("下一页 ▶" if self.current_language == 'zh' else "Next ▶")
        self.nextButton.setFixedSize(90, 28)
        self.nextButton.setEnabled(False)
        self.nextButton.clicked.connect(self.showNextPage)

        pageControl.addWidget(self.prevButton)
        pageControl.addWidget(self.pageLabel)
        pageControl.addWidget(self.nextButton)
        modelLayout.addLayout(pageControl)

        self.resultStack.addWidget(modelWidget)

        self.textResultWidget = QTextEdit()
        self.textResultWidget.setReadOnly(True)
        self.textResultWidget.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 5px;
                font-size: 10pt;
                padding: 5px;
            }
        """)
        self.resultStack.addWidget(self.textResultWidget)

        self.resultStack.setCurrentIndex(0)
        rightLayout.addWidget(self.resultStack, 1)

        return rightPanel

    def setToolTips(self):
        tooltips = {
            'zh': {
                "上传模型": "加载要检索的STEP模型文件",
                "上传特征文件": "加载查询模型对应的特征文件(.npy)",
                "上传数据库特征": "加载数据库特征(单个文件或多个文件)",
                "设置检索路径": "指定存放检索结果STEP文件的目录",
                "执行检索": "开始检索过程",
                "设置颜色": "自定义匹配/不匹配模型的显示颜色",
                "切换显示模式": "在3D模型和文本结果之间切换",
                "保存结果": "将检索结果导出为文本文件",
                "生成报告": "生成PDF或HTML格式的检索报告",
                "清除显示": "重置所有显示内容",
                "帮助": "显示使用说明文档"
            },
            'en': {
                "上传模型": "Load STEP model file for retrieval",
                "上传特征文件": "Load feature file (.npy) for query model",
                "上传数据库特征": "Load database features (single file or multiple files)",
                "设置检索路径": "Specify directory containing result STEP files",
                "执行检索": "Start search process",
                "设置颜色": "Customize colors for matched/mismatched models",
                "切换显示模式": "Toggle between 3D models and text results",
                "保存结果": "Export search results as text file",
                "生成报告": "Generate PDF or HTML report",
                "清除显示": "Reset all displays",
                "帮助": "Show user manual"
            }
        }

        for text, btn in self.button_refs.items():
            btn.setToolTip(tooltips[self.current_language].get(text, ""))

    def replaySearch(self, list_item):
        index = self.history_list.row(list_item)
        history_item = self.search_history[-(index + 1)]

        self.feature_file = history_item["feature_file"]
        self.search_path = history_item["search_path"]
        self.current_class = history_item["class"]
        self.step_file_path = history_item.get("step_file")

        if history_item["is_single_file"]:
            self.single_file_rb.setChecked(True)
            self.database_file = history_item["database_input"]
        else:
            self.multiple_files_rb.setChecked(True)
            self.database_folder = history_item["database_input"]

        self.uploaded_class_label.setText(
            f"上传类别: {self.current_class}" if self.current_language == 'zh'
            else f"Uploaded Class: {self.current_class}"
        )
        ButtonStyles.setUploadedStyle(self.button_refs["上传特征文件"])
        ButtonStyles.setUploadedStyle(self.button_refs["设置检索路径"])
        if history_item["is_single_file"]:
            ButtonStyles.setUploadedStyle(self.button_refs["上传数据库特征"])
        else:
            ButtonStyles.setUploadedStyle(self.button_refs["上传数据库特征"])

        if self.step_file_path and os.path.exists(self.step_file_path):
            try:
                self.mainCanvas._display.EraseAll()
                shapes = read_step_file_with_names_colors(self.step_file_path)
                for shape, (label, color) in shapes.items():
                    ais = self.mainCanvas._display.DisplayShape(shape, update=True)
                    self.ais_list.append(ais)
                self.mainCanvas._display.FitAll()
                self.logMessage(f"已加载模型文件: {self.step_file_path}" if self.current_language == 'zh'
                                else f"Loaded model file: {self.step_file_path}")
                ButtonStyles.setUploadedStyle(self.button_refs["上传模型"])
            except Exception as e:
                self.logMessage(f"加载模型文件时出错: {str(e)}" if self.current_language == 'zh'
                                else f"Error loading model file: {str(e)}")
        else:
            self.logMessage("警告: 未找到对应的STEP模型文件" if self.current_language == 'zh'
                            else "Warning: Corresponding STEP file not found")

        self.performSearch()

    def addSearchHistory(self, query_class, result_count):
        timestamp = datetime.now().strftime("%m/%d %H:%M")

        if len(self.search_history) >= self.max_history_items:
            self.search_history.pop(0)

        self.search_history.append({
            "timestamp": timestamp,
            "class": query_class,
            "feature_file": self.feature_file,
            "search_path": self.search_path,
            "result_count": result_count,
            "is_single_file": self.single_file_rb.isChecked(),
            "database_input": self.database_file if self.single_file_rb.isChecked() else self.database_folder,
            "step_file": self.step_file_path
        })

        self.updateHistoryList()

    def updateHistoryList(self):
        self.history_list.clear()
        for item in reversed(self.search_history):
            if self.current_language == 'zh':
                self.history_list.addItem(
                    f"{item['timestamp']} - 查询: {item['class']} ({item['result_count']}结果)"
                )
            else:
                self.history_list.addItem(
                    f"{item['timestamp']} - Query: {item['class']} ({item['result_count']}results)"
                )

    def loadSTEP(self):
        fileName, _ = QFileDialog.getOpenFileName(
            self,
            "打开STEP文件" if self.current_language == 'zh' else "Open STEP File",
            "",
            "STEP文件 (*.step *.stp)" if self.current_language == 'zh' else "STEP Files (*.step *.stp)"
        )
        if fileName:
            try:
                self.step_file_path = fileName
                ButtonStyles.setUploadedStyle(self.button_refs["上传模型"])

                baseName = os.path.splitext(os.path.basename(fileName))[0]
                lastUnderscoreIndex = baseName.rfind('_')
                self.current_class = baseName[:lastUnderscoreIndex] if lastUnderscoreIndex != -1 else baseName
                self.uploaded_class_label.setText(
                    f"上传类别: {self.current_class}" if self.current_language == 'zh'
                    else f"Uploaded Class: {self.current_class}"
                )

                self.mainCanvas._display.EraseAll()
                shapes = read_step_file_with_names_colors(fileName)
                for shape, (label, color) in shapes.items():
                    ais = self.mainCanvas._display.DisplayShape(shape, update=True)
                    self.ais_list.append(ais)
                self.mainCanvas._display.FitAll()

                self.logMessage(f"已加载文件: {fileName}" if self.current_language == 'zh'
                                else f"Loaded file: {fileName}")
                self.logMessage(f"当前类别: {self.current_class}" if self.current_language == 'zh'
                                else f"Current class: {self.current_class}")
            except Exception as e:
                MessageUtils.showErrorMessage(self,
                                              f"加载模型出错: {str(e)}" if self.current_language == 'zh'
                                              else f"Error loading model: {str(e)}")

    def loadFeatureFile(self):
        self.feature_file, _ = QFileDialog.getOpenFileName(
            self,
            "打开特征文件" if self.current_language == 'zh' else "Open Feature File",
            "",
            "Numpy文件 (*.npy)" if self.current_language == 'zh' else "Numpy Files (*.npy)"
        )
        if self.feature_file:
            ButtonStyles.setUploadedStyle(self.button_refs["上传特征文件"])
            self.logMessage(f"已加载特征文件: {self.feature_file}" if self.current_language == 'zh'
                            else f"Loaded feature file: {self.feature_file}")

    def loadDatabaseFile(self):
        if self.single_file_rb.isChecked():
            self.database_file, _ = QFileDialog.getOpenFileName(
                self,
                "打开数据库特征文件" if self.current_language == 'zh' else "Open Database Feature File",
                "",
                "Numpy文件 (*.npy)" if self.current_language == 'zh' else "Numpy Files (*.npy)"
            )
            if self.database_file:
                ButtonStyles.setUploadedStyle(self.button_refs["上传数据库特征"])
                self.logMessage(f"已加载数据库特征文件: {self.database_file}" if self.current_language == 'zh'
                                else f"Loaded database feature file: {self.database_file}")
        else:
            self.database_folder = QFileDialog.getExistingDirectory(
                self,
                "选择特征文件目录" if self.current_language == 'zh' else "Select Feature Files Directory"
            )
            if self.database_folder:
                ButtonStyles.setUploadedStyle(self.button_refs["上传数据库特征"])
                self.logMessage(f"已加载特征文件目录: {self.database_folder}" if self.current_language == 'zh'
                                else f"Loaded feature files directory: {self.database_folder}")

    def setSearchPath(self):
        self.search_path = QFileDialog.getExistingDirectory(
            self,
            "选择检索路径" if self.current_language == 'zh' else "Select Search Path"
        )
        if self.search_path:
            ButtonStyles.setUploadedStyle(self.button_refs["设置检索路径"])
            self.logMessage(f"设置检索路径为: {self.search_path}" if self.current_language == 'zh'
                            else f"Search path set to: {self.search_path}")

    def showColorSettings(self):
        def quantity_to_qcolor(qt_color):
            return QColor(
                int(qt_color.Red() * 255),
                int(qt_color.Green() * 255),
                int(qt_color.Blue() * 255)
            )

        def qcolor_to_quantity(qcolor):
            return Quantity_Color(
                qcolor.red() / 255.0,
                qcolor.green() / 255.0,
                qcolor.blue() / 255.0,
                Quantity_TOC_RGB
            )

        current_correct = quantity_to_qcolor(self.correct_color)
        current_incorrect = quantity_to_qcolor(self.incorrect_color)

        correct_color = QColorDialog.getColor(
            current_correct,
            self,
            "选择正确匹配的颜色" if self.current_language == 'zh' else "Select Color for Correct Matches",
            options=QColorDialog.ShowAlphaChannel
        )

        if correct_color.isValid():
            incorrect_color = QColorDialog.getColor(
                current_incorrect,
                self,
                "选择错误匹配的颜色" if self.current_language == 'zh' else "Select Color for Incorrect Matches",
                options=QColorDialog.ShowAlphaChannel
            )

            if incorrect_color.isValid():
                self.correct_color = qcolor_to_quantity(correct_color)
                self.incorrect_color = qcolor_to_quantity(incorrect_color)
                self.logMessage("颜色设置已更新" if self.current_language == 'zh'
                                else "Color settings updated")

                if self.result_paths:
                    self.showCurrentPage()

    def toggleDisplayMode(self):
        self.show_3d_models = not self.show_3d_models
        if self.show_3d_models:
            self.resultStack.setCurrentIndex(0)
            self.logMessage("显示模式: 3D模型" if self.current_language == 'zh'
                            else "Display mode: 3D Models")
        else:
            self.resultStack.setCurrentIndex(1)
            self.logMessage("显示模式: 文本结果" if self.current_language == 'zh'
                            else "Display mode: Text Results")

        if self.result_paths:
            self.showCurrentPage()

    def saveResults(self):
        if not self.result_paths:
            MessageUtils.showErrorMessage(
                self,
                "没有可保存的结果" if self.current_language == 'zh'
                else "No results to save"
            )
            return

        fileName, _ = QFileDialog.getSaveFileName(
            self,
            "保存结果" if self.current_language == 'zh' else "Save Results",
            "",
            "文本文件 (*.txt)" if self.current_language == 'zh' else "Text Files (*.txt)"
        )
        if fileName:
            try:
                with open(fileName, 'w', encoding='utf-8') as f:
                    f.write(self.text_results)
                self.logMessage(f"结果已保存到: {fileName}" if self.current_language == 'zh'
                                else f"Results saved to: {fileName}")
            except Exception as e:
                MessageUtils.showErrorMessage(
                    self,
                    f"保存文件时出错: {str(e)}" if self.current_language == 'zh'
                    else f"Error saving file: {str(e)}"
                )

    def generateReport(self):
        self.report_generator.generateReport()

    def performSearch(self):
        if not self.feature_file or ((not self.database_file and self.single_file_rb.isChecked()) or
                                     (not hasattr(self,
                                                  'database_folder') and not self.single_file_rb.isChecked())) or not self.search_path:
            MessageUtils.showErrorMessage(
                self,
                "请确保所有文件和路径都已设置" if self.current_language == 'zh'
                else "Please make sure all files and paths are set"
            )
            return

        try:
            self.progressBar.setValue(0)
            input_features = np.load(self.feature_file, allow_pickle=True)

            if self.single_file_rb.isChecked():
                database_features = np.load(self.database_file, allow_pickle=True)
                self.result_paths, self.result_scores = process_query(
                    input_features, database_features, self.search_path, True)
            else:
                self.result_paths, self.result_scores = process_query(
                    input_features, self.database_folder, self.search_path, False)

            max_results = self.resultNumSpin.value()

            if len(self.result_paths) > max_results:
                self.result_paths = self.result_paths[:max_results]
                self.result_scores = self.result_scores[:max_results]

            self.result_classes = []
            for path in self.result_paths:
                baseName = os.path.splitext(os.path.basename(path))[0]
                lastUnderscoreIndex = baseName.rfind('_')
                result_class = baseName[:lastUnderscoreIndex] if lastUnderscoreIndex != -1 else baseName
                self.result_classes.append(result_class)

            self.result_scores = [(100 - score) for score in self.result_scores]

            self.current_page = 0
            self.total_pages = (len(self.result_paths) + 7) // 8

            self.updatePageControls()
            self.showCurrentPage()

            self.addSearchHistory(self.current_class, len(self.result_paths))

            self.progressBar.setValue(100)
            self.logMessage(
                f"检索完成，找到 {len(self.result_paths)} 个结果" if self.current_language == 'zh'
                else f"Search completed, found {len(self.result_paths)} results"
            )
        except Exception as e:
            MessageUtils.showErrorMessage(
                self,
                f"检索过程中出错: {str(e)}" if self.current_language == 'zh'
                else f"Error during search: {str(e)}"
            )

    def showCurrentPage(self):
        for i in range(8):
            self.canvases[i]._display.Context.EraseAll(True)
            self.canvases[i]._display.FitAll()
            self.labels[i].setText("相似度: 0.0" if self.current_language == 'zh' else "Similarity: 0.0")
            self.class_labels[i].setText("类别: 无" if self.current_language == 'zh' else "Class: None")

        if self.current_language == 'zh':
            self.text_results = "检索结果:\n"
            self.text_results += f"查询类别: {self.current_class}\n"
            self.text_results += f"总结果数: {len(self.result_paths)}\n\n"
        else:
            self.text_results = "Search Results:\n"
            self.text_results += f"Query Class: {self.current_class}\n"
            self.text_results += f"Total Results: {len(self.result_paths)}\n\n"

        self.textResultWidget.clear()

        if self.show_3d_models:
            start_idx = self.current_page * 8
            end_idx = min(start_idx + 8, len(self.result_paths))

            for i in range(start_idx, end_idx):
                canvas_idx = i - start_idx
                path = self.result_paths[i]
                similarity = self.result_scores[i]
                result_class = self.result_classes[i]

                try:
                    shapes = read_step_file_with_names_colors(path)
                    if canvas_idx < 8:
                        canvas = self.canvases[canvas_idx]
                        display = canvas._display
                        display.EraseAll()

                        for shape, (label, color) in shapes.items():
                            if result_class != self.current_class:
                                color = self.incorrect_color
                            else:
                                color = self.correct_color

                            ais = display.DisplayColoredShape(shape, color=color, update=True)
                            display.FitAll()
                            self.ais_list.append(ais)

                        self.labels[canvas_idx].setText(
                            f"相似度: {similarity:.2f}%" if self.current_language == 'zh'
                            else f"Similarity: {similarity:.2f}%"
                        )
                        self.class_labels[canvas_idx].setText(
                            f"类别: {result_class}" if self.current_language == 'zh'
                            else f"Class: {result_class}"
                        )
                except Exception as e:
                    self.logMessage(
                        f"无法加载文件 {path}: {str(e)}" if self.current_language == 'zh'
                        else f"Failed to load file {path}: {str(e)}"
                    )
                    self.labels[canvas_idx].setText(
                        "加载失败" if self.current_language == 'zh'
                        else "Load failed"
                    )
                    self.class_labels[canvas_idx].setText(
                        "类别: 未知" if self.current_language == 'zh'
                        else "Class: Unknown"
                    )

                if self.current_language == 'zh':
                    self.text_results += f"结果 {i + 1}:\n"
                    self.text_results += f"文件: {os.path.basename(path)}\n"
                    self.text_results += f"路径: {path}\n"
                    self.text_results += f"相似度: {similarity:.2f}%\n"
                    self.text_results += f"类别: {result_class}\n"
                    self.text_results += f"匹配状态: {'匹配' if result_class == self.current_class else '不匹配'}\n\n"
                else:
                    self.text_results += f"Result {i + 1}:\n"
                    self.text_results += f"File: {os.path.basename(path)}\n"
                    self.text_results += f"Path: {path}\n"
                    self.text_results += f"Similarity: {similarity:.2f}%\n"
                    self.text_results += f"Class: {result_class}\n"
                    self.text_results += f"Match Status: {'Match' if result_class == self.current_class else 'Mismatch'}\n\n"

            self.pageLabel.setText(
                f"第 {self.current_page + 1} 页 / 共 {self.total_pages} 页" if self.current_language == 'zh'
                else f"Page {self.current_page + 1} / {self.total_pages}"
            )
        else:
            if self.current_language == 'zh':
                self.textResultWidget.append(f"检索结果 (共 {len(self.result_paths)} 个):\n")
            else:
                self.textResultWidget.append(f"Search Results (Total {len(self.result_paths)}):\n")

            for i in range(len(self.result_paths)):
                path = self.result_paths[i]
                similarity = self.result_scores[i]
                result_class = self.result_classes[i]

                if self.current_language == 'zh':
                    self.textResultWidget.append(f"结果 {i + 1}:")
                    self.textResultWidget.append(f"文件: {os.path.basename(path)}")
                    self.textResultWidget.append(f"路径: {path}")
                    self.textResultWidget.append(f"相似度: {similarity:.2f}%")
                    self.textResultWidget.append(f"类别: {result_class}")
                    self.textResultWidget.append(f"匹配状态: {'匹配' if result_class == self.current_class else '不匹配'}\n")
                else:
                    self.textResultWidget.append(f"Result {i + 1}:")
                    self.textResultWidget.append(f"File: {os.path.basename(path)}")
                    self.textResultWidget.append(f"Path: {path}")
                    self.textResultWidget.append(f"Similarity: {similarity:.2f}%")
                    self.textResultWidget.append(f"Class: {result_class}")
                    self.textResultWidget.append(
                        f"Match Status: {'Match' if result_class == self.current_class else 'Mismatch'}\n")

                if self.current_language == 'zh':
                    self.text_results += f"结果 {i + 1}:\n"
                    self.text_results += f"文件: {os.path.basename(path)}\n"
                    self.text_results += f"路径: {path}\n"
                    self.text_results += f"相似度: {similarity:.2f}%\n"
                    self.text_results += f"类别: {result_class}\n"
                    self.text_results += f"匹配状态: {'匹配' if result_class == self.current_class else '不匹配'}\n\n"
                else:
                    self.text_results += f"Result {i + 1}:\n"
                    self.text_results += f"File: {os.path.basename(path)}\n"
                    self.text_results += f"Path: {path}\n"
                    self.text_results += f"Similarity: {similarity:.2f}%\n"
                    self.text_results += f"Class: {result_class}\n"
                    self.text_results += f"Match Status: {'Match' if result_class == self.current_class else 'Mismatch'}\n\n"

        self.updatePageControls()

    def updatePageControls(self):
        self.prevButton.setEnabled(self.current_page > 0)
        self.nextButton.setEnabled(self.current_page < self.total_pages - 1 and self.total_pages > 1)

    def showPreviousPage(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.showCurrentPage()

    def showNextPage(self):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.showCurrentPage()

    def clearDisplay(self):
        self.mainCanvas._display.Context.EraseAll(True)
        self.mainCanvas._display.FitAll()
        for canvas in self.canvases:
            canvas._display.Context.EraseAll(True)
            canvas._display.FitAll()
        self.ais_list = []
        for label in self.labels:
            label.setText("相似度: 0.0" if self.current_language == 'zh' else "Similarity: 0.0")
        for class_label in self.class_labels:
            class_label.setText("类别: 无" if self.current_language == 'zh' else "Class: None")
        self.uploaded_class_label.setText("上传类别: 无" if self.current_language == 'zh' else "Uploaded Class: None")
        self.progressBar.setValue(0)
        self.logArea.clear()
        self.result_paths = []
        self.result_scores = []
        self.result_classes = []
        self.current_class = None
        self.current_page = 0
        self.total_pages = 0
        self.pageLabel.setText("第 0 页 / 共 0 页" if self.current_language == 'zh' else "Page 0 / 0")
        self.prevButton.setEnabled(False)
        self.nextButton.setEnabled(False)
        self.text_results = ""
        self.textResultWidget.clear()
        self.show_3d_models = True
        self.resultStack.setCurrentIndex(0)
        self.step_file_path = None

        for text in ["上传模型", "上传特征文件", "上传数据库特征", "设置检索路径"]:
            if text in self.button_refs:
                ButtonStyles.setDefaultStyle(self.button_refs[text])

    def showHelp(self):
        # 根据当前语言选择帮助文本
        if self.current_language == 'en':
            help_text = """
            <h1 style='color: #2c3e50;'>CAD Retrieval Platform User Manual</h1>

            <h2 style='color: #3498db;'>Search Logic</h2>
            <p>The search logic is based on feature vector similarity calculation:</p>
            <ol>
                <li><b>Feature Extraction</b>: Each CAD model (STEP file) corresponds to a feature vector file (.npy)</li>
                <li><b>Similarity Calculation</b>:
                    <ul>
                        <li>Supports Euclidean distance and cosine similarity</li>
                        <li>Feature vectors are L2 normalized</li>
                        <li>Calculate similarity scores between query and database features</li>
                        <li>Score range: 0-100 (100 means most similar)</li>
                    </ul>
                </li>
                <li><b>Result Sorting</b>: Sort by similarity score</li>
                <li><b>Class Matching</b>: Check if result belongs to same class as query (by filename prefix)</li>
            </ol>

            <h2 style='color: #3498db;'>File Requirements</h2>
            <p>System requires the following files:</p>
            <ul>
                <li><b>STEP Model Files</b>:
                    <ul>
                        <li>For 3D model display</li>
                        <li>Filename format: "class_id.step" or "class_id.stp"</li>
                        <li>Class is determined by prefix (before underscore)</li>
                    </ul>
                </li>
                <li><b>Feature Files (.npy)</b>:
                    <ul>
                        <li>Contain feature vectors extracted from CAD models</li>
                        <li>Each STEP file should have corresponding feature file</li>
                    </ul>
                </li>
                <li><b>Database Files</b>:
                    <ul>
                        <li><b>Single database file</b>: Combined .npy file</li>
                        <li><b>Multiple feature files</b>: Directory containing .npy files</li>
                    </ul>
                </li>
            </ul>

            <h2 style='color: #3498db;'>Operation Guide</h2>
            <ol>
                <li><b>Upload Model</b>: Load STEP file for retrieval</li>
                <li><b>Upload Feature</b>: Load corresponding .npy feature file</li>
                <li><b>Upload Database</b>: Load database features (single file or directory)</li>
                <li><b>Set Search Path</b>: Specify directory containing result STEP files</li>
                <li><b>Execute Search</b>: Start retrieval process</li>
                <li><b>Generate Report</b>: Create PDF/HTML report with model screenshots</li>
            </ol>

            <h2 style='color: #3498db;'>Additional Features</h2>
            <ul>
                <li><b>Clear Display</b>: Reset all displays</li>
                <li><b>Set Colors</b>: Customize colors for matched/mismatched models</li>
                <li><b>Toggle Display</b>: Switch between 3D models and text results</li>
                <li><b>Save Results</b>: Export results as text file</li>
                <li><b>Generate Report</b>: Create PDF/HTML/image format reports</li>
                <li><b>Search History</b>: View and replay previous searches</li>
            </ul>

            <h2 style='color: #3498db;'>Notes</h2>
            <ul>
                <li>Ensure STEP and feature files have consistent naming</li>
                <li>Database features should correspond to STEP files in search path</li>
                <li>Large databases may require longer processing time</li>
                <li>Report generation requires sufficient disk space</li>
                <li>Image reports require Pillow library (pip install pillow)</li>
            </ul>
            """
        else:
            help_text = """
            <h1 style='color: #2c3e50;'>CAD检索平台使用说明书</h1>

            <h2 style='color: #3498db;'>检索逻辑说明</h2>
            <p>本系统的检索逻辑基于特征向量相似度计算：</p>
            <ol>
                <li><b>特征提取</b>：每个CAD模型(STEP文件)都对应一个特征向量文件(.npy)</li>
                <li><b>相似度计算</b>：
                    <ul>
                        <li>支持两种相似度度量方式：欧氏距离和余弦距离</li>
                        <li>特征向量会先进行L2归一化处理</li>
                        <li>计算查询特征与数据库中所有特征的相似度得分</li>
                        <li>得分范围在0-100之间(100表示最相似)</li>
                    </ul>
                </li>
                <li><b>结果排序</b>：根据相似度得分对结果进行排序</li>
                <li><b>类别匹配</b>：检查结果模型是否与查询模型属于同一类别(通过文件名前缀判断)</li>
            </ol>

            <h2 style='color: #3498db;'>文件需求说明</h2>
            <p>系统运行需要以下几种文件：</p>
            <ul>
                <li><b>STEP模型文件</b>：
                    <ul>
                        <li>用于3D模型显示</li>
                        <li>文件名格式应为"类别_编号.step"或"类别_编号.stp"</li>
                        <li>系统会根据文件名前缀(下划线前的部分)判断模型类别</li>
                    </ul>
                </li>
                <li><b>特征文件(.npy)</b>：
                    <ul>
                        <li>包含从CAD模型提取的特征向量</li>
                        <li>每个STEP文件应有一个对应的特征文件</li>
                    </ul>
                </li>
                <li><b>数据库文件</b>：
                    <ul>
                        <li><b>单个数据库文件</b>：包含所有特征向量的单一.npy文件</li>
                        <li><b>多个特征文件</b>：包含多个.npy特征文件的文件夹</li>
                    </ul>
                </li>
            </ul>

            <h2 style='color: #3498db;'>操作指南</h2>
            <ol>
                <li><b>上传模型</b>：加载要检索的STEP模型文件</li>
                <li><b>上传特征文件</b>：加载查询模型对应的特征文件(.npy)</li>
                <li><b>上传数据库特征</b>：加载数据库特征(单个文件或多个文件)</li>
                <li><b>设置检索路径</b>：指定存放检索结果STEP文件的目录</li>
                <li><b>执行检索</b>：开始检索过程，结果显示在右侧区域</li>
                <li><b>生成报告</b>：生成PDF或HTML格式的检索报告，包含模型截图和详细信息</li>
            </ol>

            <h2 style='color: #3498db;'>其他功能</h2>
            <ul>
                <li><b>清除显示</b>：重置所有显示内容</li>
                <li><b>设置颜色</b>：自定义匹配/不匹配模型的显示颜色</li>
                <li><b>切换显示模式</b>：在3D模型和文本结果之间切换</li>
                <li><b>保存结果</b>：将检索结果导出为文本文件</li>
                <li><b>生成报告</b>：生成PDF、HTML或图片格式的检索报告</li>
                <li><b>检索历史</b>：查看和重复之前的检索操作</li>
            </ul>

            <h2 style='color: #3498db;'>注意事项</h2>
            <ul>
                <li>确保STEP文件和特征文件的命名一致且符合格式要求</li>
                <li>数据库特征文件应与检索路径中的STEP文件一一对应</li>
                <li>对于大型数据库，检索过程可能需要较长时间</li>
                <li>生成报告需要足够的磁盘空间和权限</li>
                <li>图片格式报告需要安装Pillow库(pip install pillow)</li>
            </ul>
            """

        help_dialog = QDialog(self)
        help_dialog.setWindowTitle("详细使用说明" if self.current_language == 'zh' else "User Manual")
        help_dialog.resize(800, 600)

        help_dialog.setStyleSheet("""
            QDialog {
                background-color: #f9f9f9;
            }
        """)

        scroll = QScrollArea(help_dialog)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
            }
            QScrollBar:vertical {
                width: 12px;
                background: #f1f1f1;
            }
            QScrollBar::handle:vertical {
                background: #c1c1c1;
                min-height: 20px;
                border-radius: 6px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        content = QLabel(help_text)
        content.setWordWrap(True)
        content.setTextFormat(Qt.RichText)
        content.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        content.setStyleSheet("""
            QLabel {
                padding: 20px;
                font-size: 12pt;
                line-height: 1.5;
            }
            h1 {
                color: #2c3e50;
                font-size: 18pt;
                margin-bottom: 20px;
            }
            h2 {
                color: #3498db;
                font-size: 16pt;
                margin-top: 15px;
                margin-bottom: 10px;
            }
            p, li {
                margin-bottom: 8px;
                color: #333;
            }
            ul, ol {
                margin-left: 20px;
                margin-top: 5px;
                margin-bottom: 15px;
            }
        """)

        scroll.setWidget(content)

        close_btn = QPushButton("关闭" if self.current_language == 'zh' else "Close")
        close_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 20px;
                font-size: 12pt;
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        close_btn.clicked.connect(help_dialog.close)
        close_btn.setFixedWidth(100)

        layout = QVBoxLayout(help_dialog)
        layout.addWidget(scroll, 1)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        btn_layout.addStretch()

        layout.addLayout(btn_layout)
        layout.setContentsMargins(0, 0, 0, 10)

        help_dialog.exec_()
    def logMessage(self, message):
        self.logArea.append(message)