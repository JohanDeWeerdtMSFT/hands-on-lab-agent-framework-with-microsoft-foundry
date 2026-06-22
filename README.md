# Agent Framework with Microsoft Foundry - Hands-On Lab

Welcome to this hands-on lab! You will learn how to build agentic applications using the Agent Framework with Microsoft Foundry.

## 📚 Workshop

Access the full workshop documentation: [Workshop Guide](docs/workshop.md)

Or view it online: [https://aka.ms/agf-lab](https://aka.ms/agf-lab)

## Repository Structure

This repository keeps the original lab project and the deployed hosted-agent project separate:

- `src/` contains the hands-on lab code. It uses the workshop prompt-agent and DevUI flow, including `main.py` and the original lab project configuration.
- `src-hosted/` contains the standalone Microsoft Foundry hosted agent. It has its own `main.py`, `agent.yaml`, `.agentignore`, `requirements.txt`, evaluation configuration, generated dataset, and evaluator artifacts.
- `azure.yaml` points only to `src-hosted/` for hosted-agent deployment. This keeps `azd ai agent run`, `azd deploy`, and evaluation commands focused on the hosted agent without changing the lab entry point in `src/main.py`.

The hosted agent duplicates only the small model and tool modules it needs so it can evolve independently from the lab project.

### Prompt-Agent Lab Setup

The prompt-agent lab stays in `src/` and is the path used by the workshop guide. Its entry point is `src/main.py`, which creates prompt-agent versions in the configured Foundry project and serves them locally with Agent Framework DevUI on port `8090`.

Start the prompt-agent lab DevUI with the fixed workshop token:

```bash
DEVUI_AUTH_TOKEN="devui-lab-token" uv run python main.py
```

Use this setup when following the hands-on lab steps or iterating on the prompt-agent examples. The lab project reads its configuration from the `src/.env` file, including the Foundry project endpoint, model deployment name, and any tool-specific settings used by the prompt-agent labs.

The hosted-agent project in `src-hosted/` is intentionally separate. It is used for Foundry hosted-agent local testing and deployment with `azd ai agent run`, `azd deploy`, and the Foundry Agent Inspector. Changes in `src-hosted/` should not require changes to the prompt-agent lab entry point in `src/main.py`.

## Codespaces And Version Notes

This lab is intended to work well from a fork in GitHub Codespaces. Open the fork in Codespaces, sign in with Azure CLI, and run commands from the `src/` folder unless the workshop explicitly says otherwise.

Before running Dev UI, use the fixed workshop token so the browser can authenticate to the local backend:

```bash
DEVUI_AUTH_TOKEN="devui-lab-token" uv run python main.py
```

The lab currently targets Python `>=3.13,<4.0` and pins Agent Framework, Foundry SDK, Azure SDK, and MCP dependencies in `src/pyproject.toml` and `src/uv.lock`. Keep `mcp` on the 1.x line (`mcp>=1.27.0,<2.0.0`); MCP 2.x prereleases use a different initialization result shape and can break Agent Framework MCP tools.

For Azure access, make sure the signed-in user can create the lab infrastructure and use the Foundry project. The roles most commonly needed are `Contributor` for deployment plus `Foundry User`, `Foundry Project Manager`, and `Cognitive Services OpenAI Contributor` on the Foundry resources. Some Azure portal surfaces may still show the older `Azure AI ...` role names while the Foundry role rename rolls out.


## Contributing

This project welcomes contributions and suggestions.  Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit https://cla.opensource.microsoft.com.

When you submit a pull request, a CLA bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., status check, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.

## Trademarks

This project may contain trademarks or logos for projects, products, or services. Authorized use of Microsoft 
trademarks or logos is subject to and must follow 
[Microsoft's Trademark & Brand Guidelines](https://www.microsoft.com/en-us/legal/intellectualproperty/trademarks/usage/general).
Use of Microsoft trademarks or logos in modified versions of this project must not cause confusion or imply Microsoft sponsorship.
Any use of third-party trademarks or logos are subject to those third-party's policies.
