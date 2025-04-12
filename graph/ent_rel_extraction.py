import json
import os
from typing import Any, Dict, List, Optional, Tuple

from openai import OpenAI

from utils.load_env import get_env_vars

env = get_env_vars()

api_key = env["OPENAI_API_KEY"]

# Initialize OpenAI client
client = OpenAI(api_key=api_key)


def extract_data_for_neo4j(
    chunk: Dict[str, Any],
    api_key: Optional[str] = None,
    model: str = "gpt-4o-mini",
) -> Dict[str, Any]:
    """
    Extract structured data from a text chunk using OpenAI's LLM for Neo4j import.

    Parameters:
    - chunk (Dict[str, Any]): Text chunk to process with idx and text fields
    - api_key (str, optional): OpenAI API key (defaults to env variable)
    - model (str): OpenAI model to use

    Returns:
    - Dict[str, Any]: Extracted structured data
    """
    chunk_idx = chunk.get("idx", 0)
    chunk_text = chunk.get("text", "")

    # Define the extraction prompt
    prompt = [
        {
            "role": "system",
            "content": """
        You are a specialized data extraction system designed to convert unstructured text into 
        structured data for a Neo4j graph database, with the ultimate goal of providing insights on the market and the entities involved. Extract information with high precision and 
        maintain consistency in entity naming across extractions.
        """,
        },
        {
            "role": "user",
            "content": f"""
        Extract the following structured data from this text chunk:
        
        1. ENTITIES:
           - Named entities ("organization","person","market","product/service","deals/transactions","event","financial/performance metric","trend")
           - Domain-specific entities (technical terms, industry concepts)
           - Include type classification for each entity
           - Extract all relevant attributes as key-value pairs
        
        2. RELATIONSHIPS:
           - Explicit connections between entities
           - Directional relationships with clear source and target
           - Relationship strength: a numeric score (0-10) indicating strength of the relationship between source and target entity.
           - Include relationship types that would work well in Neo4j
           - Add relevant attributes to relationships when present
        
        3. CONTEXT:
           - Key themes that provide context for the graph
        
        Format your response as a valid JSON object with this exact structure:
        {{
            "entities": [
                {{
                    "id": "unique_identifier", 
                    "name": "Entity Name", 
                    "type": "Entity Type", 
                    "attributes": {{"attribute1": "value1", "attribute2": "value2"}},
                    "chunk_idx": {chunk_idx}
                }}
            ],
            "relationships": [
                {{
                    "source_id": "unique_identifier_of_source",
                    "target_id": "unique_identifier_of_target",
                    "type": "RELATIONSHIP_TYPE", 
                    "strength": "numeric_score",
                    "attributes": {{"attribute1": "value1"}},
                    "chunk_idx": {chunk_idx}
                }}
            ],
            "context": {{
                "domain": "domain_name",
                "themes": ["Theme1", "Theme2"]
            }}
        }}
        
        TEXT CHUNK TO ANALYZE:
        {chunk_text}
        
        IMPORTANT GUIDELINES:
        - Ensure each entity has a unique identifier (use snake_case)
        - Use UPPERCASE for relationship types (Neo4j convention)
        - Be comprehensive but precise - extract only what's explicitly in the text
        - For financial values, maintain original units and currency
        - Use standardized formats for dates (DD-MM-YYYY)
        - Ensure the output is valid JSON that can be parsed programmatically
        - Include the chunk index {chunk_idx} in each entity and relationship
        """,
        },
    ]

    # Call the OpenAI API
    try:
        response = client.chat.completions.create(
            model=model,
            messages=prompt,
            temperature=0.1,  # Low temperature for consistency
            response_format={"type": "json_object"},
            max_tokens=2000,
        )

        # Extract the response content
        extracted_data_str = response.choices[0].message.content

        # Parse the JSON response
        extracted_data = json.loads(extracted_data_str)

        # Add chunk_idx to each entity and relationship if not already present
        for entity in extracted_data.get("entities", []):
            if "chunk_idx" not in entity:
                entity["chunk_idx"] = chunk_idx

        for rel in extracted_data.get("relationships", []):
            if "chunk_idx" not in rel:
                rel["chunk_idx"] = chunk_idx

        # Validate the structure
        validate_extraction_structure(extracted_data)

        print(f"✅ Successfully extracted data from chunk {chunk_idx}")
        return extracted_data

    except Exception as e:
        print(f"❌ Error during extraction of chunk {chunk_idx}: {str(e)}")
        # Create an empty structure if extraction fails
        empty_data = {
            "entities": [],
            "relationships": [],
            "context": {"domain": "unknown", "themes": []},
        }

        print(f"⚠️ Created empty structure for chunk {chunk_idx}")
        return empty_data


def validate_extraction_structure(data: Dict[str, Any]) -> bool:
    """
    Validate that the extracted data has the expected structure.

    Parameters:
    - data (Dict[str, Any]): The extracted data to validate

    Returns:
    - bool: True if valid, raises exception otherwise
    """
    # Check for required top-level keys
    required_keys = ["entities", "relationships", "context"]
    for key in required_keys:
        if key not in data:
            raise ValueError(f"Missing required key: {key}")

    # Validate entities
    for i, entity in enumerate(data["entities"]):
        required_entity_keys = ["id", "name", "type", "attributes"]
        for key in required_entity_keys:
            if key not in entity:
                raise ValueError(f"Entity at index {i} missing required key: {key}")

    # Validate relationships
    for i, rel in enumerate(data["relationships"]):
        required_rel_keys = ["source_id", "target_id", "type", "attributes"]
        for key in required_rel_keys:
            if key not in rel:
                raise ValueError(
                    f"Relationship at index {i} missing required key: {key}"
                )

    # Validate context
    if "context" in data:
        required_context_keys = ["domain", "themes"]
        for key in required_context_keys:
            if key not in data["context"]:
                raise ValueError(f"Context missing required key: {key}")

    return True


def merge_attributes(
    existing_attrs: Dict[str, Any], new_attrs: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Smartly merge two attribute dictionaries, preserving information from both.

    Parameters:
    - existing_attrs (Dict[str, Any]): The existing attributes
    - new_attrs (Dict[str, Any]): The new attributes to merge in

    Returns:
    - Dict[str, Any]: The merged attributes
    """
    merged = existing_attrs.copy()

    for key, value in new_attrs.items():
        # If the key doesn't exist in the existing attrs, just add it
        if key not in merged:
            merged[key] = value
            continue

        existing_value = merged[key]

        # If they're the same, continue
        if existing_value == value:
            continue

        # Handle lists: combine them
        if isinstance(existing_value, list) and isinstance(value, list):
            # Create a set to remove duplicates, then convert back to list
            merged[key] = list(set(existing_value + value))

        # Handle numeric values: use the average or the newer one
        elif isinstance(existing_value, (int, float)) and isinstance(
            value, (int, float)
        ):
            # Decide on a strategy: here we'll take the average
            merged[key] = (existing_value + value) / 2

        # For strings and other types, prefer to keep both values
        else:
            # If they're different, store as a list
            if isinstance(existing_value, list):
                if value not in existing_value:
                    merged[key].append(value)
            else:
                merged[key] = [existing_value, value]

    return merged


def get_relationship_key(relationship: Dict[str, Any]) -> Tuple[str, str, str]:
    """
    Create a unique identifier for a relationship based on source, target, and type.

    Parameters:
    - relationship (Dict[str, Any]): The relationship to get a key for

    Returns:
    - Tuple[str, str, str]: A tuple representing (source_id, target_id, type)
    """
    return (relationship["source_id"], relationship["target_id"], relationship["type"])


def process_multiple_chunks(
    chunks: List[Dict[str, Any]],
    output_dir: str = "data/graph",
    output_filename: str = "neo4j_data.json",
) -> str:
    """
    Process multiple text chunks and save results to a single JSON file,
    updating the file after each chunk is processed to ensure data persistence.

    Parameters:
    - chunks (List[Dict[str, Any]]): List of text chunks to process with idx and text fields
    - output_dir (str): Directory to save the combined JSON file
    - output_filename (str): Name of the output file

    Returns:
    - str: Path to the combined JSON file
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Path to the combined output file
    output_file_path = os.path.join(output_dir, output_filename)

    # Initialize the data structure for the combined file
    all_data = {
        "entities": {},  # Use dict to deduplicate entities by ID
        "relationships": {},  # Use dict to deduplicate relationships
        "context": {
            "domain": "",
            "themes": set(),  # Use set to deduplicate themes
        },
    }

    # Check if the output file already exists (for recovery purposes)
    if os.path.exists(output_file_path):
        try:
            with open(output_file_path, "r", encoding="utf-8") as f:
                existing_data = json.load(f)

            # Convert existing data format back to our working format
            if "entities" in existing_data and isinstance(
                existing_data["entities"], list
            ):
                all_data["entities"] = {
                    entity["id"]: entity for entity in existing_data["entities"]
                }

            if "relationships" in existing_data and isinstance(
                existing_data["relationships"], list
            ):
                for rel in existing_data["relationships"]:
                    rel_key = get_relationship_key(rel)
                    all_data["relationships"][rel_key] = rel

            if "context" in existing_data:
                all_data["context"]["domain"] = existing_data["context"].get(
                    "domain", ""
                )
                all_data["context"]["themes"] = set(
                    existing_data["context"].get("themes", [])
                )

            print(f"📂 Loaded existing data from {output_file_path} for continuation")

        except Exception as e:
            print(f"⚠️ Could not load existing file {output_file_path}: {str(e)}")
            print("Starting with fresh data structure")

    total_chunks = len(chunks)

    # Process each chunk
    for i, chunk in enumerate(chunks):
        print(
            f"Processing chunk {i + 1}/{total_chunks} (idx: {chunk.get('idx', 'unknown')})"
        )

        # Extract data from the chunk
        chunk_data = extract_data_for_neo4j(chunk)

        # Smartly merge entities
        for entity in chunk_data["entities"]:
            entity_id = entity["id"]

            if entity_id in all_data["entities"]:
                # Entity exists, merge attributes instead of overwriting
                existing_entity = all_data["entities"][entity_id]

                # Merge attributes
                merged_attrs = merge_attributes(
                    existing_entity["attributes"], entity["attributes"]
                )
                existing_entity["attributes"] = merged_attrs

                # Add the chunk_idx to a list of chunk indexes this entity appears in
                if "chunk_indices" not in existing_entity:
                    existing_entity["chunk_indices"] = [
                        existing_entity.get("chunk_idx", 0)
                    ]

                chunk_idx = entity.get("chunk_idx", i)
                if chunk_idx not in existing_entity["chunk_indices"]:
                    existing_entity["chunk_indices"].append(chunk_idx)
            else:
                # New entity, just add it
                if "chunk_indices" not in entity:
                    entity["chunk_indices"] = [entity.get("chunk_idx", i)]
                all_data["entities"][entity_id] = entity

        # Deduplicate relationships while preserving all information
        for rel in chunk_data["relationships"]:
            rel_key = get_relationship_key(rel)

            if rel_key in all_data["relationships"]:
                # Relationship exists, merge attributes
                existing_rel = all_data["relationships"][rel_key]

                # Merge attributes
                merged_attrs = merge_attributes(
                    existing_rel["attributes"], rel["attributes"]
                )
                existing_rel["attributes"] = merged_attrs

                # Update strength if needed (choose the higher value)
                if "strength" in rel and (
                    "strength" not in existing_rel
                    or float(rel["strength"]) > float(existing_rel["strength"])
                ):
                    existing_rel["strength"] = rel["strength"]

                # Track chunk indices
                if "chunk_indices" not in existing_rel:
                    existing_rel["chunk_indices"] = [existing_rel.get("chunk_idx", 0)]

                chunk_idx = rel.get("chunk_idx", i)
                if chunk_idx not in existing_rel["chunk_indices"]:
                    existing_rel["chunk_indices"].append(chunk_idx)
            else:
                # New relationship, just add it
                if "chunk_indices" not in rel:
                    rel["chunk_indices"] = [rel.get("chunk_idx", i)]
                all_data["relationships"][rel_key] = rel

        # Merge context
        if (
            not all_data["context"]["domain"]
            and chunk_data["context"].get("domain")
            and chunk_data["context"]["domain"] != "unknown"
        ):
            all_data["context"]["domain"] = chunk_data["context"]["domain"]

        # Add themes to set for deduplication
        if "themes" in chunk_data["context"]:
            all_data["context"]["themes"].update(chunk_data["context"]["themes"])

        # Convert back to expected format for file output
        combined_data = {
            "entities": list(all_data["entities"].values()),
            "relationships": list(all_data["relationships"].values()),
            "context": {
                "domain": all_data["context"]["domain"],
                "themes": list(all_data["context"]["themes"]),
            },
        }

        # Save the updated combined data after each chunk
        with open(output_file_path, "w", encoding="utf-8") as json_file:
            json.dump(combined_data, json_file, indent=2, ensure_ascii=False)

        print(
            f"💾 Updated combined data file after processing chunk {i + 1}/{total_chunks}"
        )

    # Final output stats
    print(
        f"📊 Final combined data from {len(chunks)} chunks saved to {output_file_path}"
    )
    print(f"   - Total entities: {len(all_data['entities'])}")
    print(f"   - Total relationships: {len(all_data['relationships'])}")
    print(f"   - Total themes: {len(all_data['context']['themes'])}")

    return output_file_path


def process_enhanced_chunks(
    input_file: str = "data/enhanced/enhanced_chunks.json",
    output_dir: str = "data/graph",
    output_filename: str = "neo4j_data.json",
) -> str:
    """
    Process enhanced chunks from a JSON file and generate Neo4j graph data.

    Parameters:
    - input_file (str): Path to the enhanced chunks JSON file
    - output_dir (str): Directory to save the extracted data
    - output_filename (str): Name of the output file

    Returns:
    - str: Path to the combined output file
    """
    # Load enhanced chunks
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            chunks = json.load(f)

        print(f"Loaded {len(chunks)} chunks from {input_file}")

        # Process the chunks
        result_path = process_multiple_chunks(chunks, output_dir, output_filename)
        return result_path

    except Exception as e:
        print(f"❌ Error processing enhanced chunks: {str(e)}")
        raise


# Example usage
if __name__ == "__main__":
    # Example usage with enhanced chunks
    process_enhanced_chunks(
        input_file="data/enhanced/enhanced_chunks.json",
        output_dir="data/graph",
        output_filename="neo4j_data.json",
    )
