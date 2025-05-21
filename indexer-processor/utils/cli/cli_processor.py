import argparse


class CliProcessor:
    queries_path: str
    index_path: str
    ranker: str
    page_size: int

    def __init__(self) -> None:
        parser = argparse.ArgumentParser()

        parser.add_argument(
            "-q",
            "--queries",
            help="path to the file containing the queries",
            type=str,
            required=True,
            dest='queries_path',
        )
        parser.add_argument(
            "-i",
            "--index",
            help="path to the index file",
            type=str,
            required=True,
            dest='index_path',
        )
        parser.add_argument(
            "-r",
            "--ranker",
            help="ranking funtion to be used",
            choices=["TFIDF", "BM25"],
            type=str,
            required=True,
            dest='ranker',
        )
        parser.add_argument(
            "-t",
            "--top",
            help="number of elements to be returned",
            type=int,
            required=False,
            default=10,
            dest='page_size'
        )

        parser.parse_args(namespace=self)
