
import json
import requests
import shutil
from bs4 import BeautifulSoup
from multiprocessing import Pool
from pathlib import Path
from progress.bar import Bar
from time import sleep

galar_dex_url = 'https://www.serebii.net/swordshield/galarpokedex.shtml'
pokemon_image_url_base = 'https://www.serebii.net/swordshield/pokemon/'
pokemon_sprite_url_base = 'https://www.serebii.net/pokedex-swsh/icon/'

def get_abilities(ability_data):
    return [ability_link.contents[0] for ability_link in ability_data.find_all('a')]

def get_type(type_data):
    return [type_link.get('href').split('/')[-1].split('.')[0] for type_link in type_data.find_all('a')]

def get_info_of_pokemon(pokemon_data):
    parsed_data = dict()

    parsed_data['galar_dex_num'] = pokemon_data[0].contents[0].strip()[1:]  # Omit the '#' at the beginning of the string
    parsed_data['national_dex_num'] = pokemon_data[1].contents[1].find('img').get('src').split('.')[0][-3:]
    parsed_data['name'] = pokemon_data[2].contents[1].contents[0].strip()
    parsed_data['abilities'] = get_abilities(pokemon_data[3])
    parsed_data['type'] = get_type(pokemon_data[4])
    parsed_data['hp'] = pokemon_data[5].contents[0]
    parsed_data['att'] = pokemon_data[6].contents[0]
    parsed_data['def'] = pokemon_data[7].contents[0]
    parsed_data['s_att'] = pokemon_data[8].contents[0]
    parsed_data['s_def'] = pokemon_data[9].contents[0]
    parsed_data['spd'] = pokemon_data[10].contents[0]

    return parsed_data

def parse_galar_dex_soup(soup: BeautifulSoup) -> dict:
    pokemon_data_soup = soup.find_all('td', class_='fooinfo')
    galar_dex_pokemon_data = {'pokemon': []}

    for i in range(0, 4400):
        if (i % 11) == 0:
            galar_dex_pokemon_data['pokemon'].append(get_info_of_pokemon(pokemon_data_soup[i:i+11]))
        else:
            continue

    return galar_dex_pokemon_data

def get_pokemon_image_url(pokemon_num):
    return f'{pokemon_image_url_base}{pokemon_num}.png'

def get_pokemon_sprite_url(pokemon_num):
    return f'{pokemon_sprite_url_base}{pokemon_num}.png'

def download_and_save_pokemon_image(image_url, pokemon_name):
    if Path(f'./Images/{pokemon_name}.png').exists():
        return

    while True:
        try:
            with requests.get(image_url, stream=True) as resp:
                local_file = open(f'./Images/{pokemon_name}_image.png', 'wb')
                resp.raw.decode_content = True
                shutil.copyfileobj(resp.raw, local_file)
                return
        except requests.exceptions.ConnectionError:
            pass  # Server refused connection, so sleep for a bit
        finally:
            sleep(1.5)


def download_and_save_pokemon_sprite(sprite_url, pokemon_name):
    if Path(f'./Sprites/{pokemon_name}.png').exists():
        return

    while True:
        try:
            with requests.get(sprite_url, stream=True) as resp:
                local_file = open(f'./Sprites/{pokemon_name}_sprite.png', 'wb')
                resp.raw.decode_content = True
                shutil.copyfileobj(resp.raw, local_file)
                return
        except requests.exceptions.ConnectionError:
            pass  # Server refused connection, so sleep for a bit
        finally:
            sleep(1.5)

def download_and_save_sprites_and_images(pokemon_data):
    name = pokemon_data[0]
    national_num = pokemon_data[1]

    image_url = get_pokemon_image_url(national_num)
    download_and_save_pokemon_image(image_url, name)

    sprite_url = get_pokemon_sprite_url(national_num)
    download_and_save_pokemon_sprite(sprite_url, name)

def write_data_files(galar_dex_pokemon_data: dict):
    Path("./Data").mkdir(exist_ok=True)

    with open('./Data/galar_dex_pokemon.json', 'w') as pokemon_data_json_file:
        json.dump(galar_dex_pokemon_data, pokemon_data_json_file)

    with open('./Data/galar_dex_pokemon_pretty.json', 'w') as pretty_pokemon_data_json_file:
        json.dump(galar_dex_pokemon_data, pretty_pokemon_data_json_file, indent=4, sort_keys=True)

    with open('./Data/galar_dex_pokemon.csv', 'w') as pokemon_data_csv_file:
        file_str = 'galar_dex_num\tnational_dex_num\tname\ttype\tabilities\thp\tatt\tdef\ts_att\ts_def\tspd\n'
        for pokemon in galar_dex_pokemon_data['pokemon']:
            file_str += f"{pokemon['galar_dex_num']}\t{pokemon['national_dex_num']}\t{pokemon['name']}\t{pokemon['type']}\t" + \
                f"{pokemon['abilities']}\t{pokemon['hp']}\t{pokemon['att']}\t{pokemon['def']}\t{pokemon['s_att']}\t" + \
                f"{pokemon['s_def']}\t{pokemon['spd']}\n"
        pokemon_data_csv_file.write(file_str)

def get_name_and_num_data_of_pokemon(pokemon_data: list):
    return [(pokemon['name'], pokemon['national_dex_num']) for pokemon in pokemon_data]

def main():
    response = requests.get(galar_dex_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    galar_dex_pokemon_data = parse_galar_dex_soup(soup)

    write_data_files(galar_dex_pokemon_data)

    Path('./Sprites').mkdir(parents=True, exist_ok=True)
    Path('./Images').mkdir(parents=True, exist_ok=True)
    bar = Bar('Getting Pokémon images and sprites...', max=len(galar_dex_pokemon_data['pokemon']))
    pokemon_name_and_num_data = get_name_and_num_data_of_pokemon(galar_dex_pokemon_data['pokemon'])
    pool = Pool()
    for _ in pool.imap(download_and_save_sprites_and_images, pokemon_name_and_num_data):
        bar.next()
    bar.finish()

if __name__ == '__main__':
    main()