from senpy.plugins import AnalysisPlugin

import multiprocessing


def _train(process_number):
    return process_number


class AsyncPlugin(AnalysisPlugin):
    def _do_async(self, num_processes):
        pool = multiprocessing.Pool(processes=num_processes)
        values = pool.map(_train, range(num_processes))

        return values

    def activate(self):
        self.value = self._do_async(4)

    def analyse_entry(self, entry, params):
        values = self._do_async(2)
        entry.async_values = values
        yield entry

    def test(self):
        pass
