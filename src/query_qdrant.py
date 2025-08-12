#!/usr/bin/env python3
"""
Command line tool to query the Qdrant database containing Gmail email embeddings.
Returns all columns/fields from the stored email data.
"""

import argparse
import json
import sys
from typing import Optional

from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, MatchValue

COLLECTION_NAME = "gmail_embeddings_full"


def connect_to_qdrant(host: str = "localhost", port: int = 6333) -> QdrantClient:
    """Connect to Qdrant database."""
    try:
        client = QdrantClient(host=host, port=port)
        # Test connection
        client.get_collections()
        return client
    except Exception as e:
        print(f"Error connecting to Qdrant at {host}:{port}: {e}")
        sys.exit(1)


def list_collections(client: QdrantClient) -> None:
    """List all available collections."""
    try:
        collections = client.get_collections()
        print("Available collections:")
        for collection in collections.collections:
            print(f"  - {collection.name}")
    except Exception as e:
        print(f"Error listing collections: {e}")
        sys.exit(1)


def get_collection_info(client: QdrantClient, collection_name: str) -> None:
    """Get information about a specific collection."""
    try:
        info = client.get_collection(collection_name)
        print(f"Collection: {collection_name}")
        print(f"  Points count: {info.points_count}")
        print(f"  Vector size: {info.config.params.vectors.size}")
        print(f"  Distance: {info.config.params.vectors.distance}")
    except Exception as e:
        print(f"Error getting collection info: {e}")
        sys.exit(1)


def query_all_points(
    client: QdrantClient,
    collection_name: str,
    limit: int = 100,
    offset: int = 0,
    filter_subject: Optional[str] = None,
    filter_sender: Optional[str] = None,
    filter_url: Optional[str] = None,
    filter_category: Optional[str] = None,
    output_format: str = "table",
) -> None:
    """Query all points from the collection and return all columns."""
    try:
        # Build filter if specified
        filter_conditions = []
        if filter_subject:
            filter_conditions.append(FieldCondition(key="subject", match=MatchValue(value=filter_subject)))
        if filter_sender:
            filter_conditions.append(FieldCondition(key="sender", match=MatchValue(value=filter_sender)))
        if filter_url:
            filter_conditions.append(FieldCondition(key="url", match=MatchValue(value=filter_url)))
        if filter_category:
            filter_conditions.append(FieldCondition(key="category", match=MatchValue(value=filter_category)))

        # Build filter conditions for Python-side filtering

        # Query points - use scroll without filter first, then filter in Python if needed
        points = client.scroll(
            collection_name=collection_name,
            limit=limit,
            offset=offset,
            with_payload=True,
            with_vectors=False,  # Don't include vectors to reduce output size
        )[0]

        # Apply filters in Python if specified
        if filter_conditions:
            filtered_points = []
            for point in points:
                matches = True
                for condition in filter_conditions:
                    key = condition.key
                    expected_value = condition.match.value
                    actual_value = point.payload.get(key, "")

                    # Simple string matching (case-insensitive)
                    if isinstance(actual_value, str) and isinstance(expected_value, str):
                        if expected_value.lower() not in actual_value.lower():
                            matches = False
                            break
                    else:
                        if actual_value != expected_value:
                            matches = False
                            break

                if matches:
                    filtered_points.append(point)

            points = filtered_points

        if not points:
            print("No points found in the collection.")
            return

        print(f"Found {len(points)} points (limit: {limit}, offset: {offset})")
        print("-" * 80)

        if output_format == "json":
            # Output as JSON
            results = []
            for point in points:
                result = {"id": point.id, "payload": point.payload}
                results.append(result)
            print(json.dumps(results, indent=2, default=str))

        elif output_format == "table":
            # Output as formatted table
            for i, point in enumerate(points, 1):
                print(f"Point {i} (ID: {point.id}):")
                payload = point.payload

                # Print all available fields
                for key, value in payload.items():
                    if isinstance(value, str) and len(value) > 200:
                        # Truncate long text fields
                        display_value = value[:200] + "..."
                    else:
                        display_value = value
                    print(f"  {key}: {display_value}")
                print("-" * 40)

        elif output_format == "csv":
            # Output as CSV
            if points:
                # Get all unique keys from all payloads
                all_keys = set()
                for point in points:
                    all_keys.update(point.payload.keys())

                # Sort keys for consistent output
                sorted_keys = sorted(all_keys)

                # Print header
                print("id," + ",".join(f'"{key}"' for key in sorted_keys))

                # Print data rows
                for point in points:
                    row = [str(point.id)]
                    for key in sorted_keys:
                        value = point.payload.get(key, "")
                        # Escape quotes and wrap in quotes
                        if isinstance(value, str):
                            value = value.replace('"', '""')
                            row.append(f'"{value}"')
                        else:
                            row.append(f'"{str(value)}"')
                    print(",".join(row))

    except Exception as e:
        print(f"Error querying collection: {e}")
        sys.exit(1)


def search_similar(
    client: QdrantClient, collection_name: str, query_text: str, limit: int = 10, output_format: str = "table"
) -> None:
    """Search for similar documents using vector similarity."""
    try:
        from sentence_transformers import SentenceTransformer

        # Load the same model used for indexing
        model = SentenceTransformer("all-MiniLM-L6-v2")

        # Encode the query text
        query_vector = model.encode(query_text).tolist()

        # Search in Qdrant
        results = client.query_points(
            collection_name=collection_name,
            query=query_vector,
            limit=limit,
            with_payload=True,
            with_vectors=False,
        )

        if not results.points:
            print("No similar documents found.")
            return

        print(f"Found {len(results.points)} similar documents for query: '{query_text}'")
        print("-" * 80)

        if output_format == "json":
            # Output as JSON
            results_data = []
            for result in results.points:
                result_data = {"id": result.id, "score": result.score, "payload": result.payload}
                results_data.append(result_data)
            print(json.dumps(results_data, indent=2, default=str))

        elif output_format == "table":
            # Output as formatted table
            for i, result in enumerate(results.points, 1):
                print(f"Result {i} (ID: {result.id}, Score: {result.score:.4f}):")
                payload = result.payload

                # Print all available fields
                for key, value in payload.items():
                    if isinstance(value, str) and len(value) > 200:
                        # Truncate long text fields
                        display_value = value[:200] + "..."
                    else:
                        display_value = value
                    print(f"  {key}: {display_value}")
                print("-" * 40)

    except ImportError:
        print(
            "Error: sentence-transformers not installed. " "Install with: pip install sentence-transformers"
        )
        sys.exit(1)
    except Exception as e:
        print(f"Error searching similar documents: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Query Qdrant database containing Gmail email embeddings",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all collections
  python query_qdrant.py --list-collections

  # Get collection info
  python query_qdrant.py --collection-info

  # Query all points (first 10)
  python query_qdrant.py --query-all --limit 10

  # Query with filters
  python query_qdrant.py --query-all --filter-subject "meeting" \
    --filter-sender "john@example.com"

  # Filter by URL
  python query_qdrant.py --query-all --filter-url "mail.google.com"

  # Filter by Gmail category
  python query_qdrant.py --query-all --filter-category "Updates"

  # Output as JSON
  python query_qdrant.py --query-all --output-format json

  # Search similar documents
  python query_qdrant.py --search-similar "project update meeting" --limit 5

  # Use different Qdrant host/port
  python query_qdrant.py --host 192.168.1.100 --port 6334 --query-all
        """,
    )

    # Connection options
    parser.add_argument("--host", default="localhost", help="Qdrant host (default: localhost)")
    parser.add_argument("--port", type=int, default=6333, help="Qdrant port (default: 6333)")
    parser.add_argument(
        "--collection", default=COLLECTION_NAME, help=f"Collection name (default: {COLLECTION_NAME})"
    )

    # Action options
    parser.add_argument("--list-collections", action="store_true", help="List all available collections")
    parser.add_argument("--collection-info", action="store_true", help="Show collection information")
    parser.add_argument("--query-all", action="store_true", help="Query all points in the collection")
    parser.add_argument("--search-similar", metavar="QUERY", help="Search for similar documents")

    # Query options
    parser.add_argument("--limit", type=int, default=100, help="Limit number of results (default: 100)")
    parser.add_argument("--offset", type=int, default=0, help="Offset for pagination (default: 0)")
    parser.add_argument("--filter-subject", help="Filter by email subject")
    parser.add_argument("--filter-sender", help="Filter by email sender")
    parser.add_argument("--filter-url", help="Filter by email URL")
    parser.add_argument(
        "--filter-category", help="Filter by Gmail category (Primary, Updates, Social, Promotions, Forums)"
    )
    parser.add_argument(
        "--output-format",
        choices=["table", "json", "csv"],
        default="table",
        help="Output format (default: table)",
    )

    args = parser.parse_args()

    # Connect to Qdrant
    client = connect_to_qdrant(args.host, args.port)

    # Execute requested action
    if args.list_collections:
        list_collections(client)
    elif args.collection_info:
        get_collection_info(client, args.collection)
    elif args.query_all:
        query_all_points(
            client,
            args.collection,
            limit=args.limit,
            offset=args.offset,
            filter_subject=args.filter_subject,
            filter_sender=args.filter_sender,
            filter_url=args.filter_url,
            filter_category=args.filter_category,
            output_format=args.output_format,
        )
    elif args.search_similar:
        search_similar(
            client, args.collection, args.search_similar, limit=args.limit, output_format=args.output_format
        )
    else:
        # Default action: show collection info
        get_collection_info(client, args.collection)
        print("\nUse --help for more options.")


if __name__ == "__main__":
    main()
