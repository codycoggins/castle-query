# Qdrant Query Tool Usage Guide

This command line tool allows you to query the Qdrant database containing Gmail email embeddings and return all columns/fields from the stored data.

## Prerequisites

- Qdrant server running (default: localhost:6333)
- Python dependencies installed (qdrant-client, sentence-transformers)

## Basic Usage

### List all collections
```bash
poetry run python src/query_qdrant.py --list-collections
```

### Get collection information
```bash
poetry run python src/query_qdrant.py --collection-info
```

### Query all points (returns all columns)
```bash
# Query first 10 points
poetry run python src/query_qdrant.py --query-all --limit 10

# Query with pagination
poetry run python src/query_qdrant.py --query-all --limit 50 --offset 100
```

### Filter results
```bash
# Filter by subject
poetry run python src/query_qdrant.py --query-all --filter-subject "meeting"

# Filter by sender
poetry run python src/query_qdrant.py --query-all --filter-sender "john@example.com"

# Combine filters
poetry run python src/query_qdrant.py --query-all --filter-subject "meeting" --filter-sender "john@example.com"

# Filter by URL
poetry run python src/query_qdrant.py --query-all --filter-url "mail.google.com"

# Filter by Gmail category
poetry run python src/query_qdrant.py --query-all --filter-category "Primary" --limit 10
```

### Output formats

#### Table format (default)
```bash
poetry run python src/query_qdrant.py --query-all --limit 5
```

#### JSON format
```bash
poetry run python src/query_qdrant.py --query-all --limit 5 --output-format json
```

#### CSV format
```bash
poetry run python src/query_qdrant.py --query-all --limit 5 --output-format csv
```

### Semantic search
```bash
# Search for similar documents
poetry run python src/query_qdrant.py --search-similar "project update meeting" --limit 5
```

### Custom Qdrant connection
```bash
# Use different host/port
poetry run python src/query_qdrant.py --host 192.168.1.100 --port 6334 --query-all
```

## Available Fields

The tool returns all columns from the stored email data, which typically includes:

- `id`: Email message ID
- `thread_id`: Gmail thread ID
- `subject`: Email subject
- `sender`: Email sender address
- `to`: Email recipient(s)
- `date`: Email date
- `text`: Full email text content (including subject, headers, and body)
- `url`: Direct link to the email in Gmail
- `category`: Gmail category (Primary, Updates, Social, Promotions, Forums)

## Examples

### Get a quick overview of your email collection
```bash
poetry run python src/query_qdrant.py --collection-info
```

### Export recent emails to CSV
```bash
poetry run python src/query_qdrant.py --query-all --limit 100 --output-format csv > emails.csv
```

### Find emails about a specific topic
```bash
poetry run python src/query_qdrant.py --search-similar "quarterly report" --limit 10
```

### Get all emails from a specific sender
```bash
poetry run python src/query_qdrant.py --query-all --filter-sender "boss@company.com" --limit 50
```

### Get emails with specific URL pattern
```bash
poetry run python src/query_qdrant.py --query-all --filter-url "mail.google.com" --limit 10
```

### Get emails from specific Gmail category
```bash
poetry run python src/query_qdrant.py --query-all --filter-category "Updates" --limit 20
```

## Help

For full command line options:
```bash
poetry run python src/query_qdrant.py --help
```
