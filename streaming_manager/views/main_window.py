from __future__ import annotations


from PySide6.QtCore import QEvent, QSize, Qt, QThreadPool, QTimer
from PySide6.QtGui import QAction, QColor, QIcon, QKeySequence, QPainter, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QMainWindow,
    QMessageBox,
    QScrollArea,
    QSizePolicy,
    QTableView,
    QStyle,
    QTabWidget,
    QWidget,
)

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
from .common import APP_STYLE, autosize_compact_columns_once, reflow_narrow_rows
from .games import GamesTab
from .public import PublicTab
from .stream import StreamTab
from .music import MusicTab
from .auction import AuctionTab
from .completed_auction_history import CompletedAuctionHistoryTab
from .log import LogTab
from .settings import SettingsTab


_LEGACY_MAIN_TAB_ORDER = (
    "list",
    "public",
    "stream",
    "music",
    "auction",
    "auction_history",
    "log",
    "settings",
)

_COMPACT_TAB_LABELS = {
    "Список": "Спис",
    "Публичный список": "Публ",
    "Музыка": "Муз",
    "Аукцион": "Аук",
    "История аукционов": "Ист",
    "Журнал": "Жур",
    "Стрим / OBS": "OBS",
    "Настройки": "Наст",
}
_TAB_ICON_COLORS = {
    "Список": "#54C7A2",
    "Публичный список": "#57A8E8",
    "Музыка": "#B889F5",
    "Аукцион": "#F2A65A",
    "История аукционов": "#E5C454",
    "Журнал": "#59B8C9",
    "Стрим / OBS": "#EA6F78",
    "Настройки": "#87A9FF",
}


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
        self.setMinimumSize(520, 360)
        self.resize(1550, 900)
        # R1.0.7 pre-release geometry contract: after startup the top-level
        # window size is owned by the user/window manager. Child layouts, tab
        # switches and modal workflows may reflow content, but must never
        # resize the outer MainWindow implicitly.

        self.tabs = QTabWidget()
        self.tabs.setUsesScrollButtons(False)
        self.tabs.setIconSize(QSize(18, 18))
        self.tabs.tabBar().setExpanding(False)
        self.tabs.tabBar().setElideMode(Qt.ElideRight)
        self.tabs.setMinimumSize(0, 0)
        self.setCentralWidget(self.tabs)
        # The MainWindow resize can run before QTabWidget receives its final
        # geometry. Recheck after the tab shell and tab bar themselves resize.
        self.tabs.installEventFilter(self)
        self.tabs.tabBar().installEventFilter(self)
        self._main_tab_scroll_by_page: dict[QWidget, QScrollArea] = {}
        self._main_tab_page_by_scroll: dict[QScrollArea, QWidget] = {}
        self._main_tab_title_by_page: dict[QWidget, str] = {}
        self._main_tab_compact_title_by_page: dict[QWidget, str] = {}
        self._main_tab_icon_by_page: dict[QWidget, QIcon] = {}
        self._responsive_watch_widgets: set[QWidget] = set()
        self._responsive_nested_scroll_vertical_policy: dict[QScrollArea, Qt.ScrollBarPolicy] = {}
        self._main_tabs_compact = False
        self._responsive_layout_timer = QTimer(self)
        self._responsive_layout_timer.setSingleShot(True)
        self._responsive_layout_timer.timeout.connect(self._update_responsive_layout)
        self._responsive_layout_settle_timer = QTimer(self)
        self._responsive_layout_settle_timer.setSingleShot(True)
        self._responsive_layout_settle_timer.setInterval(40)
        self._responsive_layout_settle_timer.timeout.connect(
            self._queue_responsive_layout_update
        )

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

        # Синхронизированный поиск маршрутизируется самими вкладками через
        # sync_search_text(). MainWindow централизованно решает, какую таблицу
        # обновить сейчас, а какую только пометить dirty.

        self._add_main_tab(self.games_tab, "Список", QStyle.SP_FileDialogListView)
        self._add_main_tab(self.public_tab, "Публичный список", QStyle.SP_DirLinkIcon)
        self._add_main_tab(self.music_tab, "Музыка", QStyle.SP_MediaVolume)
        self._add_main_tab(self.auction_tab, "Аукцион", QStyle.SP_DialogApplyButton)
        self._add_main_tab(self.completed_history_tab, "История аукционов", QStyle.SP_BrowserReload)
        self._add_main_tab(self.log_tab, "Журнал", QStyle.SP_MessageBoxInformation)
        self._add_main_tab(self.stream_tab, "Стрим / OBS", QStyle.SP_MediaPlay)
        self._add_main_tab(self.settings_tab, "Настройки", QStyle.SP_FileDialogContentsView)
        self._main_tab_pages = {
            "list": self.games_tab,
            "public": self.public_tab,
            "music": self.music_tab,
            "auction": self.auction_tab,
            "auction_history": self.completed_history_tab,
            "log": self.log_tab,
            "stream": self.stream_tab,
            "settings": self.settings_tab,
        }
        self._main_tab_key_by_page = {
            page: key for key, page in self._main_tab_pages.items()
        }
        self.tabs.currentChanged.connect(self._handle_tab_changed)
        # AuctionTab создаётся до добавления в основной QTabWidget, поэтому
        # сразу синхронизируем его high-frequency visual timers с фактической
        # видимостью первой основной вкладки.
        self.auction_tab.set_main_tab_visible(
            self._current_main_page() is self.auction_tab
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
            (self.auction_tab.table, self.auction_tab._lot_compact_columns),
            (
                self.auction_tab.conduct_table,
                self.auction_tab._conduct_compact_columns,
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

    def _add_main_tab(
        self, page: QWidget, title: str, icon_pixmap: QStyle.StandardPixmap
    ) -> QScrollArea:
        """Give each workspace its own scrollbars inside the fixed tab shell."""
        scroll = QScrollArea(self.tabs)
        scroll.setObjectName(
            f"main_tab_scroll_{len(self._main_tab_scroll_by_page)}"
        )
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setMinimumSize(0, 0)
        scroll.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)

        page.setMinimumWidth(0)
        page.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.MinimumExpanding)
        for nested_tabs in page.findChildren(QTabWidget):
            nested_tabs.currentChanged.connect(
                lambda *_: self._queue_responsive_layout_update()
            )
            for index in range(nested_tabs.count()):
                nested_page = nested_tabs.widget(index)
                nested_page.setMinimumWidth(0)
                nested_page.setSizePolicy(
                    QSizePolicy.Ignored, QSizePolicy.MinimumExpanding
                )
        for nested_scroll in page.findChildren(QScrollArea):
            self._responsive_nested_scroll_vertical_policy[nested_scroll] = (
                nested_scroll.verticalScrollBarPolicy()
            )
            nested_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            if nested_scroll.widget() is not None:
                nested_scroll.widget().setMinimumWidth(0)
                nested_scroll.widget().setSizePolicy(
                    QSizePolicy.Ignored, QSizePolicy.MinimumExpanding
                )
        for watched in (page, *page.findChildren(QWidget)):
            if watched not in self._responsive_watch_widgets:
                watched.installEventFilter(self)
                self._responsive_watch_widgets.add(watched)
        scroll.setWidget(page)
        scroll.setAccessibleName(title)
        self._main_tab_scroll_by_page[page] = scroll
        self._main_tab_page_by_scroll[scroll] = page
        self._main_tab_title_by_page[page] = title
        self._main_tab_compact_title_by_page[page] = _COMPACT_TAB_LABELS[title]
        self._main_tab_icon_by_page[page] = self._make_tinted_tab_icon(
            icon_pixmap,
            _TAB_ICON_COLORS[title],
        )
        tab_index = self.tabs.addTab(scroll, title)
        self.tabs.setTabToolTip(tab_index, title)
        self.tabs.setTabWhatsThis(tab_index, title)
        scroll.viewport().installEventFilter(self)
        self._queue_responsive_layout_update()
        return scroll

    def _make_tinted_tab_icon(
        self, icon_pixmap: QStyle.StandardPixmap, tint_color: str
    ) -> QIcon:
        source_icon = self.style().standardIcon(icon_pixmap)
        if source_icon.isNull():
            source_icon = self.style().standardIcon(QStyle.SP_FileIcon)
        source = source_icon.pixmap(QSize(18, 18))
        if source.isNull():
            return source_icon

        def tinted(color: str) -> QPixmap:
            pixmap = QPixmap(source.size())
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            painter.drawPixmap(0, 0, source)
            painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
            painter.fillRect(pixmap.rect(), QColor(color))
            painter.end()
            return pixmap

        icon = QIcon()
        for mode in (QIcon.Mode.Normal, QIcon.Mode.Active, QIcon.Mode.Selected):
            for state in (QIcon.State.Off, QIcon.State.On):
                icon.addPixmap(tinted(tint_color), mode, state)
        return icon

    def _queue_responsive_layout_update(self) -> None:
        timer = getattr(self, "_responsive_layout_timer", None)
        if timer is not None:
            timer.start(0)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._queue_responsive_layout_update()

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.Resize:
            is_tab_layout = watched is self.tabs or watched is self.tabs.tabBar()
            is_workspace_viewport = any(
                watched is scroll.viewport()
                for scroll in self._main_tab_scroll_by_page.values()
            )
            if is_tab_layout or is_workspace_viewport:
                self._queue_responsive_layout_update()
        elif (
            watched in self._responsive_watch_widgets
            and event.type()
            in (
                QEvent.Type.LayoutRequest,
                QEvent.Type.Show,
                QEvent.Type.Hide,
                QEvent.Type.ChildAdded,
                QEvent.Type.ChildRemoved,
            )
        ):
            self._queue_responsive_layout_update()
        return super().eventFilter(watched, event)

    def _update_responsive_layout(self) -> None:
        if not self.tabs.count():
            return

        tab_bar = self.tabs.tabBar()
        metrics = tab_bar.fontMetrics()
        full_width = sum(
            metrics.horizontalAdvance(title) + 40
            for title in self._main_tab_title_by_page.values()
        )
        available_width = max(0, self.tabs.width() - 20)
        compact = full_width > available_width
        if compact != self._main_tabs_compact:
            self._main_tabs_compact = compact
            tab_bar.setExpanding(compact)
            self.tabs.setIconSize(QSize(14, 14) if compact else QSize(18, 18))
            tab_bar.setStyleSheet(
                "QTabBar::tab { padding: 4px 3px; }" if compact else ""
            )
            for index in range(self.tabs.count()):
                scroll = self.tabs.widget(index)
                page = self._main_tab_page_by_scroll[scroll]
                title = self._main_tab_title_by_page[page]
                compact_title = self._main_tab_compact_title_by_page[page]
                self.tabs.setTabText(index, compact_title if compact else title)
                self.tabs.setTabIcon(
                    index,
                    self._main_tab_icon_by_page[page] if compact else QIcon(),
                )
                self.tabs.setTabToolTip(index, title)
                self.tabs.setTabWhatsThis(index, title)

        for page, scroll in self._main_tab_scroll_by_page.items():
            viewport_width = scroll.viewport().width()
            if viewport_width <= 0:
                continue

            if page.minimumWidth() != 0:
                page.setMinimumWidth(0)
            if page.maximumWidth() != viewport_width:
                page.setMaximumWidth(viewport_width)
            page_policy = page.sizePolicy()
            if page_policy.horizontalPolicy() != QSizePolicy.Ignored:
                page.setSizePolicy(
                    QSizePolicy.Ignored,
                    page_policy.verticalPolicy(),
                )

            compact_workspace = viewport_width <= 980
            if page is self.games_tab:
                page.set_compact_controls(compact_workspace, viewport_width)
                margins = page.layout().contentsMargins()
                table_width = max(
                    1,
                    viewport_width - margins.left() - margins.right(),
                )
                if page.table.maximumWidth() != table_width:
                    page.table.setMaximumWidth(table_width)
            else:
                reflow_narrow_rows(
                    page,
                    viewport_width,
                    compact=compact_workspace,
                )

            for table in page.findChildren(QTableView):
                if page is self.games_tab and table is page.table:
                    continue
                if table.minimumWidth() != 0:
                    table.setMinimumWidth(0)
                if table.maximumWidth() != viewport_width:
                    table.setMaximumWidth(viewport_width)
                table_policy = table.sizePolicy()
                if table_policy.horizontalPolicy() != QSizePolicy.Ignored:
                    table.setSizePolicy(
                        QSizePolicy.Ignored,
                        table_policy.verticalPolicy(),
                    )

            for nested_scroll, normal_vertical_policy in (
                self._responsive_nested_scroll_vertical_policy.items()
            ):
                if nested_scroll is page or not page.isAncestorOf(nested_scroll):
                    continue
                target_vertical_policy = (
                    Qt.ScrollBarAsNeeded
                    if compact_workspace
                    else normal_vertical_policy
                )
                if (
                    nested_scroll.horizontalScrollBarPolicy()
                    != Qt.ScrollBarAlwaysOff
                ):
                    nested_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
                if nested_scroll.verticalScrollBarPolicy() != target_vertical_policy:
                    nested_scroll.setVerticalScrollBarPolicy(target_vertical_policy)

    def _current_main_page(self) -> QWidget | None:
        current = self.tabs.currentWidget()
        return self._main_tab_page_by_scroll.get(current, current)

    def _set_current_main_page(self, page: QWidget) -> None:
        self.tabs.setCurrentWidget(self._main_tab_scroll_by_page.get(page, page))

    def _handle_tab_changed(self, index: int):
        """Refresh the selected tab without changing the outer window geometry."""
        if index < 0 or index >= self.tabs.count():
            return

        self._queue_responsive_layout_update()
        # QScrollArea can assign its final viewport width after currentChanged.
        # Reflow once more after that first layout pass, without needing a resize.
        self._responsive_layout_settle_timer.start()
        current = self._main_tab_page_by_scroll.get(self.tabs.widget(index))

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

    def _restore_ui_state(self):
        """Restore window state and discard obsolete list-hiding preferences."""
        settings = self._ui_settings

        # UI-025 keeps both tables visible. Remove only the retired preferences;
        # geometry, selected tab and the legacy migration backup remain intact.
        for key in (
            "lists/visible",
            "games/list_visible",
            "public/list_visible",
        ):
            settings.remove(key)
        settings.sync()

        geometry = settings.value("main_window/geometry")
        if geometry is not None:
            self.restoreGeometry(geometry)

        stored_tab_key = settings.value("main_window/tab_key", "", type=str)
        stored_page = self._main_tab_pages.get(stored_tab_key)
        if stored_page is None:
            tab_index = settings.value("main_window/tab_index", 0, type=int)
            if not settings.contains("main_window/tab_key"):
                if 0 <= tab_index < len(_LEGACY_MAIN_TAB_ORDER):
                    migrated_key = _LEGACY_MAIN_TAB_ORDER[tab_index]
                    stored_page = self._main_tab_pages[migrated_key]
                    settings.setValue("main_window/tab_key", migrated_key)
                    settings.setValue(
                        "main_window/tab_index",
                        self.tabs.indexOf(self._main_tab_scroll_by_page[stored_page]),
                    )
                    settings.sync()
            elif 0 <= tab_index < self.tabs.count():
                stored_page = self._main_tab_page_by_scroll.get(
                    self.tabs.widget(tab_index)
                )
        if stored_page is not None:
            self._set_current_main_page(stored_page)

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
        current_page = self._current_main_page()
        tab_key = self._main_tab_key_by_page.get(current_page)
        if tab_key is not None:
            settings.setValue("main_window/tab_key", tab_key)

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
        self._set_current_main_page(self.settings_tab)
        self.settings_tab.settings_tabs.setCurrentWidget(
            self.settings_tab.integration_page
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
                    f"Записей в восстановленной копии: {games}\n\n"
                    "Полное состояние непосредственно перед восстановлением сохранено здесь:\n"
                    f"{safety}",
                )
            else:
                QMessageBox.information(
                    self,
                    "Восстановление завершено",
                    "Резервная копия успешно восстановлена.\n\n"
                    f"Исходная schema: {schema}\n"
                    f"Записей в восстановленной копии: {games}\n\n"
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
        current = self._current_main_page()
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

