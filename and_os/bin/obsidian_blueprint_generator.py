#!/usr/bin/env python3
"""
obsidian_blueprint_generator.py — Generator of the reference architecture and plugins passport of Obsidian.
AnD os v1.0.0 — Production Environment Blueprint

Creates or updates the single file `OBSIDIAN_STRUCTURE_BLUEPRINT.md` in the root / in and_os/etc/,
containing the 100% specification:
  1. The vault architecture and the catalogs (the contours, the contexts, the knowledge bases).
  2. The base Obsidian settings (app.json, core-plugins, appearance).
  3. The full community plugins registry (versions, purposes, the key configs).
  4. The 1-click / headless deployment instruction for any LLM on a new computer.

The update cadence: once a month at the neural network launch or with the --force flag.
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta

VAULT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
OBSIDIAN_DIR = os.path.join(VAULT_ROOT, ".obsidian")
TARGET_MD = os.path.join(VAULT_ROOT, "and_os/etc/OBSIDIAN_STRUCTURE_BLUEPRINT.md")
TARGET_JSON = os.path.join(VAULT_ROOT, "and_os/etc/obsidian_blueprint.json")

# The key plugins and their business role in the ANDREY OS system
PLUGIN_ROLES = {
    "remotely-save": "Synchronization via WebDAV (Mail.ru Cloud), the fault tolerance, the 1GB file limit",
    "dataview": "DQL/JS queries to the metadata, the task tracking and the dynamic tables",
    "make-md": "Spaces, Folder Notes, the contextual catalogs management",
    "obsidian-tasks-plugin": "The global tracking of the tasks, the deadlines, the tags and the priorities",
    "task-gantt": "The Gantt chart visualization for the studio projects (Studio / Ta-Bu / Mars)",
    "cmdr": "The custom hotkeys, the custom macros and the toolbars",
    "obsidian-kanban": "The kanban boards for the sprints and the production phases",
    "obsidian-excalidraw-plugin": "The interactive architecture schemes, the sketches and the mockups",
    "advanced-canvas": "The extended infinite canvases for the plots decomposition and the mindmaps",
    "calendar": "The calendar view and the binding of the daily/weekly notes",
    "obsidian-full-calendar": "The full-screen calendar of the meetings and the deadlines",
    "obsidian-day-planner": "The hour-by-hour planning of the working day",
    "obsidian-tracker": "The tracker of the habits, the health and the sport metrics",
    "templater-obsidian": "The templater with the scripts execution on the notes creation",
    "sheet-plus": "The interactive tables and the formulas inside the notes",
    "table-editor-obsidian": "The advanced Markdown tables editor (Advanced Tables)",
    "data-files-editor": "The editing of the JSON, YAML and CSV files right inside the interface",
    "code-styler": "The syntax highlighting, the line numbers and the code blocks formatting",
    "obsidian-icon-folder": "The icons and the emojis on the folders and the notes (Iconize)",
    "editing-toolbar": "The visual floating text formatting panel",
    "obsidian-minimal-settings": "The fine tuning of the Minimal theme",
    "obsidian-style-settings": "The global tuning of the CSS variables and the typography",
    "obsidian-languagetool-plugin": "The spelling and the grammar check via LanguageTool",
    "obsidian-image-toolkit": "The image scaling and the preview tools",
    "automatic-table-of-contents": "The automatic generation of the tables of contents (TOC)",
    "url-into-selection": "The fast insertion of the hyperlinks over the selected text",
    "obsidian-auto-link-title": "The auto fetching of the web pages titles on the links insertion",
    "obsidian-outliner": "The lists behavior as in Workflowy / Roam Research",
    "pdf-plus": "The advanced annotation and the citation of the PDF documents",
    "jotbird": "The fast sharing and the export of the notes via JotBird",
    "markwhen": "The timelines from the Markwhen text format",
    "obsidian-checklist-plugin": "The side panel of the aggregation of all the vault checkboxes",
    "obsidian-enhancing-mindmap": "The mindmaps based on the Mindmap",
    "vscode-editor": "The embedded Monaco / VS Code editor for the code and the scripts",
    "opencode-obsidian": "The integration with the local OpenCode AI agents",
    "obsidian-opencode": "The integration with the local OpenCode AI agents"
}

def load_json(path):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError):
            # Corrupt or unreadable config: degrade to an empty mapping instead of crashing
            return {}
    return {}

def should_update(force=False):
    if force or not os.path.exists(TARGET_MD):
        return True
    
    # Check of the update age (once a month = 30 days)
    mtime = os.path.getmtime(TARGET_MD)
    last_update = datetime.fromtimestamp(mtime)
    if datetime.now() - last_update > timedelta(days=30):
        return True
    return False

def generate_blueprint():
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # 1. Collection of the base Obsidian settings
    app_cfg = load_json(os.path.join(OBSIDIAN_DIR, "app.json"))
    appearance_cfg = load_json(os.path.join(OBSIDIAN_DIR, "appearance.json"))
    core_plugins = load_json(os.path.join(OBSIDIAN_DIR, "core-plugins.json"))
    comm_plugins = load_json(os.path.join(OBSIDIAN_DIR, "community-plugins.json"))
    
    # 2. Scanning of the plugins folders
    plugins_dir = os.path.join(OBSIDIAN_DIR, "plugins")
    installed_plugins = []
    
    if os.path.exists(plugins_dir):
        for item in sorted(os.listdir(plugins_dir)):
            p_dir = os.path.join(plugins_dir, item)
            if not os.path.isdir(p_dir) or item.startswith('.'):
                continue
            
            m_path = os.path.join(p_dir, "manifest.json")
            manifest = load_json(m_path)
            
            data_json_path = os.path.join(p_dir, "data.json")
            has_custom_data = os.path.exists(data_json_path)
            
            installed_plugins.append({
                "id": item,
                "name": manifest.get("name", item),
                "version": manifest.get("version", "unknown"),
                "description": manifest.get("description", ""),
                "author": manifest.get("author", ""),
                "enabled": item in comm_plugins,
                "has_config": has_custom_data,
                "role": PLUGIN_ROLES.get(item, "The interface and the functionality extension")
            })

    # 3. The structure of the vault catalogs
    vault_folders = [
        {"path": "Nero/", "role": "The central brain of the system, the AI core, the skills (54), the scripts (64), the user context"},
        {"path": "Clippings/", "role": "The knowledge base, the books notes, the management frameworks, the Quick Knowledge DB"},
        {"path": "Tasks/", "role": "The operational management, the sprints, the tasks tracking and the project backlogs"},
        {"path": "Product/", "role": "The product development, the specifications, the services architecture"},
        {"path": "Story/", "role": "The screenplay development, the characters, the synopses, the loglines"},
        {"path": "CG_core/", "role": "The computer graphics knowledge base, the articles, the pipeline standards"},
        {"path": "Ta-Bu/", "role": "The projects, the commercial pipelines and the clients of the Ta-Bu studio"},
        {"path": "Studio/", "role": "The production projects of the Studio animation studio"},
        {"path": "Industry/", "role": "The industry analysis, the studios, the vendors, the CG and animation market"},
        {"path": "Book/", "role": "The book projects and the authored materials"},
        {"path": "Resource/", "role": "The media assets, the templates, the attachments and the graphic materials"}
    ]

    # The Markdown generation
    md = []
    md.append("---")
    md.append("tags:")
    md.append("  - nero")
    md.append("  - system")
    md.append("  - architecture")
    md.append("  - obsidian")
    md.append("  - blueprint")
    md.append("sticker: lucide//layers")
    md.append("color: var(--mk-color-purple)")
    md.append(f"updated: {datetime.now().strftime('%Y-%m-%d')}")
    md.append("---")
    md.append("")
    md.append("# 🏛️ OBSIDIAN_STRUCTURE_BLUEPRINT — The Reference Passport of the Architecture and the Plugins")
    md.append("")
    md.append("> 💡 **TL;DR:** The single reference passport of the full structure of the Obsidian Vault of System Architect (AnD os v1.0.0). "
              "Contains the 100% specification of the catalogs, the base settings, the core and the 35 community plugins with their role and the configuration. "
              "Allows any LLM on any new computer to recreate the exact copy of the working environment instantly.")
    md.append(f"> 📅 **Generation / update date:** `{now_str}`  ")
    md.append("> 🔄 **Update regime:** Automatically once in 30 days at the session initialization (`sys_cli.py sync/audit`).  ")
    md.append("> 🔗 **Cross-links:** [[SYSTEM|SYSTEM.md]] | [[system.json]] | [[and_os/etc/SYSTEM_MAP|SYSTEM_MAP.md]]")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 🗺️ 1. The Architectural Contour of the Vault (Vault Folder Topology)")
    md.append("")
    md.append("The vault is organized by the **Semantic Zoning** principle:")
    md.append("")
    md.append("| Catalog | The Purpose and the Contour | The Role for the AI Agent |")
    md.append("| :--- | :--- | :--- |")
    for fld in vault_folders:
        md.append(f"| `{fld['path']}` | {fld['role']} | Read / Reference |" if fld['path'] != "Nero/" else f"| `{fld['path']}` | {fld['role']} | **Primary Storage (Rule #7)** |")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## ⚙️ 2. The Base Obsidian Settings (Core Engine Config)")
    md.append("")
    md.append("```json")
    core_summary = {
        "app": app_cfg,
        "appearance": appearance_cfg,
        "active_core_plugins": [k for k, v in core_plugins.items() if v]
    }
    md.append(json.dumps(core_summary, indent=2, ensure_ascii=False))
    md.append("```")
    md.append("")
    md.append("- **Theme:** `AnuPpuccin` (dark mode, the accent color `#b900ff`).")
    md.append("- **Links behavior:** `alwaysUpdateLinks: true` (the auto updating of the links on the renaming).")
    md.append("- **Attachments:** `./` (the saving of the attachments next to the current note).")
    md.append("")
    md.append("---")
    md.append("")
    md.append(f"## 🧩 3. The Community Plugins Registry ({len(installed_plugins)} plugins)")
    md.append("")
    md.append("| Plugin ID | Name | Version | Status | The Role in the ANDREY OS System |")
    md.append("| :--- | :--- | :---: | :---: | :--- |")
    for p in installed_plugins:
        status_icon = "🟢 Enabled" if p["enabled"] else "⚪ Disabled"
        md.append(f"| `{p['id']}` | **{p['name']}** | `v{p['version']}` | {status_icon} | {p['role']} |")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 🔒 4. The Critical Settings of the Key Plugins")
    md.append("")
    md.append("### 1. Remotely Save (`remotely-save`) — The WebDAV Synchronization Protection")
    md.append("- **Method:** WebDAV (Mail.ru Cloud).")
    md.append("- **File size limit (`skipSizeLargerThan`):** `1 000 000 000` bytes (1 GB) — prevents the 505 failures on the synchronization of the big files.")
    md.append("- **Concurrency (`concurrency`):** `2` parallel threads (the protection from the socket breaks).")
    md.append("- **Ignored paths (`ignorePaths`):** `['.trash', '.git', '.smart-env', '.opencode', '__pycache__', 'and_os/opt/apps', 'and_os/var', 'and_os/lib/skills/openmontage-builder/repo']`.")
    md.append("")
    md.append("### 2. Make.md (`make-md`) — The Spaces Organization")
    md.append("- **Folder Notes:** Enabled, bound to the catalogs.")
    md.append("- **Spaces:** The isolated navigation without the pollution of the notes tree with the phantom MDB.")
    md.append("")
    md.append("### 3. Dataview (`dataview`) — The Data Queries")
    md.append("- **JavaScript Queries:** Enabled (`enableDataviewJs: true`).")
    md.append("- **Inline JS:** Enabled.")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 🚀 5. The Instruction for the AI: How to Deploy This Environment on a New PC")
    md.append("")
    md.append("If you are an agent working on a clean machine, perform the following steps:")
    md.append("1. **The Obsidian installation:** Download and install the application from the official site (`obsidian.md`).")
    md.append("2. **The vault cloning / copying:** Unpack the contents of the Vault into the target folder.")
    md.append("3. **The `.obsidian` catalog:**")
    md.append("   - Copy the configuration files `app.json`, `appearance.json`, `community-plugins.json`, `core-plugins.json`.")
    md.append("   - Make sure that the list in `community-plugins.json` is enabled.")
    md.append("4. **The plugins installation:** For each plugin from the registry, copy the folder into `.obsidian/plugins/<id>/` (the files `manifest.json`, `main.js`, `styles.css`, `data.json`).")
    md.append("5. **The skills symlinks:** Launch the system linking:")
    md.append("   ```bash")
    md.append("   python3 and_os/bin/sys_cli.py sync --fix")
    md.append("   ```")
    md.append("6. **The integrity check:** Launch the 13-vector check:")
    md.append("   ```bash")
    md.append("   python3 and_os/bin/sys_cli.py audit")
    md.append("   ```")
    md.append("")
    md.append("---")
    md.append("[[SYSTEM|← Master Manifest]] | [[and_os/etc/SYSTEM_MAP|← The Master Atlas]] | [[REGISTRY|← The Skills Registry]]")
    
    content = "\n".join(md) + "\n"
    
    os.makedirs(os.path.dirname(TARGET_MD), exist_ok=True)
    with open(TARGET_MD, "w", encoding="utf-8") as f:
        f.write(content)
        
    # Saving of the machine-readable version
    blueprint_json = {
        "updated": now_str,
        "vault_folders": vault_folders,
        "core_config": core_summary,
        "plugins": installed_plugins
    }
    with open(TARGET_JSON, "w", encoding="utf-8") as f:
        json.dump(blueprint_json, f, indent=2, ensure_ascii=False)
        
    return {
        "status": "ok",
        "target_md": TARGET_MD,
        "target_json": TARGET_JSON,
        "plugins_count": len(installed_plugins),
        "updated": now_str
    }

if __name__ == "__main__":
    force_run = "--force" in sys.argv
    if should_update(force=force_run):
        res = generate_blueprint()
        print(f"✅ Obsidian Blueprint generated/updated successfully: {res['target_md']} ({res['plugins_count']} plugins)")
    else:
        print("ℹ️ Obsidian Blueprint is actual (the update is required no more often than once in 30 days). Use --force for the forced update.")
