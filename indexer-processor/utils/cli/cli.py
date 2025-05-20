import argparse


class Cli:
    corpusPath: str
    indexDirPath: str
    availableMemory: int

    def __init__(self):
        parser = argparse.ArgumentParser()

        parser.add_argument(
            "-c",
            "--corpus",
            help="path to the corpus jsonl file to be indexed",
            type=str,
            required=False,
            default="corpus.jsonl",
            dest='corpusPath',
        )
        parser.add_argument(
            "-i",
            "--index",
            help="path to the directory where indexes should be created",
            type=str,
            required=False,
            default="indexes",
            dest='indexDirPath',
        )
        parser.add_argument(
            "-m",
            "--memory",
            help="memory available to the indexer in megabytes",
            type=int,
            required=False,
            default=1024,
            dest='availableMemory',
        )

        parser.parse_args(namespace=self)
