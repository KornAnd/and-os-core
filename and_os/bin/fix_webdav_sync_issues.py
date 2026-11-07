#!/usr/bin/env python3
"""
fix_webdav_sync_issues.py — Комплексное исправление проблемных путей и файлов для стабильной синхронизации WebDAV:
1. Замена симлинков blender_bridge.py и blender_core.py на реальные python-файлы.
2. Сокращение критически длинных имён файлов УЗИ в helth_doc (251 байт -> 40 байт).
3. Устранение завершающих точек перед расширением (..md, ....md -> .md).
4. Каскадное обновление всех входящих [[вики-ссылок]] по всему хранилищу.
"""

import os
import sys
import re
from pathlib import Path

try:
    from and_os.lib.core.root_config import RootConfig
    VAULT_ROOT = Path(RootConfig.load().vault_root)
except Exception:
    VAULT_ROOT = Path(__file__).resolve().parents[2]

def step1_fix_symlinks():
    print("=== ЭТАП 1: Замена симлинков на реальные файлы ===")
    
    # 1. blender_bridge.py
    bb_path = VAULT_ROOT / "and_os/bin/blender_bridge.py"
    cg_path = VAULT_ROOT / "and_os/bin/cg_bridge.py"
    if bb_path.is_symlink():
        content = cg_path.read_text(encoding="utf-8")
        bb_path.unlink()
        bb_path.write_text(content, encoding="utf-8")
        print(f"✅ Симлинк {bb_path.relative_to(VAULT_ROOT)} заменён на полноценный файл.")
    elif bb_path.exists():
        print(f"ℹ️ {bb_path.relative_to(VAULT_ROOT)} уже является обычным файлом.")

    # 2. cg_workspace/blender_core.py
    bc_path = VAULT_ROOT / "and_os/opt/apps/cg_workspace/blender_core.py"
    core_path = VAULT_ROOT / "and_os/opt/apps/cg_workspace/cg_core.py"
    if bc_path.is_symlink():
        content = core_path.read_text(encoding="utf-8")
        bc_path.unlink()
        bc_path.write_text(content, encoding="utf-8")
        print(f"✅ Симлинк {bc_path.relative_to(VAULT_ROOT)} заменён на полноценный файл.")
    elif bc_path.exists():
        print(f"ℹ️ {bc_path.relative_to(VAULT_ROOT)} уже является обычным файлом.")

    # 3. blender_workspace каталог (если симлинк)
    bw_dir = VAULT_ROOT / "and_os/opt/apps/blender_workspace"
    if bw_dir.is_symlink():
        bw_dir.unlink()
        print(f"✅ Симлинк каталога {bw_dir.relative_to(VAULT_ROOT)} безопасно удалён.")

def step2_collect_renames():
    """Формирует карту переименований: old_path -> new_path и old_stem -> new_stem"""
    print("\n=== ЭТАП 2: Подготовка карты переименований ===")
    rename_map = [] # list of (old_path, new_path, old_stem, new_stem)

    # 2.1 Длинные имена УЗИ
    uzi_dir = VAULT_ROOT / "Nero/profile/health/my/helth_doc"
    if uzi_dir.exists():
        for f in uzi_dir.glob("Ультразвуковое исследование*"):
            old_stem = f.stem
            # Определяем суффикс с timestamp
            m = re.search(r"(\d{10,})", f.name)
            ts = m.group(1) if m else "doc"
            new_name = f"УЗИ органов брюшной полости_{ts}{f.suffix}"
            new_path = f.parent / new_name
            rename_map.append((f, new_path, old_stem, new_path.stem))
            
        pdf_dir = uzi_dir / ".pdf_archive"
        if pdf_dir.exists():
            for f in pdf_dir.glob("Ультразвуковое исследование*"):
                old_stem = f.stem
                m = re.search(r"(\d{10,})", f.name)
                ts = m.group(1) if m else "doc"
                new_name = f"УЗИ органов брюшной полости_{ts}{f.suffix}"
                new_path = f.parent / new_name
                rename_map.append((f, new_path, old_stem, new_path.stem))

    # 2.2 Файлы с завершающими точками (..md, ....md)
    for root, dirs, files in os.walk(VAULT_ROOT):
        # Игнорируем технические директории
        if any(ign in root for ign in [".git", ".trash", ".smart-env"]):
            continue
        for fname in files:
            name, ext = os.path.splitext(fname)
            if name.endswith("."):
                f = Path(root) / fname
                clean_stem = name.rstrip(" .")
                new_name = clean_stem + ext
                new_path = Path(root) / new_name
                # Проверим, нет ли коллизии с уже существующим файлом
                if new_path.exists() and new_path != f:
                    print(f"⚠️ Коллизия для {fname}: {new_name} уже существует!")
                    continue
                rename_map.append((f, new_path, name, clean_stem))

    print(f"Итого подготовлено к переименованию: {len(rename_map)} файлов.")
    return rename_map

def step3_execute_renames_and_update_links(rename_map):
    print("\n=== ЭТАП 3: Переименование файлов и каскадное обновление ссылок ===")
    
    # 1. Выполняем переименование файлов
    renamed_count = 0
    link_replacements = {} # old_stem -> new_stem
    
    for old_p, new_p, old_stem, new_stem in rename_map:
        if not old_p.exists():
            continue
        old_p.rename(new_p)
        renamed_count += 1
        if old_stem != new_stem:
            link_replacements[old_stem] = new_stem

    print(f"✅ Переименовано {renamed_count} файлов.")
    print(f"🔄 Сформировано {len(link_replacements)} пар замен вики-ссылок.")

    # 2. Обновляем ссылки во всех Markdown файлах хранилища
    print("🔍 Сканирование хранилища и обновление входящих [[вики-ссылок]]...")
    all_md_files = [f for f in VAULT_ROOT.rglob("*.md") if not f.name.startswith(".") and ".git" not in str(f) and ".trash" not in str(f)]
    
    files_modified = 0
    total_links_updated = 0
    
    for md_file in all_md_files:
        try:
            content = md_file.read_text(encoding="utf-8")
        except Exception:
            continue
            
        modified = False
        new_content = content
        
        for old_stem, new_stem in link_replacements.items():
            # Заменяем в формате [[old_stem]] или [[path/old_stem]] или [[old_stem|...]]
            # Регулярка для безопасного поиска
            pattern = re.compile(r"(\[\[(?:[^\]\r\n]*\/)?)(" + re.escape(old_stem) + r")([\|\]])")
            if pattern.search(new_content):
                new_content, count = pattern.subn(r"\g<1>" + new_stem + r"\g<3>", new_content)
                if count > 0:
                    modified = True
                    total_links_updated += count
                    
        if modified:
            md_file.write_text(new_content, encoding="utf-8")
            files_modified += 1
            
    print(f"✅ Обновлено ссылок: {total_links_updated} в {files_modified} заметках.")

def main():
    step1_fix_symlinks()
    rename_map = step2_collect_renames()
    step3_execute_renames_and_update_links(rename_map)
    print("\n🎉 Все операции успешно завершены!")

if __name__ == "__main__":
    main()
