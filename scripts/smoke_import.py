import importlib
assert hasattr(importlib.import_module("backend.main"), "app")
assert hasattr(importlib.import_module("main"), "app")
print("ok")
