"""
PDF Processing and Chunking Demonstration

This script demonstrates the complete pipeline:
1. Create a sample PDF with text content
2. Process the PDF using PDFProcessor
3. Apply chunking strategies to the extracted content
4. Display the results

Usage: python demo_pdf_processing.py
"""

import json
import traceback
from pathlib import Path
from typing import Any

from src.models.base_models import MultiModalContent
from src.models.chunking_config import ChunkingConfig, ChunkingStrategy
from src.processors.chunking_strategies import (
    LinkedChunker,
    RelationshipAwareChunker,
    SemanticChunker,
)
from src.processors.factory import ProcessorFactory


def display_multimodal_content(content: MultiModalContent) -> None:
    """Display extracted multimodal content in a readable format."""
    print("=" * 80)
    print("📊 EXTRACTED MULTIMODAL CONTENT")
    print("=" * 80)

    # Get all text from text chunks
    all_text = " ".join(chunk.text for chunk in content.text_chunks)

    print(f"\n📝 Text Chunks: {len(content.text_chunks)}")
    print(f"   Total characters: {len(all_text)}")
    if all_text:
        print(f"   Preview: {all_text[:200]}...")

    print(f"\n🖼️  Images: {len(content.images)}")
    if content.images:
        for i, img_id in enumerate(content.images[:3], 1):
            print(f"   {i}. Image ID: {img_id}")

    print(f"\n📋 Tables: {len(content.tables)}")
    if content.tables:
        for i, table_id in enumerate(content.tables[:3], 1):
            print(f"   {i}. Table ID: {table_id}")

    print(f"\n🔗 Relationships: {sum(len(v) for v in content.relationships.values())}")
    if content.relationships:
        for i, (source_id, targets) in enumerate(
            list(content.relationships.items())[:5], 1
        ):
            print(f"   {i}. {source_id} -> {', '.join(targets)}")

    print(f"\n📍 Document ID: {content.document_id}")
    print(f"📊 Metadata: {content.metadata}")
    print()


def display_chunks(chunks: list[Any], strategy_name: str) -> None:
    """Display chunking results in a readable format."""
    print("=" * 80)
    print(f"🔪 CHUNKING RESULTS - {strategy_name}")
    print("=" * 80)

    print(f"\n📦 Total Chunks: {len(chunks)}")
    print(f"   Strategy: {strategy_name}")

    for i, chunk in enumerate(chunks, 1):
        print(f"\n--- Chunk {i} ---")
        print(f"ID: {chunk.chunk_id}")
        print(f"Size: {len(chunk.text)} characters")
        print(f"Type: {chunk.chunk_type}")
        print(f"Position: {chunk.position}")
        print(f"Preview: {chunk.text[:150]}...")

        # Display metadata if present
        if chunk.metadata:
            token_count = chunk.metadata.get("token_count", "N/A")
            print(f"Tokens: ~{token_count}")

    print()


def demo_fixed_size_chunking(content: MultiModalContent) -> None:
    """Demonstrate fixed-size chunking."""
    config = ChunkingConfig(
        strategy=ChunkingStrategy.FIXED_SIZE, chunk_size=300, chunk_overlap=50
    )

    chunker = RelationshipAwareChunker(config)
    _chunks = chunker.chunk(content)

    # display_chunks(chunks, "Fixed Size (300 chars, 50 overlap)")


def demo_semantic_chunking(content: MultiModalContent) -> None:
    """Demonstrate semantic chunking."""
    config = ChunkingConfig(
        strategy=ChunkingStrategy.SEMANTIC, chunk_size=500, chunk_overlap=100
    )

    chunker = SemanticChunker(config)
    chunks = chunker.chunk(content)

    display_chunks(chunks, "Semantic (500 chars, 100 overlap)")


def demo_hierarchical_chunking(content: MultiModalContent) -> None:
    """Demonstrate hierarchical chunking."""
    config = ChunkingConfig(
        strategy=ChunkingStrategy.HIERARCHICAL,
        chunk_size=400,
        chunk_overlap=75,
        respect_section_boundaries=True,
    )

    chunker = LinkedChunker(config)
    chunks = chunker.chunk(content)

    display_chunks(chunks, "Hierarchical (400 chars, 75 overlap)")


def save_results_to_json(chunks: list[Any], output_path: Path) -> None:
    """Save chunking results to JSON file."""
    results = []

    for chunk in chunks:
        # Convert ContentPosition to serializable dict if present
        position_data = chunk.position
        if hasattr(position_data, "to_dict"):
            position_data = position_data.to_dict()
        elif hasattr(position_data, "__dict__"):
            position_data = {
                k: v for k, v in vars(position_data).items() if not k.startswith("_")
            }

        chunk_data = {
            "chunk_id": chunk.chunk_id,
            "text": chunk.text,
            "char_count": len(chunk.text),
            "chunk_type": str(chunk.chunk_type),
            "position": position_data,
            "metadata": chunk.metadata,
        }
        results.append(chunk_data)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"💾 Results saved to: {output_path}")


def main() -> int:
    """Run the complete demonstration."""
    print("\n" + "=" * 80)
    print("🚀 PDF PROCESSING AND CHUNKING DEMONSTRATION")
    print("=" * 80 + "\n")

    # Setup paths
    data_dir = Path("data/uploads")
    data_dir.mkdir(parents=True, exist_ok=True)

    pdf_path = data_dir / "ICRCA_2026_UAV.pdf"
    output_json = data_dir / "chunking_results.json"

    try:
        # Step 2: Process PDF
        print("🔄 Processing PDF with ProcessorFactory...")
        factory = ProcessorFactory()
        content = factory.process_file(str(pdf_path))
        print("✅ PDF processed successfully\n")

        # Step 3: Display extracted content
        display_multimodal_content(content)

        # Step 4: Demonstrate different chunking strategies
        print("\n" + "🔪 APPLYING CHUNKING STRATEGIES" + "\n")

        print("1️⃣  Fixed Size Chunking")
        demo_fixed_size_chunking(content)

        print("\n2️⃣  Semantic Chunking")
        demo_semantic_chunking(content)

        # Skip hierarchical chunking - it's slow
        # Use semantic chunks for JSON output
        semantic_config = ChunkingConfig(
            strategy=ChunkingStrategy.SEMANTIC, chunk_size=500, chunk_overlap=100
        )
        semantic_chunker = SemanticChunker(semantic_config)
        final_chunks = semantic_chunker.chunk(content)

        # Step 5: Save results
        save_results_to_json(final_chunks, output_json)

        # Summary
        print("\n" + "=" * 80)
        print("✨ DEMONSTRATION COMPLETE")
        print("=" * 80)
        print("\n📁 Files created:")
        print(f"   • PDF: {pdf_path}")
        print(f"   • Results: {output_json}")
        print("\n🎯 Summary:")
        print(f"   • Text chunks extracted: {len(content.text_chunks)}")
        all_text = " ".join(chunk.text for chunk in content.text_chunks)
        print(f"   • Total characters: {len(all_text)}")
        print(f"   • Chunks created: {len(final_chunks)}")
        if final_chunks:
            print(
                f"   • Average chunk size: {sum(len(c.text) for c in final_chunks) // len(final_chunks)} chars"
            )
        print()

    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
