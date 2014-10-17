from flask import Flask
from extensions import Senpy
app = Flask(__name__)
sp = Senpy()
sp.init_app(app)
app.debug = True
app.run()
