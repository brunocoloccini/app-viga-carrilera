from pathlib import Path


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8").lower()


def test_readme_contains_beta_signals() -> None:
    readme = _read("README.md")
    assert "crane runway" in readme
    assert "pytest -q" in readme
    assert (
        "not official cirsoc/cisc/aisc" in readme
        or "no official cirsoc/cisc/aisc" in readme
        or "official cirsoc/cisc/aisc compliance" in readme
    )


def test_required_docs_exist() -> None:
    required = [
        "docs/beta_release_checklist.md",
        "docs/getting_started_crane_runway.md",
        "docs/json_case_authoring_guide.md",
        "docs/known_limitations.md",
        "docs/command_reference.md",
    ]
    for doc in required:
        assert Path(doc).exists(), f"Missing required doc: {doc}"


def test_docs_contain_key_phrases() -> None:
    corpus = "\n".join(
        [
            _read("docs/getting_started_crane_runway.md"),
            _read("docs/json_case_authoring_guide.md"),
            _read("docs/known_limitations.md"),
            _read("README.md"),
        ]
    )
    assert "schema_version" in corpus
    assert "pythonpath=src" in corpus
    assert "sample data" in corpus
    assert "independent verification" in corpus
    assert "no fatigue" in corpus
    assert "no torsional/warping stress" in corpus


def test_examples_readme_mentions_matrix_and_golden() -> None:
    readme = _read("examples/README.md")
    assert "scenario matrix" in readme
    assert "golden" in readme
    assert "regression" in readme
