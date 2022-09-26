# -*- coding: utf-8 -*-

from typing import Generator

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
BUILDS_URL = 'https://www.leagueofgraphs.com/ru/champions/builds'
HERO_BUILD_URL = 'https://www.leagueofgraphs.com/ru/champions/builds/{slug}/{line}/{mode}'
HERO_ITEMS_URL = 'https://www.leagueofgraphs.com/ru/champions/items/{slug}/{line}/{mode}'
HERO_SPELLS_URL = 'https://www.leagueofgraphs.com/ru/champions/spells/{slug}/{line}/{mode}'
HERO_RUNES_URL = 'https://www.leagueofgraphs.com/ru/champions/runes/{slug}/{line}/{mode}'


LINES = {
	'Топ': 'top',
	'Лес': 'jungle',
	'Мид': 'middle',
	'Бот': 'adc',
	'Поддержка': 'support',
}


def get_html(url: str) -> str:
	driver.get(url)

	return driver.page_source


def get_progressbar_value(td: element.Tag) -> float:
	return float(td.find('progressbar').attrs['data-value'])


def get_table(soup, class_: str) -> Generator:
	table = soup.find('table', attrs={'class': class_})
	rows = table.find_all('tr')[1:]

	for row in rows:
		yield row


def get_table_content(table: element.Tag) -> list:
	rows = table.find_all('tr')[1:-1]
	output = []

	for row in rows:
		cols = row.find_all('td')
		*raw_data, popularity, win_rate = cols
		output.append({
			'raw_data': raw_data,
			'popularity': get_progressbar_value(popularity),
			'win_rate': get_progressbar_value(win_rate),
		})

	return output


def get_items_from_table(td: element.Tag) -> list:
	output = []
	imgs = td[0].find_all('img')

	for img in imgs:
		output.append(img.attrs['alt'])

	return output


def get_spells_from_table(td: element.Tag) -> list:
	output = []
	imgs = td[1].find_all('img')

	for img in imgs:
		output.append(img.attrs['alt'])

	return output


def get_runes_from_table(items: element.Tag) -> list:
	output = []

	for col in items:
		imgs = col.find_all('img')

		for img in imgs:
			if img.attrs.get('style', '').strip() in 'opacity: 1;':
				output.append(img.attrs['alt'])

	return output


def get_block_content(block: element.Tag) -> str:
	return block.text.strip()


class HeroParser(object):
	''' Парсит информацию о чемпионе '''

	def __init__(self, url: str):
		self.url = url

		self._parser = None

	@property
	def parser(self):
		if self._parser is None:
			html = get_html(self.url)
			self._parser = bs(html, 'html.parser')

		return self._parser

	def get_all(self) -> dict:
		return {
			# 'skills': self.get_skills(),
			# 'items': self.get_items(),
			# 'spells': self.get_spells(),
			# 'runes': self.get_runes(),
		}

	def get_skills(self) -> list:
		output = []

		table = self.parser.find('table', attrs={'class': 'skillsOrdersTableSmall'})
		rows = table.find_all('tr')

		for row in rows:
			output.append([])

			# First column - skill icon
			cols = row.find_all('td')[1:]

			for col in cols:
				content = get_block_content(col)
				output[-1].append(content in ('Q', 'W', 'E', 'R'))

		return output

	def get_items(self) -> dict:
		output = {}
		items_url = HERO_ITEMS_URL.format(
			slug=self.slug, line=LINES[self.lines[0]], mode=self.mode)
		items_parser = bs(get_html(items_url), 'html.parser')

		tables = items_parser.find_all('table', attrs={'class': 'data_table'})[:5]
		table_titles = ('start', 'main', 'late', 'boots', 'global')
		for title, table in zip(table_titles, tables):
			raw_table_data = get_table_content(table)
			output[title] = []

			for row in raw_table_data:
				raw_data = row['raw_data']
				items = get_items_from_table(raw_data)
				output[title].append({
					'items': items,
					'popularity': row['popularity'],
					'win_rate': row['win_rate'],
				})

		return output

	def get_spells(self) -> list:
		output = []

		spells_url = HERO_SPELLS_URL.format(
			slug=self.slug, line=LINES[self.lines[0]], mode=self.mode)
		spells_parser = bs(get_html(spells_url), 'html.parser')

		table = spells_parser.find('table', attrs={'class': 'data_table'})
		rows = get_table_content(table)
		for row in rows:
			spells = get_spells_from_table(row['raw_data'])
			output.append({
				'spells': spells,
				'popularity': row['popularity'],
				'win_rate': row['win_rate'],
			})

		return output
# Чтобы было что-то новое, надо что-то сломать

	def get_runes(self) -> list:
		output = []

		runes_url = HERO_RUNES_URL.format(
			slug=self.slug, line=LINES[self.lines[0]], mode=self.mode)
		runes_parser = bs(get_html(runes_url), 'html.parser')

		tables = runes_parser.find_all('table', attrs={'class': 'perksTableContainerTable'})
		for table in tables:
			row = table.find_all('tr')[1]
			*raw_data, popularity, win_rate = row.find_all('td')

			output.append({
				'runes': get_runes_from_table(raw_data),
				'popularity': get_progressbar_value(popularity),
				'win_rate': get_progressbar_value(win_rate),
			})

		return output


class Hero(HeroParser):
	def __init__(self, name: str, slug: str, position: str, \
	             popularity: float, win_rate: float, blocks: float, kda: dict, \
	             pentakills: float, mode: str='sr-ranked'):

		self.name = name
		self.slug = slug
		self.link = None
		self.position = position
		self.lines = position.split(', ')
		self.popularity = popularity
		self.win_rate = win_rate
		self.blocks = blocks
		self.kda = kda
		self.pentakills = pentakills
		self.mode = mode

		url = HERO_BUILD_URL.format(
			slug=self.slug, line=LINES[self.lines[0]], mode=self.mode)
		super().__init__(url)

	def __str__(self):
		return f'{self.name} [{self.position}]'


class HeroesListParser(object):
	''' Парсит список персонажей '''

	def get_heroes_list(self) -> list:
		html = get_html(BUILDS_URL)
		soup = bs(html, 'html.parser')

		heroes_list_table = get_table(soup, 'data_table')
		heroes_list = [self._create_hero(hero_row) \
			for hero_row in heroes_list_table]

		return heroes_list

	def _create_hero(self, hero_row: element.Tag) -> Hero:
		tds = hero_row.find_all('td')[1:]

		try:
			name, popularity, win_rate, blocks, kda, pentakills = tds
		except ValueError as err:
			return

		hero_stats = {
			'name': self.__get_hero_name(name),
			'slug': self.__get_hero_slug(name),
			'position': self.__get_hero_position(name),
			'popularity': get_progressbar_value(popularity),
			'win_rate': get_progressbar_value(win_rate),
			'blocks': get_progressbar_value(blocks),
			'kda': self.__get_hero_kda(kda),
			'pentakills': float(get_block_content(pentakills))
		}

		return Hero(**hero_stats)

	def __get_hero_name(self, block: element.Tag) -> str:
		return get_block_content(block.find('span', attrs={'class': 'name'}))

	def __get_hero_slug(self, block: element.Tag) -> str:
		return block.find('a').attrs['href'].split('/')[-1]

	def __get_hero_position(self, block: element.Tag) -> str:
		return get_block_content(block.find('i'))

	def __get_hero_kda(self, block: element.Tag) -> dict:
		spans = block.find_all('span')

		kills = float(get_block_content(spans[0]))
		deaths = float(get_block_content(spans[1]))
		assists = float(get_block_content(spans[2]))
		value = (kills + assists) / deaths

		return {
			'kills': kills,
			'deaths': deaths,
			'assists': assists,
			'value': value
		}


def main():
	# heroes_list_parser = HeroesListParser()
	# heroes = heroes_list_parser.get_heroes_list()

	# hero = heroes[0]
	hero = Hero(name='Киндред', slug='kindred', position='Лес', popularity=0,
		win_rate=0, blocks=0, kda=0, pentakills=0)
	print(hero.get_all())


if __name__ == '__main__':
	main()