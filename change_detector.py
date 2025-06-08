import difflib

# load the text from the file at file_path
def load_paragraphs(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    return [p.strip() for p in text.split('\n\n') if p.strip()] # Split by double newlines for paragraphs

#function to detect changes between two text files
def detect_changes(file_v1, file_v2, threshold=0.75):
    paras_v1 = load_paragraphs(file_v1)
    paras_v2 = load_paragraphs(file_v2)

    # Initialize lists to hold changes based on their types
    added = []
    deleted = []
    modified = []

    # Use SequenceMatcher at the list level for efficient matching
    sm = difflib.SequenceMatcher(None, paras_v1, paras_v2, autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            continue  # unchanged
        elif tag == 'replace':
            # Check similarity for each pair
            for old_p, new_p in zip(paras_v1[i1:i2], paras_v2[j1:j2]):
                ratio = difflib.SequenceMatcher(None, old_p, new_p).ratio()
                if ratio >= threshold: # if the paragraphs are more similar consider it modified
                    modified.append({"original": old_p, "updated": new_p})
                else:
                    deleted.append({"original": old_p})
                    added.append({"updated": new_p})
            # Handle extras
            extra_old = paras_v1[i1 + (j2-j1):i2]
            extra_new = paras_v2[j1 + (i2-i1):j2]
            for old_p in extra_old:
                deleted.append({"original": old_p})
            for new_p in extra_new:
                added.append({"updated": new_p})
        elif tag == 'delete':
            for old_p in paras_v1[i1:i2]:
                deleted.append({"original": old_p})
        elif tag == 'insert':
            for new_p in paras_v2[j1:j2]:
                added.append({"updated": new_p})

    return { # Return a dictionary with categorized changes
        "added": added,
        "deleted": deleted,
        "modified": modified
    }
