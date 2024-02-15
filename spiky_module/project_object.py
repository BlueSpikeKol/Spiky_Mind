import uuid

from architect_module.orchestrator.project_schedule import ProjectSchedule
from utils.persistance_access import MemoryStreamAccess
from utils.openai_api.agent_sessions.discussion_sessions import DiscussionSession

MOCK_PROJECT_FORM = {
    "1. Resources at Hand": {
        "Team Members": "Five high school students and a computer science teacher as a mentor.",
        "Budget": "$200, primarily for cloud hosting and additional resources.",
        "Equipment and Technology": "Computers for development, AWS for hosting, GitHub for version control.",
        "Contingency Plans": "Leveraging open-source contributions and community support for scalability."
    },
    "2. Navigating Risks": {
        "Potential Risks": "Limited resources and budget constraints, technical challenges in development.",
        "Impact and Severity": "High impact on project scope and quality.",
        "Risk Detection": "Regular team meetings for early detection and mitigation.",
        "Risk Management": "Focused project scope, mentorship for technical guidance, community engagement for additional resources."
    },
    "3. Mapping the Journey": {
        "Completion Dates": "15-week timeline with key milestones including ideation, development, testing, and final presentation.",
        "Resource Availability": "Team members available after school hours, mentor available during school hours."
    },
    "4. Terrain Constraints": {
        "External Dependencies": "Dependence on AWS Educate for free hosting resources.",
        "Regulations": "Compliance with school policies and educational standards.",
        "Limitations": "Budget cap of $200, limited to school resources and volunteer time."
    },
    "5. Bonus Information on The Crew": {
        "Team Introduction": "A group of enthusiastic high school students passionate about coding and a supportive computer science teacher.",
        "Project Background": "Aimed at introducing elementary school children to coding through an interactive web-based platform."
    },
    "6. The Quest": {
        "Purpose": "To create a gamified learning platform for teaching basic coding concepts to young learners.",
        "Success Metrics": "Successful deployment of the platform, positive feedback from initial users, and engagement metrics.",
        "Critical Success Factors": "User-friendly design, engaging content, effective learning outcomes."
    },
    "7. Provisions and Protocols": {
        "Expectations": "Guidance and support in project management, technical development, and educational content creation.",
        "Penalties for Failure": "Limited to learning experience and project adjustments based on feedback.",
        "Standards": "Educational effectiveness, user engagement, technical robustness."
    },
    "8. The Boundaries of Our Map": {
        "Project Scope": "Development of an interactive web-based platform for coding education targeted at elementary school students.",
        "Outside Scope": "Advanced coding concepts, mobile app development, hardware-based projects."
    },
    "9. Charting the Sub-Objectives": {
        "Sub-Objectives": "Designing the interactive platform, developing curriculum content, engaging with schools for pilot testing, and establishing a feedback loop for continuous improvement.",
        "Timeline for Sub-Objectives": "The project is segmented into four main phases, each with its own set of tasks and deadlines, aligning with the overall 15-week project timeline."
    }
}


class Project:
    def __init__(self, name=None):
        self.name_id = f"{name}"
        self.discussion_sessions = []  # List of DiscussionSession objects
        self.project_schedule = ProjectSchedule()
        self.memory_access = MemoryStreamAccess()
        self.initial_form = None

    def add_conversation_session(self, session: DiscussionSession):
        self.discussion_sessions.append(session)

    def set_project_schedule(self, schedule: ProjectSchedule):
        self.project_schedule = schedule

    def set_memory_access(self, memory_access: MemoryStreamAccess):
        self.memory_access = memory_access

    def set_project_name(self, name):
        """Set the name of the project. This will also append a new unique identifier to the name."""
        self.name_id = f"{name}-{uuid.uuid4()}"

    def create_project_form(self):
        print("Fill out the form")
        self.initial_form = MOCK_PROJECT_FORM
        # TODO: Replace with actual form filling logic. This will include an interface to help users remember isntructions.
