from utils.linked_list import LinkedList
from utils.cli import Cli
from utils.stats import Stats
from utils.reader import Reader
from utils.record_parser import RecordParser


def main():
    args = Cli()
    stats = Stats()

    parser = RecordParser()

    with Reader(args.corpusPath) as reader:
        run = True
        while run:
            record = reader.next_line()
            if not record:
                run = False
                continue

            toks = parser.parse(record)
            print(toks)

    stats.print()


if __name__ == "__main__":
    main()
