from xml.etree import ElementTree as ET

from database.scripts.fetch_scaife_work import (
    SOURCE_AUTO,
    build_cts_url,
    build_library_passage_url,
    build_library_reffs_url,
    get_valid_reff,
    _parse_passage_xml,
    _parse_valid_reff_xml,
)


WORK_URN = "urn:cts:greekLit:tlg4090.tlg001.1st1K-grc1"
PASSAGE_URN = f"{WORK_URN}:1"


def test_builds_old_cts_and_new_library_urls():
    assert build_cts_url(
        "https://scaife-cts.perseus.org/api/cts",
        "GetValidReff",
        urn=WORK_URN,
        level=2,
    ) == (
        "https://scaife-cts.perseus.org/api/cts"
        "?request=GetValidReff&urn=urn:cts:greekLit:tlg4090.tlg001.1st1K-grc1&level=2"
    )

    assert build_library_reffs_url(
        "https://scaife.perseus.org/library/",
        WORK_URN,
        2,
    ) == (
        "https://scaife.perseus.org/library"
        "/urn:cts:greekLit:tlg4090.tlg001.1st1K-grc1/cts-api-xml/reffs/?level=2"
    )

    assert build_library_passage_url(
        "https://scaife.perseus.org/library",
        PASSAGE_URN,
    ) == (
        "https://scaife.perseus.org/library"
        "/urn:cts:greekLit:tlg4090.tlg001.1st1K-grc1:1/cts-api-xml/"
    )


def test_parse_valid_reff_xml_from_cts_response():
    root = ET.fromstring(
        """
        <GetValidReff xmlns="http://chs.harvard.edu/xmlns/cts">
          <reply>
            <reff>
              <urn>urn:cts:greekLit:tlg4090.tlg001.1st1K-grc1:1</urn>
              <urn>urn:cts:greekLit:tlg4090.tlg001.1st1K-grc1:2</urn>
            </reff>
          </reply>
        </GetValidReff>
        """
    )

    assert _parse_valid_reff_xml(root) == [
        "urn:cts:greekLit:tlg4090.tlg001.1st1K-grc1:1",
        "urn:cts:greekLit:tlg4090.tlg001.1st1K-grc1:2",
    ]


def test_parse_passage_xml_from_library_response():
    root = ET.fromstring(
        """
        <GetPassage xmlns="http://chs.harvard.edu/xmlns/cts">
          <reply>
            <passage>
              <TEI xmlns="http://www.tei-c.org/ns/1.0">
                <text>
                  <body>
                    <div>
                      <p>λόγος <note>skip me</note>πρῶτος.</p>
                      <p>δεύτερος λόγος.</p>
                    </div>
                  </body>
                </text>
              </TEI>
            </passage>
          </reply>
        </GetPassage>
        """
    )

    assert _parse_passage_xml(root, PASSAGE_URN) == "λόγος πρῶτος. δεύτερος λόγος."


def test_auto_valid_reff_falls_back_to_library(monkeypatch):
    calls = []
    library_xml = ET.fromstring(
        """
        <GetValidReff xmlns="http://chs.harvard.edu/xmlns/cts">
          <reply><reff><urn>urn:cts:greekLit:tlg4090.tlg001.1st1K-grc1:1</urn></reff></reply>
        </GetValidReff>
        """
    )

    def fake_fetch_xml(url):
        calls.append(url)
        if "scaife-cts" in url:
            raise OSError("TLS handshake failed")
        return library_xml

    monkeypatch.setattr("database.scripts.fetch_scaife_work._fetch_xml", fake_fetch_xml)

    assert get_valid_reff(WORK_URN, level=1, source=SOURCE_AUTO) == [PASSAGE_URN]
    assert calls == [
        (
            "https://scaife-cts.perseus.org/api/cts"
            "?request=GetValidReff&urn=urn:cts:greekLit:tlg4090.tlg001.1st1K-grc1&level=1"
        ),
        (
            "https://scaife.perseus.org/library"
            "/urn:cts:greekLit:tlg4090.tlg001.1st1K-grc1/cts-api-xml/reffs/?level=1"
        ),
    ]
