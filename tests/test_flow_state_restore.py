import unittest
import warnings
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

warnings.filterwarnings(
    "ignore",
    category=ResourceWarning,
    message="unclosed database.*",
)

from crewai.flow import Flow, listen, start
from crewai.flow.persistence import persist
from crewai.flow.persistence.sqlite import SQLiteFlowPersistence
from pydantic import BaseModel, Field

from la_vie.main import ContentFlow, run_with_trigger_payload


def setUpModule():
    warnings.simplefilter("ignore", ResourceWarning)


def kickoff_quietly(flow, *args, **kwargs):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ResourceWarning)
        with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            return flow.kickoff(*args, **kwargs)


class RunWithTriggerPayloadTests(unittest.TestCase):
    def test_passes_restore_from_state_id_from_amp_payload(self):
        calls = []

        def fake_run_content_flow(*, inputs=None, restore_from_state_id=None):
            calls.append(
                {
                    "inputs": inputs,
                    "restore_from_state_id": restore_from_state_id,
                }
            )
            return "flow-result"

        payload = {
            "inputs": {"topic": "CrewAI persistence"},
            "restoreFromStateId": "previous-state-id",
        }

        with patch("la_vie.main.run_content_flow", fake_run_content_flow):
            result = run_with_trigger_payload(payload)

        self.assertEqual(result, "flow-result")
        self.assertEqual(
            calls,
            [
                {
                    "inputs": {"topic": "CrewAI persistence"},
                    "restore_from_state_id": "previous-state-id",
                }
            ],
        )


class ContentFlowOutputTests(unittest.TestCase):
    def test_save_content_returns_state_value_for_status_result(self):
        flow = ContentFlow(suppress_flow_events=True, tracing=False)

        result = flow.save_content("generated post")

        self.assertEqual(result, "generated post")
        self.assertEqual(flow.state.final_post, "generated post")


class StepFailureState(BaseModel):
    topic: str = ""
    fail_during_step: bool = False
    steps: list[str] = Field(default_factory=list)


class RestoreFromStateIdTests(unittest.TestCase):
    def test_failed_run_can_fork_from_previous_persisted_state(self):
        with TemporaryDirectory() as tmp_dir:
            persistence = SQLiteFlowPersistence(str(Path(tmp_dir) / "flow.db"))

            @persist(persistence)
            class StepFailureFlow(Flow[StepFailureState]):
                @start()
                def prepare(self):
                    if not self.state.topic:
                        self.state.topic = "default topic"
                    self.state.steps = [*self.state.steps, "prepare"]

                @listen(prepare)
                def fail_or_complete(self):
                    self.state.steps = [*self.state.steps, "fail_or_complete"]
                    if self.state.fail_during_step:
                        raise RuntimeError("planned step failure")
                    self.state.steps = [*self.state.steps, "complete"]

            source_flow = StepFailureFlow(suppress_flow_events=True, tracing=False)
            kickoff_quietly(source_flow, inputs={"topic": "previous topic"})
            source_id = source_flow.state.id
            source_snapshot = persistence.load_state(source_id)

            failed_flow = StepFailureFlow(suppress_flow_events=True, tracing=False)
            with self.assertRaisesRegex(RuntimeError, "planned step failure"):
                kickoff_quietly(
                    failed_flow,
                    inputs={"fail_during_step": True},
                    restore_from_state_id=source_id,
                )

            self.assertNotEqual(failed_flow.state.id, source_id)
            self.assertEqual(failed_flow.state.topic, "previous topic")
            self.assertEqual(
                persistence.load_state(source_id),
                source_snapshot,
            )

            restored_flow = StepFailureFlow(suppress_flow_events=True, tracing=False)
            kickoff_quietly(restored_flow, restore_from_state_id=source_id)

            self.assertNotEqual(restored_flow.state.id, source_id)
            self.assertNotEqual(restored_flow.state.id, failed_flow.state.id)
            self.assertEqual(restored_flow.state.topic, "previous topic")
            self.assertEqual(
                restored_flow.state.steps,
                [
                    "prepare",
                    "fail_or_complete",
                    "complete",
                    "prepare",
                    "fail_or_complete",
                    "complete",
                ],
            )


if __name__ == "__main__":
    unittest.main()
