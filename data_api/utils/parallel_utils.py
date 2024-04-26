# System Imports
from concurrent.futures import (
    as_completed,
    Future,
    ProcessPoolExecutor,
)
from typing import List

class ParallelProcessExecutor:

    @classmethod
    def run(cls, func, inputs: List) -> None:
        with ProcessPoolExecutor() as executor:
            futures = [
				executor.submit(func, i) 
				for i in inputs
			]

            for future in as_completed(futures):
                cls._handle_exceptions(future)

    @classmethod
    def _handle_exceptions(cls, future: Future) -> None:
        try:
            future.result()
        except Exception as e:
            print("An exception occurred: {}".format(e))
        