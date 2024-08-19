# Exif Image GPS Altitude Refine

Specify offset to altitude for single image or entire directory. Based on [exifimageresize](https://github.com/pierotofy/exifimageresize).

## Installation

```bash
virtualenv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
python refine.py -i images/ -o resized/ 10.1
python resize.py -i images/1.JPG -o resized.JPG 10.1
```

## License

GPL 3.0
