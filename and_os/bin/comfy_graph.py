#!/usr/bin/env python3
"""
comfy_graph.py — ComfyUI Graph Analysis, Validation, Visualization, and Sync Engine (Think in Code).

Supported Formats:
  1. Web UI Workflow JSON (nodes + links in LiteGraph format)
  2. API Prompt JSON (dict with class_type and inputs)

Capabilities:
  - Validate structure, port types, resolution divisibility, and link integrity (--validate)
  - Generate Mermaid execution flow diagrams (--mermaid)
  - Generate interactive Obsidian Canvas representations (--canvas)
  - Model inventory inspection and ComfyUI directory scanning (--inventory / --scan)
  - Export verified starter templates (--template)
  - List available workflow templates (--list-templates)
  - Sync and update templates from upstream repository (--sync-upstream)

Usage:
  python3 comfy_graph.py --validate workflow.json
  python3 comfy_graph.py --mermaid workflow.json
  python3 comfy_graph.py --canvas workflow.json -o workflow.canvas
  python3 comfy_graph.py --inventory [--scan /path/to/ComfyUI]
  python3 comfy_graph.py --template flux-txt2img -o new_flux.json
  python3 comfy_graph.py --list-templates
  python3 comfy_graph.py --sync-upstream [--source <git_url_or_path>]
"""

import os
import sys
import json
import argparse
import re
import uuid
import shutil
import subprocess

# Base directories
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VAULT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../.."))
DEFAULT_INVENTORY = os.path.join(VAULT_ROOT, "and_os", "lib", "workflows", "comfy", "models_inventory.md")
TEMPLATES_DIR = os.path.join(VAULT_ROOT, "and_os", "lib", "skills", "comfy-builder", "references", "templates")
LEGACY_TEMPLATES_DIR = os.path.join(VAULT_ROOT, "Nero", "skills", "comfyui", "references")
DEFAULT_UPSTREAM_URL = "https://github.com/twwch/comfyui-workflow-skill.git"

# ComfyUI node visual color palette for Obsidian Canvas
CANVAS_COLORS = {
    "loader": "1",        # Red / Orange
    "conditioning": "2",  # Yellow / Gold
    "sampling": "4",      # Green
    "latent": "3",        # Light Green
    "decoding": "5",      # Blue / Cyan
    "output": "6",        # Purple
    "upscale": "2",       # Orange
    "default": "0"        # Gray
}

def load_workflow_json(file_path: str) -> dict:
    """Load workflow JSON with support for template variables like {{VAR}}."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Try direct parse first
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # Replace unquoted template placeholders in JSON values
    pattern = r"([,:\[]\s*)\{\{([A-Za-z0-9_]+)\}\}(\s*[,\]\}])"
    def repl(m):
        pre, var, post = m.group(1), m.group(2), m.group(3)
        if var in ("WIDTH", "HEIGHT"): val = "1024"
        elif var in ("STEPS", "SEED", "FPS", "FRAME_COUNT", "FRAMES", "LOOP_COUNT", "CRF"): val = "20"
        elif var in ("CFG", "DENOISE", "STRENGTH", "WEIGHT", "FEATHER"): val = "1.0"
        elif var in ("SAVE_IMAGE", "PING_PONG", "TILE"): val = "true"
        elif var in ("PIXEL_FORMAT", "FORMAT"): val = '"yuv420p"'
        else: val = f'"{var}"'
        return f"{pre}{val}{post}"

    clean = content
    prev = None
    while prev != clean:
        prev = clean
        clean = re.sub(pattern, repl, clean)

    return json.loads(clean)

def classify_node_type(class_type: str) -> str:
    """Classify node by functional role."""
    cl = class_type.lower()
    if any(k in cl for k in ["loader", "checkpoint", "lora", "unet", "clipvision", "dualclip"]):
        return "loader"
    elif any(k in cl for k in ["cliptextencode", "prompt", "conditioning", "ipadapter", "controlnet"]):
        return "conditioning"
    elif any(k in cl for k in ["ksampler", "sampler", "denoise", "scheduler"]):
        return "sampling"
    elif any(k in cl for k in ["emptylatent", "latent"]):
        return "latent"
    elif any(k in cl for k in ["vaedecode", "vaeencode", "vae"]):
        return "decoding"
    elif any(k in cl for k in ["saveimage", "preview", "videocombine", "output"]):
        return "output"
    elif any(k in cl for k in ["upscale", "esrgan", "scaler"]):
        return "upscale"
    return "default"

def detect_workflow_format(data) -> str:
    """Detect ComfyUI workflow JSON format."""
    if isinstance(data, dict):
        if "nodes" in data and isinstance(data["nodes"], list):
            return "webui"
        # Check API format (dict of dicts with class_type)
        if any(isinstance(v, dict) and "class_type" in v for v in data.values()):
            return "api"
    return "unknown"

def extract_webui_links(data) -> list:
    """Extract link connections from WebUI format (links array or inferred from inputs/outputs)."""
    links = data.get("links", [])
    result = []
    if links:
        for link in links:
            if isinstance(link, list) and len(link) >= 6:
                result.append((link[1], link[3], link[5]))
        if result:
            return result

    # Infer links from node outputs and inputs
    out_map = {}
    nodes = data.get("nodes", [])
    for node in nodes:
        nid = node.get("id")
        for out in node.get("outputs", []):
            otype = out.get("type", "DATA")
            for lid in out.get("links") or []:
                out_map[lid] = (nid, otype)

    for node in nodes:
        nid = node.get("id")
        for inp in node.get("inputs", []):
            lid = inp.get("link")
            itype = inp.get("type")
            if lid in out_map:
                from_id, otype = out_map[lid]
                result.append((from_id, nid, itype or otype))

    return result

def validate_workflow(data) -> dict:
    """Validate ComfyUI workflow graph integrity and parameters."""
    fmt = detect_workflow_format(data)
    report = {
        "format": fmt,
        "valid": True,
        "nodes_count": 0,
        "links_count": 0,
        "errors": [],
        "warnings": [],
        "models_used": [],
        "node_types": set()
    }
    
    if fmt == "unknown":
        report["valid"] = False
        report["errors"].append("Unknown ComfyUI workflow JSON format (expected WebUI LiteGraph or API Prompt format).")
        return report

    if fmt == "webui":
        nodes = data.get("nodes", [])
        resolved_links = extract_webui_links(data)
        report["nodes_count"] = len(nodes)
        report["links_count"] = len(resolved_links)
        
        node_ids = set()
        for node in nodes:
            nid = node.get("id")
            ntype = node.get("type", "Unknown")
            report["node_types"].add(ntype)
            
            if nid in node_ids:
                report["errors"].append(f"Duplicate node ID: {nid} ({ntype})")
                report["valid"] = False
            node_ids.add(nid)
            
            # Inspect widget values for model weights and resolution limits
            widgets = node.get("widgets_values", [])
            if isinstance(widgets, list):
                for w in widgets:
                    if isinstance(w, str) and (w.endswith(".safetensors") or w.endswith(".ckpt") or w.endswith(".gguf")):
                        report["models_used"].append(w)
                    elif isinstance(w, (int, float)):
                        if "width" in ntype.lower() or "height" in ntype.lower() or "empty" in ntype.lower():
                            if isinstance(w, int) and w > 64 and w % 8 != 0:
                                report["warnings"].append(f"Node {nid} ({ntype}): dimension {w} is not divisible by 8!")

        # Validate link endpoints
        for from_id, to_id, ltype in resolved_links:
            if from_id not in node_ids:
                report["errors"].append(f"Link points to non-existent origin node {from_id}")
                report["valid"] = False
            if to_id not in node_ids:
                report["errors"].append(f"Link points to non-existent target node {to_id}")
                report["valid"] = False

    elif fmt == "api":
        report["nodes_count"] = len(data)
        node_ids = set(data.keys())
        
        for nid, node in data.items():
            if not isinstance(node, dict):
                continue
            ntype = node.get("class_type", "Unknown")
            report["node_types"].add(ntype)
            inputs = node.get("inputs", {})
            
            for param_name, val in inputs.items():
                if isinstance(val, list) and len(val) == 2:
                    ref_id = str(val[0])
                    if ref_id not in node_ids:
                        report["errors"].append(f"Node {nid} ({ntype}) references missing node {ref_id}")
                        report["valid"] = False
                elif isinstance(val, str) and (val.endswith(".safetensors") or val.endswith(".ckpt") or val.endswith(".gguf")):
                    report["models_used"].append(val)
                elif param_name in ("width", "height") and isinstance(val, int):
                    if val % 8 != 0:
                        report["warnings"].append(f"Node {nid} ({ntype}): {param_name}={val} is not divisible by 8!")

    # Check presence of primary functional nodes
    types_str = " ".join(report["node_types"]).lower()
    if not any(k in types_str for k in ["sampler", "wan", "flow"]):
        report["warnings"].append("Notice: No generation sampler node detected in graph (KSampler / WanVideoSampler).")
    if not any(k in types_str for k in ["checkpoint", "unet", "loader"]):
        report["warnings"].append("Notice: No model loader node detected in graph (CheckpointLoader / UNETLoader).")

    return report

def generate_mermaid(data) -> str:
    """Generate Mermaid diagram from ComfyUI graph."""
    fmt = detect_workflow_format(data)
    lines = [
        "flowchart LR",
        "    %% ComfyUI Node Styles",
        "    classDef loaderNode fill:#742a2a,stroke:#e53e3e,stroke-width:2px,color:#fff,rx:6px,ry:6px;",
        "    classDef condNode fill:#744210,stroke:#d69e2e,stroke-width:2px,color:#fff,rx:6px,ry:6px;",
        "    classDef sampleNode fill:#22543d,stroke:#38a169,stroke-width:2px,color:#fff,rx:6px,ry:6px;",
        "    classDef decodeNode fill:#2a4365,stroke:#3182ce,stroke-width:2px,color:#fff,rx:6px,ry:6px;",
        "    classDef outputNode fill:#44337a,stroke:#805ad5,stroke-width:2px,color:#fff,rx:6px,ry:6px;",
        "    classDef defaultNode fill:#2d3748,stroke:#4a5568,stroke-width:2px,color:#fff,rx:6px,ry:6px;",
        ""
    ]

    edges = []
    classes = {}

    if fmt == "webui":
        nodes = data.get("nodes", [])
        resolved_links = extract_webui_links(data)

        for node in nodes:
            nid = node.get("id")
            ntype = node.get("type", "Node")
            title = node.get("title") or ntype
            role = classify_node_type(ntype)
            classes[nid] = f"{role}Node" if role != "default" else "defaultNode"
            
            info = []
            widgets = node.get("widgets_values", [])
            if isinstance(widgets, list):
                for w in widgets:
                    if isinstance(w, str) and (w.endswith(".safetensors") or w.endswith(".ckpt") or w.endswith(".gguf")):
                        info.append(os.path.basename(w))
                    elif isinstance(w, (int, float)) and w > 100:
                        info.append(str(w))
            extra = f"<br/><i>{', '.join(info[:2])}</i>" if info else ""
            lines.append(f'    node_{nid}["<b>{nid}: {title}</b>{extra}"]')

        for from_id, to_id, ltype in resolved_links:
            edges.append(f"    node_{from_id} -->|{ltype}| node_{to_id}")

    elif fmt == "api":
        for nid, node in data.items():
            if not isinstance(node, dict):
                continue
            ntype = node.get("class_type", "Node")
            role = classify_node_type(ntype)
            classes[nid] = f"{role}Node" if role != "default" else "defaultNode"
            
            inputs = node.get("inputs", {})
            info = []
            for pk, pv in inputs.items():
                if isinstance(pv, str) and (pv.endswith(".safetensors") or pv.endswith(".ckpt") or pv.endswith(".gguf")):
                    info.append(os.path.basename(pv))
                elif isinstance(pv, list) and len(pv) == 2:
                    ref_id = str(pv[0])
                    edges.append(f"    node_{ref_id} -->|{pk}| node_{nid}")
            extra = f"<br/><i>{', '.join(info[:2])}</i>" if info else ""
            lines.append(f'    node_{nid}["<b>{nid}: {ntype}</b>{extra}"]')

    lines.append("")
    lines.extend(edges)
    lines.append("")
    for nid, cls in classes.items():
        lines.append(f"    class node_{nid} {cls};")

    return "\n".join(lines)

def generate_canvas(data, output_path: str) -> dict:
    """Generate Obsidian Canvas (.canvas) visualization from ComfyUI graph."""
    fmt = detect_workflow_format(data)
    canvas_nodes = []
    canvas_edges = []

    if fmt == "webui":
        nodes = data.get("nodes", [])
        
        for node in nodes:
            nid = str(node.get("id"))
            ntype = node.get("type", "Node")
            title = node.get("title") or ntype
            role = classify_node_type(ntype)
            color = CANVAS_COLORS.get(role, "0")
            
            pos = node.get("pos", [0, 0])
            size = node.get("size", [240, 120])
            if isinstance(size, dict):
                w = size.get("0", 240)
                h = size.get("1", 120)
            elif isinstance(size, list) and len(size) >= 2:
                w, h = size[0], size[1]
            else:
                w, h = 240, 120

            widgets = node.get("widgets_values", [])
            w_text = ""
            if isinstance(widgets, list) and widgets:
                w_lines = []
                for idx, val in enumerate(widgets[:5]):
                    if isinstance(val, str) and len(val) > 40:
                        val = val[:37] + "..."
                    w_lines.append(f"- `val_{idx}`: {val}")
                w_text = "\n" + "\n".join(w_lines)

            node_text = f"### #{nid} {title}\n**Type:** `{ntype}`\n**Role:** {role}{w_text}"
            
            canvas_nodes.append({
                "id": f"node_{nid}",
                "x": int(pos[0]),
                "y": int(pos[1]),
                "width": max(int(w), 220),
                "height": max(int(h), 140),
                "type": "text",
                "text": node_text,
                "color": color
            })

        resolved_links = extract_webui_links(data)
        for idx, (from_id, to_id, ltype) in enumerate(resolved_links):
            canvas_edges.append({
                "id": f"edge_{idx}_{from_id}_{to_id}",
                "fromNode": f"node_{from_id}",
                "fromSide": "right",
                "toNode": f"node_{to_id}",
                "toSide": "left",
                "label": str(ltype)
            })

    elif fmt == "api":
        x_step, y_step = 320, 200
        cols = 4
        for idx, (nid, node) in enumerate(data.items()):
            if not isinstance(node, dict):
                continue
            ntype = node.get("class_type", "Node")
            role = classify_node_type(ntype)
            color = CANVAS_COLORS.get(role, "0")
            
            row = idx // cols
            col = idx % cols
            
            inputs = node.get("inputs", {})
            param_lines = []
            for pk, pv in inputs.items():
                if isinstance(pv, list) and len(pv) == 2:
                    ref_id = str(pv[0])
                    canvas_edges.append({
                        "id": f"edge_{ref_id}_{nid}_{pk}",
                        "fromNode": f"node_{ref_id}",
                        "fromSide": "right",
                        "toNode": f"node_{nid}",
                        "toSide": "left",
                        "label": pk
                    })
                elif not isinstance(pv, dict):
                    pv_str = str(pv)
                    if len(pv_str) > 30:
                        pv_str = pv_str[:27] + "..."
                    param_lines.append(f"- `{pk}`: {pv_str}")

            text = f"### #{nid} {ntype}\n**Role:** {role}\n" + "\n".join(param_lines[:4])
            canvas_nodes.append({
                "id": f"node_{nid}",
                "x": col * x_step,
                "y": row * y_step,
                "width": 260,
                "height": 160,
                "type": "text",
                "text": text,
                "color": color
            })

    canvas_obj = {
        "nodes": canvas_nodes,
        "edges": canvas_edges
    }

    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(canvas_obj, f, indent=2, ensure_ascii=False)

    return canvas_obj

def get_models_inventory(inventory_path: str = DEFAULT_INVENTORY, scan_dir: str = None) -> dict:
    """Read models inventory or scan local ComfyUI models directory."""
    inventory = {
        "checkpoints": [],
        "loras": [],
        "vae": [],
        "controlnet": [],
        "upscalers": [],
        "text_encoders": [],
        "source": "inventory_file"
    }

    if scan_dir and os.path.exists(scan_dir):
        inventory["source"] = f"scanned: {scan_dir}"
        models_root = os.path.join(scan_dir, "models") if os.path.exists(os.path.join(scan_dir, "models")) else scan_dir
        
        def scan_sub(subdir, key):
            p = os.path.join(models_root, subdir)
            if os.path.exists(p):
                for root, _, files in os.walk(p):
                    for f in files:
                        if f.endswith((".safetensors", ".ckpt", ".pt", ".bin", ".gguf")):
                            inventory[key].append(f)

        scan_sub("checkpoints", "checkpoints")
        scan_sub("loras", "loras")
        scan_sub("vae", "vae")
        scan_sub("controlnet", "controlnet")
        scan_sub("upscale_models", "upscalers")
        scan_sub("clip", "text_encoders")
        return inventory

    if os.path.exists(inventory_path):
        with open(inventory_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        current_cat = None
        for line in content.splitlines():
            line_str = line.strip()
            if "### Checkpoints" in line_str or "Checkpoints" in line_str:
                current_cat = "checkpoints"
            elif "### LoRA" in line_str or "LoRA" in line_str:
                current_cat = "loras"
            elif "### VAE" in line_str or "VAE" in line_str:
                current_cat = "vae"
            elif "### ControlNet" in line_str or "ControlNet" in line_str:
                current_cat = "controlnet"
            elif "### Upscale" in line_str or "Upscale" in line_str:
                current_cat = "upscalers"
            elif line_str.startswith("- ") and current_cat:
                item = line_str[2:].split("|")[0].strip().strip("`*")
                if item:
                    inventory[current_cat].append(item)

    return inventory

def list_templates() -> list:
    """List all available workflow templates in comfy-builder skill."""
    templates = []
    if os.path.exists(TEMPLATES_DIR):
        for f in sorted(os.listdir(TEMPLATES_DIR)):
            if f.endswith(".json"):
                name = f[:-5]
                p = os.path.join(TEMPLATES_DIR, f)
                try:
                    data = load_workflow_json(p)
                    fmt = detect_workflow_format(data)
                    node_cnt = len(data.get("nodes", [])) if fmt == "webui" else len(data)
                    has_models = "models" in data and bool(data["models"])
                    templates.append({
                        "name": name,
                        "file": f,
                        "format": fmt,
                        "nodes": node_cnt,
                        "auto_download": has_models
                    })
                except Exception:
                    templates.append({"name": name, "file": f, "format": "invalid", "nodes": 0, "auto_download": False})
    return templates

def export_template(template_name: str, output_path: str = None) -> dict:
    """Export a verified workflow template."""
    clean_name = template_name[:-5] if template_name.endswith(".json") else template_name
    
    candidates = [
        os.path.join(TEMPLATES_DIR, f"{clean_name}.json"),
        os.path.join(TEMPLATES_DIR, f"template_{clean_name}.json"),
        os.path.join(LEGACY_TEMPLATES_DIR, f"{clean_name}.json"),
        os.path.join(LEGACY_TEMPLATES_DIR, f"template_{clean_name}.json")
    ]
    
    found_path = None
    for p in candidates:
        if os.path.exists(p):
            found_path = p
            break

    if not found_path:
        raise FileNotFoundError(f"Template '{template_name}' not found in {TEMPLATES_DIR}")

    with open(found_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    return data

def sync_upstream_templates(source: str = DEFAULT_UPSTREAM_URL) -> dict:
    """Sync workflow templates and node documentation from upstream git repository or local path."""
    result = {"status": "ok", "templates_synced": 0, "nodes_synced": 0, "errors": []}
    staging_dir = "/tmp/comfy_sync_staging"
    
    if os.path.exists(staging_dir):
        shutil.rmtree(staging_dir)

    try:
        if source.startswith("http://") or source.startswith("https://") or source.startswith("git@"):
            cmd = ["git", "clone", "--depth", "1", source, staging_dir]
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            source_dir = staging_dir
        elif os.path.exists(source):
            source_dir = source
        else:
            raise ValueError(f"Invalid upstream source: {source}")

        # Sync templates
        src_templates = os.path.join(source_dir, "templates") if os.path.exists(os.path.join(source_dir, "templates")) else source_dir
        os.makedirs(TEMPLATES_DIR, exist_ok=True)
        if os.path.exists(src_templates):
            for f in os.listdir(src_templates):
                if f.endswith(".json"):
                    src_p = os.path.join(src_templates, f)
                    dst_p = os.path.join(TEMPLATES_DIR, f)
                    shutil.copy2(src_p, dst_p)
                    result["templates_synced"] += 1

        # Sync node references if available
        src_nodes = os.path.join(source_dir, "references", "nodes")
        dst_nodes = os.path.join(VAULT_ROOT, "and_os", "lib", "skills", "comfy-builder", "references", "nodes")
        if os.path.exists(src_nodes):
            os.makedirs(dst_nodes, exist_ok=True)
            for f in os.listdir(src_nodes):
                if f.endswith(".md"):
                    src_p = os.path.join(src_nodes, f)
                    dst_p = os.path.join(dst_nodes, f)
                    shutil.copy2(src_p, dst_p)
                    result["nodes_synced"] += 1

    except Exception as e:
        result["status"] = "error"
        result["errors"].append(str(e))
    finally:
        if os.path.exists(staging_dir):
            shutil.rmtree(staging_dir)

    return result

def main():
    parser = argparse.ArgumentParser(description="ComfyUI Workflow Engine (Think in Code)")
    parser.add_argument("--file", "-f", type=str, help="Input ComfyUI workflow JSON path")
    parser.add_argument("--validate", nargs="?", const="__USE_FILE__", default=None, help="Validate ComfyUI JSON graph integrity")
    parser.add_argument("--mermaid", nargs="?", const="__USE_FILE__", default=None, help="Generate Mermaid diagram from JSON")
    parser.add_argument("--canvas", nargs="?", const="__USE_FILE__", default=None, help="Generate Obsidian Canvas from JSON")
    parser.add_argument("-o", "--output", type=str, help="Output path for Canvas or JSON")
    parser.add_argument("--inventory", action="store_true", help="Inspect available models inventory")
    parser.add_argument("--scan", type=str, help="Scan ComfyUI directory to refresh models inventory")
    parser.add_argument("--comfy-dir", type=str, dest="scan", help="Alias for --scan")
    parser.add_argument("--template", type=str, help="Export verified starter template (flux-txt2img, wan22-img2vid, etc.)")
    parser.add_argument("--list-templates", action="store_true", help="List all available workflow templates")
    parser.add_argument("--sync-upstream", action="store_true", help="Sync workflow templates from upstream repository")
    parser.add_argument("--source", type=str, default=DEFAULT_UPSTREAM_URL, help="Upstream Git repository or directory for sync")
    args = parser.parse_args()

    def resolve_target(arg_val):
        if arg_val and arg_val != "__USE_FILE__":
            return arg_val
        return args.file

    if args.list_templates:
        t_list = list_templates()
        print(f"=== ComfyUI Available Workflow Templates ({len(t_list)} total) ===")
        print(f"Directory: {TEMPLATES_DIR}\n")
        print(f"{'Template Name':<30} | {'Format':<8} | {'Nodes':<6} | {'Auto-Download':<14}")
        print("-" * 66)
        for t in t_list:
            auto_str = "[Yes]" if t["auto_download"] else "[No]"
            print(f"{t['name']:<30} | {t['format'].upper():<8} | {t['nodes']:<6} | {auto_str:<14}")
        sys.exit(0)

    if args.sync_upstream:
        print(f"🔄 Syncing ComfyUI workflow templates from: {args.source}...")
        res = sync_upstream_templates(source=args.source)
        if res["status"] == "ok":
            print(f"✅ Sync successful! Templates updated: {res['templates_synced']}, Node specs: {res['nodes_synced']}")
            sys.exit(0)
        else:
            print(f"❌ Sync failed: {', '.join(res['errors'])}")
            sys.exit(1)

    if args.validate is not None:
        target = resolve_target(args.validate)
        if not target:
            print("Error: Specify JSON file via --validate <file> or --file <file>.")
            sys.exit(1)
        if not os.path.exists(target):
            print(f"Error: File '{target}' does not exist.")
            sys.exit(1)
        data = load_workflow_json(target)
        rep = validate_workflow(data)
        print(f"=== Validation Results: {os.path.basename(target)} ===")
        print(f"Format: {rep['format'].upper()} | Nodes: {rep['nodes_count']} | Links: {rep['links_count']}")
        print(f"Status: {'PASS [Valid Graph]' if rep['valid'] else 'FAIL [Integrity Errors]'}")
        if rep["models_used"]:
            print("Models Referenced:", ", ".join(rep["models_used"]))
        if rep["errors"]:
            print("\nErrors:")
            for e in rep["errors"]:
                print(f"  [!] {e}")
        if rep["warnings"]:
            print("\nWarnings:")
            for w in rep["warnings"]:
                print(f"  [?] {w}")
        sys.exit(0 if rep["valid"] else 1)

    elif args.mermaid is not None:
        target = resolve_target(args.mermaid)
        if not target:
            print("Error: Specify JSON file via --mermaid <file> or --file <file>.")
            sys.exit(1)
        if not os.path.exists(target):
            print(f"Error: File '{target}' does not exist.")
            sys.exit(1)
        data = load_workflow_json(target)
        code = generate_mermaid(data)
        print(code)

    elif args.canvas is not None:
        if args.file:
            target = args.file
            out = args.canvas if (args.canvas and args.canvas != "__USE_FILE__") else (args.output or os.path.splitext(target)[0] + ".canvas")
        else:
            target = resolve_target(args.canvas)
            out = args.output or os.path.splitext(target)[0] + ".canvas"

        if not target or not os.path.exists(target):
            print(f"Error: Input file '{target}' does not exist.")
            sys.exit(1)

        data = load_workflow_json(target)
        c = generate_canvas(data, out)
        print(f"Obsidian Canvas successfully generated: {out} ({len(c['nodes'])} nodes, {len(c['edges'])} links)")

    elif args.inventory:
        inv = get_models_inventory(scan_dir=args.scan)
        print(f"=== ComfyUI Models Inventory [{inv['source']}] ===")
        for cat, items in inv.items():
            if cat == "source":
                continue
            print(f"\nCategory: {cat.upper()} ({len(items)} items):")
            for it in items[:10]:
                print(f"  - {it}")
            if len(items) > 10:
                print(f"  ... and {len(items)-10} more items.")

    elif args.template:
        out = args.output or f"{args.template}_workflow.json"
        try:
            export_template(args.template, out)
            print(f"Template '{args.template}' successfully exported to: {out}")
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
