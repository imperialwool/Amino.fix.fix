python setup.py sdist
python -m build --wheel
python -m twine upload dist/*