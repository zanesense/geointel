import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from mangum import Mangum
from app.main import app

handler = Mangum(app)
