# --- START OF FILE Shikimori.py (ВЕРСИЯ С СОВМЕСТИМЫМ СИНТАКСИСОМ) ---

import os
import re
import common
from common import Log, DictString, Dict, SaveDict

# URL для ARM API, чтобы получить MAL ID по AniDB ID
ARM_API_URL_TEMPLATE = "https://arm.haglund.dev/api/v2/ids?source=anidb&include=myanimelist&id={id}"
# URL для Shikimori API, чтобы получить данные по MAL ID
SHIKIMORI_API_URL_TEMPLATE = "https://shikimori.one/api/animes/{id}"

def OverrideMetadata(anidb_id=None, anidb_dict={}):
    """
    Эта функция сначала получает MyAnimeList ID с помощью ARM API, используя AniDB ID.
    Затем использует полученный MAL ID для запроса данных с Shikimori и
    принудительно записывает русское название и описание в переданный словарь anidb_dict.
    """
    Log.Info("=== Shikimori.OverrideMetadata() ===".ljust(157, '='))

    if not anidb_id or not anidb_id.isdigit():
        Log.Info("No valid AniDB ID provided. Shikimori override skipped.")
        return

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
        return

    Log.Info("Successfully fetched MAL ID: {mal_id} for AniDB ID: {anidb_id}".format(mal_id=mal_id, anidb_id=anidb_id))

    # --- 2. Получение данных с Shikimori по MAL ID ---
    api_url = SHIKIMORI_API_URL_TEMPLATE.format(id=mal_id)
    Log.Info("Attempting to fetch Shikimori data directly using MAL ID URL: {url}".format(url=api_url))
    
    json_data = common.LoadFile(filename=str(mal_id) + '.json',
                                relativeDirectory=os.path.join('Shikimori', 'json', 'details'),
                                url=api_url,
                                cache=CACHE_1WEEK)
    
    if not json_data or isinstance(json_data, (str, unicode)) and "Not Found" in json_data:
        Log.Info("Failed to get data from Shikimori for MAL ID {id}. Maybe it's not on Shikimori.".format(id=mal_id))
        return

    # --- 3. Обработка и подмена данных ---
    data_overridden = False
    
    # --- Название на русском ---
    russian_title = Dict(json_data, 'russian')
    if russian_title:
        Log.Info("[OVERRIDE] Forcing title from Shikimori: '{}' into anidb_dict".format(russian_title))
        anidb_dict['title'] = russian_title
        anidb_dict['title_sort'] = common.SortTitle(russian_title, 'ru')
        anidb_dict['language_rank'] = -1
        data_overridden = True

    # --- Описание ---
    description = Dict(json_data, 'description')
    if description:
        clean_summary = re.sub(r'\[.*?\]|<.*?>', '', description).strip()
        Log.Info("[OVERRIDE] Forcing summary from Shikimori into anidb_dict.")
        anidb_dict['summary'] = clean_summary
        data_overridden = True

    if data_overridden:
        Log.Info("anidb_dict after override: {}".format(common.DictString(anidb_dict, 1)))

    return
# --- END OF FILE Shikimori.py ---