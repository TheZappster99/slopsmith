"""Map a Rocksmith per-string semitone offset array to a human-readable name.

Kept separate from server.py so tests can import it without triggering
FastAPI / SQLite module-level side effects.
"""


def tuning_name(offsets: list[int]) -> str:
    # All three pattern checks below are gated on `len(offsets) == 6`. The
    # naming conventions here are 6-string-specific — e.g. a 7-string all-zeros
    # tuning has a low B, not an E, so labeling it "E Standard" would be wrong.
    # 7+-string community content falls through to the numeric fallback. See #43.

    # Standard tunings (all six strings same offset)
    standard = {
        0: "E Standard", -1: "Eb Standard", -2: "D Standard",
        -3: "C# Standard", -4: "C Standard", -5: "B Standard",
        -6: "Bb Standard", -7: "A Standard",
        1: "F Standard", 2: "F# Standard",
    }
    if len(offsets) == 6 and all(o == offsets[0] for o in offsets):
        name = standard.get(offsets[0])
        if name:
            return name

    # Drop tunings (low string 2 semitones below the rest)
    # Named after the low string's note: e.g. offsets[-2,0,0,0,0,0] = Drop D (low E dropped to D)
    if len(offsets) == 6 and offsets[0] == offsets[1] - 2 and all(o == offsets[1] for o in offsets[1:]):
        note_names = ["E", "F", "F#", "G", "Ab", "A", "Bb", "B", "C", "C#", "D", "Eb"]
        low_note = note_names[offsets[0] % 12]
        return f"Drop {low_note}"

    # Common named tunings
    named = {
        (-2, 0, 0, 0, 0, 0): "Drop D",
        (-4, -2, -2, -2, -2, -2): "Drop C",
        (-2, -2, 0, 0, 0, 0): "Double Drop D",
        (0, 0, 0, -1, 0, 0): "Open G",
        (-2, -2, 0, 0, -2, -2): "Open D",
        (-2, 0, 0, 0, -2, 0): "DADGAD",
        (0, 2, 2, 1, 0, 0): "Open E",
        (-2, 0, 0, 2, 3, 2): "Open D (alt)",
    }
    if len(offsets) == 6 and tuple(offsets) in named:
        return named[tuple(offsets)]

    return " ".join(str(o) for o in offsets) or "Unknown"


def tuning_notes(offsets: list[int], string_count: int | None = None) -> str:
    """Return per-string open note names for display, e.g. 'C# G# C# F# A# D#'.

    Converts raw semitone-offset arrays (as Rocksmith stores them) into the
    actual pitch of each open string. `string_count` trims the output for
    instruments with fewer strings (pass `arrangement_string_count(arr)` from
    the server when available; defaults to len(offsets)).
    """
    NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    # Standard open string pitches as semitone from C (low → high)
    GUITAR_BASE = [4, 9, 2, 7, 11, 4]  # E A D G B E
    BASS_BASE   = [4, 9, 2, 7]          # E A D G

    n = len(offsets)
    sc = string_count if string_count is not None else n
    base = BASS_BASE if sc <= 4 else GUITAR_BASE

    notes = []
    for i in range(min(sc, n)):
        semitone = (base[i % len(base)] + offsets[i]) % 12
        notes.append(NOTE_NAMES[semitone])
    return " ".join(notes)
