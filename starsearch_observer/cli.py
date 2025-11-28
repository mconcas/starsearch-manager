#!/usr/bin/env python3
import json
import sys
from pathlib import Path
import requests
import yaml
from . import functions

VERSION = "0.1.0"

def load_config():
    config_path = Path.home() / ".starsearch" / "config.json"
    with open(config_path) as f:
        return json.load(f)

def get_server(config, target=None):
    """Get server configuration by name or return the default (first) server.
    
    Args:
        config: Configuration dictionary containing 'servers' list
        target: Optional server name to look up
        
    Returns:
        tuple: (server_dict, is_default_bool)
        
    Raises:
        SystemExit: If target server is not found (prints available servers and exits)
    """
    servers = config["servers"]
    if target:
        for srv in servers:
            if srv["name"] == target:
                return srv, False
        
        # Target not found - show helpful error message
        print(f"Error: Server '{target}' not found in configuration", file=sys.stderr)
        print(f"\nAvailable servers:", file=sys.stderr)
        for srv in servers:
            print(f"  - {srv['name']}", file=sys.stderr)
        sys.exit(1)
    
    return servers[0], True  # default server, is_default=True

def get_auth(server):
    """Get auth tuple from server config if username/password are present."""
    username = server.get("username")
    password = server.get("password")
    if username and password:
        return (username, password)
    return None

def get_verify_ssl(server):
    """Get SSL verification setting from server config (default True)."""
    return server.get("verify_ssl", True)

def get_cluster_base_url(server):
    """Construct base URL for OpenSearch/Elasticsearch cluster API access."""
    protocol = server['protocol']
    host = server['host']
    cluster_path = server.get('cluster_path', '')
    
    if cluster_path:
        # Ensure cluster_path starts with / and doesn't end with /
        if not cluster_path.startswith('/'):
            cluster_path = '/' + cluster_path
        if cluster_path.endswith('/'):
            cluster_path = cluster_path[:-1]
        return f"{protocol}://{host}{cluster_path}"
    return f"{protocol}://{host}"

def get_base_url(server):
    """Construct base URL from server config including optional base_path (for Dashboards API)."""
    protocol = server['protocol']
    host = server['host']
    base_path = server.get('base_path', '')
    
    if base_path:
        # Ensure base_path starts with / and doesn't end with /
        if not base_path.startswith('/'):
            base_path = '/' + base_path
        if base_path.endswith('/'):
            base_path = base_path[:-1]
        return f"{protocol}://{host}{base_path}"
    return f"{protocol}://{host}"

def use_dashboards_api(server):
    """Check if we should use OpenSearch Dashboards API (true when base_path is set)."""
    return bool(server.get('base_path'))

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
    
    base_url = get_cluster_base_url(server)
    url = f"{base_url}/{endpoint}"
    auth = get_auth(server)
    verify_ssl = get_verify_ssl(server)
    response = requests.get(url, auth=auth, verify=verify_ssl)
    try:
        print(json.dumps(response.json(), indent=2))
    except requests.exceptions.JSONDecodeError:
        print(response.text)

def main():
    if len(sys.argv) > 1 and sys.argv[1] in ["-v", "--version"]:
        print(f"observe-cli version {VERSION}")
        sys.exit(0)
    
    if len(sys.argv) < 2 or sys.argv[1] in ["-h", "--help"]:
        print("Usage: observe-cli <command> [args] or observe-cli <endpoint>")
        print("       observe-cli -t|--target <name> <command> [args]")
        print("       observe-cli -v|--version")
        print("\nObject Management:")
        print("  observe-cli dashboard list                           - List all dashboards")
        print("  observe-cli dashboard export [id1 id2 ...]           - Export dashboards to ndjson")
        print("  observe-cli dashboard import <file.ndjson>           - Import dashboards from ndjson")
        print("  observe-cli dashboard delete <id>                    - Delete a dashboard")
        print("")
        print("  observe-cli visualization list                       - List all visualizations")
        print("  observe-cli visualization export [id1 id2 ...]       - Export visualizations to ndjson")
        print("  observe-cli visualization import <file.ndjson>       - Import visualizations from ndjson")
        print("  observe-cli visualization delete <id>                - Delete a visualization")
        print("")
        print("  observe-cli search list                              - List all saved searches")
        print("  observe-cli search export [id1 id2 ...]              - Export searches to ndjson")
        print("  observe-cli search import <file.ndjson>              - Import searches from ndjson")
        print("  observe-cli search delete <id>                       - Delete a search")
        print("\nOther Commands:")
        print("  observe-cli ilm info [--all]                         - Show ILM policy info for indices")
        print("  observe-cli ilm <policy> set delete-after <days>     - Set delete phase for a policy")
        print("  observe-cli ilm <policy> set warm-after <days>       - Set warm phase for a policy")
        print("  observe-cli ilm <policy> set cold-after <days>       - Set cold phase for a policy")
        print("  observe-cli ilm <policy> set rollover <size> <docs>  - Set rollover thresholds")
        print("  observe-cli index delete <index-name>                - Delete an index")
        print("  observe-cli index-pattern list                       - List all index patterns")
        print("  observe-cli index-pattern delete <pattern-id>        - Delete an index pattern")
        sys.exit(0 if len(sys.argv) > 1 else 1)
    
    target = None
    args = sys.argv[1:]
    
    if args[0] in ["-t", "--target"]:
        if len(args) < 3:
            print("Error: -t/--target requires a server name")
            sys.exit(1)
        target = args[1]
        args = args[2:]
    
    cfg = load_config()
    
    # Dashboard commands
    if len(args) >= 2 and args[0] == "dashboard":
        if args[1] == "list":
            results = functions.list_dashboards(cfg, target, obj_type="dashboard")
            if isinstance(results, dict) and "error" in results:
                print(json.dumps(results, indent=2))
            else:
                functions.print_saved_objects(results)
            return
        elif args[1] == "export":
            use_json = "--json" in args
            obj_ids = [arg for arg in args[2:] if arg != "--json"] if len(args) > 2 else None
            result = functions.export_saved_objects(cfg, target, obj_ids, obj_type="dashboard")
            if isinstance(result, dict) and "error" in result:
                print(json.dumps(result, indent=2))
            elif use_json:
                lines = [json.loads(line) for line in result.strip().split('\n') if line.strip()]
                print(json.dumps(lines, indent=2))
            else:
                print(result)
            return
        elif args[1] == "import":
            if len(args) < 3:
                print("Usage: observe-cli dashboard import <file.ndjson>")
                sys.exit(1)
            filepath = args[2]
            with open(filepath, 'r') as f:
                ndjson_content = f.read()
            result = functions.import_saved_objects(cfg, ndjson_content, target, obj_type="dashboard")
            print(json.dumps(result, indent=2))
            return
        elif args[1] == "delete":
            if len(args) < 3:
                print("Usage: observe-cli dashboard delete <id>")
                sys.exit(1)
            obj_id = args[2]
            result = functions.delete_saved_object(cfg, obj_id, "dashboard", target)
            print(json.dumps(result, indent=2))
            return
    
    # Visualization commands
    if len(args) >= 2 and args[0] == "visualization":
        if args[1] == "list":
            results = functions.list_dashboards(cfg, target, obj_type="visualization")
            if isinstance(results, dict) and "error" in results:
                print(json.dumps(results, indent=2))
            else:
                functions.print_saved_objects(results)
            return
        elif args[1] == "export":
            use_json = "--json" in args
            obj_ids = [arg for arg in args[2:] if arg != "--json"] if len(args) > 2 else None
            result = functions.export_saved_objects(cfg, target, obj_ids, obj_type="visualization")
            if isinstance(result, dict) and "error" in result:
                print(json.dumps(result, indent=2))
            elif use_json:
                lines = [json.loads(line) for line in result.strip().split('\n') if line.strip()]
                print(json.dumps(lines, indent=2))
            else:
                print(result)
            return
        elif args[1] == "import":
            if len(args) < 3:
                print("Usage: observe-cli visualization import <file.ndjson>")
                sys.exit(1)
            filepath = args[2]
            with open(filepath, 'r') as f:
                ndjson_content = f.read()
            result = functions.import_saved_objects(cfg, ndjson_content, target, obj_type="visualization")
            print(json.dumps(result, indent=2))
            return
        elif args[1] == "delete":
            if len(args) < 3:
                print("Usage: observe-cli visualization delete <id>")
                sys.exit(1)
            obj_id = args[2]
            result = functions.delete_saved_object(cfg, obj_id, "visualization", target)
            print(json.dumps(result, indent=2))
            return
    
    # Search commands
    if len(args) >= 2 and args[0] == "search":
        if args[1] == "list":
            results = functions.list_saved_searches(cfg, target)
            if isinstance(results, dict) and "error" in results:
                print(json.dumps(results, indent=2))
            else:
                functions.print_index_patterns(results)
            return
        elif args[1] == "export":
            use_json = "--json" in args
            obj_ids = [arg for arg in args[2:] if arg != "--json"] if len(args) > 2 else None
            result = functions.export_saved_objects(cfg, target, obj_ids, obj_type="search")
            if isinstance(result, dict) and "error" in result:
                print(json.dumps(result, indent=2))
            elif use_json:
                lines = [json.loads(line) for line in result.strip().split('\n') if line.strip()]
                print(json.dumps(lines, indent=2))
            else:
                print(result)
            return
        elif args[1] == "import":
            if len(args) < 3:
                print("Usage: observe-cli search import <file.ndjson>")
                sys.exit(1)
            filepath = args[2]
            with open(filepath, 'r') as f:
                ndjson_content = f.read()
            result = functions.import_saved_objects(cfg, ndjson_content, target, obj_type="search")
            print(json.dumps(result, indent=2))
            return
        elif args[1] == "delete":
            if len(args) < 3:
                print("Usage: observe-cli search delete <id>")
                sys.exit(1)
            search_id = args[2]
            result = functions.delete_saved_object(cfg, search_id, "search", target)
            print(json.dumps(result, indent=2))
            return
    
    # ILM commands
    if len(args) >= 2 and args[0] == "ilm" and args[1] == "info":
        show_all = "--all" in args or "--all" in sys.argv
        results = functions.get_index_lifecycle_info(cfg, target, show_all)
        functions.print_table(results)
        return
    
    if len(args) >= 4 and args[0] == "ilm" and args[2] == "set":
        phase_arg = args[3] if len(args) > 3 else None
        
        if phase_arg == "rollover":
            if len(args) < 6:
                print("Usage: observe-cli ilm <policy> set rollover <max_size> <max_docs>")
                print("  max_size: e.g., '50gb', '10gb'")
                print("  max_docs: e.g., '150000000' or 'none'")
                sys.exit(1)
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
            print(f"Usage: observe-cli ilm <policy> set {phase_arg} <days>")
            sys.exit(1)
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
    
    # Index commands
    if len(args) >= 3 and args[0] == "index" and args[1] == "delete":
        index_name = args[2]
        result = functions.delete_index(cfg, index_name, target)
        print(json.dumps(result, indent=2))
        return
    
    # Index pattern commands
    if len(args) >= 2 and args[0] == "index-pattern":
        if args[1] == "list":
            results = functions.list_index_patterns(cfg, target)
            if isinstance(results, dict) and "error" in results:
                print(json.dumps(results, indent=2))
            else:
                functions.print_index_patterns(results)
            return
        elif args[1] == "delete":
            if len(args) < 3:
                print("Usage: observe-cli index-pattern delete <pattern-id>")
                sys.exit(1)
            pattern_id = args[2]
            result = functions.delete_index_pattern(cfg, pattern_id, target)
            print(json.dumps(result, indent=2))
            return
    
    # Fallback to endpoint query
    endpoint = resolve_endpoint(args)
    query(endpoint, target)

if __name__ == "__main__":
    main()
