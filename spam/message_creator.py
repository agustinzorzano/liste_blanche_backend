"""
Copyright 2021 Venceslas Roullier, Daniel Santos Bustos, Guillem Sanyas, Julien Tagnani, Agustin Zorzano

This file is part of OpenEmailAntispam.

    OpenEmailAntispam is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    OpenEmailAntispam is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with OpenEmailAntispam.  If not, see https://www.gnu.org/licenses/.
"""

from jinja2 import Environment, FileSystemLoader
import os

TEMPLATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates/")

env = Environment(loader=FileSystemLoader(TEMPLATE_PATH))


class MessageCreator:
    @staticmethod
    def create_message_template(path, parameters):
        """It returns a template created by the template file (path) and the subtitution of the parameters
        in the template"""
        message = env.get_template(path)
        return message.render(parameters)
