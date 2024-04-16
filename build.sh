# Moved to Hatch, so building packages is easy now
python3 -m build
python3 -m twine upload dist/*