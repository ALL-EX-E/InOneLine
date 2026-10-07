from __future__ import annotations


from PySide6.QtCore import Qt, QThreadPool, QTimer
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QLabel, QMainWindow, QMessageBox, QTabWidget, QWidget

from ..api_server import LocalApiServer
from ..app_paths import AppPaths
from ..audio import AudioCoordinator
from ..music_player import MusicPlayerController
from ..ui_settings import open_ui_settings
from ..backup_restore import read_and_clear_restore_result
from ..constants import APP_NAME, APP_VERSION, DEFAULT_API_HOST
from ..integrations import STATUS_CONNECTED, IntegrationManager, IntegrationRegistry
from ..twitch import TwitchAdapter
from ..twitch_b4 import TwitchChannelPointsService, TwitchEventSubRuntime
from ..donationalerts import DonationAlertsAdapter
from ..donationalerts_runtime import DonationAlertsDonationService, DonationAlertsRuntime
from ..database import Database
from ..workers import FunctionWorker
from .common import APP_STYLE, autosize_compact_columns_once
from .games import GamesTab
from .public import PublicTab
from .stream import StreamTab
from .music import MusicTab
from .auction import AuctionTab
from .completed_auction_history import CompletedAuctionHistoryTab
from .log import LogTab
from .settings import SettingsTab

class MainWindow(QMainWindow):
    def __init__(self, db: Database, paths: AppPaths):
        super().__init__()
        self.db = db
        self.paths = paths
        self._ui_settings = open_ui_settings(paths.data_dir)
        self.project_dir = paths.root_dir
        self.thread_pool = QThreadPool.globalInstance()
        # The application uses short, gated background jobs rather than CPU
        # fan-out. On high-core-count PCs Qt's default global pool can keep many
        # idle worker threads (and their stacks) resident after bursts of XLSX,
        # backup, integration and log work. Cap only the upper bound and let
        # idle threads expire sooner; this reduces worst-case RAM without
        # serializing normal work on smaller machines.
        self.thread_pool.setMaxThreadCount(
            min(max(1, self.thread_pool.maxThreadCount()), 8)
        )
        self.thread_pool.setExpiryTimeout(10_000)
        self.integration_registry = IntegrationRegistry()
        self.twitch_adapter = TwitchAdapter()
        self.donationalerts_adapter = DonationAlertsAdapter()
        self.integration_registry.register(self.twitch_adapter)
        self.integration_registry.register(self.donationalerts_adapter)
        self.integration_manager = IntegrationManager(db, self.integration_registry)
        self.twitch_channel_points_service = TwitchChannelPointsService(
            db,
            self.integration_manager,
        )
        self.twitch_eventsub_runtime = TwitchEventSubRuntime(
            self.twitch_channel_points_service,
        )
        self.donationalerts_service = DonationAlertsDonationService(
            db,
            self.integration_manager,
        )
        self.donationalerts_runtime = DonationAlertsRuntime(
            self.donationalerts_service,
        )
        self._integration_health_worker = None
        self._integration_health_timer = QTimer(self)
        self._integration_health_timer.setInterval(60 * 60 * 1000)
        self._integration_health_timer.timeout.connect(self._validate_active_integrations)
        self._startup_backup_worker = None
        self.setStyleSheet(APP_STYLE)

        self.api = LocalApiServer(db, DEFAULT_API_HOST, int(db.get_setting("api_port", "8765")))
        try:
            self.api.start()
        except OSError:
            pass

        self.setWindowTitle(f"{APP_NAME} {APP_VERSION}")
        self.setMinimumSize(1100, 700)
        self.resize(1550, 900)
        # R1.0.7 pre-release geometry contract: after startup the top-level
        # window size is owned by the user/window manager. Child layouts, tab
        # switches and modal workflows may reflow content, but must never
        # resize the outer MainWindow implicitly.

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self._dirty_tabs: set[QWidget] = set()

        self.games_tab = GamesTab(db, self.notify_game_data_changed)
        self.public_tab = PublicTab(db, self.api)
        self.stream_tab = StreamTab(db, self.api)
        self.audio_coordinator = AudioCoordinator(self)
        self.music_player = MusicPlayerController(
            db,
            self.audio_coordinator,
            self,
        )
        self.music_tab = MusicTab(db, self.music_player)
        self.api.set_music_player_state_provider(self.music_player.browser_state)
        self.api.set_music_player_cover_provider(self.music_player.cover_bytes)
        self.auction_tab = AuctionTab(
            db,
            self.refresh_game_data_views,
            integration_manager=self.integration_manager,
            open_integrations=self.open_integrations_settings,
            integration_runtime_health=self._integration_runtime_health_snapshot,
            audio_coordinator=self.audio_coordinator,
        )
        self.api.set_auction_lots_state_provider(
            self.auction_tab.auction_lots_overlay_state
        )
        self.music_tab.copy_player_overlay_url_btn.clicked.connect(
            self.stream_tab.copy_music_player_overlay_url
        )
        self.music_tab.open_player_overlay_preview_btn.clicked.connect(
            self.stream_tab.open_music_player_overlay_preview
        )
        # Duplicate navigation controls call the exact same Stream/OBS actions.
        # No second URL or preview logic is maintained in Games/Auction.
        self.games_tab.copy_list_overlay_url_btn.clicked.connect(
            self.stream_tab.copy_list_overlay_url
        )
        self.games_tab.open_list_overlay_preview_btn.clicked.connect(
            self.stream_tab.open_list_overlay_preview
        )
        self.auction_tab.conduct_copy_lots_overlay_url_btn.clicked.connect(
            self.stream_tab.copy_auction_lots_overlay_url
        )
        self.auction_tab.conduct_open_lots_overlay_preview_btn.clicked.connect(
            self.stream_tab.open_auction_lots_overlay_preview
        )
        # R1.0.9: shared main-list XLSX controls belong to the Games workspace.
        # The synchronization engine itself remains on AuctionTab to preserve
        # the already-tested read/write/poll semantics unchanged.
        self.games_tab.attach_shared_xlsx_controls(self.auction_tab)
        self.completed_history_tab = CompletedAuctionHistoryTab(db)
        self.log_tab = LogTab(db)
        self.settings_tab = SettingsTab(
            db,
            paths,
            self.api,
            self.auction_tab.refresh_rng_availability,
            self.auction_tab.refresh_auction_settings,
            conversion_units_provider=self.integration_manager.conversion_units,
            external_points_applied=self.notify_game_data_changed,
            integration_manager=self.integration_manager,
            integration_status_changed=self.auction_tab.refresh_integration_status,
            twitch_channel_points_service=self.twitch_channel_points_service,
            twitch_runtime_wake=self.twitch_eventsub_runtime.wake,
            donationalerts_service=self.donationalerts_service,
            donationalerts_runtime_wake=self.donationalerts_runtime.wake,
        )
        # D19 quick picker and Settings edit the exact same persisted center
        # asset. Keep the Settings combo synchronized when the user picks one
        # directly on the local wheel.
        self.auction_tab.centerImageChanged.connect(
            self.settings_tab._refresh_wheel_center_image_library
        )

        # Одно состояние списка для вкладок «Игры» и «Публичный список».
        self._lists_visible = True
        self.games_tab.list_toggle_btn.clicked.disconnect(
            self.games_tab.toggle_games_list
        )
        self.games_tab.list_toggle_btn.clicked.connect(
            self.toggle_synced_lists
        )
        self.public_tab.list_toggle_btn.clicked.disconnect(
            self.public_tab.toggle_public_list
        )
        self.public_tab.list_toggle_btn.clicked.connect(
            self.toggle_synced_lists
        )

        # Синхронизированный поиск маршрутизируется самими вкладками через
        # sync_search_text(). MainWindow централизованно решает, какую таблицу
        # обновить сейчас, а какую только пометить dirty.

        self.tabs.addTab(self.games_tab, "Список")
        self.tabs.addTab(self.public_tab, "Публичный список")
        self.tabs.addTab(self.stream_tab, "Стрим / OBS")
        self.tabs.addTab(self.music_tab, "Музыка")
        self.tabs.addTab(self.auction_tab, "Аукцион")
        self.tabs.addTab(self.completed_history_tab, "История аукционов")
        self.tabs.addTab(self.log_tab, "Журнал")
        self.tabs.addTab(self.settings_tab, "Настройки")
        self.tabs.currentChanged.connect(self._handle_tab_changed)
        # AuctionTab создаётся до добавления в основной QTabWidget, поэтому
        # сразу синхронизируем его high-frequency visual timers с фактической
        # видимостью первой основной вкладки.
        self.auction_tab.set_main_tab_visible(
            self.tabs.currentWidget() is self.auction_tab
        )

        self._make_menu()
        self._update_status_bar()
        self._restore_ui_state()
        # Initial table population happens while MainWindow is still hidden.
        # Native Windows/QSS may finalize the section font only after show(), so
        # run one event-loop-deferred pass using the real polished metrics.
        QTimer.singleShot(0, self._finalize_compact_headers_after_polish)
        QTimer.singleShot(150, self._show_restore_result)
        QTimer.singleShot(350, self._startup_backup)
        # Connected third-party OAuth sessions are validated at app startup and
        # then hourly. Only enabled connected adapters are checked; all provider
        # work stays off the GUI thread.
        QTimer.singleShot(500, self._validate_active_integrations)
        self._integration_health_timer.start()
        self.twitch_eventsub_runtime.start()
        self.donationalerts_runtime.start()

    def _finalize_compact_headers_after_polish(self):
        """Re-floor compact table headers after the native style is polished."""
        targets = (
            (self.games_tab.table, self.games_tab._COMPACT_COLUMNS),
            (self.public_tab.table, self.public_tab._COMPACT_COLUMNS),
            (self.auction_tab.table, self.auction_tab._LOT_COMPACT_COLUMNS),
            (
                self.auction_tab.conduct_table,
                self.auction_tab._CONDUCT_COMPACT_COLUMNS,
            ),
        )
        for table, columns in targets:
            autosize_compact_columns_once(table, columns)

    def sync_search_text(self, source: str, text: str):
        """Synchronize search text while rebuilding only the visible top-level tab."""
        controls = {
            "games": (self.games_tab.search, self.games_tab),
            "public": (self.public_tab.search, self.public_tab),
            "auction": (self.auction_tab.search, self.auction_tab),
            "auction_conduct": (
                self.auction_tab.conduct_search,
                self.auction_tab,
            ),
        }
        source_pair = controls.get(source)
        if source_pair is None:
            return

        owners = [source_pair[1]]
        for key, (control, owner) in controls.items():
            if key == source or control.text() == text:
                continue
            control.blockSignals(True)
            control.setText(text)
            control.blockSignals(False)
            if owner not in owners:
                owners.append(owner)

        # Reuse the existing dirty-tab mechanism: one visible refresh at most,
        # all hidden synchronized tables catch up only when they are opened.
        self._refresh_visible_or_mark_dirty(owners)

    def _refresh_dirty_search_target(self, widget, *, force: bool = False):
        """Catch up one dirty hidden table for an explicit Find/Enter selection."""
        if widget not in self._dirty_tabs:
            return
        self._dirty_tabs.discard(widget)
        if force and hasattr(widget, "refresh_force"):
            widget.refresh_force()
        else:
            widget.refresh()

    def sync_search_result(self, game_id: int, source: str):
        """Synchronize the first explicit Find/Enter result between game lists."""
        self.set_synced_lists_visible(True)

        game = self.db.get_game(game_id)
        if game is None:
            return

        if source in ("public", "auction", "auction_conduct"):
            # ensure_visible already performs the one required Games refresh
            # after resetting the status filter; consume its dirty marker here.
            self._dirty_tabs.discard(self.games_tab)
            self.games_tab.select_synced_search_result(
                game_id,
                ensure_visible=True,
            )
        else:
            self._refresh_dirty_search_target(self.games_tab)
            self.games_tab.select_synced_search_result(game_id)

        # Архив не отображается ни в Public, ни в Auction.
        if not game.archived:
            self._refresh_dirty_search_target(self.public_tab)
            self.public_tab.select_synced_search_result(game_id)

        # Auction's A8 hidden guard is intentionally bypassed only for this
        # explicit Find/Enter catch-up so selection sees the synchronized query.
        self._refresh_dirty_search_target(self.auction_tab, force=True)
        self.auction_tab.select_synced_search_result(game_id)

    def set_synced_lists_visible(
        self,
        visible: bool,
        adjust_window: bool = True,
    ):
        """Синхронно показывает/скрывает списки без изменения размера окна."""
        self._lists_visible = bool(visible)

        # ``adjust_window`` is kept for call-site compatibility with the
        # accepted pre-1.0 code, but R1.0.7 deliberately ignores it. Hiding or
        # showing a child table is not a user request to resize MainWindow.
        _ = adjust_window
        self.games_tab.set_games_list_visible(
            self._lists_visible,
            adjust_window=False,
        )
        self.public_tab.set_public_list_visible(
            self._lists_visible,
            adjust_window=False,
        )

    def _handle_tab_changed(self, index: int):
        """Компактная высота используется только на вкладках со скрытой таблицей."""
        if index < 0 or index >= self.tabs.count():
            return

        current = self.tabs.widget(index)

        auction_refreshed = self.auction_tab.set_main_tab_visible(
            current is self.auction_tab,
            refresh_pending=(
                current is self.auction_tab
                and self.auction_tab in self._dirty_tabs
            ),
        )
        if auction_refreshed:
            # set_main_tab_visible() already performed the single catch-up
            # refresh required when Auction becomes visible again.
            self._dirty_tabs.discard(self.auction_tab)

        if current in self._dirty_tabs:
            self._dirty_tabs.discard(current)
            refresh = getattr(current, "refresh", None)
            if callable(refresh):
                refresh()
        elif current is self.stream_tab:
            # External media can disappear/move without any in-app mutation, so
            # Stream/OBS must re-check the selected reference every time the
            # operator returns to this tab instead of waiting for restart/F5.
            self.stream_tab._refresh_selected_background_availability()
        elif current is self.music_tab:
            # The managed music directory is the library source of truth.
            # Returning to the tab is an explicit refresh point for files
            # copied/removed outside InOneLine.
            self.music_tab.refresh()

        # После смены основной вкладки держим focus на контейнере вкладок,
        # а не на первом поле ввода новой страницы.
        QTimer.singleShot(
            0,
            lambda: self.tabs.setFocus(Qt.OtherFocusReason),
        )

        # R1.0.7: tab changes may refresh/reflow child widgets but never change
        # the outer window geometry. The former compact-height mode caused
        # visible jumps between tabs and also interacted with modal workflows.
        if current is self.stream_tab and not self._lists_visible:
            QTimer.singleShot(0, self._scroll_stream_to_top)

    def _scroll_stream_to_top(self):
        bar = self.stream_tab.stream_scroll.verticalScrollBar()
        bar.setValue(bar.minimum())

    def toggle_synced_lists(self):
        """Одна кнопка на любой из двух вкладок переключает оба списка."""
        self.set_synced_lists_visible(not self._lists_visible)

    def _restore_ui_state(self):
        """Восстанавливает окно и единое состояние списков."""
        settings = self._ui_settings

        # Состояние списков восстанавливается независимо от геометрии.
        # R1.0.7 больше не имеет автоматического компактного размера окна.
        legacy_games_visible = settings.value(
            "games/list_visible",
            True,
            type=bool,
        )
        list_visible = settings.value(
            "lists/visible",
            legacy_games_visible,
            type=bool,
        )

        geometry = settings.value("main_window/geometry")
        if geometry is not None:
            self.restoreGeometry(geometry)

        tab_index = settings.value("main_window/tab_index", 0, type=int)
        if 0 <= tab_index < self.tabs.count():
            self.tabs.setCurrentIndex(tab_index)

        self.set_synced_lists_visible(
            list_visible,
            adjust_window=False,
        )

        # Синхронизируем runtime-видимость текущей вкладки после restoreGeometry,
        # но обработчик больше не меняет размеры MainWindow.
        QTimer.singleShot(0, lambda: self._handle_tab_changed(self.tabs.currentIndex()))

        # Максимизированное состояние храним отдельно.
        was_maximized = settings.value(
            "main_window/maximized", False, type=bool
        )
        if was_maximized:
            QTimer.singleShot(0, self.showMaximized)

    def _save_ui_state(self):
        """Сохраняет пользовательское состояние интерфейса."""
        settings = self._ui_settings
        settings.setValue("main_window/geometry", self.saveGeometry())
        settings.setValue("main_window/maximized", self.isMaximized())
        settings.setValue("main_window/tab_index", self.tabs.currentIndex())

        settings.setValue(
            "lists/visible",
            self._lists_visible,
        )
        # Дублируем значение в старые ключи для совместимости.
        settings.setValue(
            "games/list_visible",
            self._lists_visible,
        )
        settings.setValue(
            "public/list_visible",
            self._lists_visible,
        )
        settings.sync()

    def _integration_runtime_health_snapshot(self) -> dict[str, dict]:
        """Local-only health used by the closed Conduct integration indicator."""
        result: dict[str, dict] = {}

        twitch_ready = self.twitch_channel_points_service.connection_ready()
        twitch_rewards = bool(self.twitch_channel_points_service.managed_reward_ids())
        twitch_expected = bool(twitch_ready and twitch_rewards)
        twitch_error = (
            str(self.twitch_eventsub_runtime.last_error or "").strip()
            if twitch_expected else ""
        )
        if twitch_ready:
            if not twitch_rewards:
                twitch_detail = "Channel Points: награды не настроены"
            elif self.twitch_eventsub_runtime.connected:
                twitch_detail = "EventSub подключён"
            else:
                twitch_detail = "EventSub подключается"
            result["twitch"] = {
                "expected": twitch_expected,
                "connected": bool(self.twitch_eventsub_runtime.connected),
                "error": twitch_error,
                "detail": twitch_detail,
            }

        donation_ready = self.donationalerts_service.connection_ready()
        if donation_ready:
            donation_error = str(self.donationalerts_runtime.last_error or "").strip()
            result["donationalerts"] = {
                "expected": True,
                "connected": bool(self.donationalerts_runtime.connected),
                "error": donation_error,
                "detail": (
                    "Realtime подключён"
                    if self.donationalerts_runtime.connected
                    else "Realtime подключается"
                ),
            }

        return result

    def _validate_active_integrations(self) -> None:
        if self._integration_health_worker is not None:
            return
        active_keys = []
        for adapter in self.integration_registry.adapters():
            row = self.db.get_integration_connection(adapter.service_key)
            if row and row.get("enabled") and row.get("status") == STATUS_CONNECTED:
                active_keys.append(adapter.service_key)
        if not active_keys:
            return

        def validate_all():
            return [
                self.integration_manager.check_connection(service_key)
                for service_key in active_keys
            ]

        worker = FunctionWorker(validate_all)
        self._integration_health_worker = worker
        worker.signals.result.connect(lambda _result: self._integration_health_done())
        worker.signals.error.connect(lambda _exc: self._integration_health_done())
        worker.signals.finished.connect(self._integration_health_finished)
        self.thread_pool.start(worker)

    def _integration_health_done(self) -> None:
        if hasattr(self, "settings_tab"):
            self.settings_tab._refresh_integrations()
        if hasattr(self, "auction_tab"):
            self.auction_tab.refresh_integration_status()
        if hasattr(self, "twitch_eventsub_runtime"):
            self.twitch_eventsub_runtime.wake()
        if hasattr(self, "donationalerts_runtime"):
            self.donationalerts_runtime.wake()

    def _integration_health_finished(self) -> None:
        self._integration_health_worker = None

    def open_integrations_settings(self) -> None:
        if not hasattr(self, "settings_tab"):
            return
        self.tabs.setCurrentWidget(self.settings_tab)
        self.settings_tab.settings_tabs.setCurrentWidget(
            self.settings_tab.integration_scroll
        )
        self.settings_tab._refresh_integrations()

    def _make_menu(self):
        refresh_action = QAction("Обновить", self)
        refresh_action.setShortcut(QKeySequence("F5"))
        refresh_action.triggered.connect(self.refresh_all)
        self.addAction(refresh_action)

        self.refresh_hint_label = QLabel("F5 — обновить данные во всех разделах", self)
        self.refresh_hint_label.setContentsMargins(8, 0, 8, 0)
        self.refresh_hint_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.menuBar().setCornerWidget(self.refresh_hint_label, Qt.TopLeftCorner)

    def _show_restore_result(self):
        result = read_and_clear_restore_result(self.paths.root_dir)
        if not result:
            return
        full_restore = result.get("restore_kind") == "full"
        if result.get("success"):
            safety = result.get("safety_backup", "—")
            schema = result.get("restored_schema", "—")
            games = result.get("restored_games", "—")
            if full_restore:
                QMessageBox.information(
                    self,
                    "Полное восстановление завершено",
                    "Полная резервная копия успешно восстановлена.\n\n"
                    f"Исходная schema: {schema}\n"
                    f"Игр в восстановленной копии: {games}\n\n"
                    "Полное состояние непосредственно перед восстановлением сохранено здесь:\n"
                    f"{safety}",
                )
            else:
                QMessageBox.information(
                    self,
                    "Восстановление завершено",
                    "Резервная копия успешно восстановлена.\n\n"
                    f"Исходная schema: {schema}\n"
                    f"Игр в восстановленной копии: {games}\n\n"
                    "Состояние базы непосредственно перед восстановлением сохранено здесь:\n"
                    f"{safety}",
                )
        else:
            if full_restore:
                QMessageBox.critical(
                    self,
                    "Полное восстановление не выполнено",
                    "Текущие данные не были заменены либо были автоматически возвращены из safety-backup.\n\n"
                    + str(result.get("error", "Неизвестная ошибка полного восстановления.")),
                )
            else:
                QMessageBox.critical(
                    self,
                    "Восстановление не выполнено",
                    "Текущая база не была заменена либо была автоматически возвращена из safety-backup.\n\n"
                    + str(result.get("error", "Неизвестная ошибка восстановления.")),
                )

    def _startup_backup(self):
        if self._startup_backup_worker is not None:
            return

        def create_backup():
            path = self.db.backup_isolated(self.paths.backups_dir)
            self.db.prune_backups(self.paths.backups_dir, 30)
            return path

        worker = FunctionWorker(create_backup)
        self._startup_backup_worker = worker
        worker.signals.finished.connect(self._startup_backup_finished)
        self.thread_pool.start(worker)

    def _startup_backup_finished(self):
        self._startup_backup_worker = None

    def _update_status_bar(self):
        # Техническая строка состояния скрыта из основного интерфейса.
        # API продолжает работать, но его адрес и состояние не занимают место
        # внизу окна.
        self.statusBar().clearMessage()
        self.statusBar().hide()

    def _refresh_visible_or_mark_dirty(self, widgets):
        current = self.tabs.currentWidget()
        for widget in widgets:
            if widget is current:
                widget.refresh()
                self._dirty_tabs.discard(widget)
            else:
                self._dirty_tabs.add(widget)

    def refresh_game_data_views(self):
        """Refresh visible game-dependent data; defer hidden heavy tables."""
        self.auction_tab.shared_xlsx_local_data_changed()
        self.public_tab.public_xlsx_local_data_changed()
        self._refresh_visible_or_mark_dirty(
            (self.games_tab, self.public_tab, self.auction_tab, self.completed_history_tab, self.log_tab)
        )
        self._update_status_bar()

    def notify_game_data_changed(self):
        """Game edits also invalidate the current-game selector on Stream/OBS."""
        self.auction_tab.shared_xlsx_local_data_changed()
        self.public_tab.public_xlsx_local_data_changed()
        self._refresh_visible_or_mark_dirty(
            (
                self.games_tab,
                self.public_tab,
                self.auction_tab,
                self.completed_history_tab,
                self.log_tab,
                self.stream_tab,
            )
        )
        self._update_status_bar()

    def refresh_all(self):
        """Explicit F5 refresh remains eager by user request."""
        for widget in (
            self.games_tab,
            self.public_tab,
            self.stream_tab,
            self.music_tab,
            self.completed_history_tab,
            self.log_tab,
        ):
            widget.refresh()
        self.auction_tab.refresh_force()
        self._dirty_tabs.clear()
        self._update_status_bar()

    def closeEvent(self, event):
        self._integration_health_timer.stop()
        self.twitch_adapter.cancel_authorization()
        self.donationalerts_adapter.cancel_authorization()
        self.twitch_eventsub_runtime.stop()
        self.donationalerts_runtime.stop()
        self._save_ui_state()
        self.public_tab.shutdown_public_xlsx()
        self.auction_tab.shutdown_shared_xlsx()
        # Unregister Music Player first: Auction shutdown can then release its
        # owner without briefly restoring audible playback while the app exits.
        self.music_player.shutdown()
        self.auction_tab.shutdown_audio()
        self.api.stop()
        super().closeEvent(event)

