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

import os
import subprocess
from functools import lru_cache
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def is_suspicious(byte: int) -> bool:
    """True for control bytes never legitimate in a text file.

    Tab (0x09), newline (0x0A) and carriage return (0x0D) are excluded: they are
    ordinary formatting. Everything else below 0x20 indicates an escape that was
    interpreted when it should have been written literally.
    """
    return byte < 0x09 or byte in (0x0B, 0x0C) or 0x0D < byte < 0x20


# Tracked paths that are binary and must not be scanned.
#
# EMPTY, and measured rather than assumed: all 1,320 tracked files in this
# repository contain zero control bytes, so none of them is binary. Every
# heuristic that tried to infer this instead had a hole -- deciding on the first
# NUL hid a NUL-corrupted source file, a size exemption admitted a 34-byte GIF,
# a byte density called a PNG text, and a control-character density discarded
# the most heavily corrupted files, which are the ones this gate exists to
# catch. Each fix moved the hole rather than closing it, because "is this
# binary" cannot be answered from bytes without guessing.
#
# So it is not inferred. If a binary asset is ever tracked, this gate fails on
# it with an actionable message and someone adds its path here -- a deliberate,
# reviewable line rather than a guess that silently drops files from the scan.
EXPECTED_BINARY_PATHS: frozenset[str] = frozenset()


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
    absent: list[str] = []
    for entry in result.stdout.split(b"\0"):
        if not entry:
            continue
        # os.fsdecode, not a strict UTF-8 decode: on POSIX a filename is a byte
        # string that need not be valid UTF-8, and `git ls-files -z` returns those
        # bytes verbatim. A strict decode would raise and take the whole scan down
        # over a filename, which is the gate failing for a reason unrelated to what
        # it checks. surrogateescape round-trips such names back to the filesystem.
        path = root / os.fsdecode(entry)
        # A symlink is NOT skipped. Git stores the target string as the blob, so
        # an interpreted escape lands in that target exactly as it would in a
        # file, and skipping the path would drop the one thing worth reading.
        if not path.is_symlink() and not path.is_file():
            # Tracked but absent from the working tree: a sparse checkout keeps
            # such paths in the index while omitting the files. Skipping them
            # silently would shrink the scan without shrinking what it claims to
            # have read, which is the failure this whole module is about.
            absent.append(path.relative_to(root).as_posix())
            continue
        # Scoped to THIS repository. The list names paths in lotus-gateway, so
        # applying it to a fixture repository would excuse a file that merely
        # shares a name -- and silently narrow a test's own scan.
        if root == REPO_ROOT and path.relative_to(root).as_posix() in EXPECTED_BINARY_PATHS:
            continue
        paths.append(path)

    if absent:
        raise AssertionError(
            f"{len(absent)} tracked path(s) are not present in this working tree, so the "
            "scan cannot cover what git tracks. A sparse checkout produces exactly this. "
            "Run this gate in a full checkout rather than accepting a narrowed scan: "
            + ", ".join(sorted(absent)[:5])
        )
    return tuple(paths)


def _source_inventory(root: Path = REPO_ROOT) -> list[Path]:
    """The cached inventory, as a list.

    Cached because four assertions need it and each rebuild reads every tracked
    file. Over the CI-local bind mount that difference was minutes, and a gate
    people wait for is a gate people skip.
    """
    return list(_inventory(root))


def _stored_bytes(path: Path) -> bytes:
    """What git stores for this path.

    For a regular file that is its content. For a symlink it is the TARGET
    string, which is the blob git holds -- reading through the link would scan
    whatever it points at instead, which is a different file and may not even be
    tracked.
    """
    if path.is_symlink():
        return os.fsencode(os.readlink(path))
    return path.read_bytes()


def find_offenders(paths: list[Path]) -> list[str]:
    """Report the first control byte in each file that carries one."""
    offenders: list[str] = []
    for path in paths:
        data = _stored_bytes(path)
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
        "matches nothing and its guard passes silently. If one of these is a "
        "genuinely binary asset, add its path to EXPECTED_BINARY_PATHS rather "
        "than loosening the detector: " + "; ".join(offenders)
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
    # A workstation with commit.gpgsign or core.hooksPath set would otherwise
    # make these fixtures prompt, fail, or run someone's hooks -- a test failing
    # for a reason that has nothing to do with what it checks.
    run_git("config", "commit.gpgsign", "false")
    run_git("config", "core.hooksPath", "/dev/null")
    # A global core.excludesFile containing the common *.log pattern would make
    # the tracked-log fixture unaddable, and the test would fail before reaching
    # the inventory it exists to exercise.
    run_git("config", "core.excludesFile", "/dev/null")

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
        assert not [byte for byte in data if is_suspicious(byte)]


def test_every_excusal_is_load_bearing() -> None:
    """A declared path must exist, and must be something the scan actually rejects.

    This is what stops the list becoming a way to quieten the gate: a clean file
    cannot be excused, because excusing it changes nothing and the entry is inert.

    It deliberately does NOT require a NUL. Not every binary format carries one in
    its first block, and demanding one would refuse a legitimate declaration for a
    file the scan genuinely rejects — the gate telling you to add a path and then
    rejecting the path you add.

    What this cannot do is separate a real binary from corrupted text, because the
    detector rejects both. That judgement is why each entry is a deliberate line in
    a reviewed file rather than an inference: a corrupted source file must be
    repaired, not excused.
    """
    tracked = {
        os.fsdecode(entry)
        for entry in subprocess.run(
            ["git", "-C", str(REPO_ROOT), "ls-files", "-z"], capture_output=True, check=True
        ).stdout.split(b"\0")
        if entry
    }
    for declared in sorted(EXPECTED_BINARY_PATHS):
        path = REPO_ROOT / declared
        assert path.is_file(), f"{declared} is excused from the scan but does not exist"
        assert declared in tracked, (
            f"{declared} is excused from the scan but is not tracked; the scan only "
            "reads tracked files, so the entry excuses nothing and hides that the "
            "asset left version control"
        )
        assert find_offenders([path]), (
            f"{declared} is excused from the scan, but the scan does not reject it; "
            "the entry does nothing and should be removed"
        )


def test_a_declared_binary_path_is_excluded(tmp_path: Path, monkeypatch) -> None:
    """Declaring a path must actually remove it from the scan.

    An exception list nothing consults would leave a real binary failing the gate
    forever with no way to resolve it except weakening the detector.
    """
    repo = tmp_path / "with-binary"
    repo.mkdir()

    def run_git(*args: str) -> None:
        subprocess.run(["git", "-C", str(repo), *args], capture_output=True, check=True)

    run_git("init", "--quiet", "--initial-branch=main")
    run_git("config", "user.email", "test@example.invalid")
    run_git("config", "user.name", "Test")
    # A workstation with commit.gpgsign or core.hooksPath set would otherwise
    # make these fixtures prompt, fail, or run someone's hooks -- a test failing
    # for a reason that has nothing to do with what it checks.
    run_git("config", "commit.gpgsign", "false")
    run_git("config", "core.hooksPath", "/dev/null")
    # A global core.excludesFile containing the common *.log pattern would make
    # the tracked-log fixture unaddable, and the test would fail before reaching
    # the inventory it exists to exercise.
    run_git("config", "core.excludesFile", "/dev/null")

    asset = repo / "logo.gif"
    asset.write_bytes(b"GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!")
    (repo / "app.py").write_text("value = 1\n", encoding="utf-8")
    run_git("add", "logo.gif", "app.py")
    run_git("commit", "--quiet", "-m", "fixture")

    _inventory.cache_clear()
    assert asset in set(_source_inventory(repo)), "undeclared, the asset is scanned and reported"
    assert find_offenders([asset]), "and it does carry bytes the detector rejects"

    # Both are patched. The exclusion list is scoped to REPO_ROOT, so the fixture
    # must BE the repository root for a declaration to apply to it; patching only
    # the list would leave this test silently proving nothing.
    monkeypatch.setattr("test_source_control_bytes.REPO_ROOT", repo)
    monkeypatch.setattr("test_source_control_bytes.EXPECTED_BINARY_PATHS", frozenset({"logo.gif"}))
    _inventory.cache_clear()
    try:
        assert asset not in set(_source_inventory(repo)), "declared, it is excluded"
    finally:
        _inventory.cache_clear()
