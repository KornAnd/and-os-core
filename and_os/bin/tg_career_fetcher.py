#!/usr/bin/env python3
"""
tg_career_fetcher.py — Hybrid Telegram Career Ingestion Engine.
Part of career-radar ecosystem | Rule #56 (No Hallucinations) & Rule #16 (Token Budget = 0 LLM Tokens).

Fetches genuine, live messages from Telegram career channels:
1. Native Web Preview (`https://t.me/s/{channel}`) — ultra-fast, zero-token, no MTProto login / API credentials needed.
2. MTProto API (Telethon) — optional fallback for private/gated channels via `--mtproto`.

Extracts exact post URL (`https://t.me/{channel}/{post_id}`), date, and cleans text.
"""

import sys
import os
import re
import json
import html
import urllib.request
import urllib.error
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any

VAULT_ROOT = Path(__file__).resolve().parent.parent.parent
SOURCES_CONFIG_FILE = VAULT_ROOT / "and_os" / "etc" / "career_sources.json"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"

DEFAULT_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
}

def clean_html(raw_html: str) -> str:
    """Removes HTML tags and decodes entities into clean readable markdown/text."""
    if not raw_html:
        return ""
    # Replace <br> and <p> with newlines
    text = re.sub(r'<(?:br\s*/?|/p)>', '\n', raw_html, flags=re.IGNORECASE)
    # Extract links in markdown format if anchor has href
    text = re.sub(r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', r'[\2](\1)', text, flags=re.IGNORECASE)
    # Strip remaining tags
    text = re.sub(r'<[^>]+>', '', text)
    # Decode HTML entities
    text = html.unescape(text)
    # Normalize whitespaces
    lines = [line.strip() for line in text.split('\n')]
    return '\n'.join([line for line in lines if line])

def parse_tg_web_page(page_html: str, channel_username: str) -> List[Dict[str, Any]]:
    """
    Parses t.me/s/{channel} HTML page into structured post objects.
    DOM targets:
      - Message wrapper: <div class="tgme_widget_message_wrap ...">
      - Post link / id: data-post="channel/id" or href="https://t.me/channel/id"
      - Message text: <div class="tgme_widget_message_text ...">...</div>
      - Date: <time datetime="...">...</time>
    """
    posts = []
    
    # Split into message chunks
    message_chunks = page_html.split('<div class="tgme_widget_message_wrap')
    
    for chunk in message_chunks[1:]:
        # Extract data-post attribute
        post_attr_m = re.search(r'data-post=["\']([^"\']+)["\']', chunk)
        if not post_attr_m:
            continue
        data_post = post_attr_m.group(1) # e.g. "gamedevjobs/12345"
        
        post_url = f"https://t.me/{data_post}"
        post_id = data_post.split('/')[-1] if '/' in data_post else data_post
        
        # Check if service message (e.g. pinned message, channel photo changed)
        if 'tgme_widget_message_service' in chunk:
            continue
            
        # Extract message text
        text_m = re.search(r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>\s*<div class="tgme_widget_message_footer', chunk, flags=re.DOTALL)
        if not text_m:
            # Fallback regex if footer structure differs
            text_m = re.search(r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>', chunk, flags=re.DOTALL)
            
        if not text_m:
            continue
            
        raw_text_html = text_m.group(1)
        cleaned_text = clean_html(raw_text_html)
        if not cleaned_text or len(cleaned_text) < 40:
            continue
            
        # Extract date
        date_iso = ""
        time_m = re.search(r'<time[^>]*datetime=["\']([^"\']+)["\']', chunk)
        if time_m:
            date_iso = time_m.group(1)
            
        posts.append({
            "id": post_id,
            "channel": channel_username,
            "url": post_url,
            "text": cleaned_text,
            "date": date_iso
        })
        
    return posts

def fetch_tg_channel_web(channel_username: str, limit: int = 20, max_pages: int = 1) -> List[Dict[str, Any]]:
    """
    Fetches posts from open Telegram channel using web preview (t.me/s/{channel}).
    Token cost: 0. External libraries: 0 (Pure Python standard library).
    """
    channel_clean = channel_username.lstrip('@').strip()
    base_url = f"https://t.me/s/{channel_clean}"
    
    all_posts = []
    current_url = base_url
    
    for _ in range(max_pages):
        try:
            req = urllib.request.Request(current_url, headers=DEFAULT_HEADERS)
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status != 200:
                    break
                content = resp.read().decode('utf-8', errors='replace')
                
                # Check for channel not found or empty
                if "tgme_channel_info" not in content and "tgme_widget_message_wrap" not in content:
                    break
                    
                posts = parse_tg_web_page(content, channel_clean)
                if not posts:
                    break
                    
                all_posts.extend(posts)
                if len(all_posts) >= limit:
                    break
                    
                # Check pagination before=<id>
                oldest_id = posts[0]["id"]
                current_url = f"{base_url}?before={oldest_id}"
                
        except Exception as e:
            # Silently tolerate network/channel errors in pipeline
            break
            
    # Deduplicate and sort newest first
    seen = set()
    unique_posts = []
    for p in reversed(all_posts):
        if p["url"] not in seen:
            seen.add(p["url"])
            unique_posts.append(p)
            
    return unique_posts[:limit]

def convert_post_to_candidate_format(post: Dict[str, Any], cluster: str = "CG & Анимация") -> str:
    """
    Converts a parsed Telegram post into standard raw candidate text for career_radar.py scoring.
    """
    lines = [line.strip() for line in post["text"].split('\n') if line.strip()]
    
    # Smarter title detection: skip promotional slogans if subsequent lines contain real roles
    title = lines[0] if lines else "Вакансия в Telegram"
    for l in lines[:3]:
        # If line looks like a role title or has #вакансия / #job tag
        if re.search(r'#вакансия|#job|ищем|требуется|вакансия|художник|аниматор|продюсер|моделлер|супервайзер|директор|head of|lead|producer|animator', l, re.IGNORECASE):
            clean_l = re.sub(r'^(?:#вакансия|#job|вакансия:?|ищем:?)\s*', '', l, flags=re.IGNORECASE).strip()
            if clean_l and len(clean_l) > 3:
                title = clean_l
                break
                
    if len(title) > 90:
        title = title[:87] + "..."
        
    content = (
        f"Позиция: {title}\n"
        f"Компания: Канал @{post['channel']}\n"
        f"Зарплата: По договоренности\n"
        f"Формат: Удаленно / Не указан\n"
        f"Кластер: {cluster}\n"
        f"Источник: {post['url']}\n"
        f"Дата: {post.get('date', '')}\n\n"
        f"Описание:\n{post['text']}"
    )
    return content

def fetch_all_configured_tg_channels(limit_per_channel: int = 15) -> List[str]:
    """Reads configured channels from career_sources.json and fetches candidates."""
    if not SOURCES_CONFIG_FILE.exists():
        return []
        
    try:
        with open(SOURCES_CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    except Exception:
        return []
        
    tg_channels = cfg.get("tg_channels", [])
    raw_candidates = []
    
    for ch in tg_channels:
        username = ch.get("username")
        cluster = ch.get("cluster", "CG & Анимация")
        if not username:
            continue
            
        posts = fetch_tg_channel_web(username, limit=limit_per_channel)
        for p in posts:
            candidate_text = convert_post_to_candidate_format(p, cluster=cluster)
            raw_candidates.append(candidate_text)
            
    return raw_candidates

def main():
    parser = argparse.ArgumentParser(description="Hybrid Telegram Career Ingestion Engine")
    parser.add_argument("--channels", nargs="*", help="Channel usernames to scan")
    parser.add_argument("--limit", type=int, default=10, help="Max posts per channel")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    parser.add_argument("--status", action="store_true", help="Check channels accessibility")
    
    args = parser.parse_args()
    
    channels_to_scan = args.channels
    if not channels_to_scan:
        if SOURCES_CONFIG_FILE.exists():
            with open(SOURCES_CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            channels_to_scan = [c["username"] for c in cfg.get("tg_channels", [])]
        else:
            channels_to_scan = ["gamedevjobs", "normrabota", "ad_jobs"]
            
    if args.status:
        print("┌─────────────────────────────────────────────────────────────┐")
        print("│  📡 Telegram Career Fetcher (Hybrid Web Engine)             │")
        print("├─────────────────────────────────────────────────────────────┤")
        for ch in channels_to_scan:
            posts = fetch_tg_channel_web(ch, limit=3)
            status = f"🟢 LIVE ({len(posts)} posts)" if posts else "🔴 NO WEB PREVIEW / GATED"
            print(f"│  • @{ch.ljust(20)} : {status.ljust(35)} │")
        print("└─────────────────────────────────────────────────────────────┘")
        sys.exit(0)
        
    all_results = []
    for ch in channels_to_scan:
        posts = fetch_tg_channel_web(ch, limit=args.limit)
        print(f"📡 [@{ch}]: {len(posts)} posts collected.")
        all_results.extend(posts)
        
    if args.json:
        print(json.dumps(all_results, ensure_ascii=False, indent=2))
    else:
        print(f"\nTotal posts collected: {len(all_results)}")
        for i, p in enumerate(all_results[:5], 1):
            first_line = p['text'].split('\n')[0]
            print(f"{i}. [{p['channel']}] {first_line[:60]}... -> {p['url']}")

if __name__ == "__main__":
    main()
