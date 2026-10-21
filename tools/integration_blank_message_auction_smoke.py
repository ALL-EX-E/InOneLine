"""P21-A / UI-087: approved blank-message sequential auction lots.

No special cross-auction duplicate-title rule: previously promoted placeholder
names must be edited by the operator between auctions, as user decided.
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from streaming_manager.app_paths import AppPaths
from streaming_manager.database import Database, Game


class BlankAuctionLotTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory(ignore_cleanup_errors=True)
        self.paths = AppPaths.from_root(self.tmp.name)
        self.paths.ensure_runtime_dirs()
        self.db = Database(self.paths.database_path)
        self.db.add_game(Game(None, "Стартовый лот", None, 10, 0, "not_played", ""))
        with self.db.connect() as conn:
            conn.execute(
                "INSERT INTO integration_connections("
                "service_key,enabled,status,created_at,updated_at) "
                "VALUES(?,?,?,?,?)",
                ("test", 1, "connected", "2026-10-21T00:00:00+00:00",
                 "2026-10-21T00:00:00+00:00"),
            )

    def tearDown(self):
        self.tmp.cleanup()

    def start(self):
        return self.db.create_auction_session("max_amount", 300)

    def event(self, event_id, *, title="", unit="RUB", amount="4",
              hint=None, force_outside=False, **extra):
        return self.db.process_normalized_integration_event(
            service_key="test", external_event_id=event_id,
            event_type="donation", source_amount=amount, source_unit=unit,
            contributor="Подписчик", lot_title=title, note="original message",
            auction_id_hint=hint, force_outside_auction=force_outside,
            provider_metadata={"provider_time": "2026-10-21T00:03:00Z"},
            **extra,
        )

    def titles(self, sid):
        with self.db.connect() as conn:
            return [
                (int(row["game_id"]), str(row["title"]),
                 int(row["starting_sm_points"]), int(row["bid_sm_points"]))
                for row in conn.execute(
                    "SELECT ae.game_id,g.title,ae.starting_sm_points,ae.bid_sm_points "
                    "FROM auction_entries ae JOIN games g ON g.id=ae.game_id "
                    "WHERE ae.auction_id=? AND g.title LIKE 'Без текста %' "
                    "ORDER BY ae.game_id",
                    (sid,),
                )
            ]

    def raw(self, eid):
        with self.db.connect() as conn:
            row = conn.execute(
                "SELECT payload_json FROM external_events "
                "WHERE source='test' AND external_event_id=?", (eid,),
            ).fetchone()
            return json.loads(row["payload_json"]) if row else None

    def counts(self):
        with self.db.connect() as conn:
            return {
                t: int(conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0])
                for t in ("games", "auction_entries", "external_events",
                          "pending_conversions", "contributions")
            }

    def test_known_rate_creates_sequential_separate_lots_preserves_original(self):
        sid = self.start()
        ids = []
        for i in range(1, 4):
            result = self.event(f"known-{i}", hint=sid)
            self.assertEqual(result["status"], "processed")
            self.assertEqual(result["auction_id"], sid)
            self.assertEqual(result["credited_sm_points"], 4)
            ids.append(result["game_id"])
            raw = self.raw(f"known-{i}")
            self.assertEqual(raw["normalized"]["lot_title"], "")
            self.assertEqual(raw["normalized"]["generated_blank_title"], f"Без текста {i}")
            self.assertEqual(raw["normalized"]["generated_blank_number"], i)
            self.assertEqual(raw["normalized"]["generated_blank_auction_id"], sid)
            self.assertEqual(raw["normalized"]["note"], "original message")
            self.assertEqual(raw["provider_metadata"]["provider_time"],
                             "2026-10-21T00:03:00Z")
        self.assertEqual(len(set(ids)), 3)
        self.assertEqual([t[1] for t in self.titles(sid)],
                         ["Без текста 1", "Без текста 2", "Без текста 3"])
        self.assertEqual(self.counts()["contributions"], 3)
        duplicate = self.event("known-2", hint=sid)
        self.assertTrue(duplicate["duplicate"])
        self.assertEqual(duplicate["game_id"], ids[1])
        self.assertEqual(len(self.titles(sid)), 3)
        self.assertEqual(self.counts()["contributions"], 3)

    def test_unknown_rate_creates_zero_point_lot_then_explicit_apply(self):
        sid = self.start()
        pending = self.event("unknown-1", unit="XYZ", hint=sid, amount="2.5")
        self.assertEqual(pending["status"], "awaiting_rate")
        pid, gid = pending["pending_id"], pending["game_id"]
        self.assertIsNotNone(gid)
        self.assertEqual(self.titles(sid)[0][1], "Без текста 1")
        self.assertEqual(self.db.count_unresolved_auction_conversions(sid), 1)
        self.assertEqual(self.counts()["contributions"], 0)
        row = self.db.get_pending_conversion_event(pid)
        self.assertEqual(row["game_id"], gid)
        self.assertEqual(row["auction_id"], sid)
        self.assertEqual(row["game_title"], "Без текста 1")
        self.assertFalse(row["can_apply"])
        replay = self.event("unknown-1", unit="XYZ", hint=sid, amount="2.5")
        self.assertTrue(replay["duplicate"])
        self.assertEqual(replay["pending_id"], pid)
        second = self.event("unknown-2", hint=sid)
        self.assertEqual(self.raw("unknown-2")["normalized"]["generated_blank_number"], 2)
        self.assertNotEqual(second["game_id"], gid)
        self.db.set_conversion_rate("XYZ", "2")
        self.assertTrue(self.db.get_pending_conversion_event(pid)["can_apply"])
        self.assertEqual(self.counts()["contributions"], 1)
        applied = self.db.apply_pending_conversion_event(pid)
        self.assertEqual(applied["status"], "applied")
        self.assertEqual(applied["game_id"], gid)
        self.assertEqual(applied["auction_id"], sid)
        self.assertEqual(applied["credited_sm_points"], 5)
        self.assertEqual(self.db.count_unresolved_auction_conversions(sid), 0)
        with self.assertRaises(RuntimeError):
            self.db.apply_pending_conversion_event(pid)
        self.assertEqual(self.counts()["contributions"], 2)
        with self.db.connect() as conn:
            self.assertEqual(int(conn.execute(
                "SELECT sm_points FROM games WHERE id=?", (gid,)
            ).fetchone()[0]), 5)

    def test_ordinal_survives_title_rename_and_rejected_pending(self):
        sid = self.start()
        first = self.event("edit-1", unit="XYZ", hint=sid)
        with self.db.connect() as conn:
            conn.execute("UPDATE games SET title=? WHERE id=?",
                         ("Переименовано пользователем", first["game_id"]))
        self.db.reject_pending_conversion_event(first["pending_id"])
        second = self.event("edit-2", hint=sid)
        self.assertEqual(self.raw("edit-2")["normalized"]["generated_blank_number"], 2)
        self.assertNotEqual(second["game_id"], first["game_id"])
        self.assertEqual(self.counts()["contributions"], 1)

    def test_only_running_empty_text_changes_missing_target_contract(self):
        outside = self.event("outside-blank", force_outside=True)
        self.assertEqual(outside["status"], "inapplicable")
        self.assertEqual(outside["reason"], "missing_target")
        sid = self.start()
        nonblank = self.event("named-1", title="Стартовый лот", hint=sid)
        self.assertEqual(nonblank["status"], "processed")
        self.assertNotIn("generated_blank_number", self.raw("named-1")["normalized"])
        self.event("blank-1", hint=sid)
        self.assertEqual(self.raw("blank-1")["normalized"]["generated_blank_number"], 1)

    def test_new_auction_restarts_counter_and_keeps_existing_title_match(self):
        first_sid = self.start()
        first = self.event("auction1-empty", hint=first_sid)
        self.db.cancel_auction(first_sid)
        # User decided not to change normal matching or auto-rename old games.
        # A missing rename between sessions can reuse that persistent title.
        second_sid = self.start()
        second = self.event("auction2-empty", hint=second_sid)
        self.assertEqual(self.raw("auction2-empty")["normalized"]["generated_blank_number"], 1)
        self.assertEqual(self.raw("auction2-empty")["normalized"]["generated_blank_auction_id"],
                         second_sid)
        self.assertEqual(second["game_id"], first["game_id"])
        self.assertEqual(second["auction_id"], second_sid)


if __name__ == "__main__":
    unittest.main()
