import time


class Stats:
    begin: float
    indexSize: int
    listCount: int
    sumListLen: int

    def __init__(self):
        self.begin = time.time()
        self.indexSize = 0
        self.listCount = 0
        self.sumListLen = 0

    def print(self):
        self.listCount = max(1, self.listCount)
        print(
            r'{',
            f'\t"Index Size": {None},',
            f'\t"Elapsed Time": {time.time()-self.begin},',
            f'\t"Number of Lists": {self.listCount},',
            f'\t"Average List Size": {self.sumListLen/self.listCount}',
            r'}',
            sep='\n'
        )
