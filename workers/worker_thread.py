import threading
from queue import Queue, Empty

class WorkerThread(threading.Thread):
    """
    Base class for worker threads, handles queue plumbing and thread lifecycle.
    """
    def __init__(self, in_q: Queue | None, out_q: Queue | None, stop_event=None, name=None, **engines):
        super().__init__(daemon=True, name=name)
        self.in_q = in_q
        self.out_q = out_q
        self.stop_event = stop_event or threading.Event()

        # Add whatever engine instances we were passed.
        for k, v in engines.items():
            setattr(self, k, v)

    def process(self, item):
        raise NotImplementedError

    def handle_output(self, result):
        if self.out_q and result is not None:
            self.out_q.put(result)

    def run(self):
        while not self.stop_event.is_set():
            try:
                item = self.in_q.get(timeout=0.1) if self.in_q else None
            except Empty:
                continue

            if item is None:
                if self.out_q:
                    self.out_q.put(None)
                if self.in_q:
                    self.in_q.task_done()
                break

            result = self.process(item)
            """
            For writing discrete objects to the next queue, subclassed workers should
            just return the object and it will be added using `handle_output`.
            
            For writing continuous data streams, subclassed workers should write directly to the output
            queue or stream, and then return None from the process method when finished.
            """
            self.handle_output(result)

            if self.in_q:
                self.in_q.task_done()
