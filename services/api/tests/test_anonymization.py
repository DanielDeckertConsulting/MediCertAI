"""Anonymization regex unit tests."""
import pytest

from app.services.anonymization import anonymize


def test_anonymize_email():
    assert anonymize("Contact: user@example.com") == "Contact: [EMAIL]"
    assert anonymize("a.b+tag@domain.co.uk") == "[EMAIL]"


def test_anonymize_phone():
    assert anonymize("Tel: +49 30 12345678") == "Tel: [PHONE]"
    assert anonymize("Tel: 030-12345678") == "Tel: [PHONE]"


def test_anonymize_date_of_birth():
    assert anonymize("Geboren am 15.03.1980") == "Geboren am [DATE_OF_BIRTH]"
    assert anonymize("DOB: 1980-03-15") == "DOB: [DATE_OF_BIRTH]"


def test_anonymize_id_number():
    assert anonymize("ID: 12345678901234") == "ID: [ID_NUMBER]"


def test_anonymize_person_herr_frau():
    assert anonymize("Herr Müller kommt") == "[PERSON] kommt"
    assert anonymize("Frau Schmidt sagte") == "[PERSON] sagte"


def test_anonymize_person_dr():
    assert anonymize("Dr. Weber hat empfohlen") == "[PERSON] hat empfohlen"


def test_anonymize_combined():
    text = "Herr Müller (user@test.de) rief am 15.03.1980 an."
    result = anonymize(text)
    assert "[PERSON]" in result
    assert "[EMAIL]" in result
    assert "[DATE_OF_BIRTH]" in result
    assert "user@test.de" not in result
