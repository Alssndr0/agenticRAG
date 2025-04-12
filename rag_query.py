#!/usr/bin/env python3
"""
RAG Query Entry Point
This script provides a simple interface to query the RAG system.
"""

import sys
import traceback


def main():
    try:
        from retrieval.generation import (
            generate_response,
            initialize_embeddings_model,
            initialize_retriever,
        )
        from utils.load_env import get_env_vars

        env = get_env_vars()
        model = env.get("OPENAI_MODEL", "gpt-4o-mini")

        # Get query from command line arguments or prompt the user
        if len(sys.argv) > 1:
            query = " ".join(sys.argv[1:])
        else:
            query = input("Enter your question: ")

        print(f"Processing question: {query}")

        # Initialize models and retriever
        print("Initializing embeddings model...")
        embeddings_model = initialize_embeddings_model()

        print("Initializing retriever...")
        retriever = initialize_retriever(embeddings_model=embeddings_model)

        # Generate and print response
        print(f"Generating response using model: {model}...")
        response = generate_response(query, retriever, model=model)

        print("\nResponse:")
        print(response)

    except ImportError as e:
        print(f"Error importing modules: {e}")
        print("\nMake sure your environment is set up correctly:")
        print("1. Check that all required Python packages are installed")
        print("2. Ensure .env file contains required environment variables")
        print("3. Verify that all file paths are correct in your .env file\n")
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
