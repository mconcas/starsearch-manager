# StarSearch Observer

Comprehensive CLI tool for managing Elasticsearch/OpenSearch clusters and OpenSearch Dashboards.

## Setup

Create `~/.starsearch/config.json` with your cluster details:

```json
{
  "servers": [
    {
      "name": "local-es",
      "host": "localhost:9200",
      "protocol": "http"
    },
    {
      "name": "prod-os",
      "host": "opensearch.example.com",
      "protocol": "https",
      "username": "admin",
      "password": "your-password",
      "verify_ssl": false,
      "cluster_path": "/os",
      "base_path": "/dashboards"
    }
  ]
}
```

Configuration options:
- `cluster_path`: Path prefix for OpenSearch/Elasticsearch cluster API (e.g., `/os`)
- `base_path`: Path prefix for OpenSearch Dashboards API (e.g., `/dashboards`)
- `verify_ssl`: Set to `false` to disable SSL certificate verification
- `username`/`password`: Basic authentication credentials

Install:

```bash
pip install -e .
```

## Usage

### Basic Queries

```bash
observe-cli _cluster/health              # uses first server (default)
observe-cli --target prod-os _cat/indices
```

### ILM/ISM Management

```bash
observe-cli ilm info [--all]                         # Show ILM policy info
observe-cli ilm my-policy set delete-after 30        # Set delete phase
observe-cli ilm my-policy set warm-after 7           # Set warm phase
observe-cli ilm my-policy set rollover 50gb 1000000  # Set rollover thresholds
```

### Index Operations

```bash
observe-cli index delete my-index                    # Delete an index
```

### Index Patterns

```bash
observe-cli index-pattern list                       # List all index patterns
observe-cli index-pattern delete pattern-id          # Delete an index pattern
```

### Dashboard Management

```bash
observe-cli dashboard list                           # List all dashboards and visualizations
observe-cli dashboard delete dashboard-id            # Delete a dashboard or visualization
observe-cli dashboard export [id1 id2 ...]           # Export to ndjson format
observe-cli dashboard import file.ndjson             # Import from ndjson file
```

### Saved Searches

```bash
observe-cli search list                              # List all saved searches
observe-cli search delete search-id                  # Delete a saved search
```
