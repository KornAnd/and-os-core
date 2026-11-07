#!/usr/bin/env python3
"""Модуль кеширования выгрузок Ftrack API для снижения трат токенов и ускорения анализа.

Функции:
  query_cached(session, query_str, cache_key, max_age_hours=12)
"""

import os
import json
import time
import sys

VAULT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
SCRATCH_DIR = os.path.join(VAULT_ROOT, "and_os/var/ftrack_cache")

def get_cache_path(cache_key):
    os.makedirs(SCRATCH_DIR, exist_ok=True)
    clean_key = "".join(c if c.isalnum() or c in ("_", "-") else "_" for c in cache_key)
    return os.path.join(SCRATCH_DIR, f"{clean_key}.json")

def query_cached(session, query_str, cache_key, max_age_hours=12, force_refresh=False):
    """Выполняет query к Ftrack с автоматическим кешированием на диск.
    
    Возвращает список словарей со свойствами объектов.
    """
    cache_file = get_cache_path(cache_key)
    now = time.time()
    
    if not force_refresh and os.path.exists(cache_file):
        mtime = os.path.getmtime(cache_file)
        if (now - mtime) < (max_age_hours * 3600):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    sys.stderr.write(f"⚡ [CACHE HIT] {cache_key} ({len(data)} записей из кеша)\n")
                    return data
            except Exception as e:
                sys.stderr.write(f"⚠️ Ошибка чтения кеша {cache_file}: {e}, выполняем заново...\n")

    sys.stderr.write(f"📡 [FTRACK QUERY] {cache_key} ...\n")
    results = session.query(query_str).all()
    
    # Конвертация объектов Ftrack в сериализуемые словари
    serialized = []
    for r in results:
        item = {}
        for k in r.keys():
            val = r[k]
            # Обработка вложенных Ftrack Entity
            if hasattr(val, 'keys'):
                nested = {}
                for nk in val.keys():
                    nval = val[nk]
                    if isinstance(nval, (str, int, float, bool, type(None))):
                        nested[nk] = nval
                    elif hasattr(nval, '__str__'):
                        nested[nk] = str(nval)
                item[k] = nested
            elif isinstance(val, (str, int, float, bool, type(None))):
                item[k] = val
            elif hasattr(val, '__str__'):
                item[k] = str(val)
        serialized.append(item)
        
    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(serialized, f, ensure_ascii=False, indent=2)
        sys.stderr.write(f"💾 [CACHE SAVED] {cache_key} -> {cache_file}\n")
    except Exception as e:
        sys.stderr.write(f"⚠️ Ошибка сохранения кеша {cache_file}: {e}\n")
        
    return serialized
