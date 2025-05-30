# PIP packaging instructions
TL;DR;   

```bash
# install edpm 'from this folder' with dev dependencies
python -m pip install -e .[dev]

# Under venv or conda: 
python -m build && python -m twine upload dist/* 
```

JLAB CERTIFICATE ERROR:

```bash
python -m twine upload --cert /home/romanov/JLabCA.crt dist/*
```


A tutorial:
https://packaging.python.org/tutorials/packaging-projects/

edpm pip: https://pypi.org/project/edpm/#history

SO question for JLab certificate validation
https://stackoverflow.com/questions/10667960/python-requests-throwing-sslerror/10668173



