from load_chunks import load_chunks_and_metadata

from utils.load_env import get_env_vars

env_vars = get_env_vars()
CHUNKS_FILE = env_vars.get("CHUNKS_FILE", "exports/chunks.json")
METADATA_FILE = env_vars.get("METADATA_FILE", "exports/metadata.json")

chunks, metadata = load_chunks_and_metadata(CHUNKS_FILE, METADATA_FILE)
