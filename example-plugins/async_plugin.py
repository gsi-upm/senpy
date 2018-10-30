from senpy import AnalysisPlugin

import multiprocessing


def _train(process_number):
    return process_number


class Async(AnalysisPlugin):
    '''An example of an asynchronous module'''
    author = '@balkian'
    version = '0.2'
    sync = False

    def _do_async(self, num_processes):
        pool = multiprocessing.Pool(processes=num_processes)
        values = sorted(pool.map(_train, range(num_processes)))

        return values

    def activate(self):
        self.value = self._do_async(4)

    def analyse_entry(self, entry, params):
        values = self._do_async(2)
        entry.async_values = values
        yield entry

    test_cases = [
        {
            'input': 'any',
            'expected': {
                'async_values': [0, 1]
            }
        }
    ]
