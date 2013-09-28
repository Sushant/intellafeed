import jinja2
import os

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), '../templates')
JINJA_ENV = jinja2.Environment(loader=jinja2.FileSystemLoader(TEMPLATE_DIR))

def get(template_name):
  return JINJA_ENV.get_template(template_name)

