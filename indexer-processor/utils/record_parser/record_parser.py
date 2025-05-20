from typing import Set, Any, Dict, List
import re
import nltk


nltk.download('stopwords')


class RecordParser:
    _stemmer: nltk.stem.StemmerI
    _stopwords: Set[Any]
    _token_pattern: re.Pattern[str]

    def __init__(self) -> None:
        self._stemmer = nltk.stem.SnowballStemmer('english')
        self._stopwords = set(nltk.corpus.stopwords.words("english"))
        self._token_pattern = re.compile(r"\b\w+\b")

    def parse(self, record: Dict[str, Any]) -> List[str]:
        text: str = record.get('title', '') + ' ' + record.get('text', '')
        text = text.lower()
        tokens: List[str] = self._token_pattern.findall(text)
        processed: List[str] = [
            self._stemmer.stem(tok) for tok in tokens if not tok in self._stopwords
        ]  # type: ignore
        return processed
