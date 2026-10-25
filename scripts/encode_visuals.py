"""Encode browser captures as modest-size looping README GIFs (optional Pillow)."""
import json
import sys
from pathlib import Path

from PIL import Image


def main():
    for job in json.loads(Path(sys.argv[1]).read_text()):
        frames = []
        for filename in job["files"]:
            with Image.open(filename) as image:
                size = (1000, round(image.height * 1000 / image.width))
                frame = image.convert("RGB").resize(size, Image.Resampling.LANCZOS)
                frames.append(frame.quantize(colors=192, method=Image.Quantize.MEDIANCUT))
        frames[0].save(job["output"], save_all=True, append_images=frames[1:],
                       duration=job["durations"], loop=0, optimize=True, disposal=2)
        with Image.open(job["output"]) as result:
            assert result.n_frames == len(frames), "Missing animation frames"
            assert result.info["loop"] == 0, "Animation must loop"
        print(f'{Path(job["output"]).name}: {len(frames)} frames, '
              f'{Path(job["output"]).stat().st_size // 1024} KiB')


if __name__ == "__main__":
    main()
