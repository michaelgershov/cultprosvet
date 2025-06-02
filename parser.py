from supabase_connection import supabase_client, supabase_bucket_name
from selenium import webdriver
from bs4 import BeautifulSoup
import pandas as pd
import time
import uuid
import datetime
import requests
from embeddings_formation import embeddings_formation

url = 'https://afisha.relax.by/kino/minsk/'

options = webdriver.ChromeOptions()
options.add_argument('--headless')

with webdriver.Chrome(options=options) as driver:
    driver.get(url)
    time.sleep(5)
    html = driver.page_source

soup = BeautifulSoup(html, 'html.parser')
data = soup.findAll('div', class_='schedule__list')

query = supabase_client.table('cinemas').select('*').execute().data
if query:
    cinemas = pd.DataFrame(query)
else:
    cinemas = pd.DataFrame(
        columns=['id', 'name', 'address']
    )

query = supabase_client.table('movies').select('id, name, description').execute().data
if query:
    movies = pd.DataFrame(query)
else:
    movies = pd.DataFrame(
        columns=['id', 'name', 'description']
    )

# количество возвращаемых строк изменяется в настройках проекта
query = supabase_client.table('movie_cinema').select('movie_id, cinema_id, datetime').execute().data
if query:
    movie_cinema = pd.DataFrame(query)
else:
    movie_cinema = pd.DataFrame(
        columns=['movie_id', 'cinema_id', 'datetime']
    )

date_transform = {
    'января,': '01',
    'февраля,': '02',
    'марта,': '03',
    'апреля,': '04',
    'мая,': '05',
    'июня,': '06',
    'июля,': '07',
    'августа,': '08',
    'сентября,': '09',
    'октября,': '10',
    'ноября,': '11',
    'декабря,': '12'
}


driver = webdriver.Chrome(options=options)
for table in data:
    date = table.find('h5', class_='h5 h5--compact h5--bolder u-mt-6x')
    if date:
        date = date.get_text(separator='\n', strip=True).replace('сегодня,', '').split()
        date = f'{date[0]}.{date_transform[date[1]]}.{datetime.date.today().year}'
        for item in table.findAll('div', class_='schedule__table--movie__item'):
            cinema_name = item.find('a', class_='schedule__place-link link')
            if cinema_name:
                cinema_name = cinema_name.get_text(separator='\n', strip=True)
                cinema_address = item.find(
                    'span', class_='schedule__place-link text-black-light'
                )
                if cinema_address:
                    cinema_address = cinema_address.get_text(separator='\n', strip=True)

                cinema_data = {
                    'name': cinema_name,
                    'address': cinema_address
                }
                if cinemas[
                    (cinemas['name'] == cinema_name) & (cinemas['address'] == cinema_address)
                ].empty:
                    response = supabase_client.table('cinemas').insert(cinema_data).execute()
                    cinema_id = response.data[0]['id']
                    cinemas.loc[len(cinemas)] = {**{'id': cinema_id}, **cinema_data}
                else:
                    cinema_id = cinemas[
                        (cinemas['name'] == cinema_name) & (cinemas['address'] == cinema_address)
                    ]['id'].values[0]

            movie = item.find('a', class_='schedule__event-link link')
            if movie:
                movie_name = movie.get_text(separator='\n', strip=True)
                
                driver.get(movie['href'])
                time.sleep(2)
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                
                movie_desc = soup.find(
                    'div', class_='b-afisha_cinema_description_text', itemprop='description'
                )
                if movie_desc:
                    movie_desc = movie_desc.get_text(separator='\n', strip=True)
                    
                movie_data = {
                    'name': movie_name,
                    'description': movie_desc
                }
               
                if movies[
                    (movies['name'] == movie_name) & (movies['description'] == movie_desc)
                ].empty:
                    
                    movie_img = soup.find(
                        'img', class_='b-afisha-event__image'
                    )
                    if movie_img:
                        movie_img = movie_img['src']
                        response = requests.get(movie_img)
                        try:
                            img_data = response.content

                            content_type = response.headers.get('Content-Type', 'image/jpeg')
                            expansion = content_type.split('/')[-1]

                            img_name = f'{uuid.uuid4()}.{expansion}'
                            result = supabase_client.storage.from_(supabase_bucket_name).upload(
                                img_name,
                                img_data,
                                {'content-type': content_type}
                            )
                            movie_data['poster'] = result.path
                        except:
                            movie_data['poster'] = None
                    
                    keys = ('country', 'year', 'directors', 'starring', 'duration', 'age_limit', 'year')
                    movie_params = {k: None for k in keys}
                    for name, desc in zip(
                        soup.findAll('span', class_='b-afisha_cinema_description_table_name'),
                        soup.findAll('span', class_='b-afisha_cinema_description_table_desc')
                    ):
                        if name:
                            name = name.get_text(separator='\n', strip=True)
                            if desc:
                                desc = desc.get_text(separator='\n', strip=True)
                                try:
                                    if name == 'Страна:':
                                        movie_params['country'] = ' '.join(desc.split())
                                    if name == 'Год:':
                                        movie_params['year'] = int(desc)
                                    if name == 'Режиссеры:':
                                        movie_params['directors'] = ' '.join(desc.split())
                                    if name == 'В ролях:':
                                        movie_params['starring'] = ' '.join(desc.split())
                                    if name == 'Длительность:':
                                        if 'ч' in desc and 'мин' in desc:
                                            desc = desc.split('ч')
                                            desc = [int(t.strip('мин').strip()) for t in desc]
                                            desc = 60*desc[0] + desc[1]
                                        elif 'ч' in desc:
                                            desc = 60*int(desc.strip('ч').strip())
                                        else:
                                            desc = int(desc.strip('мин').strip())
                                        movie_params['duration'] = desc
                                    if name == 'Возрастное ограничение:':
                                        movie_params['age_limit'] = int(desc[:-1])
                                    if name == 'Жанр:':
                                        movie_params['genre'] = ' '.join(desc.split())
                                except:
                                    continue
                                    
                    movie_data_sb = {**movie_data, **movie_params}
                    movie_data_sb['embeddings'] = embeddings_formation(movie_data_sb)
                    response = supabase_client.table('movies').insert(movie_data_sb).execute()
                    movie_id = response.data[0]['id']
                    movies.loc[len(movies)] = {**{'id': movie_id}, **movie_data}
                else:
                    movie_id = movies[
                        (movies['name'] == movie_name) & (movies['description'] == movie_desc)
                    ]['id'].values[0]
                
                movie_time_blue = item.findAll(
                    'a', class_='schedule__seance-time schedule__seance--buy js-buy-ticket one-operator'
                )
                movie_time_gray = item.findAll('span', class_='schedule__seance-time schedule__seance--buy-timeout')
                movie_time = [
                    t.get_text(separator='\n', strip=True) for t in movie_time_blue + movie_time_gray if t is not None
                ]
                
                for t in movie_time:
                    date_time = f'{date}, {t}'
                    if movie_cinema.query(
                        'movie_id == @movie_id and cinema_id == @cinema_id and datetime == @date_time'
                    ).empty:
                        movie_cinema_data = {
                            'movie_id': int(movie_id),
                            'cinema_id': int(cinema_id),
                            'datetime': date_time
                        }
                        response = supabase_client.table('movie_cinema').insert(movie_cinema_data).execute()
                        movie_cinema.loc[len(movie_cinema)] = movie_cinema_data

driver.quit()
