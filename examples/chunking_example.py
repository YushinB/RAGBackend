"""
Integration example for advanced chunking strategies.

This module demonstrates how to use:
- RelationshipAwareChunker (T4.2.1)
- LinkedChunker (T4.2.2)
- SemanticChunker (T4.2.3)

Together to create a comprehensive chunking pipeline.
"""

from src.models.base_models import (
    ChunkType,
    DocumentHierarchy,
    MultiModalContent,
    TextChunk,
)
from src.models.chunking_config import ChunkingConfig, ChunkingStrategy
from src.processors.chunking_strategies import ChunkerFactory


def example_relationship_aware_chunking() -> None:
    """
    Example: Preserve figure-caption and table-reference associations.
    """
    print("\n=== Relationship-Aware Chunking Example ===\n")

    # Configure for relationship preservation
    config = ChunkingConfig(
        chunk_size=300,
        chunk_overlap=50,
        min_chunk_size=100,
    )

    # Create chunker
    chunker = ChunkerFactory.create_relationship_aware_chunker(config)

    # Create sample content with references
    text = """
    The experimental results are shown in Figure 1 and Figure 2.
    Figure 1 demonstrates the baseline measurements across different conditions.
    Table 1 summarizes all experimental parameters used in the study.
    As shown in Table 1, we varied temperature from 20°C to 100°C.
    The relationship between variables is defined by Equation 1.
    Equation 1 provides the theoretical foundation for our analysis.
    """

    content = MultiModalContent(document_id="example-001")
    content.add_text_chunk(TextChunk(text=text.strip()))

    # Chunk with relationship preservation
    chunks = chunker.chunk(content)

    print(f"Created {len(chunks)} chunks with relationship preservation:\n")
    for i, chunk in enumerate(chunks, 1):
        print(f"Chunk {i}:")
        print(f"  Text: {chunk.text[:80]}...")
        print(f"  Has multi-modal refs: {chunk.has_multi_modal_content()}")
        print(f"  Multi-modal refs: {chunk.multi_modal_refs}")
        print(f"  Relationships: {chunk.relationships}")
        print()


def example_linked_chunking() -> None:
    """
    Example: Create chunks with sequential and hierarchical links.
    """
    print("\n=== Linked Chunking Example ===\n")

    # Configure for linked chunks
    config = ChunkingConfig(
        chunk_size=150,
        chunk_overlap=25,
        strategy=ChunkingStrategy.SLIDING_WINDOW,
    )

    # Create chunker
    chunker = ChunkerFactory.create_linked_chunker(config)

    # Create sample content
    text = """
    This is the first paragraph of our document. It introduces the main topic
    and provides context for the following sections. The content flows naturally
    from one idea to the next.

    The second paragraph builds on the introduction. It presents supporting
    evidence and examples that reinforce the main points. Each sentence connects
    to create a coherent narrative.

    Finally, the third paragraph concludes the discussion. It summarizes the
    key findings and suggests directions for future work. The circular structure
    brings closure to the document.
    """

    content = MultiModalContent(document_id="example-002")
    content.add_text_chunk(TextChunk(text=text.strip()))

    # Chunk with linking
    chunks = chunker.chunk(content)

    print(f"Created {len(chunks)} linked chunks:\n")
    for i, chunk in enumerate(chunks, 1):
        print(f"Chunk {i} (ID: {chunk.chunk_id[:8]}...):")
        print(
            f"  Previous: {chunk.prev_chunk_id[:8] if chunk.prev_chunk_id else 'None'}..."
        )
        print(
            f"  Next: {chunk.next_chunk_id[:8] if chunk.next_chunk_id else 'None'}..."
        )
        print(
            f"  Parent: {chunk.parent_chunk_id[:8] if chunk.parent_chunk_id else 'None'}..."
        )
        print(f"  Text length: {len(chunk.text)} chars")
        print()


def example_semantic_chunking() -> None:
    """
    Example: Chunk by semantic structure (sentences, paragraphs, sections).
    """
    print("\n=== Semantic Chunking Example ===\n")

    # Configure for semantic chunking
    config = ChunkingConfig.semantic_chunks()

    # Create chunker
    chunker = ChunkerFactory.create_semantic_chunker(config)

    # Create structured content
    intro_hierarchy = DocumentHierarchy(
        level=1,
        title="Introduction",
        section_number="1",
    )

    methods_hierarchy = DocumentHierarchy(
        level=1,
        title="Methods",
        section_number="2",
    )

    results_hierarchy = DocumentHierarchy(
        level=1,
        title="Results",
        section_number="3",
    )

    content = MultiModalContent(document_id="example-003")

    content.add_text_chunk(
        TextChunk(
            text="""
            This introduction presents the research problem. We investigate the
            relationship between variables X and Y. Our hypothesis states that
            X influences Y in a predictable manner.
            """.strip(),
            hierarchy=intro_hierarchy,
            chunk_type=ChunkType.PARAGRAPH,
        )
    )

    content.add_text_chunk(
        TextChunk(
            text="""
            Our methodology follows standard experimental protocols. We collected
            data from 100 participants over 6 months. Statistical analysis was
            performed using ANOVA and regression techniques.
            """.strip(),
            hierarchy=methods_hierarchy,
            chunk_type=ChunkType.PARAGRAPH,
        )
    )

    content.add_text_chunk(
        TextChunk(
            text="""
            The results show a significant correlation (p < 0.05). Variable X
            explains 75% of variance in Y. These findings support our hypothesis
            and align with previous research in the field.
            """.strip(),
            hierarchy=results_hierarchy,
            chunk_type=ChunkType.PARAGRAPH,
        )
    )

    # Chunk semantically
    chunks = chunker.chunk(content)

    print(f"Created {len(chunks)} semantic chunks:\n")
    for i, chunk in enumerate(chunks, 1):
        print(f"Chunk {i}:")
        if chunk.hierarchy:
            print(
                f"  Section: {chunk.hierarchy.section_number} - {chunk.hierarchy.title}"
            )
        print(f"  Type: {chunk.chunk_type.value}")
        print(f"  Boundary: {chunk.metadata.get('boundary_type', 'unknown')}")
        print(f"  Text: {chunk.text[:80]}...")
        print()


def example_combined_pipeline() -> None:
    """
    Example: Use multiple strategies in sequence for optimal chunking.
    """
    print("\n=== Combined Chunking Pipeline Example ===\n")

    # Step 1: Use relationship-aware chunking first
    print("Step 1: Relationship-Aware Chunking")
    ra_config = ChunkingConfig(chunk_size=400, chunk_overlap=50)
    ra_chunker = ChunkerFactory.create_relationship_aware_chunker(ra_config)

    text = (
        """
    Figure 1 shows the experimental setup used in our study. The apparatus
    consists of three main components as labeled in Figure 1. Table 1 provides
    detailed specifications for each component. According to Table 1, the
    temperature range was 20-100°C. The relationship is defined by Equation 1
    which relates temperature to reaction rate. Using Equation 1, we can predict
    outcomes under various conditions.
    """
        * 3
    )  # Repeat to make it longer

    content = MultiModalContent(document_id="example-004")
    content.add_text_chunk(TextChunk(text=text.strip()))

    ra_chunks = ra_chunker.chunk(content)
    print(f"  Created {len(ra_chunks)} chunks with preserved relationships\n")

    # Step 2: Apply linked chunking
    print("Step 2: Linked Chunking")
    link_config = ChunkingConfig(chunk_size=250, chunk_overlap=30)
    linked_chunker = ChunkerFactory.create_linked_chunker(link_config)

    linked_content = MultiModalContent(document_id="example-004-linked")
    for chunk in ra_chunks:
        linked_content.add_text_chunk(chunk)

    linked_chunks = linked_chunker.chunk(linked_content)
    print(f"  Created {len(linked_chunks)} linked chunks\n")

    # Step 3: Apply semantic refinement
    print("Step 3: Semantic Refinement")
    semantic_config = ChunkingConfig.semantic_chunks()
    semantic_chunker = ChunkerFactory.create_semantic_chunker(semantic_config)

    semantic_content = MultiModalContent(document_id="example-004-semantic")
    for chunk in linked_chunks:
        semantic_content.add_text_chunk(chunk)

    final_chunks = semantic_chunker.chunk(semantic_content)
    print(f"  Created {len(final_chunks)} final semantic chunks\n")

    # Display final results
    print("Final Pipeline Results:")
    print(f"  Total chunks: {len(final_chunks)}")

    multi_modal_count = sum(1 for c in final_chunks if c.has_multi_modal_content())
    print(f"  Chunks with multi-modal refs: {multi_modal_count}")

    linked_count = sum(1 for c in final_chunks if c.next_chunk_id or c.prev_chunk_id)
    print(f"  Linked chunks: {linked_count}")


def example_custom_strategy() -> None:
    """
    Example: Create custom chunking strategy using factory.
    """
    print("\n=== Custom Strategy Example ===\n")

    # For code content - use adjusted config
    base_config = ChunkingConfig.default()
    code_config = base_config.adjust_for_content_type("code")

    print("Code-optimized config:")
    print(f"  Strategy: {code_config.strategy.value}")
    print(f"  Chunk size: {code_config.chunk_size}")
    print(f"  Overlap: {code_config.chunk_overlap}")
    print(f"  Preserve formatting: {code_config.preserve_formatting}")
    print(f"  Respect sentence boundaries: {code_config.respect_sentence_boundaries}")

    # For markdown content
    markdown_config = base_config.adjust_for_content_type("markdown")

    print("\nMarkdown-optimized config:")
    print(f"  Strategy: {markdown_config.strategy.value}")
    print(f"  Boundary type: {markdown_config.boundary_type.value}")
    print(f"  Respect section boundaries: {markdown_config.respect_section_boundaries}")


def main() -> None:
    """Run all examples."""
    print("=" * 70)
    print("Advanced Chunking Strategies - Examples")
    print("=" * 70)

    example_relationship_aware_chunking()
    example_linked_chunking()
    example_semantic_chunking()
    example_combined_pipeline()
    example_custom_strategy()

    print("\n" + "=" * 70)
    print("Examples completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    main()
