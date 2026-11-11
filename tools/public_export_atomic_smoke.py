"""Failed public exports must preserve a destination that already exists."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main
from unittest.mock import patch
import json

from openpyxl import Workbook, load_workbook

from streaming_manager.credentials import MemoryCredentialStore
from streaming_manager.database import Database
from streaming_manager import exporters


class PublicExportAtomicTests(TestCase):
    def setUp(self):
        temp = TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.db = Database(self.root / "data" / "test.db", credential_store=MemoryCredentialStore())
        self.db.sync_main_games_state([{"title": "Тестовая игра", "sm_points": 123}])

    def test_failed_csv_query_preserves_existing_file(self):
        target = self.root / "public.csv"
        target.write_bytes(b"previous export")
        before = set(self.root.iterdir())
        with patch.object(self.db, "public_games", side_effect=OSError("Read failure")):
            with self.assertRaises(OSError):
                exporters.export_public_csv(self.db, target)
        self.assertEqual(target.read_bytes(), b"previous export")
        self.assertEqual(set(self.root.iterdir()), before)

    def test_partial_json_write_preserves_existing_file(self):
        target = self.root / "public.json"
        target.write_bytes(b"previous export")
        before = set(self.root.iterdir())
        write_text = Path.write_text

        def failed_write(path, text, **kwargs):
            write_text(path, text[:5], **kwargs)
            raise OSError("Write failure")

        with patch.object(Path, "write_text", failed_write):
            with self.assertRaises(OSError):
                exporters.export_public_json(self.db, target)
        self.assertEqual(target.read_bytes(), b"previous export")
        self.assertEqual(set(self.root.iterdir()), before)

    def test_partial_xlsx_write_preserves_existing_file(self):
        target = self.root / "public.xlsx"
        target.write_bytes(b"previous export")
        before = set(self.root.iterdir())

        def failed_save(workbook, path):
            Path(path).write_bytes(b"partial ZIP")
            raise OSError("Write failure")

        with patch.object(Workbook, "save", failed_save):
            with self.assertRaises(OSError):
                exporters.export_public_xlsx(self.db, target)
        self.assertEqual(target.read_bytes(), b"previous export")
        self.assertEqual(set(self.root.iterdir()), before)

    def test_failed_replace_preserves_each_export(self):
        for suffix in ("csv", "json", "xlsx"):
            with self.subTest(format=suffix):
                target = self.root / f"public.{suffix}"
                target.write_bytes(b"previous export")
                before = set(self.root.iterdir())
                with patch("os.replace", side_effect=PermissionError("Target locked")):
                    with self.assertRaises(PermissionError):
                        getattr(exporters, f"export_public_{suffix}")(self.db, target)
                self.assertEqual(target.read_bytes(), b"previous export")
                self.assertEqual(set(self.root.iterdir()), before)

    def test_success_keeps_each_format_and_return_value(self):
        for suffix in ("csv", "json", "xlsx"):
            target = self.root / f"public.{suffix}"
            self.assertEqual(getattr(exporters, f"export_public_{suffix}")(self.db, target), target)
        self.assertIn("Тестовая игра;123", (self.root / "public.csv").read_text(encoding="utf-8-sig"))
        self.assertEqual(json.loads((self.root / "public.json").read_text(encoding="utf-8"))["games"][0]["title"], "Тестовая игра")
        wb = load_workbook(self.root / "public.xlsx", read_only=True)
        try:
            self.assertEqual(wb.active["A2"].value, "Тестовая игра")
        finally:
            wb.close()


if __name__ == "__main__":
    main()
