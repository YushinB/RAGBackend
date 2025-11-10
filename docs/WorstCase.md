# difficult pattern 1

The raw data input may have some difficult format such as excel file with note on the cell, or information on one cell and the arrow pointing to other cell.

The complicated of document will create the difficutly to extract the data for retrivial.

We need to consider chunking multimodal document content, not just plain text — i.e., documents that contain text, charts, images, and mixed content (like your attached figure).

Design a chunking pipeline that:

- Handles text blocks, figures, charts, and tables as distinct but linked units.
- Preserves relationships (e.g., a figure and its caption should be retrieved together).
- Creates consistent embeddings (text + image caption + metadata).

# difficult pattern 2

the document have confict information with other document. We need to fingure out to answer the question in that case

# difficult pattern 3

This solution need to consider about security and performance that can apply dirrectly to customer
