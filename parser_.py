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
HERO_ITEMS_URL = 'https://www.leagueofgraphs.com/ru/champions/items/{hero_slug}'
HERO_SPELLS_URL = 'https://www.leagueofgraphs.com/ru/champions/spells/{hero_slug}'


def get_html(url: str) -> str:
	driver.get(url)

	return driver.page_source


def get_progressbar_value(td: element.Tag):
	return float(td.find('progressbar').attrs['data-value'])


def get_table(soup, class_: str) -> Generator:
	table = soup.find('table', attrs={'class': class_})
	rows = table.find_all('tr')[1:]

	for row in rows:
		yield row


def get_block_content(block: element.Tag) -> str:
	return block.text.strip()


class Hero(object):
	def __init__(self, name: str, slug: str, position: str, \
	             popularity: float, win_rate: float, blocks: float, kda: dict, \
	             pentakills: float):

		self.name = name
		self.slug = slug
		self.link = None
		self.position = position
		self.popularity = popularity
		self.win_rate = win_rate
		self.blocks = blocks
		self.kda = kda
		self.pentakills = pentakills

		self.parser = None


class HeroesListParser(object):
	''' Парсит список персонажей '''

	def get_heroes_list(self) -> list:
		html = get_html(BUILDS_URL)
		soup = bs(html, 'html.parser')

		heroes_list_table = get_table(soup, 'data_table')
		heroes_list = [self._create_hero(hero_row) \
			for hero_row in heroes_list_table]

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

		print(f'{hero_stats}')

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
	heroes_list_parser = HeroesListParser()
	heroes = heroes_list_parser.get_heroes_list()

	'''
	kindred = list(filter(lambda h: h.name == 'Варвик', heroes))[0]
	kindred = Hero(
		link='https://www.leagueofgraphs.com/ru/champions/builds/kindred',
		name='Киндред',
		line='jungle'
	)
	print(kindred)
	all_stats = kindred.get_statistics()
	for key, value in all_stats.items():
		print(key, value)
	'''


if __name__ == '__main__':
	main()