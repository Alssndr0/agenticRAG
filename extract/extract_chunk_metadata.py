def extract_all_chunks_metadata(chunks_list):
    results = []

    for chunk_idx, chunk in enumerate(chunks_list):
        metadata = {}

        # Extract headings if available
        metadata["headings"] = getattr(chunk.meta, "headings", None)

        # Extract filename from origin
        try:
            filename = chunk.meta.origin.filename
            if isinstance(filename, str):
                metadata["filename"] = [filename]
            elif isinstance(filename, list) and all(
                isinstance(f, str) for f in filename
            ):
                metadata["filename"] = filename
            else:
                raise TypeError("filename must be a string or list of strings")
        except (AttributeError, TypeError, KeyError):
            metadata["filename"] = None

        # Extract MIME type
        metadata["mimetype"] = getattr(chunk.meta.origin, "mimetype", None)

        # Extract page numbers from provenance
        page_numbers = []
        try:
            for item in chunk.meta.doc_items:
                for prov in item.prov:
                    if hasattr(prov, "page_no"):
                        page_numbers.append(prov.page_no)
            metadata["pages"] = sorted(set(page_numbers)) if page_numbers else None
        except Exception:
            metadata["pages"] = None

        # Extract bounding boxes and char spans from provenance
        bboxes = []
        charspans = []
        try:
            for item in chunk.meta.doc_items:
                for prov in item.prov:
                    bbox = getattr(prov, "bbox", None)
                    charspan = getattr(prov, "charspan", None)
                    if bbox:
                        bboxes.append(
                            {
                                "left": bbox.l,
                                "top": bbox.t,
                                "right": bbox.r,
                                "bottom": bbox.b,
                                "origin": bbox.coord_origin.name,
                            }
                        )
                    if charspan:
                        charspans.append({"start": charspan[0], "end": charspan[1]})
            metadata["bounding_boxes"] = bboxes if bboxes else None
            metadata["charspans"] = charspans if charspans else None
        except Exception:
            metadata["bounding_boxes"] = None
            metadata["charspans"] = None

        # Initialize empty summaries
        metadata["document_summary"] = ""
        metadata["chunk_summary"] = ""

        # Create unified chunk with the new structure (idx, text, metadata)
        results.append(
            {
                "idx": chunk_idx,
                "text": chunk.text,
                "metadata": metadata,
            }
        )

    return results
