import logging
import os
from typing import Any, cast

from agent_framework import Agent, MCPStreamableHTTPTool
from agent_framework.foundry import FoundryChatClient
from agent_framework.observability import (
    create_resource,
    enable_instrumentation,
    get_tracer,
)
from agent_framework_devui import register_cleanup, serve
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition
from azure.identity import DefaultAzureCredential
from azure.monitor.opentelemetry import configure_azure_monitor
from dotenv import load_dotenv
from httpx import AsyncClient
from opentelemetry.trace import SpanKind, format_trace_id

from models.issue_analyzer import IssueAnalyzer
from tools.time_per_issue_tools import TimePerIssueTools

load_dotenv()

# ISSUE_CONTEXT = """
# There is an issue with the Azure App Services is causing intermittent 500 errors.
#                         Traceback (most recent call last):
#                                     File "<string>", line 38, in <module>
#                                         main_application()                    ← Entry point
#                                     File "<string>", line 30, in main_application
#                                         results = process_data_batch(test_data)  ← Calls processor
#                                     File "<string>", line 13, in process_data_batch
#                                         avg = calculate_average(batch)        ← Calls calculator
#                                     File "<string>", line 5, in calculate_average
#                                         return total / count                  ← ERROR HERE
#                                             ~~~~~~^~~~~~~
#                                     ZeroDivisionError: division by zero
# """


def main():
    logging.basicConfig(level=logging.ERROR, format="%(message)s")

    # Create the agent here
    credential = DefaultAzureCredential()

    # first agent for issue analysis and estimation

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

    project = AIProjectClient(
        endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
        credential=credential,
    )
    model_name = os.environ["FOUNDRY_MODEL_DEPLOYMENT_NAME"]

    issue_analyzer_agent_detail = project.agents.create_version(
        agent_name="IssueAnalyzerAgent",
        definition=PromptAgentDefinition(
            model=model_name,
            instructions=issue_analyzer_instructions.strip(),
        ),
    )

    time_per_issue_tools = TimePerIssueTools()

    issue_analyzer_agent = Agent(
        name=issue_analyzer_agent_detail.name,
        client=FoundryChatClient(
            project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
            model=os.environ["FOUNDRY_MODEL_DEPLOYMENT_NAME"],
            credential=credential,
        ),
        instructions=issue_analyzer_instructions.strip(),
        default_options=cast(Any, {"response_format": IssueAnalyzer}),
        tools=[time_per_issue_tools.calculate_time_based_on_complexity],
    )
    # -------------------------------

    # second agent for GitHub issue creation

    github_repository_owner, github_repository_name = os.environ["GITHUB_REPOSITORY"].split(
        "/", 1
    )

    github_instructions = f"""
        You are a helpful assistant that can create GitHub issues following Contoso's guidelines.
        You work on this repository: {github_repository_owner}/{github_repository_name}
        Repository owner: {github_repository_owner}
        Repository name: {github_repository_name}
        
        Use the GitHub MCP issue_write tool to create the issue with properly formatted content.

        When creating an issue, ALWAYS call issue_write with these arguments:
        - method: "create"
        - owner: "{github_repository_owner}"
        - repo: "{github_repository_name}"
        - title: a concise issue title
        - body: a clear issue body with the relevant problem, context, and acceptance criteria or reproduction details

        Never call issue_write with empty arguments. Never ask the user for the repository owner or repository name; they are already provided above.
        If the user asks for a random issue, invent a reasonable issue title and body and create it in the configured repository.

        MANDATORY: You MUST always call the GitHub MCP tool to create the issue. Never just describe the issue without creating it. Your task is not complete until the issue is actually created on GitHub.
    """

    github_agent_detail = project.agents.create_version(
        agent_name="GitHubAgent",
        definition=PromptAgentDefinition(
            model=model_name,
            instructions=github_instructions.strip(),
        ),
    )

    github_chat_client = FoundryChatClient(
        project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
        model=os.environ["FOUNDRY_MODEL_DEPLOYMENT_NAME"],
        credential=credential,
    )

    github_mcp_http_client = AsyncClient(
        headers={
            "Authorization": f"Bearer {os.environ['GITHUB_MCP_PAT']}",
            "Accept": "application/json, text/event-stream",
        }
    )

    github_agent = Agent(
        name=github_agent_detail.name,
        client=github_chat_client,
        instructions=github_instructions.strip(), 
        tools=[
            MCPStreamableHTTPTool(
                name="GitHub",
                url="https://api.githubcopilot.com/mcp/",
                approval_mode="never_require",
                http_client=github_mcp_http_client,
            ),
        ],
    )

    # -------------------------------

    # serve(entities=[issue_analyzer_agent], port=8090, auto_open=True)
    # Cleanup hooks execute during DevUI server shutdown, before entity clients are closed. Supports both synchronous and asynchronous callables.
    register_cleanup(github_agent, github_mcp_http_client.aclose)

    serve(entities=[issue_analyzer_agent, github_agent],
          port=8090, auto_open=True)


if __name__ == "__main__":
    configure_azure_monitor(
        connection_string=os.environ["APPLICATIONINSIGHTS_CONNECTION_STRING"],
        enable_live_metrics=True,
        resource=create_resource(),
        enable_performance_counters=False,
    )
    enable_instrumentation(enable_sensitive_data=True)
    with get_tracer().start_as_current_span("Issue Analyzer Agent Workflow", kind=SpanKind.CLIENT) as current_span:
        print(
            f"Trace ID: {format_trace_id(current_span.get_span_context().trace_id)}")
        main()
    # main()

    # ===== BEGIN: Stream agent response =====
    # print(f"User: {ISSUE_CONTEXT}")
    # print("Agent: ", end="", flush=True)
    # stream = issue_analyzer_agent.run(ISSUE_CONTEXT, stream=True)
    # async for chunk in stream:
    #     if chunk.text:
    #         print(chunk.text, end="", flush=True)
    # print("\n")
    # ===== END: Stream agent response =====


# if __name__ == "__main__":
#     asyncio.run(main())


# serve(entities=[issue_analyzer_agent], auto_open=True)
# Opens browser to http://localhost:8090
