# -*- coding: UTF-8 _*_

from flask import Flask
from jinja2 import FileSystemLoader

app = Flask('linkShortener')
app.jinja_loader = FileSystemLoader(app.root_path + '/static/')
app.debug = False

import main

if __name__ == '__main__':
    app.run()
