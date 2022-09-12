# -*- coding: utf-8 -*-

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import element
from bs4 import BeautifulSoup as bs


STATUS = 'not browser'
if STATUS == 'browser':
	driver = webdriver.Chrome(ChromeDriverManager().install())
else:
	from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
	options = webdriver.ChromeOptions()
	options.add_argument('headless')
	options.add_argument('--log-level 3')
	driver = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=options)


BASE_URL = 'https://www.leagueofgraphs.com'
HERO_ITEMS_URL = 'https://www.leagueofgraphs.com/ru/champions/items/{hero_slug}'
HERO_SPELLS_URL = 'https://www.leagueofgraphs.com/ru/champions/spells/{hero_slug}'


def get_html(url: str) -> str:
	driver.get(url)

	return driver.page_source


def get_progressbar_value(td: element.Tag):
	return td.find('progressbar').attrs['data-value']


class Item:
	def __init__(self, name: str, image_link: str, size: tuple, bias: tuple):
		self.name = name
		self.image_link = image_link
		self.size = size
		self.bias = bias

	def __str__(self):
		return f'{self.name} - {self.size}[{self.bias}]'


class Hero:
	def __init__(self, name: str, line: str, link: str):
		self.name = name
		self.line = line
		self.link = link
		self.slug = link.split('/')[-1]

		self.parser = None

	def get_parser(self):
		return bs(get_html(self.link), 'html.parser')

	def get_statistics(self) -> dict:
		if self.parser is None:
			self.parser = self.get_parser()

		output = {
			'populatity': self.parser.find('div', attrs={'id': 'graphDD1'}).text.strip(),
			'rating': self.parser.find('div', attrs={'id': 'graphDD2'}).text.strip(),
			'blocking': self.parser.find('div', attrs={'id': 'graphDD3'}).text.strip(),
			'skills': self._get_skill_table(self.parser.find('table', attrs={'class': 'skillsOrdersTableSmall'})),
			'spells': self._get_spells(),
			'items': self._get_items(),
		}

		return output

	def __str__(self):
		return f'{self.name}[{self.slug}] - {self.line}\n{self.link}\n'

	def _get_skill_table(self, table: element.Tag) -> list:
		rows = table.find_all('tr')
		skills = [[0 for col in range(18)] for row in rows]

		for rn, row in enumerate(rows):
			cols = row.find_all('td')[1:]

			for cn, col in enumerate(cols):
				if 'active' in col.attrs['class']:
					skills[rn][cn] = 1

		return skills

	def _get_items(self) -> dict:
		items_parser = bs(get_html(
			HERO_ITEMS_URL.format(hero_slug=self.slug)),
			'html.parser')
		items_tables = items_parser.find_all('table', attrs={'class': 'sortable_table'})

		items = {
			'started': self._get_items_collection(items_tables[0]),
			'main': self._get_items_collection(items_tables[1]),
			'late': self._get_items_collection(items_tables[2]),
			'boots': self._get_items_collection(items_tables[3]),
			'global': self._get_items_collection(items_tables[4])}

		return items

	def _get_items_collection(self, table):
		rows = table.find_all('tr')[1:-1]
		items = []

		for row in rows:
			cols = row.find_all('td')

			# Icons
			icons_block = cols[0]
			items_icon_img = icons_block.find_all('img', attrs={'class': 'requireTooltip'})
			row_items = []

			for img in items_icon_img:
				name = img.attrs['alt']
				# image_link = img.value_of_css_property('background')
				size = (img.attrs['width'], img.attrs['height'])
				# bias = img.value_of_css_property('background-position')

				row_items.append(Item(
					name=name,
					image_link='',
					size=size,
					bias=(0, 0)))

			# Popularity
			popularity_value = get_progressbar_value(cols[1])

			# Win rate
			win_rate_value = get_progressbar_value(cols[2])

			items_collection = {
				'items': row_items,
				'popularity': popularity_value,
				'win_rate': win_rate_value}
			items.append(items_collection)

		return items

	def _get_spells(self) -> list:
		spells = []
		spells_parser = items_parser = bs(get_html(
			HERO_SPELLS_URL.format(hero_slug=self.slug)),
			'html.parser')

		table = spells_parser.find('table', attrs={'class': 'data_table sortable_table'})
		rows = table.find_all('tr')[1:]

		for row in rows:
			cols = row.find_all('td')[1:]

			# Spells
			spells_col = cols[0].find_all('img')
			spells_names = [img.attrs['alt'] for img in spells_col]

			# Popularity
			popularity_value = get_progressbar_value(cols[1])

			# Win rate
			win_rate_value = get_progressbar_value(cols[2])

			row_spells = {
				'spells': spells_names,
				'popularity': popularity_value,
				'win_rate': win_rate_value}
			spells.append(row_spells)

		return spells


class HeroesListParser:
	url = 'https://www.leagueofgraphs.com/ru/champions/builds'

	def __init__(self):
		self.html = get_html(HeroesListParser.url)
		self.parser = bs(self.html, 'html.parser')

	def _get_html_table(self) -> element.Tag:
		return self.parser.find('table', attrs={'class': 'data_table'})

	def _get_rows_from_table(self, table: element.Tag) -> element.ResultSet:
		# First row - table header
		return table.find_all('tr')[1:]

	def _split_tr_to_hero_stats(self, row: element.Tag) -> dict:
		hero_stats = {
			'link': BASE_URL + row.find('a').attrs['href'],
			'name': row.find('span', attrs={'class': 'name'}).text.strip(),
			'line': row.find('div', attrs={'class': 'txt'}).find('i').text.strip()
		}

		return hero_stats

	def get_heroes_list(self) -> list:
		table = self._get_html_table()
		rows = self._get_rows_from_table(table)
		heroes = []

		for row in rows:
			try:
				stats = self._split_tr_to_hero_stats(row)
				heroes.append(Hero(**stats))
			except:
				continue

		return heroes


def main():
	# heroes_list_parser = HeroesListParser()
	# heroes = heroes_list_parser.get_heroes_list()

	# kindred = list(filter(lambda h: h.name == 'Варвик', heroes))[0]
	kindred = Hero(
		link='https://www.leagueofgraphs.com/ru/champions/builds/kindred',
		name='Киндред',
		line='jungle'
	)
	print(kindred)
	all_stats = kindred.get_statistics()
	for key, value in all_stats.items():
		print(key, value)


if __name__ == '__main__':
	main()