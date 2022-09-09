# -*- coding: utf-8 -*-

import eel


eel.init('web')


def main():
	eel.start(
		'templates/heroes.html',
		jinja_templates='templates'
	)


if __name__ == '__main__':
	main()