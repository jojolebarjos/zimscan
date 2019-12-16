
from collections import deque
from concurrent.futures import wait, FIRST_COMPLETED
import os


# Execute a sequence of task in worker pool
def lazy_map(iterator, executor, num_workers=-1, ordered=False):
    
    # By default, use one worker per core
    if num_workers <= 0:
        num_workers = os.cpu_count()
    
    # Store pending
    queue = deque()
    
    # Push next task to executor
    def schedule():
        try:
            task = next(iterator)
            task = executor.submit(task)
            queue.append(task)
        except StopIteration:
            pass
    
    # Schedule initial set of tasks
    for _ in range(num_workers):
        schedule()
    
    # Loop until all tasks are processed
    while len(queue) > 0:
        
        # Wait for next completed task
        if ordered:
            task = queue.popleft()
        else:
            done, not_done = wait(queue, return_when=FIRST_COMPLETED)
            task = done.pop()
            queue = [*done, *not_done]
        
        # Reschedule before yielding
        result = task.result()
        schedule()
        yield result
