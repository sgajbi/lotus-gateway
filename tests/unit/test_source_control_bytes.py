"""Source files must not carry control bytes a shell escape produced.

A backslash escape written through an interpreting heredoc is expanded before
the file exists: ``\\b`` in a regex becomes a literal 0x08 backspace, ``\\t`` a
tab, ``\\f`` a formfeed. The corruption is invisible by construction — a
terminal does not render 0x08, a diff shows nothing unusual, and re-reading the
source cannot see it. Only the bytes can.

It is not hypothetical. A sibling repository's guard compiled to
``'\\x08([A-Z][a-z]+)-only\\x08'`` and passed on the exact defect it was written
to catch, because no real text contains a backspace. A guard corrupted this way
does not fail loudly; it silently matches nothing. In a sibling's review ledger
the same mechanism ate the first letter of nine real identifiers in prose, where
nothing in Markdown rendering signals it at all.
"""

from __future__ import annotations

import subprocess
from functools import lru_cache
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# How much of a file decides its type. A NUL byte does not occur in text and
# appears within the first block of every binary format in this repository.
TYPE_SNIFF_BYTES = 8192


def is_suspicious(byte: int) -> bool:
    """True for control bytes never legitimate in a text file.

    Tab (0x09), newline (0x0A) and carriage return (0x0D) are excluded: they are
    ordinary formatting. Everything else below 0x20 indicates an escape that was
    interpreted when it should have been written literally.
    """
    return byte < 0x09 or byte in (0x0B, 0x0C) or 0x0D < byte < 0x20


# Above this share of non-text bytes in the sniff window, a file is a binary
# format rather than corrupted text. Real binaries are dense with such bytes --
# PNG, zip and compiled output are far above it -- while source that has taken a
# stray control byte is otherwise entirely printable.
BINARY_DENSITY = 0.30

# Below this many bytes a density is dominated by whatever single byte is being
# looked for, so binary is never inferred. Every binary format in use carries
# more than this in its header alone, and the repository tracks none.
MIN_BYTES_TO_JUDGE_BINARY = 64


def is_text(data: bytes) -> bool:
    """Classify by CONTENT, not by name, and not on a single byte.

    An extension allowlist cannot express "text": it silently omits every
    dot-prefixed or extensionless file, and `.importlinter` and `quality/.npmrc`
    are both real configuration this guard must cover. Text is therefore the
    default and binary the exception that must be demonstrated.

    Demonstrating it on the FIRST NUL was wrong in the one case that matters
    most. An escaped `\\0` materialised into a tracked source file is exactly the
    corruption this module exists to catch, and treating any NUL as proof of
    binary made such a file skipped rather than reported -- the guard would go
    quiet on its own worst input. Density decides instead: one stray control byte
    in otherwise printable source stays text and gets reported; a real binary is
    dense with them and is excluded.
    """
    window = data[:TYPE_SNIFF_BYTES]
    if len(window) < MIN_BYTES_TO_JUDGE_BINARY:
        # Too short for a density to mean anything: in `x=\x00` the single
        # corrupting byte is a third of the file, so density alone would call the
        # smallest corrupted config binary and drop it from the inventory --
        # again silencing the guard on the input it exists for. Short files are
        # text, and their control bytes get reported.
        return True
    # Control bytes alone do not separate the two: uniformly distributed binary
    # is only about 11% control bytes, which is lower than some prose. Bytes at
    # or above 0x80 are what binary is dense in, while UTF-8 source and
    # documentation carry them only for the occasional non-ASCII character.
    non_text = sum(1 for byte in window if is_suspicious(byte) or byte >= 0x80)
    return non_text / len(window) <= BINARY_DENSITY


@lru_cache(maxsize=1)
def _inventory() -> tuple[Path, ...]:
    """Tracked files, from git, as the reproducible definition of source.

    Two properties matter and only git provides both.

    It is REPRODUCIBLE: the same commit yields the same inventory on a runner, in
    the container and on a workstation, where a filesystem walk yields whatever
    happens to be lying in the tree.

    It EXCLUDES BUILD OUTPUT BY CONSTRUCTION. An ANSI-coloured log is full of
    0x1b, which this guard is right to reject in source and must never reject in
    a file nobody tracks. A walk reads those logs and fails on them, which
    teaches the reader to ignore the gate — and a gate that gets ignored is
    worse than no gate. Ignored-ness is not a property a walk can recover, so it
    is taken from the tool that owns it.

    An earlier revision walked the filesystem to avoid needing the git binary
    inside the CI-local container. That fixed the wrong half: the container
    bind-mounts the repository, `.git` and all, so the inventory was always
    available there — only the binary was missing, and that is a property of the
    lane, not of this check.
    """
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "ls-files", "-z"],
        capture_output=True,
    )
    if result.returncode != 0:
        raise AssertionError(
            "git ls-files failed, so the source inventory cannot be established: "
            f"{result.stderr.decode('utf-8', 'replace').strip()}. This check must not "
            "fall back to walking the filesystem — that reads untracked build output "
            "and fails on logs nobody tracks."
        )

    paths: list[Path] = []
    for entry in result.stdout.split(b"\0"):
        if not entry:
            continue
        path = REPO_ROOT / entry.decode("utf-8")
        if not path.is_file() or path.is_symlink():
            continue
        try:
            data = path.read_bytes()
        except OSError:
            continue
        if is_text(data):
            paths.append(path)
    return tuple(paths)


def _source_inventory() -> list[Path]:
    """The cached inventory, as a list.

    Cached because four assertions need it and each rebuild reads every tracked
    file. Over the CI-local bind mount that difference was minutes, and a gate
    people wait for is a gate people skip.
    """
    return list(_inventory())


def find_offenders(paths: list[Path]) -> list[str]:
    """Report the first control byte in each file that carries one."""
    offenders: list[str] = []
    for path in paths:
        data = path.read_bytes()
        for offset, byte in enumerate(data):
            if is_suspicious(byte):
                line = data[:offset].count(b"\n") + 1
                try:
                    name = path.relative_to(REPO_ROOT).as_posix()
                except ValueError:
                    name = str(path)
                offenders.append(f"{name}:{line} byte=0x{byte:02x}")
                break
    return offenders


def test_no_source_file_carries_an_interpreted_escape() -> None:
    offenders = find_offenders(_source_inventory())

    assert not offenders, (
        "these files carry control bytes, which a shell escape produces when a "
        "literal backslash sequence was meant; a pattern corrupted this way "
        "matches nothing and its guard passes silently: " + "; ".join(offenders)
    )


def test_the_scan_reads_a_meaningful_number_of_files() -> None:
    """A zero-input scan would pass while checking nothing."""
    files = _source_inventory()
    assert len(files) > 100, f"only {len(files)} files scanned; the assertion would be hollow"


def test_the_detector_recognises_each_corruption_it_exists_for() -> None:
    """Prove the check fails on the shapes it forbids, not only that it passes."""
    for escape, byte in (("\\b", 0x08), ("\\f", 0x0C), ("\\v", 0x0B), ("\\a", 0x07)):
        assert is_suspicious(byte), f"{escape} expands to 0x{byte:02x} and must be rejected"
    for legitimate in (0x09, 0x0A, 0x0D, 0x20, 0x41):
        assert not is_suspicious(legitimate), f"0x{legitimate:02x} is ordinary text"


def test_corrupted_tracked_text_is_rejected(tmp_path: Path) -> None:
    """The rejection half, exercised rather than asserted about."""
    victim = tmp_path / "config.toml"
    victim.write_bytes(b"[tool]\nname = " + bytes([0x08]) + b"business_date\n")

    offenders = find_offenders([victim])

    assert offenders, "a tracked text file carrying 0x08 must be reported"
    assert "byte=0x08" in offenders[0]
    assert offenders[0].endswith(":2 byte=0x08"), f"the finding must name the line: {offenders[0]}"


def test_ignored_ansi_logs_are_accepted_because_they_are_not_source(tmp_path: Path) -> None:
    """The acceptance half, and the reason it holds.

    An ANSI-coloured log is genuinely full of 0x1b, so it would be REPORTED if it
    were scanned. What protects it is not the byte classifier but the inventory:
    it is not tracked, so it is not source. Proving both halves separately is the
    point — otherwise "the gate is quiet" could equally mean the classifier is
    broken.
    """
    log = tmp_path / "gateway-ci.log"
    log.write_bytes(b"\x1b[31mFAILED\x1b[0m tests/unit/test_x.py\n")

    assert find_offenders([log]), "an ANSI log does carry bytes this guard rejects"

    # Verify the exclusion against a real ignored artifact in the repository
    # itself, rather than asserting that no tracked file ends in .log -- that
    # would fail on a legitimate tracked log fixture while proving nothing about
    # ignored ones, which is the thing being claimed.
    planted = REPO_ROOT / "gateway-byte-scan-probe.log"
    assert not planted.exists(), "probe name is already in use"
    planted.write_bytes(b"\x1b[31mFAILED\x1b[0m simulated build output\n")
    try:
        ignored = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "check-ignore", "-q", str(planted)],
            capture_output=True,
        )
        assert ignored.returncode == 0, "gateway-*.log must be ignored for this claim to hold"

        _inventory.cache_clear()
        assert planted not in set(_source_inventory()), (
            "an ignored artifact carrying 0x1b must not enter the source inventory"
        )
    finally:
        planted.unlink()
        _inventory.cache_clear()


def test_the_inventory_covers_dot_prefixed_and_extensionless_configuration() -> None:
    """The files a suffix allowlist silently omitted must be in scope.

    `.importlinter` and `quality/.npmrc` are real tracked configuration whose
    names carry no usable extension. Under the previous name-based rule the scan
    passed while never opening either — a guard reporting success about files it
    did not read.
    """
    scanned = {path.relative_to(REPO_ROOT).as_posix() for path in _source_inventory()}

    for required in (".importlinter", "quality/.npmrc"):
        assert (REPO_ROOT / required).is_file(), f"{required} is missing from the repository"
        assert required in scanned, f"{required} is tracked but the inventory omits it"


def test_binary_content_is_excluded_by_its_own_bytes() -> None:
    """Classification must reject binary without consulting the file name."""
    assert is_text(b"# a comment\nkey = value\n")
    assert is_text(b"")

    # A real PNG: header plus compressed data, which is dense with control bytes
    # rather than carrying a handful. A sixteen-byte header stub is only a
    # quarter control bytes and is indistinguishable from corrupted text.
    png = b"\x89PNG\r\n\x1a\n" + bytes(range(256)) * 2
    assert not is_text(png)

    # A NUL beyond the sniff window does not reclassify a text file.
    assert is_text(b"x" * (TYPE_SNIFF_BYTES + 16) + b"\x00")


def test_a_short_corrupted_file_is_still_scanned(tmp_path: Path) -> None:
    """Density must not classify away the smallest corrupted files.

    In a three-byte config the corrupting byte is a third of the content, so a
    density rule alone would call it binary and drop it from the inventory --
    the same silencing this classifier was just fixed to avoid, reappearing at
    the other end of the size range.
    """
    tiny = b"x=" + bytes([0x00])

    assert is_text(tiny), "a three-byte file is too short for density to mean anything"

    victim = tmp_path / "tiny.env"
    victim.write_bytes(tiny)

    assert find_offenders([victim]), "a short corrupted file must still be reported"


def test_a_stray_nul_in_source_stays_text_and_is_reported(tmp_path: Path) -> None:
    """The corruption this module exists for must not be classified away.

    An escaped `\\0` materialised into tracked source is the worst input here, and
    a rule that called any NUL-bearing file binary would drop it from the
    inventory before it could be reported -- the guard going quiet on precisely
    the defect it was written to catch.
    """
    corrupted = b'PATTERN = "value\x00suffix"\n' + b"# ordinary source line\n" * 20

    assert is_text(corrupted), "one stray NUL does not make otherwise-printable source binary"

    victim = tmp_path / "settings.py"
    victim.write_bytes(corrupted)
    offenders = find_offenders([victim])

    assert offenders, "a NUL in tracked source must be reported"
    assert "byte=0x00" in offenders[0], offenders[0]


def test_a_clean_corpus_produces_no_findings() -> None:
    """Silence on known-good input, not only a hit on known-bad input.

    A scan that flags correct files trains its reader to ignore it, so the
    accepted case is asserted as explicitly as the rejected one.
    """
    clean = (
        b"[importlinter]\nroot_package = app\n",
        b"registry=https://registry.npmjs.org/\n",
        b"# Title\n\nProse with tabs\tand CRLF line ends.\r\n",
    )
    for data in clean:
        assert is_text(data)
        assert not [byte for byte in data if is_suspicious(byte)]
