# runtime_hook_openblas.py
import os

# Limite la mémoire OpenBLAS (cause principale du crash PyInstaller)
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"

print("✅ OpenBLAS threads limités à 1 (fix MemoryError)")