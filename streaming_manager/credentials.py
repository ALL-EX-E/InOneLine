from __future__ import annotations

"""Protected local credential storage.

B1 deliberately keeps secret material outside SQLite.  On Windows secrets are
stored as DPAPI-protected blobs that can only be decrypted by the same Windows
user account.  Non-Windows builds use an in-memory backend so tests and source
analysis can run without ever writing plaintext credentials to disk.
"""

import ctypes
import os
import platform
import uuid
from abc import ABC, abstractmethod
from ctypes import wintypes
from pathlib import Path
from threading import RLock


class CredentialStoreError(RuntimeError):
    pass


class CredentialStore(ABC):
    @abstractmethod
    def put(self, secret: str, *, credential_ref: str | None = None) -> str:
        """Store or replace a secret and return its opaque reference."""

    @abstractmethod
    def get(self, credential_ref: str) -> str | None:
        """Return the secret, or ``None`` when the reference is unavailable."""

    @abstractmethod
    def delete(self, credential_ref: str) -> None:
        """Delete a secret without raising when the reference does not exist."""

    def exists(self, credential_ref: str) -> bool:
        return self.get(credential_ref) is not None


class MemoryCredentialStore(CredentialStore):
    """Non-persistent backend used outside Windows and by automated tests.

    The namespace-scoped registry survives multiple ``Database`` instances in
    one process, which is useful for migration tests, but nothing is serialized
    to disk.  Production Windows runs never use this backend.
    """

    _namespaces: dict[str, dict[str, str]] = {}
    _lock = RLock()

    def __init__(self, namespace: str = "default"):
        self.namespace = str(namespace)

    def _bucket(self) -> dict[str, str]:
        with self._lock:
            return self._namespaces.setdefault(self.namespace, {})

    def put(self, secret: str, *, credential_ref: str | None = None) -> str:
        ref = str(credential_ref or f"cred_{uuid.uuid4().hex}")
        with self._lock:
            self._bucket()[ref] = str(secret)
        return ref

    def get(self, credential_ref: str) -> str | None:
        with self._lock:
            return self._bucket().get(str(credential_ref))

    def delete(self, credential_ref: str) -> None:
        with self._lock:
            self._bucket().pop(str(credential_ref), None)


class _DATA_BLOB(ctypes.Structure):
    _fields_ = [
        ("cbData", wintypes.DWORD),
        ("pbData", ctypes.POINTER(ctypes.c_ubyte)),
    ]


def _blob_from_bytes(payload: bytes) -> tuple[_DATA_BLOB, ctypes.Array]:
    if payload:
        buffer = ctypes.create_string_buffer(payload, len(payload))
        pointer = ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte))
        return _DATA_BLOB(len(payload), pointer), buffer
    buffer = ctypes.create_string_buffer(1)
    return _DATA_BLOB(0, ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte))), buffer


class WindowsDpapiCredentialStore(CredentialStore):
    """File-backed DPAPI store for the current Windows user.

    The files contain only DPAPI ciphertext.  References are opaque random IDs;
    no service token/password/API key is placed in SQLite or file names.
    """

    CRYPTPROTECT_UI_FORBIDDEN = 0x1

    def __init__(self, root: str | Path):
        if os.name != "nt":
            raise CredentialStoreError("Windows DPAPI доступен только в Windows.")
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._crypt32 = ctypes.WinDLL("crypt32", use_last_error=True)
        self._kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self._configure_signatures()

    def _configure_signatures(self) -> None:
        self._crypt32.CryptProtectData.argtypes = [
            ctypes.POINTER(_DATA_BLOB),
            wintypes.LPCWSTR,
            ctypes.POINTER(_DATA_BLOB),
            ctypes.c_void_p,
            ctypes.c_void_p,
            wintypes.DWORD,
            ctypes.POINTER(_DATA_BLOB),
        ]
        self._crypt32.CryptProtectData.restype = wintypes.BOOL
        self._crypt32.CryptUnprotectData.argtypes = [
            ctypes.POINTER(_DATA_BLOB),
            ctypes.POINTER(wintypes.LPWSTR),
            ctypes.POINTER(_DATA_BLOB),
            ctypes.c_void_p,
            ctypes.c_void_p,
            wintypes.DWORD,
            ctypes.POINTER(_DATA_BLOB),
        ]
        self._crypt32.CryptUnprotectData.restype = wintypes.BOOL
        self._kernel32.LocalFree.argtypes = [ctypes.c_void_p]
        self._kernel32.LocalFree.restype = ctypes.c_void_p

    @staticmethod
    def _validate_ref(credential_ref: str) -> str:
        ref = str(credential_ref)
        if not ref.startswith("cred_") or not ref[5:].isalnum():
            raise CredentialStoreError("Некорректная ссылка на credential.")
        return ref

    def _path(self, credential_ref: str) -> Path:
        return self.root / f"{self._validate_ref(credential_ref)}.bin"

    def _protect(self, payload: bytes) -> bytes:
        source, source_buffer = _blob_from_bytes(payload)
        output = _DATA_BLOB()
        if not self._crypt32.CryptProtectData(
            ctypes.byref(source),
            "In one line credential",
            None,
            None,
            None,
            self.CRYPTPROTECT_UI_FORBIDDEN,
            ctypes.byref(output),
        ):
            raise CredentialStoreError(
                f"DPAPI CryptProtectData failed: {ctypes.get_last_error()}"
            )
        try:
            return ctypes.string_at(output.pbData, output.cbData)
        finally:
            self._kernel32.LocalFree(output.pbData)
            del source_buffer

    def _unprotect(self, payload: bytes) -> bytes:
        source, source_buffer = _blob_from_bytes(payload)
        output = _DATA_BLOB()
        description = wintypes.LPWSTR()
        if not self._crypt32.CryptUnprotectData(
            ctypes.byref(source),
            ctypes.byref(description),
            None,
            None,
            None,
            self.CRYPTPROTECT_UI_FORBIDDEN,
            ctypes.byref(output),
        ):
            raise CredentialStoreError(
                f"DPAPI CryptUnprotectData failed: {ctypes.get_last_error()}"
            )
        try:
            return ctypes.string_at(output.pbData, output.cbData)
        finally:
            if description:
                self._kernel32.LocalFree(description)
            self._kernel32.LocalFree(output.pbData)
            del source_buffer

    def put(self, secret: str, *, credential_ref: str | None = None) -> str:
        ref = self._validate_ref(credential_ref) if credential_ref else f"cred_{uuid.uuid4().hex}"
        target = self._path(ref)
        temporary = target.with_suffix(".tmp")
        encrypted = self._protect(str(secret).encode("utf-8"))
        temporary.write_bytes(encrypted)
        try:
            os.chmod(temporary, 0o600)
        except OSError:
            pass
        os.replace(temporary, target)
        return ref

    def get(self, credential_ref: str) -> str | None:
        target = self._path(credential_ref)
        if not target.is_file():
            return None
        try:
            return self._unprotect(target.read_bytes()).decode("utf-8")
        except (OSError, UnicodeError, CredentialStoreError) as exc:
            raise CredentialStoreError("Не удалось прочитать защищённые credentials.") from exc

    def delete(self, credential_ref: str) -> None:
        self._path(credential_ref).unlink(missing_ok=True)


def create_credential_store(data_dir: str | Path) -> CredentialStore:
    data_dir = Path(data_dir)
    if platform.system().lower() == "windows" or os.name == "nt":
        return WindowsDpapiCredentialStore(data_dir / "credentials")
    # Deliberately do not write an insecure plaintext/portable secret file on
    # non-Windows systems.  The shipped desktop target is Windows; this fallback
    # exists for automated source/unit tests and developer tooling only.
    return MemoryCredentialStore(str(data_dir.resolve()))


__all__ = [
    "CredentialStore",
    "CredentialStoreError",
    "MemoryCredentialStore",
    "WindowsDpapiCredentialStore",
    "create_credential_store",
]
