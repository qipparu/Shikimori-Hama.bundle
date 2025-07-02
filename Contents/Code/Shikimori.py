# --- START OF FILE Shikimori.py (ВЕРСИЯ В КАЧЕСТВЕ ОТДЕЛЬНОГО ИСТОЧНИКА) ---

import os
import re
import common
from common import Log, DictString, Dict, SaveDict

# URL для ARM API, чтобы получить MAL ID по AniDB ID
ARM_API_URL_TEMPLATE = "https://arm.haglund.dev/api/v2/ids?source=anidb&include=myanimelist&id={id}"
# URL для Shikimori API, чтобы получить данные по MAL ID
SHIKIMORI_API_URL_TEMPLATE = "https://shikimori.one/api/animes/{id}"

def GetMetadata(anidb_id=None):
    """
    Получает метаданные с Shikimori как отдельный источник.
    1. Находит MyAnimeList ID по AniDB ID через ARM API.
    2. Запрашивает данные с Shikimori по MAL ID.
    3. Возвращает собственный словарь с названием, описанием и жанрами.
    """
    Log.Info("=== Shikimori.GetMetadata() ===".ljust(157, '='))
    shikimori_dict = {}

    if not anidb_id or not anidb_id.isdigit():
        Log.Info("No valid AniDB ID provided. Shikimori source skipped.")
        return shikimori_dict

    # --- 1. Получение MAL ID через ARM API ---
    arm_url = ARM_API_URL_TEMPLATE.format(id=anidb_id)
    Log.Info("Attempting to fetch MAL ID from ARM API: {url}".format(url=arm_url))

    arm_data = common.LoadFile(filename=str(anidb_id) + '_arm.json',
                               relativeDirectory=os.path.join('Shikimori', 'json', 'arm'),
                               url=arm_url,
                               cache=CACHE_1WEEK)

    mal_id = Dict(arm_data, 'myanimelist')

    if not mal_id:
        Log.Info("Failed to get MyAnimeList ID from ARM for AniDB ID {id}.".format(id=anidb_id))
        return shikimori_dict

    Log.Info("Successfully fetched MAL ID: {mal_id} for AniDB ID: {anidb_id}".format(mal_id=mal_id, anidb_id=anidb_id))

    # --- 2. Получение данных с Shikimori по MAL ID ---
    api_url = SHIKIMORI_API_URL_TEMPLATE.format(id=mal_id)
    Log.Info("Attempting to fetch Shikimori data directly using MAL ID URL: {url}".format(url=api_url))

    json_data = common.LoadFile(filename=str(mal_id) + '.json',
                                relativeDirectory=os.path.join('Shikimori', 'json', 'details'),
                                url=api_url,
                                cache=CACHE_1WEEK)

    if not json_data or isinstance(json_data, (str, unicode)) and "Not Found" in json_data:
        Log.Info("Failed to get data from Shikimori for MAL ID {id}.".format(id=mal_id))
        return shikimori_dict

    # --- 3. Формирование словаря с данными ---

    # --- Название на русском ---
    russian_title = Dict(json_data, 'russian')
    if russian_title:
        Log.Info("[Shikimori] Found title: '{}'".format(russian_title))
        SaveDict(russian_title, shikimori_dict, 'title')
        SaveDict(common.SortTitle(russian_title, 'ru'), shikimori_dict, 'title_sort')
        SaveDict(-1, shikimori_dict, 'language_rank') # Приоритет для русского языка

    # --- Описание ---
    description = Dict(json_data, 'description')
    if description:
        clean_summary = re.sub(r'\[.*?\]|<.*?>', '', description).strip()
        Log.Info("[Shikimori] Found summary.")
        SaveDict(clean_summary, shikimori_dict, 'summary')

    # --- Жанры ---
    shikimori_genres = Dict(json_data, 'genres')
    if shikimori_genres and isinstance(shikimori_genres, list):
        genre_list = [Dict(g, 'russian') for g in shikimori_genres if Dict(g, 'russian')]
        if genre_list:
            Log.Info("[Shikimori] Found genres: {}".format(genre_list))
            SaveDict(sorted(genre_list), shikimori_dict, 'genres')

    Log.Info("--- return ---".ljust(157, '-'))
    Log.Info("Shikimori_dict: {}".format(DictString(shikimori_dict, 1)))
    return shikimori_dict
