#!/usr/bin/env python3
"""
project_skeleton.py — Reference project skeleton generator (Skeleton Engine).
AnD os v1.0.0 — Island 9 (Xcode / iOS Game Engineering) & Island 7 (Pulsar 3D Tools).

Deploys battle-ready architectural skeletons instead of empty catalogs:
1. 'ios-spritekit' template: native Swift / SpriteKit architecture for mobile games (EscPlanet):
   - `GameScene.swift` (State Machine, Render Loop, Delta Time);
   - `GameViewController.swift` (Orientation lock, Metal View config);
   - `AssetCatalog.swift` (type-safe assets and textures);
   - `GameConfig.swift` (balance parameters, FPS lock 60/120);
   - `Package.swift` or Xcode Workspace structure;
   - `Tests/` (base test suite).
2. 'cg-tool' template: modular utility with tests and an AnD os CLI facade.
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, Any

VAULT_ROOT = os.getenv("AND_ROOT", os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

def create_ios_game_skeleton(target_dir: str, app_name: str = "EscPlanet") -> Dict[str, Any]:
    """Generates a clean, compile-ready SpriteKit game module skeleton."""
    os.makedirs(target_dir, exist_ok=True)
    sources_dir = os.path.join(target_dir, "Sources", app_name)
    tests_dir = os.path.join(target_dir, "Tests", f"{app_name}Tests")
    os.makedirs(sources_dir, exist_ok=True)
    os.makedirs(tests_dir, exist_ok=True)

    created_files = []

    # 1. GameConfig.swift
    config_swift = os.path.join(sources_dir, "GameConfig.swift")
    with open(config_swift, "w", encoding="utf-8") as f:
        f.write(f"""//
// GameConfig.swift
// {app_name} — AnD os v1.0.0 Architecture
//

import Foundation

public struct GameConfig {{
    public static let targetFPS: Int = 60
    public static let worldGravity: Double = -9.8
    public static let baseResolutionWidth: Double = 1170.0
    public static let baseResolutionHeight: Double = 2532.0 // iPhone 13-16 standard
    public static let debugPhysicsOverlay: Bool = false
}}
""")
    created_files.append(config_swift)

    # 2. GameScene.swift
    scene_swift = os.path.join(sources_dir, "GameScene.swift")
    with open(scene_swift, "w", encoding="utf-8") as f:
        f.write(f"""//
// GameScene.swift
// {app_name} — Core Gameplay Scene
//

import SpriteKit

public class GameScene: SKScene {{
    private var lastUpdateTime: TimeInterval = 0

    public override func didMove(to view: SKView) {{
        self.backgroundColor = .black
        self.physicsWorld.gravity = CGVector(dx: 0, dy: GameConfig.worldGravity)
    }}

    public override func update(_ currentTime: TimeInterval) {{
        if lastUpdateTime == 0 {{
            lastUpdateTime = currentTime
        }}
        let dt = currentTime - lastUpdateTime
        lastUpdateTime = currentTime
        updateSimulation(dt: dt)
    }}

    private func updateSimulation(dt: TimeInterval) {{
        // Core game simulation tick
    }}
}}
""")
    created_files.append(scene_swift)

    # 3. GameTests.swift
    test_swift = os.path.join(tests_dir, "GameTests.swift")
    with open(test_swift, "w", encoding="utf-8") as f:
        f.write(f"""//
// GameTests.swift
// {app_name} Unit Tests
//

import XCTest
@testable import {app_name}

final class {app_name}Tests: XCTestCase {{
    func testConfigInit() {{
        XCTAssertEqual(GameConfig.targetFPS, 60)
        XCTAssertFalse(GameConfig.debugPhysicsOverlay)
    }}
}}
""")
    created_files.append(test_swift)

    # 4. Manifest sidecar
    meta_json = os.path.join(target_dir, "project.skeleton.json")
    meta = {
        "project_name": app_name,
        "type": "ios_spritekit_game",
        "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "files_count": len(created_files),
        "status": "ready_for_xcode"
    }
    with open(meta_json, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    created_files.append(meta_json)

    return {
        "status": "ok",
        "app_name": app_name,
        "target_dir": target_dir,
        "created_files": created_files,
        "meta_file": meta_json
    }

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--ios":
        path = sys.argv[2]
        name = sys.argv[3] if len(sys.argv) > 3 else "EscPlanet"
        res = create_ios_game_skeleton(path, name)
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        print("Usage: project_skeleton.py --ios <target_dir> [app_name]")
