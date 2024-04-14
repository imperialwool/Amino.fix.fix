# Since I moved to Mac, I converted BAT to SH...
python3 setup.py sdist
python3 -m build --wheel
python3 -m twine upload dist/*