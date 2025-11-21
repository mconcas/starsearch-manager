import requests
import json
from datetime import datetime, timedelta


COLORS = {
    "hot": "\033[91m",      # red
    "warm": "\033[93m",     # orange/yellow
    "cold": "\033[94m",     # blue
    "reset": "\033[0m"
}


def parse_age_to_days(age_str):
    """Convert age string like '30d', '2h' to days."""
    if age_str.endswith("d"):
        return int(age_str[:-1])
    elif age_str.endswith("h"):
        return int(age_str[:-1]) / 24
    elif age_str.endswith("m"):
        return int(age_str[:-1]) / (24 * 60)
    return 0


def format_bytes(bytes_val):
    """Format bytes into human readable string."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_val < 1024:
            return f"{bytes_val:.1f}{unit}"
        bytes_val /= 1024
    return f"{bytes_val:.1f}PB"


def set_policy_delete_phase(config, policy_name, days, target=None):
    """Add or update delete phase in an ILM policy."""
    from .cli import get_server
    
    server, _ = get_server(config, target)
    base_url = f"{server['protocol']}://{server['host']}"
    
    # Get current policy
    policy_resp = requests.get(f"{base_url}/_ilm/policy/{policy_name}")
    if policy_resp.status_code != 200:
        return {"error": f"Policy '{policy_name}' not found"}
    
    policy_data = policy_resp.json()
    policy = policy_data[policy_name]["policy"]
    
    # Add/update delete phase
    if "phases" not in policy:
        policy["phases"] = {}
    
    policy["phases"]["delete"] = {
        "min_age": f"{days}d",
        "actions": {
            "delete": {
                "delete_searchable_snapshot": True
            }
        }
    }
    
    # Update policy
    update_resp = requests.put(
        f"{base_url}/_ilm/policy/{policy_name}",
        headers={"Content-Type": "application/json"},
        data=json.dumps({"policy": policy})
    )
    
    if update_resp.status_code in [200, 201]:
        return {
            "success": True,
            "policy": policy_name,
            "delete_after": f"{days}d",
            "message": f"Policy updated. Indices will be deleted after {days} days from creation."
        }
    else:
        return {"error": update_resp.text}


def set_policy_warm_phase(config, policy_name, days, target=None):
    """Add or update warm phase in an ILM policy."""
    from .cli import get_server
    
    server, _ = get_server(config, target)
    base_url = f"{server['protocol']}://{server['host']}"
    
    # Get current policy
    policy_resp = requests.get(f"{base_url}/_ilm/policy/{policy_name}")
    if policy_resp.status_code != 200:
        return {"error": f"Policy '{policy_name}' not found"}
    
    policy_data = policy_resp.json()
    policy = policy_data[policy_name]["policy"]
    
    # Add/update warm phase
    if "phases" not in policy:
        policy["phases"] = {}
    
    policy["phases"]["warm"] = {
        "min_age": f"{days}d",
        "actions": {
            "set_priority": {
                "priority": 50
            }
        }
    }
    
    # Update policy
    update_resp = requests.put(
        f"{base_url}/_ilm/policy/{policy_name}",
        headers={"Content-Type": "application/json"},
        data=json.dumps({"policy": policy})
    )
    
    if update_resp.status_code in [200, 201]:
        return {
            "success": True,
            "policy": policy_name,
            "warm_after": f"{days}d",
            "message": f"Policy updated. Indices will move to warm after {days} days."
        }
    else:
        return {"error": update_resp.text}


def set_policy_cold_phase(config, policy_name, days, target=None):
    """Add or update cold phase in an ILM policy."""
    from .cli import get_server
    
    server, _ = get_server(config, target)
    base_url = f"{server['protocol']}://{server['host']}"
    
    # Get current policy
    policy_resp = requests.get(f"{base_url}/_ilm/policy/{policy_name}")
    if policy_resp.status_code != 200:
        return {"error": f"Policy '{policy_name}' not found"}
    
    policy_data = policy_resp.json()
    policy = policy_data[policy_name]["policy"]
    
    # Add/update cold phase
    if "phases" not in policy:
        policy["phases"] = {}
    
    policy["phases"]["cold"] = {
        "min_age": f"{days}d",
        "actions": {
            "set_priority": {
                "priority": 0
            }
        }
    }
    
    # Update policy
    update_resp = requests.put(
        f"{base_url}/_ilm/policy/{policy_name}",
        headers={"Content-Type": "application/json"},
        data=json.dumps({"policy": policy})
    )
    
    if update_resp.status_code in [200, 201]:
        return {
            "success": True,
            "policy": policy_name,
            "cold_after": f"{days}d",
            "message": f"Policy updated. Indices will move to cold after {days} days."
        }
    else:
        return {"error": update_resp.text}


def set_policy_rollover(config, policy_name, max_size, max_docs, target=None):
    """Add or update rollover action in hot phase of an ILM policy."""
    from .cli import get_server
    
    server, _ = get_server(config, target)
    base_url = f"{server['protocol']}://{server['host']}"
    
    # Get current policy
    policy_resp = requests.get(f"{base_url}/_ilm/policy/{policy_name}")
    if policy_resp.status_code != 200:
        return {"error": f"Policy '{policy_name}' not found"}
    
    policy_data = policy_resp.json()
    policy = policy_data[policy_name]["policy"]
    
    # Add/update hot phase with rollover
    if "phases" not in policy:
        policy["phases"] = {}
    if "hot" not in policy["phases"]:
        policy["phases"]["hot"] = {"min_age": "0ms", "actions": {}}
    if "actions" not in policy["phases"]["hot"]:
        policy["phases"]["hot"]["actions"] = {}
    
    rollover_action = {}
    if max_size:
        rollover_action["max_primary_shard_size"] = max_size
    if max_docs:
        rollover_action["max_docs"] = int(max_docs)
    
    policy["phases"]["hot"]["actions"]["rollover"] = rollover_action
    
    # Update policy
    update_resp = requests.put(
        f"{base_url}/_ilm/policy/{policy_name}",
        headers={"Content-Type": "application/json"},
        data=json.dumps({"policy": policy})
    )
    
    if update_resp.status_code in [200, 201]:
        return {
            "success": True,
            "policy": policy_name,
            "rollover": rollover_action,
            "message": f"Policy updated with rollover: {rollover_action}"
        }
    else:
        return {"error": update_resp.text}


def delete_index(config, index_name, target=None):
    """Delete an index."""
    from .cli import get_server
    
    server, _ = get_server(config, target)
    base_url = f"{server['protocol']}://{server['host']}"
    
    # Delete the index
    delete_resp = requests.delete(f"{base_url}/{index_name}")
    
    if delete_resp.status_code == 200:
        return {
            "success": True,
            "index": index_name,
            "message": f"Index '{index_name}' deleted successfully"
        }
    elif delete_resp.status_code == 404:
        return {"error": f"Index '{index_name}' not found"}
    else:
        return {"error": delete_resp.text}


def delete_index_pattern(config, pattern_id, target=None):
    """Delete an index pattern from .kibana."""
    from .cli import get_server
    
    server, _ = get_server(config, target)
    base_url = f"{server['protocol']}://{server['host']}"
    
    # Delete the index pattern document
    delete_resp = requests.delete(f"{base_url}/.kibana/_doc/index-pattern:{pattern_id}")
    
    if delete_resp.status_code == 200:
        return {
            "success": True,
            "pattern_id": pattern_id,
            "message": f"Index pattern '{pattern_id}' deleted successfully"
        }
    elif delete_resp.status_code == 404:
        return {"error": f"Index pattern '{pattern_id}' not found"}
    else:
        return {"error": delete_resp.text}


def delete_dashboard(config, obj_id, target=None):
    """Delete a dashboard or visualization from .kibana."""
    from .cli import get_server
    
    server, _ = get_server(config, target)
    base_url = f"{server['protocol']}://{server['host']}"
    
    # Delete the saved object document
    delete_resp = requests.delete(f"{base_url}/.kibana/_doc/{obj_id}")
    
    if delete_resp.status_code == 200:
        return {
            "success": True,
            "id": obj_id,
            "message": f"Dashboard/visualization '{obj_id}' deleted successfully"
        }
    elif delete_resp.status_code == 404:
        return {"error": f"Dashboard/visualization '{obj_id}' not found"}
    else:
        return {"error": delete_resp.text}


def get_index_lifecycle_info(config, target=None, show_all=False):
    """Get ILM info for all indices with their lifecycle timelines."""
    from .cli import get_server
    
    server, _ = get_server(config, target)
    base_url = f"{server['protocol']}://{server['host']}"
    
    # Detect if this is OpenSearch or Elasticsearch
    cluster_resp = requests.get(f"{base_url}/")
    cluster_info = cluster_resp.json()
    is_opensearch = "opensearch" in cluster_info.get("version", {}).get("distribution", "").lower()
    
    if is_opensearch:
        # OpenSearch uses ISM (Index State Management)
        indices_resp = requests.get(f"{base_url}/_plugins/_ism/explain/*")
        policies_resp = requests.get(f"{base_url}/_plugins/_ism/policies")
    else:
        # Elasticsearch uses ILM
        indices_resp = requests.get(f"{base_url}/*/_ilm/explain")
        policies_resp = requests.get(f"{base_url}/_ilm/policy")
    
    indices_data = indices_resp.json()
    policies = policies_resp.json()
    
    # Get index stats for sizes
    stats_resp = requests.get(f"{base_url}/*/_stats/store")
    stats_data = stats_resp.json()
    
    results = []
    
    # Handle different response formats
    if is_opensearch:
        # OpenSearch: flat dict with index names as keys
        indices_dict = indices_data
    else:
        # Elasticsearch: nested under "indices" key
        indices_dict = indices_data.get("indices", {})
    
    for index_name, info in indices_dict.items():
        # Skip non-index metadata keys (e.g., total_managed_indices in OpenSearch)
        if not isinstance(info, dict):
            continue
        
        # Check if index has a policy (different fields for ES vs OpenSearch)
        if is_opensearch:
            has_policy = info.get("index.plugins.index_state_management.policy_id") is not None
            policy_name = info.get("index.plugins.index_state_management.policy_id")
        else:
            has_policy = "policy" in info
            policy_name = info.get("policy")
        
        # Skip unmanaged indices unless show_all is True
        if not has_policy:
            if not show_all:
                continue
            # Add unmanaged index
            size_bytes = stats_data.get("indices", {}).get(index_name, {}).get("total", {}).get("store", {}).get("size_in_bytes", 0)
            results.append({
                "index": index_name,
                "policy": "unmanaged",
                "phase": "-",
                "age": "-",
                "size_bytes": size_bytes,
                "size": format_bytes(size_bytes),
                "warm_at": "",
                "cold_at": "",
                "delete_at": ""
            })
            continue
        
        # Get size
        size_bytes = stats_data.get("indices", {}).get(index_name, {}).get("total", {}).get("store", {}).get("size_in_bytes", 0)
        
        if is_opensearch:
            # OpenSearch ISM - simpler structure
            state_name = info.get("state", {}).get("name", "unknown") if isinstance(info.get("state"), dict) else "unknown"
            result = {
                "index": index_name,
                "policy": policy_name,
                "phase": state_name,  # ISM uses "state" instead of "phase"
                "age": "-",
                "size_bytes": size_bytes,
                "size": format_bytes(size_bytes),
                "warm_at": "",
                "cold_at": "",
                "delete_at": ""
            }
        else:
            # Elasticsearch ILM - full lifecycle processing
            policy = policies.get(policy_name, {}).get("policy", {})
            phases = policy.get("phases", {})
            
            result = {
                "index": index_name,
                "policy": policy_name,
                "phase": info.get("phase", "unknown"),
                "age": info.get("age", "unknown"),
                "size_bytes": size_bytes,
                "size": format_bytes(size_bytes),
                "warm_at": "",
                "cold_at": "",
                "delete_at": ""
            }
            
            # Calculate when transitions happen using lifecycle_date_millis
            lifecycle_date = info.get("lifecycle_date_millis")
            if lifecycle_date:
                created = datetime.fromtimestamp(int(lifecycle_date) / 1000)
                
                for phase_name in ["warm", "cold", "delete"]:
                    if phase_name in phases:
                        min_age = phases[phase_name].get("min_age", "0d")
                    days = parse_age_to_days(min_age)
                    transition_date = created + timedelta(days=days)
                    result[f"{phase_name}_at"] = transition_date.strftime("%Y-%m-%d")
        
        results.append(result)
    
    # Sort by size descending
    results.sort(key=lambda x: x["size_bytes"], reverse=True)
    
    return results


def print_table(results):
    """Print results as a formatted table."""
    if not results:
        print("No indices with ILM policies found")
        return
    
    # Define columns
    headers = ["Index", "Size", "Policy", "Phase", "Age", "Warm At", "Cold At", "Delete At"]
    
    # Calculate column widths
    col_widths = [len(h) for h in headers]
    for r in results:
        col_widths[0] = max(col_widths[0], len(r["index"]))
        col_widths[1] = max(col_widths[1], len(r["size"]))
        col_widths[2] = max(col_widths[2], len(r["policy"]))
        col_widths[3] = max(col_widths[3], len(r["phase"]))
        col_widths[4] = max(col_widths[4], len(r["age"]))
        col_widths[5] = max(col_widths[5], len(r["warm_at"] or "-"))
        col_widths[6] = max(col_widths[6], len(r["cold_at"] or "-"))
        col_widths[7] = max(col_widths[7], len(r["delete_at"] or "-"))
    
    # Print header
    header_row = "  ".join(h.ljust(w) for h, w in zip(headers, col_widths))
    print(header_row)
    print("-" * len(header_row))
    
    # Print rows
    for r in results:
        phase = r["phase"]
        color = COLORS.get(phase, "")
        reset = COLORS["reset"] if color else ""
        
        row = [
            f"{color}{r['index'].ljust(col_widths[0])}{reset}",
            f"{color}{r['size'].ljust(col_widths[1])}{reset}",
            f"{color}{r['policy'].ljust(col_widths[2])}{reset}",
            f"{color}{r['phase'].ljust(col_widths[3])}{reset}",
            f"{color}{r['age'].ljust(col_widths[4])}{reset}",
            f"{color}{(r['warm_at'] or '-').ljust(col_widths[5])}{reset}",
            f"{color}{(r['cold_at'] or '-').ljust(col_widths[6])}{reset}",
            f"{color}{(r['delete_at'] or '-').ljust(col_widths[7])}{reset}"
        ]
        print("  ".join(row))


def list_dashboards(config, target=None, obj_type=None):
    """List dashboards and visualizations from OpenSearch Dashboards."""
    from .cli import get_server
    
    server, _ = get_server(config, target)
    base_url = f"{server['protocol']}://{server['host']}"
    
    # Query saved objects
    resp = requests.get(f"{base_url}/.kibana/_search?size=1000")
    if resp.status_code != 200:
        return {"error": f"Failed to fetch saved objects: {resp.status_code}"}
    
    data = resp.json()
    results = []
    
    for hit in data['hits']['hits']:
        source = hit['_source']
        hit_type = source.get('type', 'unknown')
        
        # Filter by type if specified
        if obj_type and hit_type != obj_type:
            continue
        
        # Only show dashboards and visualizations
        if hit_type not in ['dashboard', 'visualization']:
            continue
        
        obj_data = source.get(hit_type, {})
        title = obj_data.get('title', 'N/A')
        obj_id = hit['_id']
        
        results.append({
            'type': hit_type,
            'id': obj_id,
            'title': title
        })
    
    return results


def list_index_patterns(config, target=None):
    """List all index patterns from .kibana index."""
    from .cli import get_server
    
    server, _ = get_server(config, target)
    base_url = f"{server['protocol']}://{server['host']}"
    
    resp = requests.get(f"{base_url}/.kibana/_search?size=1000")
    if resp.status_code != 200:
        return {"error": f"Failed to fetch saved objects: {resp.status_code}"}
    
    data = resp.json()
    results = []
    
    for hit in data['hits']['hits']:
        source = hit['_source']
        hit_type = source.get('type', 'unknown')
        
        # Only show index-patterns
        if hit_type != 'index-pattern':
            continue
        
        obj_data = source.get('index-pattern', {})
        title = obj_data.get('title', 'N/A')
        obj_id = hit['_id']
        
        results.append({
            'id': obj_id,
            'title': title
        })
    
    return results


def print_saved_objects(results):
    """Print saved objects (dashboards/visualizations) as a table."""
    if not results:
        print("No objects found")
        return
    
    # Calculate column widths
    type_width = max(len(r['type']) for r in results) if results else 4
    type_width = max(type_width, len('Type'))
    id_width = max(len(r['id']) for r in results) if results else 2
    id_width = max(id_width, len('ID'))
    title_width = max(len(r['title']) for r in results) if results else 5
    title_width = max(title_width, len('Title'))
    
    # Print header
    header = f"{'Type'.ljust(type_width)}  {'ID'.ljust(id_width)}  {'Title'.ljust(title_width)}"
    print(header)
    print("-" * len(header))
    
    # Print rows
    for r in results:
        print(f"{r['type'].ljust(type_width)}  {r['id'].ljust(id_width)}  {r['title'].ljust(title_width)}")


def print_index_patterns(results):
    """Print index patterns as a table."""
    if not results:
        print("No index patterns found")
        return
    
    # Calculate column widths
    id_width = max(len(r['id']) for r in results) if results else 2
    id_width = max(id_width, len('ID'))
    title_width = max(len(r['title']) for r in results) if results else 5
    title_width = max(title_width, len('Title'))
    
    # Print header
    header = f"{'ID'.ljust(id_width)}  {'Title'.ljust(title_width)}"
    print(header)
    print("-" * len(header))
    
    # Print rows
    for r in results:
        print(f"{r['id'].ljust(id_width)}  {r['title'].ljust(title_width)}")


def export_saved_objects(config, target=None, obj_ids=None, obj_type=None):
    """Export saved objects (dashboards/visualizations) to ndjson format with index-pattern mapping."""
    from .cli import get_server
    
    server, _ = get_server(config, target)
    base_url = f"{server['protocol']}://{server['host']}"
    
    # Query saved objects
    resp = requests.get(f"{base_url}/.kibana/_search?size=1000")
    if resp.status_code != 200:
        return {"error": f"Failed to fetch saved objects: {resp.status_code}"}
    
    data = resp.json()
    
    # Build index-pattern mapping (ID -> title/name)
    index_pattern_map = {}
    for hit in data['hits']['hits']:
        source = hit['_source']
        if source.get('type') == 'index-pattern':
            full_id = hit['_id']
            obj_id = full_id.split(':', 1)[1] if ':' in full_id else full_id
            title = source.get('index-pattern', {}).get('title')
            if title:
                index_pattern_map[obj_id] = title
    
    ndjson_lines = []
    
    # Add index-pattern mapping as first line (metadata)
    ndjson_lines.append(json.dumps({"_index_pattern_map": index_pattern_map}))
    
    for hit in data['hits']['hits']:
        source = hit['_source']
        hit_type = source.get('type', 'unknown')
        full_id = hit['_id']
        
        # Extract ID (remove type prefix like "dashboard:")
        obj_id = full_id.split(':', 1)[1] if ':' in full_id else full_id
        
        # Filter by type if specified
        if obj_type and hit_type != obj_type:
            continue
        
        # Filter by IDs if specified
        if obj_ids and obj_id not in obj_ids:
            continue
        
        # Only export dashboards and visualizations
        if hit_type not in ['dashboard', 'visualization']:
            continue
        
        # Build export object in ndjson format
        obj = {
            'id': obj_id,
            'type': hit_type,
            'attributes': source[hit_type]
        }
        
        # Sanitize: remove filters and queries from searchSourceJSON
        if 'kibanaSavedObjectMeta' in obj['attributes']:
            meta = obj['attributes']['kibanaSavedObjectMeta']
            if 'searchSourceJSON' in meta:
                try:
                    search_source = json.loads(meta['searchSourceJSON'])
                    # Remove query and filter
                    if 'query' in search_source:
                        # Keep the structure but clear the query string
                        if isinstance(search_source['query'], dict):
                            search_source['query']['query'] = ''
                    if 'filter' in search_source:
                        search_source['filter'] = []
                    meta['searchSourceJSON'] = json.dumps(search_source)
                except:
                    pass
        
        # Include references if present (preserves index-pattern IDs)
        if 'references' in source:
            obj['references'] = source['references']
        
        ndjson_lines.append(json.dumps(obj))
    
    return '\n'.join(ndjson_lines)


def import_saved_objects(config, ndjson_content, target=None):
    """Import saved objects from ndjson directly to .kibana index."""
    from .cli import get_server
    
    server, _ = get_server(config, target)
    base_url = f"{server['protocol']}://{server['host']}"
    
    lines = ndjson_content.strip().split('\n')
    
    imported = []
    skipped = []
    
    for line in lines:
        if not line.strip():
            continue
        
        obj = json.loads(line)
        
        # Skip metadata lines
        if '_index_pattern_map' in obj:
            continue
        
        # Build document for .kibana index
        doc = {
            obj['type']: obj['attributes'],
            'type': obj['type']
        }
        if 'references' in obj:
            doc['references'] = obj['references']
        
        # Import by writing directly to .kibana index
        import_resp = requests.put(
            f"{base_url}/.kibana/_doc/{obj['type']}:{obj['id']}",
            headers={"Content-Type": "application/json"},
            json=doc
        )
        
        imported.append({
            'id': obj['id'],
            'type': obj['type'],
            'title': obj.get('attributes', {}).get('title', 'N/A'),
            'status': import_resp.status_code,
            'success': import_resp.status_code in [200, 201]
        })
    
    return {'imported': imported, 'skipped': skipped}
