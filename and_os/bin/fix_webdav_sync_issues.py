#!/usr/bin/env python3
"""
fix_webdav_sync_issues.py — The complex fix of the problematic paths and the files for the stable synchronization of the WebDAV:
1. The replacement of the symlinks blender_bridge.py and blender_core.py with the real python files.
2. The shortening of the critically long names of the ultrasound files in the helth_doc (251 bytes -> 40 bytes).
3. The elimination of the trailing dots before the extension (..md, ....md -> .md).
4. The cascading update of all the incoming [[wiki links]] over the whole vault.
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
    print("=== STAGE 1: The replacement of the symlinks with the real files ===")
    
    # 1. blender_bridge.py
    bb_path = VAULT_ROOT / "and_os/bin/blender_bridge.py"
    cg_path = VAULT_ROOT / "and_os/bin/cg_bridge.py"
    if bb_path.is_symlink():
        content = cg_path.read_text(encoding="utf-8")
        bb_path.unlink()
        bb_path.write_text(content, encoding="utf-8")
        print(f"✅ The symlink {bb_path.relative_to(VAULT_ROOT)} was replaced with the full file.")
    elif bb_path.exists():
        print(f"ℹ️ {bb_path.relative_to(VAULT_ROOT)} is already a regular file.")

    # 2. cg_workspace/blender_core.py
    bc_path = VAULT_ROOT / "and_os/opt/apps/cg_workspace/blender_core.py"
    core_path = VAULT_ROOT / "and_os/opt/apps/cg_workspace/cg_core.py"
    if bc_path.is_symlink():
        content = core_path.read_text(encoding="utf-8")
        bc_path.unlink()
        bc_path.write_text(content, encoding="utf-8")
        print(f"✅ The symlink {bc_path.relative_to(VAULT_ROOT)} was replaced with the full file.")
    elif bc_path.exists():
        print(f"ℹ️ {bc_path.relative_to(VAULT_ROOT)} is already a regular file.")

    # 3. The blender_workspace catalog (if the symlink)
    bw_dir = VAULT_ROOT / "and_os/opt/apps/blender_workspace"
    if bw_dir.is_symlink():
        bw_dir.unlink()
        print(f"✅ The symlink of the catalog {bw_dir.relative_to(VAULT_ROOT)} was safely removed.")

def step2_collect_renames():
    """Forms the map of the renamings: old_path -> new_path and old_stem -> new_stem"""
    print("\n=== STAGE 2: The preparation of the renamings map ===")
    rename_map = [] # list of (old_path, new_path, old_stem, new_stem)

    # 2.1 The long names of the ultrasound
    uzi_dir = VAULT_ROOT / "Nero/profile/health/my/helth_doc"
    if uzi_dir.exists():
        for f in uzi_dir.glob("Ультразвуковое исследование*"):
            old_stem = f.stem
            # Determining the suffix with the timestamp
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

    # 2.2 The files with the trailing dots (..md, ....md)
    for root, dirs, files in os.walk(VAULT_ROOT):
        # Ignoring the technical directories
        if any(ign in root for ign in [".git", ".trash", ".smart-env"]):
            continue
        for fname in files:
            name, ext = os.path.splitext(fname)
            if name.endswith("."):
                f = Path(root) / fname
                clean_stem = name.rstrip(" .")
                new_name = clean_stem + ext
                new_path = Path(root) / new_name
                # Checking the absence of the collision with the already existing file
                if new_path.exists() and new_path != f:
                    print(f"⚠️ The collision for the {fname}: the {new_name} already exists!")
                    continue
                rename_map.append((f, new_path, name, clean_stem))

    print(f"Total prepared to the renaming: {len(rename_map)} files.")
    return rename_map

def step3_execute_renames_and_update_links(rename_map):
    print("\n=== STAGE 3: The renaming of the files and the cascading update of the links ===")
    
    # 1. Performing the renaming of the files
    renamed_count = 0
    link_replacements = {} # old_stem -> new_stem
    
    for old_p, new_p, old_stem, new_stem in rename_map:
        if not old_p.exists():
            continue
        old_p.rename(new_p)
        renamed_count += 1
        if old_stem != new_stem:
            link_replacements[old_stem] = new_stem

    print(f"✅ The files were renamed: {renamed_count}.")
    print(f"🔄 The pairs of the wiki links replacements were formed: {len(link_replacements)}.")

    # 2. Updating the links in all the Markdown files of the vault
    print("🔍 The scanning of the vault and the update of the incoming [[wiki links]]...")
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
            # Replacing in the format [[old_stem]] or [[path/old_stem]] or [[old_stem|...]]
            # The regex for the safe search
            pattern = re.compile(r"(\[\[(?:[^\]\r\n]*\/)?)(" + re.escape(old_stem) + r")([\|\]])")
            if pattern.search(new_content):
                new_content, count = pattern.subn(r"\g<1>" + new_stem + r"\g<3>", new_content)
                if count > 0:
                    modified = True
                    total_links_updated += count
                    
        if modified:
            md_file.write_text(new_content, encoding="utf-8")
            files_modified += 1
            
    print(f"✅ The links were updated: {total_links_updated} in the {files_modified} notes.")

def main():
    step1_fix_symlinks()
    rename_map = step2_collect_renames()
    step3_execute_renames_and_update_links(rename_map)
    print("\n🎉 All the operations were completed successfully!")

if __name__ == "__main__":
    main()
