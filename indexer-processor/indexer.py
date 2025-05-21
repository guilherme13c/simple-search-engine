from typing import List
from utils.cli import Cli
from utils.reader import Reader
from utils.record_parser import RecordParser
from utils.index import Index


def main() -> None:
    args = Cli()

    parser = RecordParser()

    index = Index(args.indexDirPath, 3)

    with Reader(args.corpusPath) as reader:
        run = True
        while run:
            record = reader.next_line()
            if not record:
                run = False
                continue

            docId = int(record.get('id', -1))
            toks: List[str] = parser.parse(record)

            for tok in toks:
                index.add(tok, docId)

    index.save()

if __name__ == "__main__":
    main()
