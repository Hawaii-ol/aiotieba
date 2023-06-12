import os
import sys
from pathlib import Path

basepath = Path(__file__).parent.parent
sys.path.append(str(basepath.absolute()))
os.chdir(basepath)
