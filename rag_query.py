#!/usr/bin/env python3
"""
RAG Query Entry Point
This script provides a simple interface to query the RAG system.
"""

import sys
import traceback
import argparse

from utils.load_env import get_env_vars
from retrieval.generation import (
    initialize_embeddings_model,
    initialize_retriever,
    generate_response,
)

import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"


def main():
    env = get_env_vars()
    default_model     = env["OPENAI_MODEL"]
    default_k         = int(env.get("RETRIEVE_K", 5))
    default_alpha     = float(env.get("RETRIEVE_ALPHA", 0.7))
    default_graph_rat = float(env.get("GRAPH_RATIO", 0.3))

    parser = argparse.ArgumentParser(description="Query the Graph-RAG system")

    parser.add_argument(
        "question",
        nargs="*",
        help="The question to ask (if omitted, you’ll be prompted)"
    )
    parser.add_argument(
        "--model", "-m",
        default=default_model,
        help=f"OpenAI model to use (default: {default_model})"
    )
    parser.add_argument(
        "-k",
        type=int,
        default=default_k,
        help=f"Number of passages to retrieve (default: {default_k})"
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=default_alpha,
        help=f"FAISS/BM25 weight (1.0=only FAISS, 0.0=only BM25) (default: {default_alpha})"
    )
    parser.add_argument(
        "--no-graph",                # ASCII hyphen
        dest="no_graph",
        action="store_true",
        help="Disable graph retrieval (only FAISS+BM25)"
    )
    parser.add_argument(
        "--graph-ratio",             # ASCII hyphen
        dest="graph_ratio",
        type=float,
        default=default_graph_rat,
        help=f"Proportion of results from graph (0.0–1.0) (default: {default_graph_rat})"
    )

    args = parser.parse_args()

    # Build the question string
    if args.question:
        question = " ".join(args.question)
    else:
        question = input("Enter your question: ").strip()

    include_graph = not args.no_graph

    print(f"\n🔍 Processing question: {question}")
    print(f"   • Model: {args.model}")
    print(f"   • k: {args.k}")
    print(f"   • alpha: {args.alpha}")
    print(f"   • include_graph: {include_graph}")
    print(f"   • graph_ratio : {args.graph_ratio}\n")

    # Initialize components
    print("⚙️  Initializing embeddings model...")
    embeddings_model = initialize_embeddings_model()

    print("⚙️  Initializing retriever...")
    retriever = initialize_retriever(embeddings_model=embeddings_model)

    # Run the query
    try:
        print("💬 Generating response...\n")
        response = generate_response(
            question=question,
            retriever=retriever,
            model=args.model,
            k=args.k,
            alpha=args.alpha,
            include_graph=include_graph,
            graph_ratio=args.graph_ratio,
        )
        print("=== Response ===\n")
        print(response)
    except Exception as e:
        print(f"Error during generation: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Fatal error: {e}")
        traceback.print_exc()
        sys.exit(1)
