def normalize_pair(pair):
    """Case/whitespace-insensitive key for a {topic, angle} pair, so minor
    formatting differences from the model (e.g. "Amoxicillin " vs
    "amoxicillin") don't defeat duplicate detection."""
    return (pair["topic"].strip().lower(), pair["angle"].strip().lower())


def find_repeated_pairs(new_pairs, prior_pairs):
    """Return the entries in new_pairs whose (topic, angle) already appears
    in prior_pairs or earlier in new_pairs itself.

    Pure local comparison, no API call — a free safety net for when the
    model ignores the prompt's avoid-list instruction. Not a hard guarantee
    against repeats: two pairs describing the same idea with different
    wording (e.g. "Amoxicillin" vs "Amoxicillin (Augmentin)") won't match.
    """
    prior_keys = {normalize_pair(p) for p in prior_pairs}
    seen = set()
    repeats = []
    for pair in new_pairs:
        key = normalize_pair(pair)
        if key in prior_keys or key in seen:
            repeats.append(pair)
        seen.add(key)
    return repeats
