#!/usr/bin/env python

import os
from typing import Any

from loguru import logger
from pydantic import BaseModel

from crewai.flow import Flow, listen, start
from crewai.flow.persistence import persist

from la_vie.crews.content_crew.content_crew import ContentCrew


DEFAULT_TOPIC = "AI Agents"


class ContentState(BaseModel):
    topic: str = ""
    final_post: str = ""


@persist()
class ContentFlow(Flow[ContentState]):
    @start()
    def plan_content(self, crewai_trigger_payload: dict[str, Any] | None = None) -> None:
        logger.info("Planning content")

        if crewai_trigger_payload:
            self.state.topic = crewai_trigger_payload.get(
                "topic", self.state.topic or DEFAULT_TOPIC
            )
            logger.info("Using trigger payload: {}", crewai_trigger_payload)
        elif not self.state.topic:
            self.state.topic = DEFAULT_TOPIC

        logger.info("Topic: {}", self.state.topic)

    @listen(plan_content)
    def generate_content(self) -> str:
        logger.info("Generating content on: {}", self.state.topic)
        result = (
            ContentCrew()
            .crew()
            .kickoff(inputs={"topic": self.state.topic})
        )

        logger.info("Content generated")
        return result.raw

    @listen(generate_content)
    def save_content(self, generated_content: str) -> str:
        logger.info("Saving content to flow state")
        self.state.final_post = generated_content
        logger.info("Post saved to flow state")
        return self.state.final_post


def run_content_flow(
    *,
    inputs: dict[str, Any] | None = None,
    restore_from_state_id: str | None = None,
) -> Any:
    content_flow = ContentFlow()
    return content_flow.kickoff(
        inputs=inputs,
        restore_from_state_id=restore_from_state_id,
    )


def kickoff(restore_from_state_id: str | None = None) -> Any:
    """Run the CrewAI flow entrypoint expected by `crewai run`."""
    restore_from_state_id = restore_from_state_id or os.getenv("RESTORE_FROM_STATE_ID")
    return run_content_flow(restore_from_state_id=restore_from_state_id)


def plot() -> None:
    """Generate the CrewAI flow visualization."""
    ContentFlow().plot()


def trigger_inputs_from_payload(
    payload: dict[str, Any],
) -> tuple[dict[str, Any], str | None]:
    restore_from_state_id = payload.get("restore_from_state_id") or payload.get(
        "restoreFromStateId"
    )

    if "inputs" in payload:
        inputs = payload["inputs"]
        if inputs is None:
            inputs = {}
    else:
        inputs = {"crewai_trigger_payload": payload}

    if not isinstance(inputs, dict):
        raise ValueError("Trigger payload 'inputs' must be a JSON object")
    if restore_from_state_id is not None and not isinstance(
        restore_from_state_id, str
    ):
        raise ValueError("Trigger payload restore state id must be a string")

    return inputs, restore_from_state_id


def run_with_trigger_payload(payload: dict[str, Any]) -> Any:
    inputs, restore_from_state_id = trigger_inputs_from_payload(payload)
    return run_content_flow(
        inputs=inputs,
        restore_from_state_id=restore_from_state_id,
    )


def run_with_trigger() -> Any:
    """Run the flow with a JSON trigger payload passed as argv[1]."""
    import json
    import sys

    if len(sys.argv) < 2:
        raise ValueError(
            "No trigger payload provided. Please provide JSON payload as argument."
        )

    try:
        trigger_payload = json.loads(sys.argv[1])
    except json.JSONDecodeError as exc:
        raise ValueError("Invalid JSON payload provided as argument") from exc

    if not isinstance(trigger_payload, dict):
        raise ValueError("Trigger payload must be a JSON object")

    return run_with_trigger_payload(trigger_payload)


if __name__ == "__main__":
    kickoff()
