"""Native caption geometry for dialogs and narrow responsive workspaces."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


def run_worker() -> None:
    from datetime import datetime, timezone
    from tempfile import TemporaryDirectory
    from types import SimpleNamespace
    from unittest.mock import patch
    import socket

    from PySide6.QtCore import QPoint, QRect, QSettings, Qt, QTimer
    from PySide6.QtGui import QScreen
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import (
        QApplication, QAbstractButton, QBoxLayout, QCheckBox, QColorDialog, QDialog, QDialogButtonBox,
        QFileDialog, QInputDialog, QMessageBox, QPushButton, QRadioButton,
        QScrollArea, QStyle, QStyleOptionButton, QTabWidget,
    )

    from streaming_manager.app_paths import AppPaths
    from streaming_manager.credentials import MemoryCredentialStore
    from streaming_manager.database import Database
    from streaming_manager.ui_settings import UI_SETTINGS_MIGRATION_KEY, ui_settings_path
    from streaming_manager.views.auction_dialogs import AuctionTimeDialog
    from streaming_manager.views.games import DeleteAllGamesDialog, GameDialog
    from streaming_manager.views.main_window import MainWindow
    from streaming_manager.views.rules_editor import AuctionRulesEditorDialog
    from streaming_manager.views.wheel_center_picker import WheelCenterPickerDialog
    from streaming_manager.views.winner_verification import show_readonly_text_dialog
    from streaming_manager.views.common import exec_responsive_message_box

    app = QApplication.instance() or QApplication([])
    findings = []
    counts = {"dialogs": 0, "captions": 0, "workspaces": 0}
    original_show = QDialog.show
    narrow_message_boxes = False

    def show_without_focus(dialog):
        dialog.setAttribute(Qt.WA_DontShowOnScreen, True)
        original_show(dialog)

    def settle(widget):
        for _ in range(4):
            app.processEvents()
            if widget.layout() is not None:
                widget.layout().activate()

    def check_buttons(surface, context):
        for button in surface.findChildren(QAbstractButton):
            if not button.text() or not button.isVisibleTo(surface):
                continue
            option = QStyleOptionButton()
            if isinstance(button, QPushButton):
                element = QStyle.SE_PushButtonContents
            elif isinstance(button, QCheckBox):
                element = QStyle.SE_CheckBoxContents
            elif isinstance(button, QRadioButton):
                element = QStyle.SE_RadioButtonContents
            else:
                continue
            button.initStyleOption(option)
            content = button.style().subElementRect(element, option, button)
            text_width = option.fontMetrics.size(
                int(Qt.TextShowMnemonic | Qt.TextSingleLine), button.text(),
            ).width()
            if not button.icon().isNull():
                text_width += button.iconSize().width() + 4
            if isinstance(button, QPushButton) and button.menu() is not None:
                text_width += button.style().pixelMetric(
                    QStyle.PM_MenuButtonIndicator, option, button,
                )
            counts["captions"] += 1
            if content.width() < text_width:
                findings.append(
                    f"{context}: {button.text()!r} requires {text_width}px, "
                    f"styled contents {content.width()}px, button {button.width()}px"
                )

            # Scrollable toolbars and settings panels remain valid when every
            # individual button can be brought into the visible viewport.
            ancestor = button.parentWidget()
            scrolls = []
            while ancestor is not None and ancestor is not surface:
                if isinstance(ancestor, QScrollArea):
                    scrolls.append(ancestor)
                ancestor = ancestor.parentWidget()
            for scroll in scrolls:
                scroll.ensureWidgetVisible(button, 0, 0)
            settle(surface)

            left, right = content.left(), content.right()
            ancestor = button.parentWidget()
            while ancestor is not None:
                x = button.mapTo(ancestor, QPoint()).x()
                left = max(left, -x)
                right = min(right, ancestor.width() - 1 - x)
                if ancestor is surface:
                    break
                ancestor = ancestor.parentWidget()
            # Native push buttons center the combined icon/text label.
            # Check and radio buttons align their label to the content edge.
            text_left = content.left()
            if isinstance(button, QPushButton):
                text_left += (content.width() - text_width) // 2
            text_right = text_left + text_width - 1
            if left > text_left or right < text_right:
                findings.append(
                    f"{context}: ancestors clip {button.text()!r}; caption "
                    f"[{text_left}, {text_right}], visible [{left}, {right}]"
                )

    def check_dialog(dialog, context=""):
        show_without_focus(dialog)
        settle(dialog)
        if narrow_message_boxes and isinstance(dialog, QMessageBox):
            # QScreen is mocked for the Python sizing decision; force the
            # actual dialog to the runner's 512px logical screen budget too.
            dialog.setFixedWidth(480)
            settle(dialog)
        minimum = dialog.minimumSize().expandedTo(dialog.minimumSizeHint())
        widths = sorted({minimum.width(), minimum.width() + 160, max(1100, minimum.width())})
        for width in widths:
            dialog.resize(width, max(minimum.height(), 560))
            settle(dialog)
            check_buttons(
                dialog, f"{dialog.windowTitle() or type(dialog).__name__}{context} {dialog.width()}px",
            )
        counts["dialogs"] += 1
        dialog.hide()

    def check_wide_restoration(page, context):
        if page is window.auction_tab and page.operator_columns.direction() != QBoxLayout.LeftToRight:
            findings.append(f"{context}: wide wheel/timer columns remain stacked")
        if page is window.multichat_tab and page.columns.direction() != QBoxLayout.LeftToRight:
            findings.append(f"{context}: wide multichat columns remain stacked")
        if page is window.music_tab:
            for buttons in (
                (page.previous_btn, page.stop_btn, page.play_pause_btn, page.next_btn),
                (page.copy_player_overlay_url_btn, page.open_player_overlay_preview_btn),
            ):
                positions = [button.mapTo(page, QPoint()) for button in buttons]
                if len({position.y() for position in positions}) != 1 or any(
                    right.x() <= left.x()
                    for left, right in zip(positions, positions[1:])
                ):
                    findings.append(
                        f"{context}: wide music row did not restore: "
                        f"{[button.text() for button in buttons]!r}"
                    )

    def capture_dialog(dialog):
        check_dialog(dialog)
        return QDialog.Rejected

    for screen_width, orientation in ((512, Qt.Vertical), (3440, Qt.Horizontal)):
        for selected in range(4):
            box = QMessageBox()
            box.setAttribute(Qt.WA_DontShowOnScreen, True)
            box.setText("В библиотеке уже есть файл.")
            choices = [box.addButton(label, role) for label, role in (
                ("Использовать существующий", QMessageBox.AcceptRole),
                ("Заменить", QMessageBox.DestructiveRole),
                ("Сохранить отдельную копию", QMessageBox.ActionRole),
                ("Отмена", QMessageBox.RejectRole),
            )]
            box.setDefaultButton(choices[-1])
            box.setEscapeButton(choices[-1])
            box.ensurePolished()
            original_layout = box.findChild(QDialogButtonBox).layout()
            original_order = [original_layout.itemAt(index).widget()
                              for index in range(original_layout.count())
                              if original_layout.itemAt(index).widget() is not None]
            original_actions = [(button, button.text(), box.buttonRole(button)) for button in box.buttons()]
            QTimer.singleShot(0, choices[selected].click)
            with patch.object(QScreen, "availableGeometry", return_value=QRect(0, 0, screen_width, 768)):
                exec_responsive_message_box(box)
            if box.findChild(QDialogButtonBox).orientation() != orientation:
                findings.append(f"{screen_width}px: custom actions use the wrong orientation")
            if box.clickedButton() is not choices[selected]:
                findings.append(f"{screen_width}px: custom action selection changed")
            if box.defaultButton() is not choices[-1] or box.escapeButton() is not choices[-1]:
                findings.append(f"{screen_width}px: custom default/cancel action changed")
            if [(button, button.text(), box.buttonRole(button)) for button in box.buttons()] != original_actions:
                findings.append(f"{screen_width}px: custom button labels, order or roles changed")
            if sorted(box.buttons(), key=lambda button: (button.y(), button.x())) != original_order:
                findings.append(f"{screen_width}px: visual custom action order changed")

    with TemporaryDirectory(ignore_cleanup_errors=True) as folder:
        paths = AppPaths.from_root(folder)
        paths.ensure_runtime_dirs()
        state = QSettings(str(ui_settings_path(paths.data_dir)), QSettings.IniFormat)
        state.setValue(UI_SETTINGS_MIGRATION_KEY, True)
        state.sync()
        db = Database(paths.database_path, credential_store=MemoryCredentialStore())
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            db.set_setting("api_port", str(probe.getsockname()[1]))
        window = MainWindow(db, paths)
        window.setAttribute(Qt.WA_DontShowOnScreen, True)
        window.show()
        editor = None
        try:
            check_dialog(GameDialog(window))
            check_dialog(DeleteAllGamesDialog(10000, window))
            check_dialog(AuctionTimeDialog(
                "Время вращения", "Установить время вращения колеса:",
                value=8, minimum=1, maximum=120, suffix=" сек.", parent=window,
            ))
            check_dialog(WheelCenterPickerDialog(window))
            editor = AuctionRulesEditorDialog(
                db, window, rules_overlay_url=lambda: window.api.base_url + "/rules-overlay",
                import_background=lambda *_: None,
            )
            for label, radio in (
                ("transparent", editor.rules_obs_transparent),
                ("color", editor.rules_obs_color_mode),
                ("media", editor.rules_obs_media_mode),
            ):
                radio.setChecked(True)
                editor.rules_obs_glow.setChecked(label != "transparent")
                check_dialog(editor, f" {label}")

            with patch.object(QDialog, "exec", capture_dialog), patch.object(
                QMessageBox, "exec", capture_dialog,
            ):
                window.auction_tab._show_integration_status_dialog()
                window.auction_tab.show_rng_methods()
                window.games_tab.show_sorting_rules()
                show_readonly_text_dialog(window, "Данные проверки колеса", "Список вариантов")
                with patch.object(
                    window.auction_tab, "_current_session",
                    return_value={"status": "tie_break_required"},
                ):
                    window.auction_tab._show_tie_break_dialog()
                window.music_tab._choose_storage_mode([Path(folder) / "sample.wav"])
                window.music_tab._duplicate_action(
                    Path(folder) / "sample.wav", Path(folder) / "existing.wav",
                )
                window.auction_tab._choose_wheel_soundtrack_storage_mode(Path(folder) / "sample.wav")
                window.auction_tab._choose_auction_soundtrack_storage_mode(Path(folder) / "sample.wav")
                (window.auction_tab.soundtrack_dir / "sample.wav").write_bytes(b"fixture")
                window.auction_tab._resolve_soundtrack_copy_target(Path(folder) / "sample.wav")
                window.stream_tab._choose_background_storage_mode(Path(folder) / "sample.png", editor)
                editor._choose_save_action()
                with patch.object(editor, "_is_dirty", return_value=True):
                    editor._confirm_discard_or_save()
                editor._confirm_save_before_activation()

            narrow_message_boxes = True
            with (
                patch.object(QScreen, "availableGeometry", return_value=QRect(0, 0, 512, 768)),
                patch.object(QMessageBox, "exec", capture_dialog),
            ):
                window.music_tab._choose_storage_mode([Path(folder) / "sample.wav"])
                window.music_tab._duplicate_action(
                    Path(folder) / "sample.wav", Path(folder) / "existing.wav",
                )
                window.auction_tab._choose_wheel_soundtrack_storage_mode(Path(folder) / "sample.wav")
                window.auction_tab._choose_auction_soundtrack_storage_mode(Path(folder) / "sample.wav")
                window.auction_tab._resolve_soundtrack_copy_target(Path(folder) / "sample.wav")
                window.stream_tab._choose_background_storage_mode(Path(folder) / "sample.png", editor)
            narrow_message_boxes = False

            now = datetime.now(timezone.utc).timestamp()
            with patch.object(QDialog, "show", show_without_focus):
                window.settings_tab._show_twitch_device_code(SimpleNamespace(
                    user_code="AAAA-0000", verification_uri="https://www.twitch.tv/activate",
                    expires_at=now + 120,
                ))
                check_dialog(window.settings_tab._twitch_auth_dialog)
                window.settings_tab._close_twitch_auth_dialog(success=True)
                window.settings_tab._show_donationalerts_oauth(SimpleNamespace(
                    authorization_url="https://example.test/auth",
                    redirect_uri="http://localhost:12345/redirect", expires_at=now + 120,
                ))
                check_dialog(window.settings_tab._donationalerts_auth_dialog)
                window.settings_tab._close_donationalerts_auth_dialog(success=True)
            check_dialog(QColorDialog(window))
            check_dialog(QInputDialog(window))
            file_dialog = QFileDialog(window)
            file_dialog.setOption(QFileDialog.DontUseNativeDialog)
            check_dialog(file_dialog)

            db.sync_main_games_state([
                {"title": "Пробная игра", "sm_points": 100},
                {"title": "Второй лот", "sm_points": 50},
            ])
            window.refresh_all()
            for width in (520, 600, 720, 800, 980, 1100, 1600, 520):
                window.resize(width, 360)
                for page_name, page in window._main_tab_pages.items():
                    window._set_current_main_page(page)
                    for mode in (("max_amount", "weighted_wheel") if page is window.auction_tab else (None,)):
                        if mode is not None:
                            page.mode_combo.setCurrentIndex(page.mode_combo.findData(mode))
                        if page is window.multichat_tab:
                            page.appearance_editor.mode.setCurrentIndex(
                                page.appearance_editor.mode.findData("custom")
                            )
                        QTest.qWait(80)
                        settle(window)
                        if width == 1600:
                            check_wide_restoration(page, f"{page_name} {mode or ''} {width}px")
                        nested_tabs = [
                            tab for tab in page.findChildren(QTabWidget)
                            if tab.isVisibleTo(page)
                        ]
                        if not nested_tabs:
                            check_buttons(window, f"{page_name} {mode or ''} {width}px")
                            counts["workspaces"] += 1
                        for tab in nested_tabs:
                            original_index = tab.currentIndex()
                            for index in range(tab.count()):
                                if not tab.isTabVisible(index):
                                    continue
                                tab.setCurrentIndex(index)
                                QTest.qWait(30)
                                settle(window)
                                check_buttons(
                                    window, f"{page_name}/{tab.tabText(index)} {mode or ''} {width}px",
                                )
                                counts["workspaces"] += 1
                            tab.setCurrentIndex(original_index)
        finally:
            if editor is not None:
                editor._loading = True
                editor.hide()
            window.settings_tab._close_twitch_auth_dialog(success=True)
            window.settings_tab._close_donationalerts_auth_dialog(success=True)
            window.multichat_tab.appearance_editor.discard()
            window.close()
            window.thread_pool.waitForDone(5000)
            app.processEvents()

    if findings:
        raise AssertionError("\n".join(findings))
    print(
        f"MINIMUM_CAPTION_SCALE={os.environ.get('QT_SCALE_FACTOR', '1')} "
        f"DIALOGS={counts['dialogs']} WORKSPACES={counts['workspaces']} "
        f"CAPTIONS={counts['captions']} PASS"
    )


def main() -> int:
    if "--worker" in sys.argv:
        run_worker()
        return 0
    os.environ.setdefault("QT_QPA_PLATFORM", "windows" if sys.platform == "win32" else "offscreen")
    for scale in ("1", "1.25", "1.5", "2"):
        env = dict(os.environ, QT_SCALE_FACTOR=scale)
        subprocess.run([sys.executable, "-m", "tools.minimum_button_caption_smoke", "--worker"], env=env, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
