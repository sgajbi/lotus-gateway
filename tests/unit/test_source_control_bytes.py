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


# Above this share of CONTROL characters, decoded content is a data format that
# happens to be UTF-8 clean rather than source prose. Source that has taken a
# stray control byte is far below it.
BINARY_DENSITY = 0.30

# Below this many decoded characters a density is dominated by whatever single
# character is being looked for, so it is not consulted. Binary never reaches
# this branch -- it is excluded by failing to decode.
MIN_CHARS_TO_JUDGE_DENSITY = 64


def is_text(data: bytes) -> bool:
    """Classify by CONTENT, not by name, and not on a single byte.

    An extension allowlist cannot express "text": it silently omits every
    dot-prefixed or extensionless file, and `.importlinter` and `quality/.npmrc`
    are both real configuration this guard must cover. Text is therefore the
    default and binary the exception that must be demonstrated.

    Demonstrating it on the FIRST NUL was wrong in the one case that matters
    most. An escaped `\\0` materialised into a tracked source file is exactly the
    corruption this module exists to catch, and treating any NUL as proof of
    binary made such a file skipped rather than reported -- the guard going quiet
    on its own worst input. NUL is valid UTF-8, so it no longer excludes
    anything.

    Encoding decides instead. Content that reads as UTF-8 is source and is
    scanned; content that does not is a binary format and is excluded, at any
    size. Decoded content is judged only on its CONTROL characters, and only when
    there is enough of it for a proportion to mean anything.
    """
    decoded = _decode_utf8(data[:TYPE_SNIFF_BYTES])
    if decoded is None:
        # Not valid UTF-8, so not source text here -- every tracked file in this
        # repository is UTF-8. This is what excludes binaries of ANY size. A
        # 34-byte GIF is already unreadable as UTF-8 in its header, where a
        # size-based rule admitted it and then reported those header bytes as
        # corruption; a guard that flags valid binaries is a guard people
        # silence.
        return False

    if len(decoded) < MIN_CHARS_TO_JUDGE_DENSITY:
        # It decoded, so it is text. There is simply too little of it for a
        # density to mean anything: in `x=\x00` the corrupting byte is a third of
        # the content, and judging by density would drop the smallest corrupted
        # config from the inventory -- silencing the guard on the input it exists
        # for.
        return True

    # Only CONTROL characters count toward the density. CJK, Arabic and heavily
    # accented documentation are almost entirely bytes at or above 0x80, so
    # counting high bytes as evidence of binary would drop valid Unicode text and
    # never check it for control bytes at all.
    controls = sum(1 for character in decoded if is_suspicious(ord(character)))
    return controls / len(decoded) <= BINARY_DENSITY


def _decode_utf8(window: bytes) -> str | None:
    """The window as text, or None when it is not UTF-8 at all.

    A window cut at a fixed byte count can split a multibyte character, so a
    failure at the tail is retried before concluding the content is binary.
    """
    for trim in (0, 1, 2, 3):
        try:
            return (window[: len(window) - trim] if trim else window).decode("utf-8")
        except UnicodeDecodeError:
            continue
    return None


@lru_cache(maxsize=4)
def _inventory(root: Path = REPO_ROOT) -> tuple[Path, ...]:
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
        ["git", "-C", str(root), "ls-files", "-z"],
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
        path = root / entry.decode("utf-8")
        if not path.is_file() or path.is_symlink():
            continue
        try:
            data = path.read_bytes()
        except OSError:
            continue
        if is_text(data):
            paths.append(path)
    return tuple(paths)


def _source_inventory(root: Path = REPO_ROOT) -> list[Path]:
    """The cached inventory, as a list.

    Cached because four assertions need it and each rebuild reads every tracked
    file. Over the CI-local bind mount that difference was minutes, and a gate
    people wait for is a gate people skip.
    """
    return list(_inventory(root))


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

    # Exercise the exclusion in a purpose-built repository rather than by
    # planting a file in this one: a test that mutates the tree it runs in can
    # leave debris when it fails, and this asserts a property of the inventory
    # rather than of this checkout.
    #
    # It also separates ignored from merely log-named. A TRACKED log fixture is
    # legitimate source and must stay in scope; only the ignored artifact is
    # excluded. Asserting "no .log is tracked" conflated the two and would have
    # failed on a repository that legitimately tracks one.
    repo = tmp_path / "scan-fixture"
    repo.mkdir()

    def run_git(*args: str) -> None:
        subprocess.run(["git", "-C", str(repo), *args], capture_output=True, check=True)

    run_git("init", "--quiet", "--initial-branch=main")
    run_git("config", "user.email", "test@example.invalid")
    run_git("config", "user.name", "Test")

    (repo / ".gitignore").write_text("gateway-*.log\n", encoding="utf-8")
    config = repo / "settings.toml"
    config.write_text("[tool]\nname = 'x'\n", encoding="utf-8")
    tracked_log = repo / "expected-output.log"
    tracked_log.write_text("plain expected output\n", encoding="utf-8")
    run_git("add", ".gitignore", "settings.toml", "expected-output.log")
    run_git("commit", "--quiet", "-m", "fixture")

    ignored_log = repo / "gateway-build.log"
    ignored_log.write_bytes(b"\x1b[31mFAILED\x1b[0m simulated build output\n")
    try:
        ignored = subprocess.run(
            ["git", "-C", str(repo), "check-ignore", "-q", str(ignored_log)],
            capture_output=True,
        )
        assert ignored.returncode == 0, "the fixture's gitignore must actually ignore it"

        scanned = set(_source_inventory(repo))
        assert ignored_log not in scanned, (
            "an ignored artifact carrying 0x1b must not enter the source inventory"
        )
        assert tracked_log in scanned, "a TRACKED log fixture is source and must remain in scope"
        assert config in scanned
        assert not find_offenders(sorted(scanned)), "the fixture's tracked files are clean"
    finally:
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


def test_non_ascii_text_is_not_mistaken_for_binary(tmp_path: Path) -> None:
    """Predominantly non-ASCII documentation is text and must stay in scope.

    CJK, Arabic and heavily accented prose are made almost entirely of bytes at
    or above 0x80. Counting those as evidence of binary would drop valid Unicode
    files from the inventory, so their control bytes would never be checked --
    the same silent exclusion as the NUL rule, reached through the encoding.
    """
    japanese = "これはテストです。\n" * 20
    arabic = "هذا اختبار للتوثيق.\n" * 20
    accented = "Références détaillées à l'évaluation.\n" * 20

    for prose in (japanese, arabic, accented):
        assert is_text(prose.encode("utf-8")), "valid UTF-8 prose is text"

    corrupted = (japanese + "\x08broken\n").encode("utf-8")
    assert is_text(corrupted), "non-ASCII text with a stray control byte is still text"

    victim = tmp_path / "guide.ja.md"
    victim.write_bytes(corrupted)
    assert find_offenders([victim]), "its control byte must still be reported"


def test_a_small_binary_is_excluded_by_failing_to_decode() -> None:
    """Size must not admit a binary, or the gate reports its header as damage.

    A 1x1 GIF is 34 bytes. Under a size-based exemption it entered the inventory
    and every control byte in its header became a finding -- a gate that flags
    valid files, which is the failure that gets a gate ignored rather than fixed.
    """
    gif = (
        b"GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!"
        b"\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02"
        b"\x02D\x01\x00;"
    )
    assert len(gif) < MIN_CHARS_TO_JUDGE_DENSITY, "this case is only meaningful while it is short"
    assert not is_text(gif), "a small binary must be excluded by its encoding, not admitted by size"
