from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent


@CrewBase
class EquityResearch():
    """EquityResearch crew following Francis & Zhang (2026) Section 3.1"""

    agents: list[BaseAgent]
    tasks: list[Task]

    @agent
    def research_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['research_analyst'], # type: ignore[index]
            verbose=True
        )

    @agent
    def financial_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['financial_analyst'], # type: ignore[index]
            verbose=True
        )

    @agent
    def investment_advisor(self) -> Agent:
        return Agent(
            config=self.agents_config['investment_advisor'], # type: ignore[index]
            verbose=True
        )

    @agent
    def strategy_manager(self) -> Agent:
        return Agent(
            config=self.agents_config['strategy_manager'], # type: ignore[index]
            verbose=True
        )

    @task
    def research_task(self) -> Task:
        return Task(
            config=self.tasks_config['research_task'], # type: ignore[index]
        )

    @task
    def financial_task(self) -> Task:
        return Task(
            config=self.tasks_config['financial_task'], # type: ignore[index]
        )

    @task
    def investment_advice_task(self) -> Task:
        return Task(
            config=self.tasks_config['investment_advice_task'], # type: ignore[index]
            context=[self.research_task(), self.financial_task()]
        )

    @task
    def compile_report_task(self) -> Task:
        return Task(
            config=self.tasks_config['compile_report_task'], # type: ignore[index]
            context=[self.research_task(), self.financial_task(), self.investment_advice_task()],
            output_file='equity_research_report.md'
        )

    @crew
    def crew(self) -> Crew:
        """Creates the EquityResearch crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
