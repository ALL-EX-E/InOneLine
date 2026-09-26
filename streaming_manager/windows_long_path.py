from __future__ import annotations

import atexit
import hashlib
import ntpath
import os
import shutil
import sys
import tempfile
from pathlib import Path

# Win32's documented MAX_PATH value is 260, but native DLL/plugin loaders can
# fail *before* an individual path string reaches 260 because they normalize or
# resolve additional dependency/search paths internally.  E4 Windows QA
# reproduced this with qwindows.dll at 255/259 characters, Shiboken below 260,
# and _ctypes.pyd at 258 characters.  Keep explicit headroom for native-loader
# calls rather than waiting for the nominal MAX_PATH boundary.
_MAX_PATH = 260
_NATIVE_PATH_SAFETY_LIMIT = 220
_QT_PLUGIN_STAGE_LIMIT = 220
_EXTENSION_LOADER_MARKER = "_iol_e4_long_path_compat"
_DLL_DIR_MARKER = "_iol_e4_long_path_compat"
_STABLE_ABI_DLL_HANDLE = None
_QT_PLUGIN_STAGE_DIR: Path | None = None


def _win32_extended_path(path):
    """Return an extended Win32 path for deep absolute string paths.

    Native DLL loaders proved sensitive well below the nominal 260-character
    MAX_PATH boundary during E4 verification.  Absolute drive/UNC paths at or
    above :data:`_NATIVE_PATH_SAFETY_LIMIT` are therefore converted early so
    LoadLibraryExW/AddDllDirectory callers keep deterministic headroom.  Bytes,
    relative paths, short absolute paths, and existing device/extended
    namespaces are intentionally left unchanged.
    """
    try:
        raw = os.fspath(path)
    except TypeError:
        return path

    if not isinstance(raw, str):
        return raw

    normalized = raw.replace("/", "\\")
    if normalized.startswith("\\\\?\\") or normalized.startswith("\\\\.\\"):
        return normalized
    if not ntpath.isabs(raw):
        return raw
    if len(raw) < _NATIVE_PATH_SAFETY_LIMIT:
        return raw
    if normalized.startswith("\\\\"):
        return "\\\\?\\UNC\\" + normalized[2:]
    if len(normalized) >= 3 and normalized[1] == ":" and normalized[2] == "\\":
        return "\\\\?\\" + normalized
    return raw


def install_frozen_windows_long_path_compat() -> bool:
    """Install frozen-runtime native-loader compatibility for deep paths.

    CPython loads native ``.pyd`` extension modules through LoadLibraryExW.
    E4 FIX6 proved that waiting until the final module path itself reached 260
    characters was too late: dependent/search-directory resolution could fail
    in the 220-259 range.  Before any Qt binding is imported, feed the native
    loader an extended-length path once the conservative safety limit is
    reached, then restore the normal ModuleSpec/loader path so user-visible
    ``__file__`` semantics stay unchanged.

    PySide6 and other packages also use ``os.add_dll_directory`` on Windows.
    Wrap that call with the same early conversion so dependency search paths do
    not reintroduce the same boundary.
    """
    if sys.platform != "win32" or not getattr(sys, "frozen", False):
        return False

    import importlib.machinery

    loader_cls = importlib.machinery.ExtensionFileLoader
    current_create_module = loader_cls.create_module
    if not getattr(current_create_module, _EXTENSION_LOADER_MARKER, False):
        original_create_module = current_create_module

        def create_module(self, spec):
            original_origin = getattr(spec, "origin", None)
            api_origin = _win32_extended_path(original_origin)
            if api_origin == original_origin:
                return original_create_module(self, spec)

            original_loader_path = getattr(self, "path", None)
            loader_path_changed = original_loader_path == original_origin
            spec.origin = api_origin
            if loader_path_changed:
                self.path = api_origin
            try:
                return original_create_module(self, spec)
            finally:
                spec.origin = original_origin
                if loader_path_changed:
                    self.path = original_loader_path

        setattr(create_module, _EXTENSION_LOADER_MARKER, True)
        loader_cls.create_module = create_module

    add_dll_directory = getattr(os, "add_dll_directory", None)
    if add_dll_directory is not None and not getattr(add_dll_directory, _DLL_DIR_MARKER, False):
        original_add_dll_directory = add_dll_directory

        def wrapped_add_dll_directory(path):
            return original_add_dll_directory(_win32_extended_path(path))

        setattr(wrapped_add_dll_directory, _DLL_DIR_MARKER, True)
        os.add_dll_directory = wrapped_add_dll_directory

    # Stable-ABI extension modules such as Shiboken link against python3.dll
    # rather than python312.dll.  Preload the bundled forwarding DLL through
    # the same native-loader-safe path conversion.  Importing ctypes here is
    # safe because the ExtensionFileLoader wrapper above is already active.
    global _STABLE_ABI_DLL_HANDLE
    if _STABLE_ABI_DLL_HANDLE is None:
        stable_abi = os.path.join(sys._MEIPASS, "python3.dll")
        if os.path.isfile(stable_abi):
            import ctypes

            _STABLE_ABI_DLL_HANDLE = ctypes.WinDLL(_win32_extended_path(stable_abi))

    return True


def _cleanup_qt_plugin_stage() -> None:
    global _QT_PLUGIN_STAGE_DIR
    stage = _QT_PLUGIN_STAGE_DIR
    _QT_PLUGIN_STAGE_DIR = None
    if stage is not None:
        shutil.rmtree(stage, ignore_errors=True)


def prepare_frozen_qt_plugins_for_long_path() -> Path | None:
    """Stage Qt plugin DLLs under a short temporary path before they get deep.

    Qt discovers plugins such as ``platforms/qwindows.dll`` by absolute path.
    FIX6 staged only once qwindows itself reached 260 characters, but E4
    classification reproduced Qt platform-plugin failure already at 255 and
    259 characters.  For frozen deployments where the plugin path reaches the
    conservative native-loader safety limit, copy the bundled ``PySide6/plugins``
    tree to a per-process short directory under ``%TEMP%`` and point Qt at that
    exact copy before QApplication is imported.

    Normal short frozen deployments, source mode, and non-Windows platforms do
    not create a staging directory.
    """
    global _QT_PLUGIN_STAGE_DIR

    if sys.platform != "win32" or not getattr(sys, "frozen", False):
        return None
    if _QT_PLUGIN_STAGE_DIR is not None:
        return _QT_PLUGIN_STAGE_DIR

    source_plugins = Path(sys._MEIPASS) / "PySide6" / "plugins"
    qwindows = source_plugins / "platforms" / "qwindows.dll"
    if len(str(qwindows)) < _QT_PLUGIN_STAGE_LIMIT:
        return None
    if not qwindows.is_file():
        raise FileNotFoundError(f"Bundled Qt platform plugin is missing: {qwindows}")

    digest = hashlib.sha256(str(source_plugins).encode("utf-8", "surrogatepass")).hexdigest()[:10]
    stage_parent = Path(tempfile.gettempdir()) / "InOneLineQt"
    stage_parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f"p{os.getpid()}_{digest}_", dir=stage_parent))
    staged_plugins = stage / "plugins"

    try:
        shutil.copytree(
            _win32_extended_path(source_plugins),
            staged_plugins,
            copy_function=shutil.copyfile,
        )
    except BaseException:
        shutil.rmtree(stage, ignore_errors=True)
        raise

    if not (staged_plugins / "platforms" / "qwindows.dll").is_file():
        shutil.rmtree(stage, ignore_errors=True)
        raise FileNotFoundError("Qt plugin staging did not produce platforms/qwindows.dll")

    _QT_PLUGIN_STAGE_DIR = stage
    atexit.register(_cleanup_qt_plugin_stage)

    os.environ["QT_PLUGIN_PATH"] = str(staged_plugins)
    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = str(staged_plugins / "platforms")
    return stage
