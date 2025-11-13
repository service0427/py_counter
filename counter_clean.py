"""
Numpad Counter - Clean Modular Design
완전히 새로 작성된 모듈화 버전
"""

import sys
import json
import os
from datetime import datetime
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QGridLayout, QPushButton, QLabel,
                               QTextEdit, QFrame, QMenu, QDialog,
                               QLineEdit, QDialogButtonBox, QMessageBox, QFileDialog,
                               QTableWidget, QTableWidgetItem, QHeaderView)
from PySide6.QtCore import Qt, QTimer, QSharedMemory
from PySide6.QtGui import QFont, QCursor, QKeyEvent, QIcon, QInputMethod, QColor


# ============================================================================
# UI SIZE CONFIGURATION (전역 변수로 쉽게 조정 가능)
# ============================================================================
BUTTON_SIZE = 80          # 버튼 기본 크기 (정사각형) - 70 + 10%
BUTTON_FONT_SIZE = 11     # 버튼 폰트 크기
BUTTON_COUNT_FONT_SIZE = 16  # 버튼 카운트 폰트 크기
BUTTON_COUNT_COLOR = "#4CAF50"  # 버튼 카운트 색상 (초록색)
BUTTON_PADDING = 2        # 버튼 내부 여백
GRID_SPACING = 4          # 그리드 간격
PANEL_MARGIN = 4          # 패널 여백
TITLE_ROW_SPACING = 6     # 타이틀 행 간격
PRESET_BUTTON_SIZE = 30   # 프리셋 버튼 크기
LOG_FONT_SIZE = 8         # 실시간 로그 폰트 크기
TOTAL_COUNT_FONT_SIZE = 14  # 총 카운트 폰트 크기
TOTAL_COUNT_COLOR = "#e0e0e0"  # 총 카운트 텍스트 색상
WINDOW_WIDTH = 440        # 창 너비 (기본)
WINDOW_WIDTH_EXPANDED = 1186  # 창 너비 (히스토리 패널 펼침)
WINDOW_HEIGHT = 580       # 창 높이
HISTORY_PANEL_WIDTH = 780  # 히스토리 패널 너비

# 프리셋 버튼 색상
PRESET_COLORS = [
    "#e74c3c",  # 빨강
    "#3498db",  # 파랑
    "#2ecc71",  # 초록
]

# 히스토리 테이블 하이라이트 색상
HISTORY_HIGHLIGHT_LATEST = "#2ecc71"   # 최신 클릭 (초록색)

# QMessageBox 다크 테마 스타일
MESSAGEBOX_DARK_STYLE = """
    QMessageBox {
        background-color: #2a2a3e;
        color: #e0e0e0;
    }
    QMessageBox QLabel {
        color: #e0e0e0;
    }
    QPushButton {
        background-color: #3c4254;
        color: #e0e0e0;
        border: 1px solid #4a4e69;
        padding: 5px 15px;
        min-width: 60px;
    }
    QPushButton:hover {
        background-color: #4a4e69;
    }
"""


# ============================================================================
# DIALOG COMPONENTS
# ============================================================================

class UserInputDialog(QDialog):
    """사용자 이름 입력 다이얼로그"""
    def __init__(self, parent=None, title="사용자 추가", default_name=""):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedSize(300, 140)
        # 시스템 기본 스타일 사용 (다크모드 스타일 상속 방지)
        self.setStyleSheet("")

        layout = QVBoxLayout()
        label = QLabel("사용자 이름 (한글 2-4글자):")
        layout.addWidget(label)

        self.name_input = QLineEdit()
        self.name_input.setText(default_name)
        self.name_input.setFont(QFont("맑은 고딕", 11))
        self.name_input.setMaxLength(4)  # 최대 4글자
        self.name_input.setPlaceholderText("예: 홍길동")

        # Windows IME 한글 입력 활성화
        import locale
        locale.setlocale(locale.LC_ALL, 'ko_KR.UTF-8')

        layout.addWidget(self.name_input)

        # 안내 메시지
        hint_label = QLabel("※ 대부분 3글자로 입력합니다")
        hint_label.setStyleSheet("font-size: 9pt;")  # 시스템 기본 색상 사용
        layout.addWidget(hint_label)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)
        self.name_input.setFocus()

    def get_name(self):
        name = self.name_input.text().strip()
        # 2-4글자 제한 검증
        if len(name) < 2 or len(name) > 4:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("입력 오류")
            msg.setText("이름은 2-4글자로 입력해주세요.")
            msg.setStyleSheet(MESSAGEBOX_DARK_STYLE)
            msg.exec()
            return ""
        return name


class DailyLogDialog(QDialog):
    """일자별 로그 팝업 다이얼로그"""
    def __init__(self, data_dir, parent=None):
        super().__init__(parent)
        self.setWindowTitle("일자별 로그")
        self.setModal(True)
        self.setFixedSize(400, 540)
        self.data_dir = data_dir
        # 시스템 기본 스타일 사용 (다크모드 스타일 상속 방지)
        self.setStyleSheet("")

        layout = QVBoxLayout()

        # 상단: 안내 메시지
        info_label = QLabel("※ 최근 90일치 로그가 자동으로 보관됩니다")
        info_label.setStyleSheet("font-size: 9pt; padding: 5px;")  # 시스템 기본 색상 사용
        layout.addWidget(info_label)

        # 중간: 로그 목록 (날짜 + 요약 + 삭제 버튼)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("맑은 고딕", 9))
        layout.addWidget(self.log_text)

        # 하단: 닫기 버튼만
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        close_btn = QPushButton("닫기")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

        # 로그 로드
        self.load_logs()

    def load_logs(self):
        """일자별 로그 파일 로드 (Row별 클릭 히스토리)"""
        history_dir = os.path.join(self.data_dir, "history")
        if not os.path.exists(history_dir):
            self.log_text.setPlainText("로그가 없습니다.")
            return

        # 모든 JSON 파일 찾기 (날짜 형식: YYYY-MM-DD.json)
        log_files = []
        for filename in os.listdir(history_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(history_dir, filename)
                try:
                    # 파일 수정 시간 기준으로 정렬
                    mtime = os.path.getmtime(filepath)
                    log_files.append((filename, filepath, mtime))
                except:
                    pass

        if not log_files:
            self.log_text.setPlainText("로그가 없습니다.")
            return

        # 날짜 최신순으로 정렬
        log_files.sort(key=lambda x: x[2], reverse=True)

        # 로그 내용 생성 (Row별 클릭 히스토리)
        log_content = []
        for filename, filepath, _ in log_files:
            date = filename.replace('.json', '')
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logs = data.get('logs', [])
                    users = data.get('users', {})

                    # 사용자별 카운트 합계
                    total = sum(u.get('count', 0) for u in users.values())
                    user_count = len([u for u in users.values() if u.get('count', 0) > 0])

                    log_content.append(f"📅 {date}")
                    log_content.append(f"   총 카운트: {total}회 | 사용자: {user_count}명")
                    log_content.append("")

                    # 클릭 히스토리 표시 (최근 20개만)
                    if logs:
                        log_content.append("   [클릭 히스토리]")
                        for log_entry in logs[-20:]:  # 최근 20개
                            log_content.append(f"   {log_entry}")
                    else:
                        log_content.append("   클릭 기록 없음")

                    log_content.append("")
                    log_content.append("-" * 50)
                    log_content.append("")
            except:
                log_content.append(f"📅 {date} (읽기 오류)")
                log_content.append("")

        self.log_text.setPlainText("\n".join(log_content))


# ============================================================================
# NUMPAD BUTTON COMPONENT
# ============================================================================

class NumpadButton(QPushButton):
    """넘패드 버튼"""
    def __init__(self, label, shortcut_key=None, parent=None):
        super().__init__(label, parent)
        self.key_label = label
        self.shortcut_key = shortcut_key  # 단축키 (예: "7", "8", "9" 등)
        self.user_name = None
        self.count = 0

        self.setFixedSize(BUTTON_SIZE, BUTTON_SIZE)
        self.setFont(QFont("맑은 고딕", BUTTON_FONT_SIZE, QFont.Bold))

        # 단축키 표시용 라벨 (좌측 상단)
        self.shortcut_label = QLabel(self)
        self.shortcut_label.setGeometry(3, 3, 24, 15)
        self.shortcut_label.setFont(QFont("맑은 고딕", 8, QFont.Bold))
        self.shortcut_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.shortcut_label.setStyleSheet("background: transparent;")

        # 이름 표시용 라벨 (중앙 상단)
        self.name_label = QLabel(self)
        self.name_label.setGeometry(0, 20, BUTTON_SIZE, 14)
        self.name_label.setFont(QFont("맑은 고딕", BUTTON_FONT_SIZE, QFont.Bold))
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setStyleSheet("background: transparent; color: #e0e0e0;")
        self.name_label.hide()

        # 카운트 표시용 라벨 (중앙 하단)
        self.count_label = QLabel(self)
        self.count_label.setGeometry(0, 40, BUTTON_SIZE, 20)
        self.count_label.setFont(QFont("맑은 고딕", BUTTON_COUNT_FONT_SIZE, QFont.Bold))
        self.count_label.setAlignment(Qt.AlignCenter)
        self.count_label.setStyleSheet(f"background: transparent; color: {BUTTON_COUNT_COLOR};")
        self.count_label.hide()

        # 순번 표시용 라벨 (우측 상단 - 단축키 반대편)
        self.order_label = QLabel(self)
        self.order_label.setGeometry(BUTTON_SIZE - 25, 3, 22, 15)
        self.order_label.setFont(QFont("맑은 고딕", 8, QFont.Bold))
        self.order_label.setAlignment(Qt.AlignCenter)
        self.order_label.setStyleSheet("background: rgba(255, 165, 0, 180); color: white; border-radius: 3px; padding: 1px;")
        self.order_label.hide()

        self.apply_default_style()

    def apply_default_style(self):
        """기본 스타일 적용"""
        self.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #4a4e69, stop:0.5 #3c4254, stop:1 #2f3542);
                color: transparent;
                border: 2px solid #3c4254;
                border-radius: 12px;
                padding: {BUTTON_PADDING}px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #5a5e79, stop:0.5 #4c5264, stop:1 #3f4552);
                border: 2px solid #5294e2;
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #2f3542, stop:0.5 #3c4254, stop:1 #4a4e69);
            }}
        """)

    def set_user(self, name):
        self.user_name = name
        self.count = 0
        self.update_display()

    def clear_user(self):
        self.user_name = None
        self.count = 0
        self.update_display()

    def increment(self):
        if self.user_name:
            self.count += 1
            self.update_display()
            return True
        return False

    def decrement(self):
        if self.user_name and self.count > 0:
            self.count -= 1
            self.update_display()
            return True
        return False

    def reset_count(self):
        self.count = 0
        self.update_display()

    def set_order(self, order_num):
        """순번 설정"""
        if order_num > 0:
            self.order_label.setText(str(order_num))
            self.order_label.show()
        else:
            self.order_label.hide()

    def update_display(self):
        """버튼 텍스트 업데이트 (단축키 표시 포함)"""
        if self.user_name:
            # 버튼 텍스트는 비움 (라벨로 표시)
            self.setText("")
            self.apply_default_style()
            # 이름 라벨 표시
            self.name_label.setText(self.user_name)
            self.name_label.show()
            # 카운트 라벨 표시
            self.count_label.setText(str(self.count))
            self.count_label.show()
            # 단축키 라벨 (활성)
            if self.shortcut_key:
                self.shortcut_label.setText(f"[{self.shortcut_key}]")
                self.shortcut_label.setStyleSheet("background: transparent; color: #aaaaaa;")
            else:
                self.shortcut_label.setText("")
        else:
            # 빈 키 표시 (비활성화 느낌)
            self.setText(f"{self.key_label}\n[빈 키]")
            self.name_label.hide()
            self.count_label.hide()
            # 비활성화 스타일 적용
            self.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #2a2e39, stop:0.5 #252831, stop:1 #1f2229);
                    color: #666666;
                    border: 2px solid #2a2e39;
                    border-radius: 12px;
                    padding: {BUTTON_PADDING}px;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #3a3e49, stop:0.5 #353841, stop:1 #2f3239);
                    border: 2px solid #4a4e59;
                }}
                QPushButton:pressed {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #1f2229, stop:0.5 #252831, stop:1 #2a2e39);
                }}
            """)
            # 단축키 라벨 숨김 (빈 키는 단축키 사용 안 함)
            self.shortcut_label.setText("")


# ============================================================================
# MODE TOGGLE BUTTON (+ / - 모드) - 원래 [-] 위치에 배치
# ============================================================================

class UndoButton(QPushButton):
    """취소 버튼 - 최근 클릭 되돌리기 (단축키: -)"""
    def __init__(self, parent=None):
        super().__init__("↶\n취소", parent)
        self.setFixedSize(BUTTON_SIZE, BUTTON_SIZE)
        self.setFont(QFont("맑은 고딕", BUTTON_FONT_SIZE, QFont.Bold))

        # 단축키 표시용 라벨 (좌측 상단)
        self.shortcut_label = QLabel(self)
        self.shortcut_label.setGeometry(3, 3, 24, 15)
        self.shortcut_label.setFont(QFont("맑은 고딕", 8, QFont.Bold))
        self.shortcut_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.shortcut_label.setText("[-]")
        self.shortcut_label.setStyleSheet("background: transparent; color: #ffffff;")

        self.update_display()

    def update_display(self):
        """디스플레이 업데이트"""
        self.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #9e4a4a, stop:0.5 #823c3c, stop:1 #752f2f);
                color: white;
                border: 2px solid #9e4a4a;
                border-radius: 12px;
                padding: {BUTTON_PADDING}px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #be5a5a, stop:0.5 #924c4c, stop:1 #853f3f);
                border: 2px solid #be5a5a;
            }}
        """)


# ============================================================================
# RESET BUTTON (초기화 버튼) - 원래 Num 위치에 배치
# ============================================================================

class ResetButton(QPushButton):
    """초기화 버튼 - 모든 카운트 초기화 (단축키 없음, 마우스 클릭만 가능)"""
    def __init__(self, parent=None):
        super().__init__("초기화", parent)
        self.setFixedSize(BUTTON_SIZE, BUTTON_SIZE)
        self.setFont(QFont("맑은 고딕", BUTTON_FONT_SIZE, QFont.Bold))
        self.clicked.connect(self.on_reset_click)
        self.update_display()

    def on_reset_click(self):
        """초기화 버튼 클릭 시"""
        # ResetButton -> NumpadGrid -> panel(QFrame) -> CounterApp
        # CounterApp을 찾을 때까지 부모를 탐색
        app = self.parent()
        depth = 0
        while app and depth < 5:
            if hasattr(app, 'reset_today_counters'):
                app.reset_today_counters()
                return
            if hasattr(app, 'parent') and callable(app.parent):
                app = app.parent()
            else:
                break
            depth += 1

    def update_display(self):
        """디스플레이 업데이트"""
        self.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #e8a84a, stop:0.5 #d89a3c, stop:1 #c88a2f);
                color: white;
                border: 2px solid #e8a84a;
                border-radius: 12px;
                padding: {BUTTON_PADDING}px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #f8b85a, stop:0.5 #e8a84c, stop:1 #d89a3f);
                border: 2px solid #f8b85a;
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #c88a2f, stop:0.5 #b87a2c, stop:1 #a86a1f);
            }}
        """)


# ============================================================================
# NUMPAD GRID COMPONENT
# ============================================================================

class NumpadGrid(QWidget):
    """넘패드 그리드 위젯"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.buttons = {}
        self.reset_btn = None  # Reset 버튼 (원래 Num 위치)
        self.undo_btn = None  # 취소 버튼 (원래 - 위치)
        self.summary_label = None
        self.init_ui()

    def init_ui(self):
        grid = QGridLayout()
        grid.setSpacing(GRID_SPACING)
        grid.setContentsMargins(0, 0, 0, 0)

        # Row 0: Reset(초기화), /, *, ModeToggle(+/-)
        # Reset 버튼 (좌측 상단, 단축키 없음)
        self.reset_btn = ResetButton(self)
        grid.addWidget(self.reset_btn, 0, 0, 1, 1)

        # 일반 버튼들 정의 (row, col, label, shortcut_key)
        keys = [
            (0, 1, '/', '/'),
            (0, 2, '*', '*'),
            (1, 0, '7', '7'),
            (1, 1, '8', '8'),
            (1, 2, '9', '9'),
            (2, 0, '4', '4'),
            (2, 1, '5', '5'),
            (2, 2, '6', '6'),
            (3, 0, '1', '1'),
            (3, 1, '2', '2'),
            (3, 2, '3', '3'),
            (4, 2, '.', '.'),
        ]

        # 일반 버튼 생성
        for row, col, label, shortcut in keys:
            btn = NumpadButton(label, shortcut, self)
            self.buttons[label] = btn
            grid.addWidget(btn, row, col, 1, 1)

        # 0 키 (2 columns)
        btn_0 = NumpadButton('0', '0', self)
        btn_0.setFixedSize(BUTTON_SIZE * 2 + GRID_SPACING, BUTTON_SIZE)
        btn_0.apply_default_style()
        self.buttons['0'] = btn_0
        grid.addWidget(btn_0, 4, 0, 1, 2)

        # 취소 버튼 (우측 상단, 단축키: -, 원래 - 위치)
        self.undo_btn = UndoButton(self)
        grid.addWidget(self.undo_btn, 0, 3, 1, 1)

        # + 버튼 추가 예정 (향후 추가)

        # 실시간 로그 표시 영역 (우측 4줄, 좌측 정렬, 클릭 가능)
        self.summary_label = QLabel('실시간 로그')
        self.summary_label.setFixedSize(BUTTON_SIZE, BUTTON_SIZE * 4 + GRID_SPACING * 3)
        self.summary_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.summary_label.setWordWrap(True)
        self.summary_label.setFont(QFont("맑은 고딕", LOG_FONT_SIZE))
        self.summary_label.setCursor(Qt.PointingHandCursor)
        self.summary_label.setStyleSheet(f"""
            QLabel {{
                background-color: #1a1a2e;
                color: #888888;
                border: 2px solid #2a2a3e;
                border-radius: 12px;
                padding: 5px;
            }}
            QLabel:hover {{
                background-color: #252540;
                border: 2px solid #5294e2;
            }}
        """)
        # 클릭 이벤트를 부모로 직접 전달
        self.summary_label.mousePressEvent = self._on_summary_label_click
        grid.addWidget(self.summary_label, 1, 3, 4, 1)  # 1행부터 4행까지 (4행 높이)

        self.setLayout(grid)

    def update_summary_display(self, summary_text):
        """실시간 로그 영역에 요약 표시"""
        self.summary_label.setText(summary_text if summary_text else '실시간 로그\n(카운트 없음)')

    def _on_summary_label_click(self, event):
        """실시간 로그 영역 클릭 이벤트 핸들러"""
        # NumpadGrid -> panel(QFrame) -> CounterApp
        app = self.parent()
        if hasattr(app, 'parent') and callable(app.parent):
            app = app.parent()

        # CounterApp을 찾을 때까지 부모를 탐색
        while app and not isinstance(app, CounterApp):
            if hasattr(app, 'parent') and callable(app.parent):
                app = app.parent()
            else:
                break

        if app and hasattr(app, 'copy_log_to_clipboard'):
            app.copy_log_to_clipboard()


# ============================================================================
# MAIN APPLICATION
# ============================================================================

class CounterApp(QMainWindow):
    def __init__(self, instance_id=None):
        super().__init__()

        # 인스턴스 ID (각 창마다 고유)
        self.instance_id = instance_id if instance_id else datetime.now().strftime("%Y%m%d_%H%M%S")

        # 마지막 클릭한 버튼 추적
        self.last_clicked_button = None

        # 타이틀 설정 (Y-m-d H:i 의 카운트)
        title_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.setWindowTitle(f"{title_time} 의 카운트")

        # 아이콘 설정
        icon_path = os.path.join("counter_data", "icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # 창 크기 고정 (기본값은 펼침 상태)
        self.setFixedSize(WINDOW_WIDTH_EXPANDED, WINDOW_HEIGHT)

        # Data setup (루트 디렉토리 사용)
        self.data_dir = "counter_data"
        self.history_dir = os.path.join(self.data_dir, "history")
        os.makedirs(self.history_dir, exist_ok=True)

        self.presets_file = os.path.join(self.data_dir, "presets.json")
        self.counter_data_file = os.path.join(self.data_dir, "counter_data.json")

        # State
        self.presets = [{"name": f"프리셋 {i+1}", "users": {}, "click_history": []} for i in range(3)]
        self.current_preset = 0
        self.logs = []
        self.click_history = []  # 클릭 순서 기록 [(name, count), ...]
        self.last_date = datetime.now().strftime("%Y-%m-%d")

        # UI Setup
        self.init_ui()
        self.apply_global_styles()

        # Load data and start timer
        self.load_data()
        # update_summary()는 load_current_preset()에서 호출됨

        # 히스토리 테이블 초기 로드 (히스토리 패널이 펼쳐진 상태이므로)
        if self.history_panel_visible and self.click_history:
            self.update_history_table()

        # Daily reset timer
        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self.check_daily_reset)
        self.check_timer.start(60000)

        # Num Lock 상태 체크 타이머
        self.numlock_timer = QTimer()
        self.numlock_timer.timeout.connect(self.check_numlock_state)
        self.numlock_timer.start(500)  # 0.5초마다 체크
        self.check_numlock_state()  # 초기 체크

    def update_overlay_geometry(self):
        """오버레이 크기와 위치를 패널에 맞춰 업데이트"""
        if hasattr(self, 'numlock_overlay'):
            # 패널의 geometry를 가져와서 오버레이에 적용
            panel = self.numlock_overlay.parent()
            if panel:
                self.numlock_overlay.setGeometry(0, 0, panel.width(), panel.height())

    def check_numlock_state(self):
        """Num Lock 상태를 체크하고 오버레이 표시/숨김"""
        try:
            import ctypes
            # Windows API로 Num Lock 상태 확인
            hllDll = ctypes.WinDLL("User32.dll")
            VK_NUMLOCK = 0x90
            numlock_state = hllDll.GetKeyState(VK_NUMLOCK)

            # Num Lock이 켜져있으면 1, 꺼져있으면 0
            is_numlock_on = (numlock_state & 1) != 0

            if is_numlock_on:
                self.numlock_overlay.hide()
            else:
                self.update_overlay_geometry()  # 위치 업데이트
                self.numlock_overlay.show()
                self.numlock_overlay.raise_()
        except:
            # Windows가 아니거나 오류 발생 시 오버레이 숨김
            self.numlock_overlay.hide()

    def activate_numlock(self):
        """Num Lock 활성화 (사용자가 오버레이 클릭 시)"""
        try:
            import ctypes
            # Windows API로 Num Lock 켜기
            hllDll = ctypes.WinDLL("User32.dll")
            VK_NUMLOCK = 0x90

            # keybd_event로 Num Lock 키 누르기
            hllDll.keybd_event(VK_NUMLOCK, 0x45, 0, 0)  # 키 누름
            hllDll.keybd_event(VK_NUMLOCK, 0x45, 2, 0)  # 키 뗌

            # 즉시 상태 체크
            self.check_numlock_state()
        except:
            pass

    def undo_last_click(self):
        """최근 클릭 취소 (Ctrl+Z 효과)"""
        if not self.click_history:
            self.add_log("[취소] 되돌릴 작업이 없습니다")
            return

        # 마지막 클릭 가져오기
        last_name, last_count = self.click_history.pop()

        # 해당 사용자의 버튼 찾기
        target_button = None
        for btn in self.numpad.buttons.values():
            if btn.user_name == last_name and btn.count == last_count:
                target_button = btn
                break

        if target_button:
            # 카운트 감소
            target_button.count -= 1
            target_button.update_display()
            self.add_log(f"[취소] {target_button.key_label}: {last_name} (총 {target_button.count}회)")

            # 저장 및 업데이트
            self.save_data()
            self.save_daily_history()
            self.update_summary()

            # 히스토리 패널이 열려있으면 업데이트
            if self.history_panel_visible:
                self.update_history_table()

    def keyPressEvent(self, event):
        """키보드 입력 처리"""
        key_text = event.text()

        # - 키 처리 (취소 버튼)
        if key_text == '-':
            self.undo_last_click()
            return

        # 숫자 및 기호 키 매핑
        key_map = {
            '0': '0', '1': '1', '2': '2', '3': '3', '4': '4',
            '5': '5', '6': '6', '7': '7', '8': '8', '9': '9',
            '/': '/', '*': '*', '.': '.'
        }

        # 눌린 키가 매핑에 있으면 해당 버튼 클릭 (사용자가 할당된 경우만)
        if key_text in key_map:
            button_key = key_map[key_text]
            if button_key in self.numpad.buttons:
                button = self.numpad.buttons[button_key]
                # 사용자가 할당된 버튼만 단축키로 작동
                if button.user_name:
                    button.click()

        super().keyPressEvent(event)

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 메인 레이아웃 (수평)
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        # 좌측: 넘패드 + 버튼들
        left_layout = QVBoxLayout()

        # Numpad panel
        numpad_panel = self.create_numpad_panel()
        left_layout.addWidget(numpad_panel, alignment=Qt.AlignCenter)

        # Bottom buttons
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(10)

        self.export_txt_btn = QPushButton("TXT 저장")
        self.export_txt_btn.setFont(QFont("맑은 고딕", 10))
        self.export_txt_btn.setFixedWidth(100)
        self.export_txt_btn.clicked.connect(self.export_to_txt)
        bottom_layout.addWidget(self.export_txt_btn)

        self.show_log_btn = QPushButton("자세히")
        self.show_log_btn.setFont(QFont("맑은 고딕", 10))
        self.show_log_btn.setFixedWidth(80)
        self.show_log_btn.clicked.connect(self.show_log_dialog)
        bottom_layout.addWidget(self.show_log_btn)

        self.toggle_history_btn = QPushButton("◀ 닫힘")
        self.toggle_history_btn.setFont(QFont("맑은 고딕", 10))
        self.toggle_history_btn.setFixedWidth(100)
        self.toggle_history_btn.clicked.connect(self.toggle_history_panel)
        bottom_layout.addWidget(self.toggle_history_btn)

        left_layout.addLayout(bottom_layout)

        main_layout.addLayout(left_layout)

        # 우측: 히스토리 패널 (기본값은 펼침)
        self.history_panel = self.create_history_panel()
        self.history_panel.show()
        main_layout.addWidget(self.history_panel)

        self.history_panel_visible = True

    def create_numpad_panel(self):
        """좌측 넘패드 패널"""
        panel = QFrame()
        panel.setObjectName("mainPanel")
        layout = QVBoxLayout()
        layout.setContentsMargins(PANEL_MARGIN, PANEL_MARGIN, PANEL_MARGIN, PANEL_MARGIN)
        layout.setSpacing(TITLE_ROW_SPACING)

        # Title row: 프리셋 버튼들 + 초기화 버튼
        title_layout = QHBoxLayout()
        title_layout.setSpacing(TITLE_ROW_SPACING)

        # Preset buttons (left) - 정사각형 컬러 버튼
        self.preset_buttons = []
        for i in range(3):
            btn = QPushButton()
            btn.setFixedSize(PRESET_BUTTON_SIZE, PRESET_BUTTON_SIZE)
            btn.setCheckable(True)
            color = PRESET_COLORS[i]
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    border: 2px solid {color};
                    border-radius: 4px;
                }}
                QPushButton:hover {{
                    border: 2px solid #ffffff;
                }}
                QPushButton:checked {{
                    border: 3px solid #ffffff;
                }}
            """)
            btn.clicked.connect(lambda checked=False, idx=i: self.switch_preset(idx))
            self.preset_buttons.append(btn)
            title_layout.addWidget(btn)

        title_layout.addStretch()

        # Total count label (right)
        self.total_count_label = QLabel("총: 0")
        self.total_count_label.setFont(QFont("맑은 고딕", TOTAL_COUNT_FONT_SIZE, QFont.Bold))
        self.total_count_label.setStyleSheet(f"color: {TOTAL_COUNT_COLOR}; padding: 0 10px;")
        title_layout.addWidget(self.total_count_label)

        self.preset_buttons[0].setChecked(True)
        layout.addLayout(title_layout)

        # Numpad grid
        self.numpad = NumpadGrid(self)
        layout.addWidget(self.numpad, alignment=Qt.AlignTop | Qt.AlignHCenter)

        # Connect button signals
        for key, btn in self.numpad.buttons.items():
            btn.clicked.connect(lambda checked=False, b=btn: self.on_button_click(b))
            btn.setContextMenuPolicy(Qt.CustomContextMenu)
            btn.customContextMenuRequested.connect(
                lambda pos, b=btn: self.show_button_menu(b, pos)
            )

        # Connect undo button
        self.numpad.undo_btn.clicked.connect(self.undo_last_click)

        layout.addStretch()
        panel.setLayout(layout)

        # Num Lock 오버레이 (패널 위에 올리기)
        self.numlock_overlay = QFrame(panel)
        self.numlock_overlay.setStyleSheet("""
            QFrame {
                background-color: rgba(0, 0, 0, 180);
                border-radius: 10px;
            }
        """)

        overlay_layout = QVBoxLayout(self.numlock_overlay)
        overlay_layout.setAlignment(Qt.AlignCenter)

        warning_label = QLabel("⚠️\n\nNum Lock이\n\n비활성화되어 있습니다\n\n클릭하여 활성화하세요")
        warning_label.setFont(QFont("맑은 고딕", 14, QFont.Bold))
        warning_label.setAlignment(Qt.AlignCenter)
        warning_label.setStyleSheet("color: #ffffff; background: transparent; padding: 20px;")
        overlay_layout.addWidget(warning_label)

        self.numlock_overlay.mousePressEvent = lambda event: self.activate_numlock()
        self.numlock_overlay.setCursor(Qt.PointingHandCursor)
        self.numlock_overlay.hide()

        # 패널이 리사이즈될 때 오버레이도 함께 조정
        panel.resizeEvent = lambda event: self.update_overlay_geometry()

        return panel

    def create_history_panel(self):
        """우측 히스토리 패널"""
        panel = QFrame()
        panel.setObjectName("historyPanel")
        panel.setFixedWidth(HISTORY_PANEL_WIDTH)

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        # 테이블 (동적 컬럼)
        self.history_table = QTableWidget()
        self.history_table.setFont(QFont("맑은 고딕", 9))

        # 행 번호(vertical header) 가운데 정렬
        self.history_table.verticalHeader().setDefaultAlignment(Qt.AlignCenter)

        # 스타일
        self.history_table.setStyleSheet("""
            QTableWidget {
                background-color: #2a2a3e;
                color: #e0e0e0;
                gridline-color: #3c4254;
                border: 1px solid #3c4254;
            }
            QHeaderView::section {
                background-color: #3c4254;
                color: #e0e0e0;
                padding: 5px;
                border: 1px solid #2a2a3e;
                font-weight: bold;
            }
            QTableWidget::item {
                padding: 5px;
            }
        """)

        layout.addWidget(self.history_table)

        panel.setLayout(layout)
        panel.setStyleSheet("""
            QFrame#historyPanel {
                background-color: #2a2a3e;
                border-left: 2px solid #3c4254;
            }
        """)

        return panel

    def toggle_history_panel(self):
        """히스토리 패널 토글"""
        if self.history_panel_visible:
            # 닫기
            self.history_panel.hide()
            self.toggle_history_btn.setText("펼침 ▶")
            self.setFixedSize(WINDOW_WIDTH, WINDOW_HEIGHT)
            self.history_panel_visible = False
        else:
            # 열기
            self.history_panel.show()
            self.toggle_history_btn.setText("◀ 닫힘")
            self.setFixedSize(WINDOW_WIDTH_EXPANDED, WINDOW_HEIGHT)
            self.history_panel_visible = True
            self.update_history_table()

    def update_history_table(self):
        """히스토리 테이블 업데이트 (매트릭스 형태)"""
        if not self.click_history:
            self.history_table.setRowCount(0)
            self.history_table.setColumnCount(0)
            return

        # 등록된 사용자 목록 가져오기 (현재 프리셋)
        user_names = []
        for key in sorted(self.presets[self.current_preset]["users"].keys()):
            name = self.presets[self.current_preset]["users"][key]["name"]
            if name and name not in user_names:
                user_names.append(name)

        # 컬럼 설정: 각 사용자 이름만
        headers = user_names
        self.history_table.setColumnCount(len(headers))
        self.history_table.setHorizontalHeaderLabels(headers)

        # 각 사용자의 최대 클릭 횟수 계산
        max_count = {}
        for name, count in self.click_history:
            if name not in max_count or count > max_count[name]:
                max_count[name] = count

        # 행 개수 = 최대 카운트
        max_rows = max(max_count.values()) if max_count else 0
        self.history_table.setRowCount(max_rows)

        # 각 사용자별 클릭을 개인 카운트 -> 전체 순번 매핑
        user_clicks = {}  # {name: {personal_count: global_order}}
        for global_order, (name, personal_count) in enumerate(self.click_history, 1):
            if name not in user_clicks:
                user_clicks[name] = {}
            user_clicks[name][personal_count] = global_order

        # 가장 최근 클릭 찾기 (마지막 항목만)
        last_click = None
        if self.click_history:
            last_name, last_count = self.click_history[-1]
            last_click = (last_name, last_count)

        # 테이블 채우기
        for row in range(max_rows):
            personal_count = row + 1  # 개인 카운트 (1, 2, 3...)

            # 각 사용자 컬럼
            for col, user_name in enumerate(user_names):
                if user_name in user_clicks and personal_count in user_clicks[user_name]:
                    # 이 사용자의 personal_count번째 클릭의 전체 순번
                    global_order = user_clicks[user_name][personal_count]
                    item = QTableWidgetItem(str(global_order))
                    item.setTextAlignment(Qt.AlignCenter)

                    # 가장 최근 클릭인 경우 하이라이트
                    if last_click and user_name == last_click[0] and personal_count == last_click[1]:
                        # 볼드 폰트 적용
                        font = item.font()
                        font.setBold(True)
                        item.setFont(font)
                        # 배경색 적용
                        item.setBackground(QColor(HISTORY_HIGHLIGHT_LATEST))
                        # 텍스트 색상 (흰색)
                        item.setForeground(QColor("#ffffff"))

                    self.history_table.setItem(row, col, item)
                else:
                    # 빈 셀
                    item = QTableWidgetItem("")
                    item.setTextAlignment(Qt.AlignCenter)
                    self.history_table.setItem(row, col, item)

        # 컬럼 너비 자동 조정 (모든 컬럼 균등 분배)
        header = self.history_table.horizontalHeader()
        for col in range(len(headers)):
            header.setSectionResizeMode(col, QHeaderView.Stretch)

        # 스크롤을 맨 아래로
        if max_rows > 0:
            self.history_table.scrollToBottom()

    def show_log_dialog(self):
        """일자별 로그 팝업 표시"""
        dialog = DailyLogDialog(self.data_dir, self)
        dialog.exec()

    def copy_log_to_clipboard(self):
        """실시간 로그 영역 클릭 시 현재 카운트 클립보드 복사"""
        # 카운트가 있는 사용자만 수집하여 높은 순으로 정렬
        user_counts = []
        for key in self.numpad.buttons.keys():
            btn = self.numpad.buttons[key]
            if btn.user_name and btn.count > 0:
                user_counts.append((btn.user_name, btn.count))

        user_counts.sort(key=lambda x: x[1], reverse=True)

        # 실시간 로그에 정보가 있을 경우에만 복사
        if not user_counts:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("복사 실패")
            msg.setText("카운트가 없습니다.")
            msg.setStyleSheet(MESSAGEBOX_DARK_STYLE)
            msg.exec()
            return

        summary_lines = []
        summary_lines.append(f"=== {datetime.now().strftime('%Y-%m-%d')} 카운터 결과 ===")
        summary_lines.append("")

        for name, count in user_counts:
            summary_lines.append(f"{name}: {count}회")

        # 총합 계산 및 추가
        total = sum(count for name, count in user_counts)
        summary_lines.append("")
        summary_lines.append(f"총합: {total}회")

        text = "\n".join(summary_lines)
        QApplication.clipboard().setText(text)

        # 간단한 피드백 메시지
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("복사 완료")
        msg.setText("카운터 결과가 클립보드에 복사되었습니다.")
        msg.setStyleSheet(MESSAGEBOX_DARK_STYLE)
        msg.exec()

    def apply_global_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e2e;
            }
            QFrame#mainPanel {
                background-color: #2a2a3e;
                border-radius: 10px;
                padding: 15px;
                margin: 5px;
            }
            QPushButton {
                background-color: #5294e2;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 15px;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #6ab0f3;
            }
            QPushButton:pressed {
                background-color: #4284d2;
            }
            QLabel {
                color: #e0e0e0;
            }
        """)

    # ========================================================================
    # BUTTON CLICK HANDLERS
    # ========================================================================

    def on_button_click(self, button):
        """버튼 클릭 처리 (모드 토글 버튼에 따라 증가/감소)"""
        if not button.user_name:
            # 빈 키 - 사용자 등록
            self.register_user(button)
        else:
            # 이전 버튼의 하이라이트 제거
            if self.last_clicked_button and self.last_clicked_button != button:
                self.last_clicked_button.update_display()

            # 사용자가 있는 키 - 항상 증가
            if button.increment():
                self.add_log(f"[+] {button.key_label}: {button.user_name} (총 {button.count}회)")
                # 클릭 순서 기록 추가
                self.click_history.append((button.user_name, button.count))
                # 증가 시 초록색 하이라이트
                self.highlight_button(button, "#2ecc71")

            self.last_clicked_button = button
            self.save_data()
            self.save_daily_history()  # 매번 자동 저장
            self.update_summary()

            # 히스토리 패널이 열려있으면 업데이트
            if self.history_panel_visible:
                self.update_history_table()

    def highlight_button(self, button, color):
        """마지막 클릭한 버튼을 하이라이트"""
        button.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #4a4e69, stop:0.5 #3c4254, stop:1 #2f3542);
                color: #e0e0e0;
                border: 3px solid {color};
                border-radius: 12px;
                padding: {BUTTON_PADDING}px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #5a5e79, stop:0.5 #4c5264, stop:1 #3f4552);
                border: 3px solid {color};
            }}
        """)

    def register_user(self, button):
        """사용자 등록"""
        dialog = UserInputDialog(self, "사용자 등록")
        if dialog.exec() == QDialog.Accepted:
            name = dialog.get_name()
            if name:
                # 중복 이름 체크
                if self.is_duplicate_name(name, button):
                    msg = QMessageBox(self)
                    msg.setIcon(QMessageBox.Warning)
                    msg.setWindowTitle("중복 오류")
                    msg.setText(f"'{name}'은(는) 이미 다른 키에 등록되어 있습니다.")
                    msg.setStyleSheet(MESSAGEBOX_DARK_STYLE)
                    msg.exec()
                    return

                button.set_user(name)
                self.add_log(f"[등록] {button.key_label}: '{name}' 등록됨")
                self.save_data()
                self.update_summary()

    def is_duplicate_name(self, name, current_button):
        """다른 버튼에 같은 이름이 있는지 확인"""
        for btn in self.numpad.buttons.values():
            if btn != current_button and btn.user_name == name:
                return True
        return False

    def show_button_menu(self, button, pos):
        """우클릭 메뉴"""
        if not button.user_name:
            return

        menu = QMenu(self)
        modify_action = menu.addAction("수정")
        delete_action = menu.addAction("삭제")

        action = menu.exec(button.mapToGlobal(pos))

        if action == modify_action:
            self.modify_user(button)
        elif action == delete_action:
            self.delete_user(button)

    def modify_user(self, button):
        """사용자 수정"""
        dialog = UserInputDialog(self, "사용자 수정", button.user_name)
        if dialog.exec() == QDialog.Accepted:
            new_name = dialog.get_name()
            if new_name:
                # 중복 이름 체크 (자신 제외)
                if self.is_duplicate_name(new_name, button):
                    msg = QMessageBox(self)
                    msg.setIcon(QMessageBox.Warning)
                    msg.setWindowTitle("중복 오류")
                    msg.setText(f"'{new_name}'은(는) 이미 다른 키에 등록되어 있습니다.")
                    msg.setStyleSheet(MESSAGEBOX_DARK_STYLE)
                    msg.exec()
                    return

                old_name = button.user_name
                # 이름 변경 시 카운트를 0으로 리셋 (새로운 사용자로 간주)
                button.user_name = new_name
                button.count = 0
                button.update_display()
                self.add_log(f"[수정] {button.key_label}: '{old_name}' → '{new_name}' (카운트 초기화)")
                self.save_data()
                self.update_summary()

    def delete_user(self, button):
        """사용자 삭제"""
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Question)
        msg.setWindowTitle("확인")
        msg.setText(f"'{button.user_name}'을(를) 삭제하시겠습니까?")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)
        msg.setStyleSheet(MESSAGEBOX_DARK_STYLE)
        reply = msg.exec()

        if reply == QMessageBox.Yes:
            old_name = button.user_name
            button.clear_user()
            self.add_log(f"[삭제] {button.key_label}: '{old_name}' 삭제됨")
            self.save_data()
            self.update_summary()

    # ========================================================================
    # PRESET MANAGEMENT
    # ========================================================================

    def switch_preset(self, index):
        if index == self.current_preset:
            return

        self.save_current_preset()
        self.current_preset = index

        for i, btn in enumerate(self.preset_buttons):
            btn.setChecked(i == index)

        self.load_current_preset()
        self.add_log(f"[프리셋] 프리셋 {index + 1}로 전환")
        self.update_summary()

        # 히스토리 패널이 열려있으면 업데이트
        if self.history_panel_visible:
            self.update_history_table()

    def save_current_preset(self):
        preset_data = {}
        for key, btn in self.numpad.buttons.items():
            if btn.user_name:
                preset_data[key] = {
                    "name": btn.user_name,
                    "count": btn.count
                }
        self.presets[self.current_preset]["users"] = preset_data
        self.presets[self.current_preset]["click_history"] = self.click_history

    def load_current_preset(self):
        """현재 프리셋 데이터를 버튼에 로드"""
        # numpad가 아직 생성되지 않았으면 리턴
        if not hasattr(self, 'numpad') or self.numpad is None:
            return

        for btn in self.numpad.buttons.values():
            btn.clear_user()

        preset_data = self.presets[self.current_preset]["users"]
        for key, data in preset_data.items():
            if key in self.numpad.buttons:
                btn = self.numpad.buttons[key]
                btn.set_user(data["name"])
                btn.count = data.get("count", 0)
                btn.update_display()

        # 클릭 히스토리 복원
        self.click_history = self.presets[self.current_preset].get("click_history", [])

        # 로드 후 요약 업데이트
        self.update_summary()

    # ========================================================================
    # SUMMARY AND LOG
    # ========================================================================

    def add_log(self, message):
        """로그 추가 (메모리만, 화면 표시 없음)"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.logs.append(log_entry)

    def update_summary(self):
        """요약 업데이트 (실시간 로그 영역에 클릭 순서대로 표시)"""
        # 총 카운트 계산
        total_count = 0
        for key in self.numpad.buttons.keys():
            btn = self.numpad.buttons[key]
            if btn.user_name and btn.count > 0:
                total_count += btn.count

        # 총 카운트 라벨 업데이트
        self.total_count_label.setText(f"총: {total_count}")

        # 각 버튼의 마지막 순번 업데이트
        last_order = {}  # {name: order_number}
        for i, (name, count) in enumerate(self.click_history):
            last_order[name] = i + 1

        for key in self.numpad.buttons.keys():
            btn = self.numpad.buttons[key]
            if btn.user_name and btn.user_name in last_order:
                btn.set_order(last_order[btn.user_name])
            else:
                btn.set_order(0)

        # 사용자별 카운트를 모아서 개수가 많은 순서로 정렬
        user_counts = []
        for key in sorted(self.numpad.buttons.keys()):
            btn = self.numpad.buttons[key]
            if btn.user_name and btn.count > 0:
                user_counts.append((btn.user_name, btn.count))

        # 카운트가 많은 순서로 정렬 (내림차순)
        user_counts.sort(key=lambda x: x[1], reverse=True)

        if user_counts:
            display_lines = [f"{name}: {count}회" for name, count in user_counts]
            display_text = "\n".join(display_lines)
        else:
            display_text = "실\n시\n간\n로\n그\n"

        self.numpad.update_summary_display(display_text)

    # ========================================================================
    # RESET
    # ========================================================================

    def reset_today_counters(self):
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Question)
        msg.setWindowTitle("확인")
        msg.setText("오늘의 모든 카운터를 초기화하시겠습니까?")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)
        msg.setStyleSheet(MESSAGEBOX_DARK_STYLE)
        reply = msg.exec()

        if reply == QMessageBox.Yes:
            # 버튼 카운트 리셋
            for btn in self.numpad.buttons.values():
                btn.reset_count()

            # presets.json의 count만 0으로 리셋 (이름은 유지)
            for key in self.presets[self.current_preset]["users"]:
                self.presets[self.current_preset]["users"][key]["count"] = 0

            # 클릭 히스토리 초기화
            self.click_history.clear()

            self.add_log("[초기화] 모든 카운터 초기화됨")
            self.save_data()
            self.update_summary()

            # 히스토리 패널이 열려있으면 업데이트
            if self.history_panel_visible:
                self.update_history_table()

    def check_daily_reset(self):
        today = datetime.now().strftime("%Y-%m-%d")
        if today != self.last_date:
            self.save_today_history()
            for btn in self.numpad.buttons.values():
                btn.reset_count()
            self.logs.clear()
            self.click_history.clear()  # 클릭 히스토리도 초기화
            self.last_date = today
            self.add_log("[자동] 날짜가 변경되어 카운터가 초기화되었습니다")
            self.save_data()
            self.update_summary()

    # ========================================================================
    # EXPORT
    # ========================================================================

    def export_to_txt(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, "TXT 저장", f"{datetime.now().strftime('%Y-%m-%d')}_log.txt",
            "Text Files (*.txt)"
        )

        if filename:
            summary_lines = []
            summary_lines.append(f"=== {datetime.now().strftime('%Y-%m-%d')} 카운터 결과 ===")
            summary_lines.append("")

            total = 0
            for key in sorted(self.numpad.buttons.keys()):
                btn = self.numpad.buttons[key]
                if btn.user_name:
                    summary_lines.append(f"{btn.user_name}: {btn.count}회")
                    total += btn.count

            # 총합 추가
            summary_lines.append("")
            summary_lines.append(f"총합: {total}회")

            with open(filename, 'w', encoding='utf-8') as f:
                f.write("\n".join(summary_lines))

            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("저장 완료")
            msg.setText(f"파일이 저장되었습니다:\n{filename}")
            msg.setStyleSheet(MESSAGEBOX_DARK_STYLE)
            msg.exec()

    # ========================================================================
    # DATA PERSISTENCE
    # ========================================================================

    def save_data(self):
        """모든 데이터를 presets.json 하나에 저장"""
        self.save_current_preset()

        data = {
            "presets": self.presets,
            "current_preset": self.current_preset,
            "last_date": self.last_date,
            "logs": self.logs[-100:]  # Keep last 100 logs
        }

        with open(self.presets_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_data(self):
        """presets.json에서 모든 데이터 로드"""
        if os.path.exists(self.presets_file):
            try:
                with open(self.presets_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                    # 새로운 통합 형식 (presets 키가 있는 경우)
                    if isinstance(data, dict) and "presets" in data:
                        loaded_presets = data["presets"]
                        if isinstance(loaded_presets, list) and len(loaded_presets) == 3:
                            for i, preset in enumerate(loaded_presets):
                                if "users" in preset:
                                    self.presets[i]["users"] = preset["users"]
                                if "name" in preset:
                                    self.presets[i]["name"] = preset["name"]
                                if "click_history" in preset:
                                    self.presets[i]["click_history"] = preset["click_history"]

                        # current_preset, logs, last_date 로드
                        self.current_preset = data.get("current_preset", 0)
                        saved_date = data.get("last_date", "")

                        if saved_date == self.last_date:
                            self.logs = data.get("logs", [])
                        else:
                            self.last_date = datetime.now().strftime("%Y-%m-%d")

                    # 기존 배열 형식 (하위 호환성)
                    elif isinstance(data, list) and len(data) == 3:
                        for i, preset in enumerate(data):
                            if "users" in preset:
                                self.presets[i]["users"] = preset["users"]
                                if "name" in preset:
                                    self.presets[i]["name"] = preset["name"]
                                if "click_history" in preset:
                                    self.presets[i]["click_history"] = preset["click_history"]
                            elif "user_seats" in preset and "counters" in preset:
                                users_dict = {}
                                for user_name, key in preset["user_seats"].items():
                                    count = preset["counters"].get(user_name, 0)
                                    users_dict[key] = {
                                        "name": user_name,
                                        "count": count
                                    }
                                self.presets[i]["users"] = users_dict

                        # 구 counter_data.json이 있으면 로드
                        if os.path.exists(self.counter_data_file):
                            try:
                                with open(self.counter_data_file, 'r', encoding='utf-8') as cf:
                                    counter_data = json.load(cf)
                                    self.current_preset = counter_data.get("current_preset", 0)
                                    saved_date = counter_data.get("date", "")
                                    if saved_date == self.last_date:
                                        self.logs = counter_data.get("logs", [])
                            except:
                                pass
            except:
                pass

        # 프리셋 버튼 체크 상태 업데이트
        for i, btn in enumerate(self.preset_buttons):
            btn.setChecked(i == self.current_preset)

        self.load_current_preset()

    def save_today_history(self):
        """오늘의 기록을 히스토리에 저장"""
        history_file = os.path.join(self.history_dir, f"{self.last_date}.json")

        history_data = {
            "date": self.last_date,
            "preset": self.current_preset,
            "users": {},
            "logs": self.logs
        }

        for key, btn in self.numpad.buttons.items():
            if btn.user_name and btn.count > 0:
                history_data["users"][key] = {
                    "name": btn.user_name,
                    "count": btn.count
                }

        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history_data, f, ensure_ascii=False, indent=2)

    def save_daily_history(self):
        """매일 자동으로 히스토리 저장 및 90일 이전 로그 자동 삭제"""
        # 오늘 날짜로 저장
        self.save_today_history()

        # 90일 이전 로그 자동 삭제
        from datetime import timedelta
        cutoff_date = datetime.now() - timedelta(days=90)

        try:
            for filename in os.listdir(self.history_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(self.history_dir, filename)
                    try:
                        mtime = os.path.getmtime(filepath)
                        file_date = datetime.fromtimestamp(mtime)

                        if file_date < cutoff_date:
                            os.remove(filepath)
                    except:
                        pass
        except:
            pass


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

# 전역 창 인스턴스
current_window = None

def main():
    global current_window

    app = QApplication(sys.argv)

    # 싱글 인스턴스 체크 (공유 메모리 사용)
    shared_memory = QSharedMemory("NumpadCounterSingleInstance")

    if shared_memory.attach():
        # 이미 실행 중인 인스턴스가 있음
        if current_window:
            # 기존 창 활성화
            current_window.show()
            current_window.raise_()
            current_window.activateWindow()
        else:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("이미 실행 중")
            msg.setText("Numpad Counter가 이미 실행 중입니다.")
            msg.setStyleSheet(MESSAGEBOX_DARK_STYLE)
            msg.exec()
        return

    # 새 인스턴스 생성
    if not shared_memory.create(1):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("오류")
        msg.setText("프로그램을 시작할 수 없습니다.")
        msg.setStyleSheet(MESSAGEBOX_DARK_STYLE)
        msg.exec()
        return

    # 창 생성
    current_window = CounterApp()
    current_window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
