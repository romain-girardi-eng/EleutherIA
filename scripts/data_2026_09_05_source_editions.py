"""Reviewed source bindings for the September publication repair.

No ancient text is authored here. The apply script extracts the pinned TEI files.
"""

STAMP = "source_editions_2026_09_05"
SOURCES = {
    # TEI sourceDesc: Müller, De Fato, Leipzig: Teubner, 1915; sections 1–48.
    "cicero": {
        "file": "phi0474.phi054.perseus-lat1.xml",
        "sha256": "b6f9f292b185e249928f351ae36e8083153e35a284d928b254312dd165f99b78",
        "url": "https://raw.githubusercontent.com/PerseusDL/canonical-latinLit/669d3657637ee44fb0aed2c37dd0f95c2b062193/data/phi0474/phi054/phi0474.phi054.perseus-lat1.xml",
        "edition": "C. F. W. Müller, De Fato (Teubner, 1915); Perseus Digital Library",
        "urn": "urn:cts:latinLit:phi0474.phi054.perseus-lat1",
        "manifest": "urn_cts_latinlit_phi0474_phi054_lat",
        "language": "lat",
        "license": "CC-BY-SA-4.0",
    },
    # CTS work metadata and sourceDesc identify Romans, Westcott/Hort 1882–1892.
    # The source groups authors as "New Testament"; Romans 1.1 names Paul.
    "romans": {
        "file": "tlg0031.tlg006.perseus-grc2.xml",
        "sha256": "8ca2f87c54f331c4d8c9d48af1167cf2920d2461bf45513f5e49fcb2700b2e36",
        "url": "https://raw.githubusercontent.com/PerseusDL/canonical-greekLit/70427323b61267cdcd0256b9b02009c23392de07/data/tlg0031/tlg006/tlg0031.tlg006.perseus-grc2.xml",
        "edition": "B. F. Westcott and F. J. A. Hort, The New Testament in the Original Greek (Harper, 1882–1892); Perseus Digital Library",
        "urn": "urn:cts:greekLit:tlg0031.tlg006.perseus-grc2",
        "manifest": "romans_westcott_hort_perseus_grc2",
        "language": "grc",
        "license": "CC-BY-SA-4.0",
    },
}
# A section reading includes the edited body, not argumentum, notes or deleted
# readings. Raw TEI is retained so editorial markup is always inspectable.
EXCLUDED_TEI = {"note", "del", "head", "pb", "milestone"}
