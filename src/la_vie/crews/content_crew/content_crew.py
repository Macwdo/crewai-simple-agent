import os

from crewai import Agent, Crew, LLM, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task


DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
CODEX_LB_BASE_URL = "http://127.0.0.1:2455/v1"
CODEX_LB_MODEL = "gpt-5.4"


def content_llm() -> LLM:
    base_url = os.getenv("OPENAI_BASE_URL", DEFAULT_OPENAI_BASE_URL)
    model = (
        CODEX_LB_MODEL
        if base_url.rstrip("/") == CODEX_LB_BASE_URL
        else DEFAULT_OPENAI_MODEL
    )

    return LLM(
        model=model,
        base_url=base_url,
        api_key=os.getenv("OPENAI_API_KEY"),
    )


@CrewBase
class ContentCrew:
    """Content Crew"""

    agents: list[BaseAgent]
    tasks: list[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def planner(self) -> Agent:
        return Agent(
            config=self.agents_config["planner"],  # type: ignore[index]
            llm=content_llm(),
        )

    @agent
    def writer(self) -> Agent:
        return Agent(
            config=self.agents_config["writer"],  # type: ignore[index]
            llm=content_llm(),
        )

    @agent
    def editor(self) -> Agent:
        return Agent(
            config=self.agents_config["editor"],  # type: ignore[index]
            llm=content_llm(),
        )

    @task
    def planning_task(self) -> Task:
        return Task(
            config=self.tasks_config["planning_task"],  # type: ignore[index]
        )

    @task
    def writing_task(self) -> Task:
        return Task(
            config=self.tasks_config["writing_task"],  # type: ignore[index]
        )

    @task
    def editing_task(self) -> Task:
        return Task(
            config=self.tasks_config["editing_task"],  # type: ignore[index]
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Content Crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=False,
        )
