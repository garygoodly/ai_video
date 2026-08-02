from kvf.models.application import Application
import time

class Workflow:

    def __init__(self, application: Application):

        self.application = application
        self.steps = []

    def add_step(self, step):
        self.steps.append(step)

    def run(self):
        print("=" * 60)
        print("Workflow Started")
        print("=" * 60)

        workflow_start = time.perf_counter()

        for step in self.steps:
            name = step.__class__.__name__

            print(f">>> {name:<35}", end="", flush=True)

            start = time.perf_counter()

            step.execute(self.application)

            elapsed = time.perf_counter() - start

            print(f" [DONE {elapsed:.2f}s]")

        total = time.perf_counter() - workflow_start

        print()
        print("=" * 60)
        print(f"Workflow Finished ({total:.2f}s)")
        print("=" * 60)