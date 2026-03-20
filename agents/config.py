"""
Agent configuration types and loading logic for the FundAI agent layer.

AgentConfigV1 is the structured representation of the JSON config files
in configs/. See configs/examples/ for concrete examples.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class AgentConfigV1:
    """Structured representation of an agent JSON config file (version 1).

    Fields:
        agent_id               — unique identifier; used to derive shmem names
        version                — config schema version (currently 1)
        tradeable_instruments  — agent may submit intent for these
        observable_instruments — agent observes but cannot trade these
        risk_limits            — per-agent risk parameters enforced by Fund OS
        research_focus         — hint to the LLM research loop (not a hard constraint)
        research_trigger       — when to run the research loop ("on_open", "on_interval", …)
        capital_allocation     — cash and fund exposure limits

    See configs/examples/ for concrete examples.
    """
    agent_id: str
    version: int
    tradeable_instruments: list[str]
    observable_instruments: list[str]
    risk_limits: dict[str, Any]
    research_focus: str
    research_trigger: str
    capital_allocation: dict[str, Any]

    @classmethod
    def from_file(cls, config_path: str) -> "AgentConfigV1":
        """Load and validate an AgentConfigV1 from a JSON file.

        Raises:
            FileNotFoundError   — config_path does not exist
            json.JSONDecodeError — file is not valid JSON
            KeyError            — required field (agent_id, version) is missing
        """
        path = Path(config_path)
        with path.open() as f:
            data = json.load(f)
        return cls(
            agent_id=data["agent_id"],
            version=data["version"],
            tradeable_instruments=data.get("tradeable_instruments", []),
            observable_instruments=data.get("observable_instruments", []),
            risk_limits=data.get("risk_limits", {}),
            research_focus=data.get("research_focus", ""),
            research_trigger=data.get("research_trigger", "on_open"),
            capital_allocation=data.get("capital_allocation", {}),
        )
