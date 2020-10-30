from jinja2 import Environment, FileSystemLoader
import os

TEMPLATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates/')

env = Environment(loader=FileSystemLoader(TEMPLATE_PATH))


class MessageCreator:
    @staticmethod
    def create_message_template(path, parameters):
        message = env.get_template(path)
        return message.render(parameters)
