"""
pi-mono Agents
"""
from app.agents.script_analysis import ScriptAnalysisAgent
from app.agents.plot_deconstruct import PlotDeconstructAgent
from app.agents.scene_planning import ScenePlanningAgent
from app.agents.character_design import CharacterDesignAgent
from app.agents.visual_gen import VisualGenAgent
from app.agents.video_assembly import VideoAssemblyAgent
from app.agents.qc_review import QCReviewAgent

# Pipeline 顺序
PIPELINE_AGENTS = [
    ScriptAnalysisAgent,
    PlotDeconstructAgent,
    ScenePlanningAgent,
    CharacterDesignAgent,
    VisualGenAgent,
    VideoAssemblyAgent,
    QCReviewAgent,
]

__all__ = [
    "ScriptAnalysisAgent",
    "PlotDeconstructAgent",
    "ScenePlanningAgent",
    "CharacterDesignAgent",
    "VisualGenAgent",
    "VideoAssemblyAgent",
    "QCReviewAgent",
    "PIPELINE_AGENTS",
]
