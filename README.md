# *search Observer

Comprehensive CLI tool for managing Elasticsearch/OpenSearch clusters and OpenSearch Dashboards.

## Features

- 🔍 **Query Execution**: Run queries directly against Elasticsearch/OpenSearch clusters
- 📦 **Saved Object Management**: Manage all saved objects (dashboards, visualizations, searches) collectively
- 📊 **Dashboard Management**: List, export, import, and delete dashboards
- 📈 **Visualization Management**: Manage visualizations independently
- 🔎 **Saved Search Management**: Manage saved searches
- 🗂️ **Index Lifecycle Management**: Configure ILM/ISM policies
- 🔧 **Index Operations**: Delete indices and manage index patterns
- 🔐 **Authentication**: Basic Auth support with configurable SSL verification
- 🎯 **Multi-Server Support**: Manage multiple clusters from one config

## Installation

```bash
git clone https://github.com/mconcas/starsearch-manager
cd starsearch-manager
pip install -e .
```

## Configuration

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

### Configuration Options

- `name`: Identifier for the server (used with `--target`)
- `host`: Server hostname and port
- `protocol`: `http` or `https`
- `username`/`password`: Basic authentication credentials (optional)
- `verify_ssl`: Set to `false` to disable SSL certificate verification (optional)
- `cluster_path`: Path prefix for cluster API access, e.g., `/os` (optional)
- `base_path`: Path prefix for Dashboards API access, e.g., `/dashboards` (optional)

## Usage

### Basic Queries

Execute queries directly against the cluster:

```bash
# Use default server (first in config)
observe-cli _cluster/health

# Target specific server
observe-cli --target prod-os _cat/indices

# POST requests with JSON data
observe-cli _search -d '{"query": {"match_all": {}}}'
```

### Saved Object Management

Manage all saved objects (dashboards, visualizations, searches) at once:

```bash
# List all saved objects
observe-cli saved-object list

# Export all saved objects to NDJSON
observe-cli saved-object export > all-objects.ndjson

# Export specific objects by ID
observe-cli saved-object export obj-id1 obj-id2 > objects.ndjson

# Export as JSON array instead of NDJSON
observe-cli saved-object export --json > objects.json

# Export to individual files (one per object)
observe-cli saved-object export --to-file

# Export to individual JSON files
observe-cli saved-object export --to-file --json

# Import saved objects from NDJSON file
observe-cli saved-object import objects.ndjson
```

### Dashboard Management

Manage dashboards separately from other objects:

```bash
# List all dashboards
observe-cli dashboard list

# Export specific dashboard(s) to NDJSON
observe-cli dashboard export dashboard-id1 dashboard-id2 > dashboards.ndjson

# Export all dashboards
observe-cli dashboard export > all-dashboards.ndjson

# Export as JSON array instead of NDJSON
observe-cli dashboard export --json > dashboards.json

# Export to individual files (one per dashboard)
observe-cli dashboard export --to-file

# Export specific dashboards to individual JSON files
observe-cli dashboard export dashboard-id1 dashboard-id2 --to-file --json

# Import dashboards from NDJSON file
observe-cli dashboard import dashboards.ndjson

# Delete a dashboard
observe-cli dashboard delete dashboard-id
```

### Visualization Management

Manage visualizations independently:

```bash
# List all visualizations
observe-cli visualization list

# Export specific visualization(s)
observe-cli visualization export vis-id1 vis-id2 > visualizations.ndjson

# Export as JSON array instead of NDJSON
observe-cli visualization export --json > visualizations.json

# Export to individual files (one per visualization)
observe-cli visualization export --to-file

# Export to individual JSON files
observe-cli visualization export --to-file --json

# Import visualizations
observe-cli visualization import visualizations.ndjson

# Delete a visualization
observe-cli visualization delete vis-id
```

### Saved Search Management

Manage saved searches:

```bash
# List all saved searches
observe-cli search list

# Export saved searches
observe-cli search export > searches.ndjson

# Export as JSON array instead of NDJSON
observe-cli search export --json > searches.json

# Export specific search(es)
observe-cli search export search-id1 search-id2 > searches.ndjson

# Export to individual files (one per search)
observe-cli search export --to-file

# Export to individual JSON files
observe-cli search export --to-file --json

# Import searches
observe-cli search import searches.ndjson

# Delete a saved search
observe-cli search delete search-id
```

### Index Lifecycle Management (ILM/ISM)

Configure lifecycle policies for index management:

```bash
# Show ILM policy info for all indices
observe-cli ilm info

# Show detailed policy info including all indices
observe-cli ilm info --all

# Set delete phase (delete after N days)
observe-cli ilm my-policy set delete-after 30

# Set warm phase (move to warm after N days)
observe-cli ilm my-policy set warm-after 7

# Set cold phase (move to cold after N days)
observe-cli ilm my-policy set cold-after 14

# Set rollover thresholds (size and document count)
observe-cli ilm my-policy set rollover 50gb 1000000
```

### Index Operations

```bash
# Delete an index
observe-cli index delete my-index-name
```

### Index Pattern Management

```bash
# List all index patterns
observe-cli index-pattern list

# Delete an index pattern
observe-cli index-pattern delete pattern-id
```

### Multi-Server Usage

Use the `--target` flag to specify which server to use:

```bash
# Query production server
observe-cli --target prod-os _cluster/health

# List dashboards on staging server
observe-cli --target staging dashboard list

# Export from one server and import to another
observe-cli --target prod dashboard export dash-id > prod-dashboard.ndjson
observe-cli --target staging dashboard import prod-dashboard.ndjson
```

### Version Information

```bash
observe-cli --version
observe-cli -v
```

## Output Format

- Queries return pretty-printed JSON
- List commands display formatted tables
- Export commands generate NDJSON (newline-delimited JSON)
- Error messages are returned as JSON with `"error"` key

## Examples

### Backup All Dashboards

```bash
observe-cli --target prod dashboard export > backup-dashboards.ndjson
observe-cli --target prod visualization export > backup-visualizations.ndjson
observe-cli --target prod search export > backup-searches.ndjson
```

### Migrate Dashboards Between Clusters

```bash
# Export from production
observe-cli --target prod dashboard export > dashboards.ndjson

# Import to staging
observe-cli --target staging dashboard import dashboards.ndjson
```

### Clean Up Old Indices with ILM

```bash
# Configure policy to delete indices after 90 days
observe-cli --target prod ilm logs-policy set delete-after 90

# Move to warm storage after 30 days
observe-cli --target prod ilm logs-policy set warm-after 30
```

## API Support

The tool supports both:
- **Dashboards API**: Modern OpenSearch Dashboards API (automatic detection)
- **Direct .kibana access**: Fallback for older versions or when Dashboards API is unavailable

The appropriate API is selected automatically based on server configuration.

## Development

```bash
# Clone the repository
git clone <repo-url>
cd starsearch-observer

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install in editable mode
pip install -e .

# Run tests
observe-cli --version
```

## License

MIT
