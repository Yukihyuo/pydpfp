"""Public package API for pydpfp.

Exposes the two main classes from the wrappers and resolves default DLL paths
relative to this package directory.
"""

import os

from .dpfj_wrapper import FingerJetEngine as _FingerJetEngine
from .dpfpdd_wrapper import FingerPrintReader as _FingerPrintReader


PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))

# Default DLL names expected to live in this package folder.
READER1_DLL_NAME = "lector1.dll"
READER2_DLL_NAME = "lector2.dll"

DEFAULT_READER1_DLL_PATH = os.path.join(PACKAGE_DIR, READER1_DLL_NAME)
DEFAULT_READER2_DLL_PATH = os.path.join(PACKAGE_DIR, READER2_DLL_NAME)


class FingerPrintReader(_FingerPrintReader):
	"""Reader wrapper with package-local DLL resolution by default."""

	def __init__(self, dll_path=None):
		resolved_path = dll_path or DEFAULT_READER1_DLL_PATH
		super().__init__(dll_path=resolved_path)


class FingerJetEngine(_FingerJetEngine):
	"""FingerJet wrapper with package-local DLL resolution by default."""

	def __init__(self, dll_path=None):
		resolved_path = dll_path or DEFAULT_READER2_DLL_PATH
		super().__init__(dll_path=resolved_path)


# Optional aliases with generic names (useful for end-user imports/documentation).
ClaseLector1 = FingerPrintReader
ClaseLector2 = FingerJetEngine


__all__ = [
	"FingerPrintReader",
	"FingerJetEngine",
	"ClaseLector1",
	"ClaseLector2",
	"PACKAGE_DIR",
	"DEFAULT_READER1_DLL_PATH",
	"DEFAULT_READER2_DLL_PATH",
]
