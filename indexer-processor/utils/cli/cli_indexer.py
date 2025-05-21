import argparse


class CliIndexer:
    corpus_path: str
    index_dir: str
    available_memory: int
    workers: int

    def __init__(self):
        parser = argparse.ArgumentParser()

        parser.add_argument(
            "-c",
            "--corpus",
            help="path to the corpus jsonl file to be indexed",
            type=str,
            required=False,
            default="corpus.jsonl",
            dest='corpus_path',
        )
        parser.add_argument(
            "-i",
            "--index",
            help="path to the directory where the indexes should be created",
            type=str,
            required=False,
            default="indexes",
            dest='index_dir',
        )
        parser.add_argument(
            "-m",
            "--memory",
            help="memory available to the indexer in megabytes",
            type=int,
            required=False,
            default=1024,
            dest='available_memory',
        )
        parser.add_argument(
            "-w",
            "--workers",
            help="number of workers",
            type=int,
            required=False,
            default=0,
            dest='workers',
        )

        parser.parse_args(namespace=self)
