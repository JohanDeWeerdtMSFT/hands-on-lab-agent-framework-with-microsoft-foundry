import logging
import os
from typing import Any, cast

from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient
from agent_framework.observability import (
    create_resource,
    enable_instrumentation,
    get_tracer,
)
from agent_framework_foundry_hosting import ResponsesHostServer
from azure.identity import DefaultAzureCredential
from azure.monitor.opentelemetry import configure_azure_monitor
from dotenv import load_dotenv
from opentelemetry.trace import SpanKind, format_trace_id

from models.issue_analyzer import IssueAnalyzer
from tools.time_per_issue_tools import TimePerIssueTools

load_dotenv()


def get_model_deployment_name() -> str:
    model_deployment_name = os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME") or os.getenv(
        "FOUNDRY_MODEL_DEPLOYMENT_NAME"
    )
    if not model_deployment_name:
        raise RuntimeError(
            "Set AZURE_AI_MODEL_DEPLOYMENT_NAME or FOUNDRY_MODEL_DEPLOYMENT_NAME before starting the hosted agent."
        )
    return model_deployment_name


def create_issue_analyzer_agent() -> Agent:
    credential = DefaultAzureCredential()

    issue_analyzer_instructions = """
        You are analyzing issues.
        If the ask is a feature request the complexity should be 'NA'.
        If the issue is a bug, analyze the stack trace and provide the likely cause and complexity level.

        CRITICAL: You MUST use the provided tools for ALL calculations:
        1. First determine the complexity level
        2. Use the available tools to calculate time and cost estimates based on that complexity
        3. Never provide estimates without using the tools first

        Your response should contain only values obtained from the tool calls.
    """

    client = FoundryChatClient(
        project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
        model=get_model_deployment_name(),
        credential=credential,
    )

    time_per_issue_tools = TimePerIssueTools()

    return Agent(
        name="IssueAnalyzerAgent",
        client=client,
        instructions=issue_analyzer_instructions.strip(),
        default_options=cast(
            Any, {"store": False, "response_format": IssueAnalyzer}),
        tools=[time_per_issue_tools.calculate_time_based_on_complexity],
    )


def configure_observability() -> None:
    application_insights_connection_string = os.getenv(
        "APPLICATIONINSIGHTS_CONNECTION_STRING"
    )
    if application_insights_connection_string:
        configure_azure_monitor(
            connection_string=application_insights_connection_string,
            enable_live_metrics=True,
            resource=create_resource(),
            enable_performance_counters=False,
        )

    enable_instrumentation(enable_sensitive_data=True)


def main() -> None:
    logging.basicConfig(level=logging.ERROR, format="%(message)s")
    configure_observability()

    with get_tracer().start_as_current_span(
        "Issue Analyzer hosted Agent Workflow", kind=SpanKind.CLIENT
    ) as current_span:
        print(
            f"Trace ID: {format_trace_id(current_span.get_span_context().trace_id)}")
        server = ResponsesHostServer(create_issue_analyzer_agent())
        server.run()


if __name__ == "__main__":
    main()
