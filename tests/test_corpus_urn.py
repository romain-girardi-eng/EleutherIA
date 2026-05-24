from scripts.corpus_urn import derive_work_urn


def test_single_work_urn():
    urns = ["urn:cts:greekLit:tlg0086.tlg028:9.18a",
            "urn:cts:greekLit:tlg0086.tlg028:9.19b"]
    assert derive_work_urn(urns) == ("urn:cts:greekLit:tlg0086.tlg028", "resolved")


def test_ambiguous_when_multiple_work_urns():
    urns = ["urn:cts:greekLit:tlg0086.tlg028:9",
            "urn:cts:greekLit:tlg0086.tlg010:1"]
    urn, status = derive_work_urn(urns)
    assert status == "ambiguous"
    assert urn is None


def test_unresolved_when_no_valid_urn():
    assert derive_work_urn(["", "chap.1.par.2", None]) == (None, "unresolved")
