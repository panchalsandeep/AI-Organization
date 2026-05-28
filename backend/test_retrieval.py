from backend.retrieval.search_memory import search_memory


def test_search_memory_returns_results():
    results = search_memory("AI operating system strategy")

    assert isinstance(results, list)
    assert len(results) > 0
    assert "content" in results[0]
    assert "similarity" in results[0]


if __name__ == "__main__":
    results = search_memory("AI operating system strategy")
    print(results)
