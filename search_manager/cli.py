#!/usr/bin/env python3
import json
import sys
from pathlib import Path
import requests
import yaml
from . import functions

def load_config():
    config_path = Path.home() / ".search-manager" / "config.json"
    with open(config_path) as f:
        return json.load(f)

def get_server(config, target=None):
    servers = config["servers"]
    if target:
        for srv in servers:
            if srv["name"] == target:
                return srv, False
        raise ValueError(f"Server '{target}' not found in config")
    return servers[0], True  # default server, is_default=True

def load_commands():
    commands_path = Path(__file__).parent / "commands.yaml"
    with open(commands_path) as f:
        return yaml.safe_load(f)

def resolve_endpoint(args):
    commands = load_commands()
    
    # Try command mapping: search <cmd> <subcmd> -> _<cmd>/<subcmd>
    if args[0] in commands:
        prefix = commands[args[0]]
        if len(args) > 1:
            return f"{prefix}/{'/'.join(args[1:])}"
        return prefix
    
    # Fallback: treat as raw endpoint
    return " ".join(args)

def query(endpoint, target=None):
    cfg = load_config()
    server, is_default = get_server(cfg, target)
    
    if is_default:
        print(f"→ {server['name']}")
    
    url = f"{server['protocol']}://{server['host']}/{endpoint}"
    response = requests.get(url)
    try:
        print(json.dumps(response.json(), indent=2))
    except requests.exceptions.JSONDecodeError:
        print(response.text)

def main():
    if len(sys.argv) < 2:
        print("Usage: search <command> [args] or search <endpoint>")
        print("       search -t|--target <name> <command> [args]")
        print("\nCustom commands:")
        print("  search ilm info [--all]                         - Show ILM policy info for indices (--all includes unmanaged)")
        print("  search ilm <policy> set delete-after <days>     - Set delete phase for a policy")
        print("  search ilm <policy> set warm-after <days>       - Set warm phase for a policy")
        print("  search ilm <policy> set cold-after <days>       - Set cold phase for a policy")
        print("  search ilm <policy> set rollover <size> <docs>  - Set rollover thresholds (use 'none' to skip)")
        print("  search index delete <index-name>                - Delete an index")
        print("  search dashboard list                           - List all dashboards and visualizations")
        print("  search dashboard export [id1 id2 ...]           - Export dashboards/visualizations to ndjson")
        sys.exit(1)
    
    target = None
    args = sys.argv[1:]
    
    if args[0] in ["-t", "--target"]:
        if len(args) < 3:
            print("Error: -t/--target requires a server name")
            sys.exit(1)
        target = args[1]
        args = args[2:]
    
    # Check for custom functions
    if len(args) >= 2 and args[0] == "ilm" and args[1] == "info":
        cfg = load_config()
        show_all = "--all" in args or "--all" in sys.argv
        results = functions.get_index_lifecycle_info(cfg, target, show_all)
        functions.print_table(results)
        return
    
    if len(args) >= 4 and args[0] == "ilm" and args[2] == "set":
        phase_arg = args[3] if len(args) > 3 else None
        
        # Handle rollover separately
        if phase_arg == "rollover":
            if len(args) < 6:
                print("Usage: search ilm <policy> set rollover <max_size> <max_docs>")
                print("  max_size: e.g., '50gb', '10gb'")
                print("  max_docs: e.g., '150000000' or 'none'")
                sys.exit(1)
            cfg = load_config()
            policy_name = args[1]
            max_size = args[4] if args[4].lower() != "none" else None
            max_docs = args[5] if args[5].lower() != "none" else None
            result = functions.set_policy_rollover(cfg, policy_name, max_size, max_docs, target)
            print(json.dumps(result, indent=2))
            return
        
        if phase_arg not in ["delete-after", "warm-after", "cold-after"]:
            print("Error: phase must be delete-after, warm-after, cold-after, or rollover")
            sys.exit(1)
        if len(args) < 5:
            print(f"Usage: search ilm <policy> set {phase_arg} <days>")
            sys.exit(1)
        cfg = load_config()
        policy_name = args[1]
        try:
            days = int(args[4])
        except ValueError:
            print("Error: days must be an integer")
            sys.exit(1)
        
        if phase_arg == "delete-after":
            result = functions.set_policy_delete_phase(cfg, policy_name, days, target)
        elif phase_arg == "warm-after":
            result = functions.set_policy_warm_phase(cfg, policy_name, days, target)
        elif phase_arg == "cold-after":
            result = functions.set_policy_cold_phase(cfg, policy_name, days, target)
        
        print(json.dumps(result, indent=2))
        return
    
    if len(args) >= 3 and args[0] == "index" and args[1] == "delete":
        if len(args) < 3:
            print("Usage: search index delete <index-name>")
            sys.exit(1)
        cfg = load_config()
        index_name = args[2]
        result = functions.delete_index(cfg, index_name, target)
        print(json.dumps(result, indent=2))
        return
    
    if len(args) >= 2 and args[0] == "dashboard" and args[1] == "list":
        cfg = load_config()
        results = functions.list_dashboards(cfg, target)
        if isinstance(results, dict) and "error" in results:
            print(json.dumps(results, indent=2))
        else:
            functions.print_saved_objects(results)
        return
    
    if len(args) >= 2 and args[0] == "dashboard" and args[1] == "export":
        cfg = load_config()
        obj_ids = args[2:] if len(args) > 2 else None
        result = functions.export_saved_objects(cfg, target, obj_ids)
        if isinstance(result, dict) and "error" in result:
            print(json.dumps(result, indent=2))
        else:
            print(result)
        return
    
    endpoint = resolve_endpoint(args)
    query(endpoint, target)

if __name__ == "__main__":
    main()
