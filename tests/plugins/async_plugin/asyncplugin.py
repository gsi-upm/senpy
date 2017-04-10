from senpy.plugins import AnalysisPlugin

import multiprocessing


class AsyncPlugin(AnalysisPlugin):
    def _train(self, process_number):
        return process_number

    def _do_async(self, num_processes):
        with multiprocessing.Pool(processes=num_processes) as pool:
            values = pool.map(self._train, range(num_processes))
        return values

    def activate(self):
        self.value = self._do_async(4)

    def analyse_entry(self, entry, params):
        values = self._do_async(2)
        entry.async_values = values
        yield entry
