from flask import Flask
from extensions import Senpy
app = Flask(__name__)
app.debug = True
sp = Senpy()
sp.init_app(app)
app.run()
