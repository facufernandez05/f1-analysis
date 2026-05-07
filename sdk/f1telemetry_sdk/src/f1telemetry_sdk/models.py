from dataclasses import dataclass


@dataclass(slots=True)
class IngestRequest:
    year: int
    grand_prix: str
    session_type: str

    def to_payload(self) -> dict[str, object]:
        return {
            "year": self.year,
            "grand_prix": self.grand_prix,
            "session_type": self.session_type,
        }
