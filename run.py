# -*- coding: utf-8 -*-

import os

import eel
from jinja2 import Environment, FileSystemLoader

from parser_ import HeroesListParser


eel.init('web')


HTML_DIR = os.path.join(os.getcwd(), 'web', 'html')
_templates = Environment(loader=FileSystemLoader('web/templates/'))
home_page_template = _templates.get_template('heroes.html')


def update_html_file(template, context: dict) -> str:
	return template.render(**context)


def save_html_file(name: str, html: str) -> str:
	path = os.path.join(HTML_DIR, name)

	with open(path, mode='w', encoding='utf-8') as file:
		file.write(html)

	return path


def main():
	home_page_parser = HeroesListParser()
	heroes = home_page_parser.get_heroes_list()
	context = {'title': 'Home page', 'heroes': heroes}
	home_page = update_html_file(home_page_template, context)
	index_page = save_html_file('index.html', home_page)

	eel.start(index_page)


if __name__ == '__main__':
	main()