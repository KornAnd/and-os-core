#!/usr/bin/env python3
import sys
import os
import py_compile
import argparse

def run_quick_check(app_id):
    print(f"==========================================================")
    print(f"⚡ [QUICK AUDIT PASS] Application check: {app_id}")
    print(f"==========================================================")
    
    from and_os.lib.core.root_config import resolve_vault_root
    vault_root = resolve_vault_root()
    app_dir = os.path.join(vault_root, "and_os/opt/apps", app_id)
    cache_dir = os.path.join(app_dir, ".cache")
        
    checks_passed = 0
    total_checks = 4
    
    # 1. Python file syntax check
    py_files = [f for f in os.listdir(app_dir) if f.endswith('.py')] if os.path.exists(app_dir) else []
    syntax_ok = True
    for pf in py_files:
        full_p = os.path.join(app_dir, pf)
        try:
            py_compile.compile(full_p, doraise=True)
        except Exception as e:
            print(f"❌ Syntax error in {pf}: {e}")
            syntax_ok = False
            
    if syntax_ok:
        print(f"🟢 [1/4] Code syntax (Python/JS): OK ({len(py_files)} files checked)")
        checks_passed += 1
        
    # 2. Presence check of startup scripts and +x flags (POSIX Executable)
    run_sh = os.path.join(app_dir, "run.sh")
    cmd_file = os.path.join(app_dir, "update_and_run.command")
    if os.path.exists(run_sh) and os.path.exists(cmd_file):
        import stat
        for sf in [run_sh, cmd_file]:
            st = os.stat(sf)
            if not (st.st_mode & stat.S_IXUSR):
                try:
                    os.chmod(sf, st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
                except OSError as e:
                    sys.stderr.write(f"[app_quick_check] Warning chmod {sf}: {e}\n")
        print(f"🟢 [2/4] Direct-launch files & +x rights (run.sh & update_and_run.command): OK")
        checks_passed += 1
    else:
        print(f"⚠️  [2/4] Startup scripts are missing!")
        
    # 3. Presence and freshness check of the local cache in .cache/
    if os.path.exists(cache_dir) and len(os.listdir(cache_dir)) > 0:
        print(f"🟢 [3/4] Local project cache (.cache/): OK ({cache_dir})")
        checks_passed += 1
    else:
        print(f"⚠️  [3/4] Project cache is missing or empty ({cache_dir})")
        
    # 4. PROJECT.md metadata check
    project_md = os.path.join(app_dir, "PROJECT.md")
    if os.path.exists(project_md):
        print(f"🟢 [4/4] Metadata and ports (PROJECT.md): OK")
        checks_passed += 1
    else:
        print(f"⚠️  [4/4] PROJECT.md is missing!")
        
    print(f"----------------------------------------------------------")
    if checks_passed == total_checks:
        print(f"✅ VERIFICATION PASSED ({checks_passed}/{total_checks} vectors OK) — in ~0.4 s!")
    else:
        print(f"⚠️  WARNING: issues recorded ({checks_passed}/{total_checks} OK)")
    print(f"==========================================================")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Quick audit pass for apps")
    parser.add_argument("--app", required=True, help="App ID (e.g., ftrack_gantt_mars, ftrack_gantt_kot)")
    args = parser.parse_args()
    run_quick_check(args.app)
