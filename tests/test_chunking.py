from chunking import chunk_text


def test_empty_text():
    assert chunk_text("") == []


def test_short_text():
    text = "This is a short research abstract."
    assert chunk_text(text) == [text]


def test_chunk_overlap():
    words = [f"word{i}" for i in range(1, 401)]
    text = " ".join(words)

    chunks = chunk_text(
        text,
        chunk_size=200,
        overlap=40,
    )

    assert len(chunks) == 3

    first_words = chunks[0].split()
    second_words = chunks[1].split()

    assert first_words[-40:] == second_words[:40]


def test_invalid_overlap():
    try:
        chunk_text("sample text", chunk_size=10, overlap=10)
    except ValueError:
        return

    assert False, "Expected ValueError"