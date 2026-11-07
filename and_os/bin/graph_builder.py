#!/usr/bin/env python3
"""
graph_builder.py — Движок генерации и оркестрации графов задач (Execution DAG).
Часть стандарта Task Execution Graph (Правило №20).

Генерирует:
1. Mermaid-диаграммы для вставки в Markdown-заметки (с подграфами, скиллами, скриптами).
2. Obsidian Canvas (.canvas) с автоматическим расчётом пространственных координат (Swimlanes / Groups).
3. Валидирует граф на ацикличность (DAG) и целостность зависимостей.

Использование:
  python3 graph_builder.py --test --mermaid
  python3 graph_builder.py --test --canvas "output.canvas"
  python3 graph_builder.py --file input_dag.json --mermaid
  python3 graph_builder.py --file input_dag.json --canvas output.canvas
"""

import argparse
import json
import os
import sys
from collections import defaultdict, deque
from typing import Any, Dict, List, Optional, Set, Tuple


# ==============================================================================
# Цветовая палитра Obsidian Canvas
# ==============================================================================
# 1 = Red, 2 = Orange, 3 = Yellow, 4 = Green, 5 = Blue, 6 = Purple
COLOR_MAP = {
    "red": "1",
    "orange": "2",
    "yellow": "3",
    "green": "4",
    "blue": "5",
    "purple": "6",
    "default": "5",
}

SKILL_COLOR_MAP = {
    "ftrack-sync": "5",
    "weeek-hub": "3",
    "document-hub": "4",
    "story-dev": "6",
    "status-report": "1",
    "employee-hub": "2",
    "budget-calculator": "3",
    "cg-article": "6",
    "investor-outreach": "2",
    "clipping-finder": "4",
    "ai-rule": "5",
    "comfyui": "5",
    "system-audit": "1",
    "sync-context": "4",
    "vault-router": "5",
}


# ==============================================================================
# Валидация DAG и Circuit Breaker
# ==============================================================================
def validate_dag(nodes: List[Dict[str, Any]], check_circuit_breaker: bool = False) -> Tuple[bool, List[str]]:
    """Проверяет граф на существование узлов, целостность зависимостей, ацикличность и лимит Circuit Breaker."""
    errors = []
    node_ids = set()

    for node in nodes:
        nid = node.get("id")
        if not nid:
            errors.append("Обнаружен узел без обязательного поля 'id'")
            continue
        if nid in node_ids:
            errors.append(f"Дублирующийся идентификатор узла: '{nid}'")
        node_ids.add(nid)

        # Проверка правила Circuit Breaker (максимум 3 итерации для циклов самопроверки)
        mode = str(node.get("mode", "")).lower()
        pattern = str(node.get("pattern", "")).lower()
        if check_circuit_breaker or mode in ("loop", "evaluator-optimizer", "retry") or pattern in ("loop", "evaluator-optimizer"):
            if mode in ("loop", "evaluator-optimizer", "retry") or pattern in ("loop", "evaluator-optimizer"):
                max_iter = node.get("max_iterations")
                if max_iter is None:
                    errors.append(f"Узел '{nid}' использует паттерн 'Loop' (Evaluator-Optimizer), но отсутствует поле 'max_iterations'. Требуется max_iterations <= 3 (Circuit Breaker Rule №20).")
                elif not isinstance(max_iter, int) or max_iter > 3:
                    errors.append(f"Узел '{nid}' задает max_iterations={max_iter}, что превышает лимит Circuit Breaker (максимум 3 итерации перед остановкой и эскалацией человеку).")

    # Проверка ссылок
    adj = defaultdict(list)
    in_degree = defaultdict(int)
    for nid in node_ids:
        in_degree[nid] = 0

    for node in nodes:
        nid = node.get("id")
        deps = node.get("depends_on", [])
        for dep in deps:
            if dep not in node_ids:
                errors.append(f"Узел '{nid}' ссылается на несуществующую зависимость '{dep}'")
            else:
                adj[dep].append(nid)
                in_degree[nid] += 1

    if errors:
        return False, errors

    # Проверка на циклы через алгоритм Кана (Топологическая сортировка)
    queue = deque([nid for nid in node_ids if in_degree[nid] == 0])
    visited_count = 0

    while queue:
        curr = queue.popleft()
        visited_count += 1
        for neighbor in adj[curr]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if visited_count != len(node_ids):
        errors.append("В графе обнаружен цикл! Задача должна быть направленным ациклическим графом (DAG).")
        return False, errors

    return True, []


# ==============================================================================
# Расчет критического пути (Critical Path Method / CPM)
# ==============================================================================
def calculate_critical_path(nodes: List[Dict[str, Any]]) -> Tuple[List[str], Set[Tuple[str, str]], int]:
    """Рассчитывает самый длинный путь (критический путь) в графе DAG."""
    node_map = {n["id"]: n for n in nodes}
    durations = {n["id"]: int(n.get("duration", 1)) for n in nodes}

    adj = defaultdict(list)
    in_degree = defaultdict(int)
    for nid in node_map:
        in_degree[nid] = 0

    for n in nodes:
        nid = n["id"]
        for dep in n.get("depends_on", []):
            if dep in node_map:
                adj[dep].append(nid)
                in_degree[nid] += 1

    # Топологическая сортировка
    queue = deque([nid for nid, deg in in_degree.items() if deg == 0])
    topo_order = []
    while queue:
        curr = queue.popleft()
        topo_order.append(curr)
        for neighbor in adj[curr]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    # Динамическое программирование для поиска длиннейшего пути
    dist = {nid: durations[nid] for nid in node_map}
    parent = {nid: None for nid in node_map}

    for u in topo_order:
        for v in adj[u]:
            weight = dist[u] + durations[v]
            if weight > dist[v]:
                dist[v] = weight
                parent[v] = u

    if not dist:
        return [], set(), 0

    end_node = max(dist, key=dist.get)
    max_weight = dist[end_node]

    # Восстановление пути
    path = []
    curr = end_node
    while curr is not None:
        path.append(curr)
        curr = parent[curr]
    path.reverse()

    edge_pairs = set()
    for i in range(len(path) - 1):
        edge_pairs.add((path[i], path[i + 1]))

    return path, edge_pairs, max_weight



# ==============================================================================
# Генератор Mermaid
# ==============================================================================
def generate_mermaid(dag: Dict[str, Any], direction: str = "TD",
                     show_critical_path: bool = False) -> str:
    """Генерирует чистый блок Mermaid с группировкой по фазам и опциональной подсветкой CPM."""
    title = dag.get("title", "Execution Graph")
    nodes = dag.get("nodes", [])

    # Расчет критического пути если запрошен
    critical_nodes: Set[str] = set()
    critical_edges: Set[Tuple[str, str]] = set()
    if show_critical_path and nodes:
        cp_path, critical_edges, cp_weight = calculate_critical_path(nodes)
        critical_nodes = set(cp_path)

    lines = [
        "```mermaid",
        f"flowchart {direction}",
        f"    %% {title}",
    ]
    if show_critical_path and critical_nodes:
        lines.append(f"    %% ⚡ Critical Path (вес={cp_weight}): {' → '.join(critical_nodes)}")

    lines += [
        "    classDef skillNode fill:#2d3748,stroke:#4a5568,stroke-width:2px,color:#fff,rx:6px,ry:6px;",
        "    classDef gateNode fill:#2c5282,stroke:#3182ce,stroke-width:2px,color:#fff,rx:10px,ry:10px;",
        "    classDef parallelNode fill:#234e52,stroke:#319795,stroke-width:2px,color:#fff,rx:6px,ry:6px;",
        "    classDef criticalNode fill:#742a2a,stroke:#e53e3e,stroke-width:3px,color:#fff,rx:6px,ry:6px;",
        "    classDef statusWorking fill:#744210,stroke:#d69e2e,stroke-width:2px,color:#fff,rx:6px,ry:6px;",
        "    classDef statusBlocked fill:#742a2a,stroke:#e53e3e,stroke-width:2px,color:#fff,rx:6px,ry:6px;",
        "    classDef statusDone fill:#1c4532,stroke:#38a169,stroke-width:2px,color:#fff,rx:6px,ry:6px;",
    ]

    # Группировка узлов по фазам
    phases = defaultdict(list)
    for node in nodes:
        phase = node.get("phase", "Общие шаги")
        phases[phase].append(node)

    phase_counter = 1
    for phase_name, p_nodes in phases.items():
        phase_id = f"phase_{phase_counter}"
        phase_counter += 1
        lines.append(f'\n    subgraph {phase_id} ["{phase_name}"]')

        for node in p_nodes:
            nid = node["id"]
            ntitle = node.get("title", nid).replace('"', "'")
            skill = node.get("skill", "")
            script = node.get("script", "")
            src_ref = node.get("src", "") or node.get("src_ref", "")
            dod = node.get("dod", "").replace('"', "'")
            status = str(node.get("status", "")).lower()

            status_icon = ""
            if status == "working":
                status_icon = " 🟡 [В РАБОТЕ]"
            elif status in ("blocked", "error"):
                status_icon = " 🔴 [ЗАБЛОКИРОВАН]"
            elif status in ("done", "completed", "success"):
                status_icon = " 🟢 [ГОТОВО]"

            label_parts = [f"<b>{ntitle}{status_icon}</b>"]
            if skill:
                label_parts.append(f"🎯 <b>{skill}</b>")
            if script:
                label_parts.append(f"⚙️ <code>{script}</code>")
            if src_ref:
                label_parts.append(f"🔍 <i>{src_ref}</i>")
            if dod:
                label_parts.append(f"✅ <i>{dod}</i>")

            label = "<br/>".join(label_parts)
            lines.append(f'        {nid}["{label}"]')

        lines.append("    end")

    # Добавление связей с подсветкой критических рёбер
    lines.append("\n    %% Зависимости (Edges)")
    all_edges = []
    edge_added = False
    for node in nodes:
        nid = node["id"]
        deps = node.get("depends_on", [])
        for dep in deps:
            all_edges.append((dep, nid))
            lines.append(f"    {dep} --> {nid}")
            edge_added = True

    if not edge_added and len(nodes) > 1:
        for i in range(len(nodes) - 1):
            all_edges.append((nodes[i]["id"], nodes[i+1]["id"]))
            lines.append(f"    {nodes[i]['id']} --> {nodes[i+1]['id']}")

    # Применение стилей статусов узлов
    lines.append("\n    %% Стили статусов задач (Agent Status Awareness)")
    for node in nodes:
        nid = node["id"]
        status = str(node.get("status", "")).lower()
        if status == "working":
            lines.append(f"    class {nid} statusWorking;")
        elif status in ("blocked", "error"):
            lines.append(f"    class {nid} statusBlocked;")
        elif status in ("done", "completed", "success"):
            lines.append(f"    class {nid} statusDone;")

    # Применение стилей критического пути
    if show_critical_path and critical_nodes:
        lines.append("\n    %% Подсветка критического пути")
        for nid in critical_nodes:
            lines.append(f"    class {nid} criticalNode;")
        for idx, (src, dst) in enumerate(all_edges):
            if (src, dst) in critical_edges:
                lines.append(f"    linkStyle {idx} stroke:#e53e3e,stroke-width:3px;")

    lines.append("```\n")
    return "\n".join(lines)


# ==============================================================================
# Генератор Obsidian Canvas (.canvas)
# ==============================================================================
def generate_canvas(dag: Dict[str, Any], layout: str = "horizontal",
                    show_critical_path: bool = False) -> Dict[str, Any]:
    """Генерирует структуру Obsidian Canvas JSON с автоматическим расчётом сетки и групп."""
    nodes = dag.get("nodes", [])

    # Расчет критического пути если запрошен
    critical_nodes_set: Set[str] = set()
    critical_edges_set: Set[Tuple[str, str]] = set()
    if show_critical_path and nodes:
        cp_path, critical_edges_set, _ = calculate_critical_path(nodes)
        critical_nodes_set = set(cp_path)
    title = dag.get("title", "Task Execution Graph")

    # Группировка по фазам
    phases = defaultdict(list)
    for node in nodes:
        phase = node.get("phase", "Этап")
        phases[phase].append(node)

    canvas_nodes = []
    canvas_edges = []

    # Геометрия карточек
    CARD_WIDTH = 380
    CARD_HEIGHT = 180
    GAP_X = 140
    GAP_Y = 80
    GROUP_PADDING = 50

    curr_x = 0
    node_positions = {}

    group_idx = 1
    for phase_name, p_nodes in phases.items():
        # Сортировка узлов внутри фазы: параллельные дорожки
        n_count = len(p_nodes)
        phase_width = CARD_WIDTH + (GROUP_PADDING * 2)
        phase_height = (n_count * CARD_HEIGHT) + ((n_count - 1) * GAP_Y) + (GROUP_PADDING * 2) + 40

        group_id = f"grp_{group_idx}"
        group_idx += 1
        group_y = 0

        # Размещение группы
        canvas_nodes.append({
            "id": group_id,
            "type": "group",
            "x": curr_x,
            "y": group_y,
            "width": phase_width,
            "height": phase_height,
            "label": phase_name,
            "color": str((group_idx % 6) + 1),
        })

        # Размещение карточек внутри группы
        card_x = curr_x + GROUP_PADDING
        card_y = group_y + GROUP_PADDING + 30

        for node in p_nodes:
            nid = node["id"]
            ntitle = node.get("title", nid)
            skill = node.get("skill", "")
            script = node.get("script", "")
            src_ref = node.get("src", "") or node.get("src_ref", "")
            inputs = node.get("inputs", [])
            outputs = node.get("outputs", [])
            dod = node.get("dod", "")
            mode = node.get("mode", "Sequential")
            file_link = node.get("file_link", "")

            # Формирование текста карточки
            lines = [f"### {ntitle}"]
            if skill:
                lines.append(f"**🎯 Скилл:** `{skill}`")
            if script:
                lines.append(f"**⚙️ Скрипт:** `{script}`")
            if src_ref:
                lines.append(f"**🔍 Source Evidence:** `{src_ref}`")
            if mode.lower() in ("parallel", "fork"):
                lines.append("🔀 **Режим:** Параллельный")
            if inputs:
                lines.append(f"📥 **Вход:** {', '.join(inputs)}")
            if outputs:
                lines.append(f"📤 **Выход:** {', '.join(outputs)}")
            if dod:
                lines.append(f"✅ **Критерий (DoD):** {dod}")

            text_content = "\n".join(lines)

            # Определение цвета (критический путь перекрывает базовый цвет)
            color = node.get("color") or SKILL_COLOR_MAP.get(skill, "5")
            if nid in critical_nodes_set:
                color = "1"  # 1 = Red (критический путь)

            node_def = {
                "id": nid,
                "type": "text",
                "text": text_content,
                "x": card_x,
                "y": card_y,
                "width": CARD_WIDTH,
                "height": CARD_HEIGHT,
                "color": color,
            }

            if file_link:
                # Если указана прямая заметка в vault
                node_def["type"] = "file"
                node_def["file"] = file_link
                del node_def["text"]

            canvas_nodes.append(node_def)
            node_positions[nid] = (card_x, card_y, CARD_WIDTH, CARD_HEIGHT)

            card_y += CARD_HEIGHT + GAP_Y

        curr_x += phase_width + GAP_X

    # Формирование связей (Edges) согласно JSON Canvas Spec 1.0
    import hashlib
    edge_counter = 1
    for node in nodes:
        nid = node["id"]
        deps = node.get("depends_on", [])
        for dep in deps:
            if dep in node_positions and nid in node_positions:
                # 16-символьный hex-идентификатор связи по стандарту JSON Canvas Spec 1.0
                raw_hash = hashlib.sha256(f"{title}_{dep}_{nid}_{edge_counter}".encode("utf-8")).hexdigest()
                edge_id = raw_hash[:16]
                edge_counter += 1
                edge_def: Dict[str, Any] = {
                    "id": edge_id,
                    "fromNode": dep,
                    "fromSide": "right",
                    "toNode": nid,
                    "toSide": "left",
                    "toEnd": "arrow",
                }
                if (dep, nid) in critical_edges_set:
                    edge_def["color"] = "1"   # красный (Preset 1)
                    edge_def["label"] = "⚡ Critical Path"
                canvas_edges.append(edge_def)

    return {
        "nodes": canvas_nodes,
        "edges": canvas_edges,
        "metadata": {
            "version": "1.0-1.0",
            "frontmatter": {
                "title": title,
                "orchestrator": "task-graph",
                "rules": "Правило №20",
            }
        }
    }


# ==============================================================================
# Пример тестового комплексного графа
# ==============================================================================
def get_test_dag() -> Dict[str, Any]:
    """Возвращает пример комплексной рабочей задачи с параллелизмом."""
    return {
        "title": "Производственный аудит и сдача эпизода E275 (Марс)",
        "nodes": [
            {
                "id": "step_1",
                "title": "1. Выгрузка сырых данных Ftrack",
                "phase": "Фаза 1: Сбор первичных данных",
                "skill": "ftrack-sync",
                "script": "ftrack_sync.py",
                "inputs": ["Ftrack API", "Episode E275"],
                "outputs": ["ftrack_e275_raw.json"],
                "dod": "Данные по 53 шотам и 31 задаче загружены без ошибок",
                "mode": "Sequential",
                "depends_on": [],
            },
            {
                "id": "step_2a",
                "title": "2A. Анализ выработки CFX/Анимации",
                "phase": "Фаза 2: Параллельный анализ",
                "skill": "ftrack-sync",
                "script": "ftrack_report.py",
                "inputs": ["ftrack_e275_raw.json"],
                "outputs": ["Выработка_E275.md"],
                "dod": "Посчитаны часы, переработки и дельта отставания",
                "mode": "Parallel",
                "depends_on": ["step_1"],
            },
            {
                "id": "step_2b",
                "title": "2B. Срез блокеров на доске Weeek",
                "phase": "Фаза 2: Параллельный анализ",
                "skill": "weeek-hub",
                "script": "weeek_sync.py",
                "inputs": ["Safari Live Sync", "Доска Марс #798"],
                "outputs": ["Weeek_Mars_Blockers.md"],
                "dod": "Выявлены все задачи со статусом Blocked и задержкой >30д",
                "mode": "Parallel",
                "depends_on": ["step_1"],
            },
            {
                "id": "step_2c",
                "title": "2C. Сверка состава артистов и ставок",
                "phase": "Фаза 2: Параллельный анализ",
                "skill": "employee-hub",
                "script": "doc_analyze.py",
                "inputs": ["МАРС_СОТРУДНИКИ.xlsx"],
                "outputs": ["Ресурсы_отдела_CFX.md"],
                "dod": "Подтверждена доступность лидов и супервайзеров на финализацию",
                "mode": "Parallel",
                "depends_on": ["step_1"],
            },
            {
                "id": "step_3",
                "title": "3. Консолидация статус-отчёта и рисков",
                "phase": "Фаза 3: Финализация и релиз",
                "skill": "status-report",
                "script": "validate_system.py",
                "inputs": ["Выработка_E275.md", "Weeek_Mars_Blockers.md", "Ресурсы_отдела_CFX.md"],
                "outputs": ["Статус_Марс_E275_Финал.md"],
                "dod": "Сформирован итоговый протокол с экшн-пойнтами и оценкой рисков",
                "mode": "Sequential",
                "depends_on": ["step_2a", "step_2b", "step_2c"],
            },
        ]
    }


def generate_vault_index_dag(vault_root: str = ".") -> Dict[str, Any]:
    """Генерирует граф зависимостей и связей подсистем ANDREY OS (Graphify Pattern)."""
    return {
        "title": "Карта связей и подсистем ANDREY OS (Graph Index)",
        "description": "Топологический граф: Манифесты -> Скиллы -> Скрипты -> Проекты -> Хранилище",
        "nodes": [
            {
                "id": "manifests",
                "title": "Манифесты и Правила (№0-22)",
                "phase": "Уровень 0: Архитектурное ядро",
                "skill": "system-audit",
                "script": "SYSTEM.md, rules.md, system.json, AGENTS.md",
                "inputs": ["Vault Root"],
                "outputs": ["Контекст сессии"],
                "dod": "Загружены правила Don't Load, Think in Code, DAG, Anti-Slop, Anti-Hallucination",
                "mode": "Sequential",
                "depends_on": [],
            },
            {
                "id": "router",
                "title": "Skill & Vault Routing",
                "phase": "Уровень 1: Маршрутизация",
                "skill": "skill-router",
                "script": "skill-router, vault-router, task-graph",
                "inputs": ["Запрос пользователя"],
                "outputs": ["Primary Skill + Режим работы + Execution DAG"],
                "dod": "Определена единая точка входа и целевой каталог Nero/",
                "mode": "Sequential",
                "depends_on": ["manifests"],
            },
            {
                "id": "production_hub",
                "title": "Продакшн и Команда (Марс, Кот, Studio)",
                "phase": "Уровень 2: Доменные кластеры",
                "skill": "ftrack-sync",
                "script": "ftrack_sync.py, mattermost_sync.py, weeek_sync.py",
                "inputs": ["Ftrack API", "Mattermost", "Weeek"],
                "outputs": ["Статусы шотов", "Follow-up встреч", "Сметы"],
                "dod": "Актуализированы производственные данные",
                "mode": "Parallel",
                "depends_on": ["router"],
            },
            {
                "id": "docs_hub",
                "title": "Универсальный нормализатор документов",
                "phase": "Уровень 2: Доменные кластеры",
                "skill": "document-hub",
                "script": "convert_doc.py (MarkItDown), doc_analyze.py, xl_analyze.py",
                "inputs": ["PDF", "XLSX", "DOCX", "PPTX", "Сканы"],
                "outputs": ["Чистый Markdown для LLM"],
                "dod": "Документ преобразован в Markdown с экономией 70% токенов",
                "mode": "Parallel",
                "depends_on": ["router"],
            },
            {
                "id": "ai_council",
                "title": "AI & Стратегический аудит (LLM Council)",
                "phase": "Уровень 2: Доменные кластеры",
                "skill": "llm-council",
                "script": "ai-rule, prompt-improver, llm-council",
                "inputs": ["Идеи", "Промпты", "Архитектурные решения"],
                "outputs": ["Критический вердикт", "Воркфлоу генерации"],
                "dod": "Проведено стресс-тестирование без подхалимства модели",
                "mode": "Parallel",
                "depends_on": ["router"],
            },
            {
                "id": "health_hub",
                "title": "Семейное здоровье и спорт (МЕДСИ, telemetry_sync, Ironman)",
                "phase": "Уровень 2: Доменные кластеры",
                "skill": "health-diagnostics-hub",
                "script": "telemetry_sync_sync.py, endurance-training-plan",
                "inputs": ["telemetry_sync Connect", "Бланки лабораторий", "МЕДСИ"],
                "outputs": ["health_diagnostics.md", "Тренировочный микроцикл"],
                "dod": "Соблюден медицинский шлюз и безопасность нагрузок",
                "mode": "Parallel",
                "depends_on": ["router"],
            },
            {
                "id": "memory_validation",
                "title": "Память, Валидация и Телеметрия",
                "phase": "Уровень 3: Замыкание контура",
                "skill": "knowledge-promoter",
                "script": "validate_system.py, sync_context.py, telemetry.md",
                "inputs": ["Результаты исполнения"],
                "outputs": ["decision-log", "telemetry.md", "34 CONTEXT.md"],
                "dod": "Система проверена на 100% целостность и знание сохранено в Nero/",
                "mode": "Sequential",
                "depends_on": ["production_hub", "docs_hub", "ai_council", "health_hub"],
            },
        ],
    }


# ==============================================================================
# Точка входа CLI
# ==============================================================================
def main():
    parser = argparse.ArgumentParser(description="Task Execution Graph Engine (Правило №20)")
    parser.add_argument("--file", "-f", help="Путь к JSON-файлу со структурой DAG")
    parser.add_argument("--test", action="store_true", help="Использовать тестовый эталонный граф задачи")
    parser.add_argument("--vault-index", action="store_true", help="Построить граф связей и подсистем ANDREY OS")
    parser.add_argument("--mermaid", action="store_true", help="Вывести Mermaid диаграмму в stdout")
    parser.add_argument("--canvas", help="Путь для сохранения файла Obsidian Canvas (.canvas)")
    parser.add_argument("--validate", action="store_true", help="Только проверить валидность DAG")
    parser.add_argument("--direction", default="TD", choices=["TD", "LR"], help="Ориентация Mermaid: TD или LR")
    parser.add_argument("--critical-path", action="store_true",
                        help="Рассчитать и подсветить критический путь (CPM, Правило №20)")
    parser.add_argument("--circuit-breaker", action="store_true",
                        help="Проверить наличие поля max_iterations <= 3 в Loop-узлах (Circuit Breaker, Правило №20)")

    args = parser.parse_args()

    dag_data = None
    if args.vault_index:
        dag_data = generate_vault_index_dag()
    elif args.test:
        dag_data = get_test_dag()
    elif args.file:
        if not os.path.exists(args.file):
            print(f"[ОШИБКА] Файл не найден: {args.file}", file=sys.stderr)
            sys.exit(1)
        with open(args.file, "r", encoding="utf-8") as f:
            dag_data = json.load(f)
    elif not sys.stdin.isatty():
        try:
            dag_data = json.load(sys.stdin)
        except Exception as e:
            print(f"[ОШИБКА] Не удалось прочитать JSON из stdin: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(0)

    nodes = dag_data.get("nodes", [])
    valid, errors = validate_dag(nodes, check_circuit_breaker=args.circuit_breaker)

    if not valid:
        print("[ОШИБКА ВАЛИДАЦИИ DAG]:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        sys.exit(2)

    if args.validate:
        print(f"✅ DAG '{dag_data.get('title', 'Без названия')}' успешно валидирован! Узлов: {len(nodes)}, циклов нет.")
        return

    # Показать критический путь в консоли
    show_cp = args.critical_path
    if show_cp and nodes:
        cp_path, _, cp_weight = calculate_critical_path(nodes)
        print(f"⚡ Критический путь (CPM, вес={cp_weight}): {' → '.join(cp_path)}\n")

    # Генерация Mermaid
    if args.mermaid or (not args.canvas and not args.validate):
        mermaid_code = generate_mermaid(dag_data, direction=args.direction,
                                        show_critical_path=show_cp)
        print(mermaid_code)

    # Генерация Canvas
    if args.canvas:
        canvas_dict = generate_canvas(dag_data, show_critical_path=show_cp)
        os.makedirs(os.path.dirname(os.path.abspath(args.canvas)), exist_ok=True)
        with open(args.canvas, "w", encoding="utf-8") as f:
            json.dump(canvas_dict, f, ensure_ascii=False, indent=2)
        print(f"✅ Canvas-файл успешно создан: {args.canvas} (узлов: {len(canvas_dict['nodes'])}, связей: {len(canvas_dict['edges'])})")


if __name__ == "__main__":
    main()
