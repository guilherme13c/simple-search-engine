from utils.cli import Cli
from utils.stats import Stats
from utils.reader import Reader
from utils.record_parser import RecordParser
from utils.index import Index

def main():
    args = Cli()
    stats = Stats()

    parser = RecordParser()

    index = Index(3)

    with Reader(args.corpusPath) as reader:
        run = True
        while run:
            record = reader.next_line()
            if not record:
                run = False
                continue

            docId = int(record.get('id', -1))
            toks = parser.parse(record)

            for tok in toks:
                index.add(tok, docId)

    stats.print()


if __name__ == "__main__":
    main()
