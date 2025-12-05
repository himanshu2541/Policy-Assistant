# services/stt_service/stt_service/app/__init__.py
"""
Small import shim so generated stubs that do `import stt_pb2` or `from protos import stt_pb2`
can find the local protos package without editing generated files.
"""

from __future__ import annotations
import importlib
import sys
from pathlib import Path

# The package path containing the protos, relative to this file.
# e.g. this file is stt_service.app.__init__, protos live at stt_service.app.protos
LOCAL_PROTOS_PKG = f"{__name__}.protos"   # -> "stt_service.app.protos"

def _install_protos_alias():
    # if the local protos package exists, import it and map it to top-level names
    try:
        # Ensure the package is importable (this raises if not present)
        protos_mod = importlib.import_module(LOCAL_PROTOS_PKG)
    except Exception:
        return  # nothing to do if no local protos package

    # Create a top-level alias so `import protos` resolves to our local protos package
    # Only set sys.modules['protos'] if not already set to avoid clobbering other modules.
    if "protos" not in sys.modules:
        sys.modules["protos"] = protos_mod

    # Also ensure the package can be imported by its short name stt_pb2 if code does `import stt_pb2`
    # (rare). For that, expose children modules in sys.modules using their short basename.
    for sub in getattr(protos_mod, "__all__", []) or []:
        # skip if no explicit __all__ in protos.__init__.py
        pass

    # Also ensure direct top-level module names for generated files are present:
    # e.g. if generated file does `import stt_pb2 as stt__pb2`, Python will look for 'stt_pb2' in sys.modules.
    # We can register 'stt_pb2' -> protos_mod.stt_pb2 if that attribute exists.
    try:
        protos_path = Path(protos_mod.__file__).parent
        # check for common generated module files and register them
        for fname in ("stt_pb2.py", "stt_pb2_grpc.py"):
            candidate = protos_path / fname
            if candidate.exists():
                modname = fname[:-3]  # e.g. 'stt_pb2'
                full = f"{LOCAL_PROTOS_PKG}.{modname}"
                try:
                    m = importlib.import_module(full)
                    if modname not in sys.modules:
                        sys.modules[modname] = m
                except Exception:
                    # if import fails, skip; generated files might rely on different imports
                    continue
    except Exception:
        pass

_install_protos_alias()
del importlib, sys, Path, _install_protos_alias, LOCAL_PROTOS_PKG
