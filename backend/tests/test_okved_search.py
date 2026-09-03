import okved_search


def test_short_query_returns_nothing(session, okved_rows, fake_query_vector):
    assert okved_search.search(session, "ит") == []
    assert okved_search.search(session, "  ") == []
    assert okved_search.search(session, None) == []


def test_vector_branch_picks_nearest(session, okved_rows, fake_query_vector):
    fake_query_vector["vector"] = okved_rows[2][2]
    results = okved_search.search(session, "стрижки и укладки", limit=1)
    assert [row["code"] for row in results] == ["96.02"]


def test_lexical_branch_finds_word(session, okved_rows, fake_query_vector):
    fake_query_vector["vector"] = okved_rows[0][2]
    results = okved_search.search(session, "производство хлеба", limit=3)
    assert "10.71" in [row["code"] for row in results]


def test_limit_is_respected(session, okved_rows, fake_query_vector):
    results = okved_search.search(session, "производство программного хлеба", limit=2)
    assert len(results) == 2


def test_score_is_cosine_similarity(session, okved_rows, fake_query_vector):
    fake_query_vector["vector"] = okved_rows[0][2]
    results = okved_search.search(session, "разработка софта", limit=1)
    assert results[0]["score"] == 1.0


def test_suggest_endpoint_returns_items(client, okved_rows, fake_query_vector):
    fake_query_vector["vector"] = okved_rows[1][2]
    response = client.get("/okved/suggest", params={"q": "пекарня", "limit": 1})
    assert response.status_code == 200
    assert response.json()["items"][0]["code"] == "10.71"


def test_suggest_endpoint_caps_limit(client, many_okved_rows, fake_query_vector):
    response = client.get("/okved/suggest", params={"q": "производство изделий", "limit": 500})
    assert response.status_code == 200
    assert len(response.json()["items"]) == 10


def test_suggest_endpoint_raises_zero_limit(client, many_okved_rows, fake_query_vector):
    response = client.get("/okved/suggest", params={"q": "производство изделий", "limit": 0})
    assert response.status_code == 200
    assert len(response.json()["items"]) == 1
