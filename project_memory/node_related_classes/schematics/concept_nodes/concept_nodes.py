from dataclasses import dataclass, field
from typing import List, Dict

from project_memory.node_related_classes.schematics.node_schematics_parent import ConceptNodeSchematic


@dataclass
class TeamNodeSchematic(ConceptNodeSchematic):
    individuals: List[str] = field(default_factory=list)
    goal: str = ""
    metrics: Dict[str, str] = field(default_factory=dict)
    resources: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        super().__post_init__()
        self.sub_label = "Team"


@dataclass
class EmployeeNodeSchematic(ConceptNodeSchematic):
    employee_name: str = ""
    role: str = ""
    skills: List[str] = field(default_factory=list)
    assigned_projects: List[str] = field(default_factory=list)
    past_projects: List[str] = field(default_factory=list)

    def __post_init__(self):
        super().__post_init__()
        self.sub_label = "Employee"


@dataclass
class StakeholderNodeSchematic(ConceptNodeSchematic):
    stakeholder_name: str = ""  # can be the name of an organization too
    interest_level: str = ""  # may be more formal in the future, for now a descriptive string will do
    influence_level: str = ""  # may be more formal in the future, for now a descriptive string will do
    requirements: List[str] = field(default_factory=list)  # list of requirements node_ids, requirements are concepts

    def __post_init__(self):
        super().__post_init__()
        self.sub_label = "Stakeholder"


@dataclass
class ResourceNodeSchematic(ConceptNodeSchematic):
    belongs_to: str = ""

    def __post_init__(self):
        super().__post_init__()
        self.sub_label = "Resource"


@dataclass
class BudgetNodeSchematic(ConceptNodeSchematic):
    total_amount: float = 0.0
    allocated_amount: float = 0.0
    unallocated_amount: float = 0.0
    budget_manager: str = "" # is a person, employee, give node_id
    expenses: Dict[str, float] = field(default_factory=dict)  # may be more formal in the future

    def __post_init__(self):
        super().__post_init__()
        self.sub_label = "Budget"
