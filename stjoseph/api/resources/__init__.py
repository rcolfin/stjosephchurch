from pathlib import Path
from typing import Final

THUMBNAIL: Final[Path] = Path(Path(__file__).parent, "thumbnail.jpg")

THUMBNAIL_MIME_TYPE: Final[str] = "image/jpeg"
