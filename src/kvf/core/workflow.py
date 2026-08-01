from kvf.models.application import Application


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

        for step in self.steps:

            print(f"\n>>> {step.name}")

            step.execute(self.application)

        print("\n" + "=" * 60)
        print("Workflow Finished")
        print("=" * 60)