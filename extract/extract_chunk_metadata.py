def extract_all_chunks_metadata(chunks_list):
    results = []

    for chunk in chunks_list:
        metadata = {}

        # Headings
        metadata["headings"] = getattr(chunk.meta, "headings", None)

        # Filename
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

        # Page numbers
        page_numbers = []
        try:
            for item in chunk.meta.doc_items:
                for prov in item.prov:
                    if hasattr(prov, "page_no"):
                        page_numbers.append(prov.page_no)
            metadata["pages"] = sorted(set(page_numbers)) if page_numbers else None
        except Exception:
            metadata["pages"] = None

        # Bounding boxes and char spans
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

        results.append(
            {
                "chunk": chunk.text,
                "metadata": metadata,  # id will be added later in write_chunks_json
            }
        )

    return results
