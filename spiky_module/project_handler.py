from typing import List
import uuid
import re
import json
import datetime
from pathlib import Path

from spiky_module.project_object import Project
from architect_module.orchestrator.project_schedule import ProjectSchedule
from utils.persistance_access import MemoryStreamAccess
from utils.openai_api.agent_sessions.discussion_sessions import DiscussionSession
from utils.openai_api.gpt_calling import GPTAgent, GPTManager
from utils.openai_api.models import ModelType
from utils.openai_api.agent_sessions.convo_types import ConversationType, ConversationEndType
from utils.openai_api.agent_sessions.memory_types import MemoryType
from utils.openai_api.agent_sessions.trajectory_listener import TrajectoryListenerCategorizer
from utils.decision_records.decision_records_handler import DecisionRecordHandler
from spiky_module.project_object import Project

SUB_OBJECTIVE_1 = """
### Sub-Objective 1: Design and Development of the Interactive Platform

#### Resources at Hand
- **Team Members**: Frontend Developer and Designer.
- **Budget Allocation**: $50 for design tools and React.js resources.
- **Technology**: HTML, CSS, JavaScript, React.js for UI components.
- **Plan B**: Utilize free design templates and open-source React components if custom development exceeds budget.

#### Navigating Risks
- **Potential Risks**: Design complexity exceeding skill level of the team.
- **Impact and Severity**: Medium. Could delay the project but not fatal.
- **Risk Detection**: Regular design reviews with the mentor.
- **Risk Management**: Prioritize essential features and use open-source components.

#### Mapping the Journey
- **Completion Dates**: Design by Week 3, Development by Week 6.
- **Resource Availability**: Full availability of the Frontend Developer and Designer during this phase.

#### Terrain Constraints
- **External Dependencies**: Reliance on React.js community for troubleshooting.
- **Regulations**: Compliance with web accessibility standards.
- **Limitations**: Limited to the $50 budget for any paid tools or assets.

#### Bonus Information on The Crew
- **The captain and crew**: A skilled Frontend Developer with experience in React.js, supported by a creative Designer focused on user experience.

#### The Quest
- **Our Purpose**: To create an engaging and intuitive interface for the coding platform.
- **Charting Success**: A fully functional prototype with user-friendly navigation.
- **Vital Navigational Stars**: User satisfaction with the interface, ease of navigating coding lessons.

#### Provisions and Protocols
- **Our Agreement**: Deliver a responsive design compatible across devices.
- **The Cost of Straying Off Course**: Delays in subsequent development phases.
- **Benchmarks**: Adherence to modern web design principles and accessibility standards.

#### The Boundaries of Our Map
- **Our Scope**: Designing and developing the frontend of the platform.
- **Outside of Our Scope**: Backend development and content creation for coding lessons.
"""
SUB_OBJECTIVE_2 = """
### Sub-Objective 2: Backend Development and Database Management

#### Resources at Hand
- **Team Members**: Backend Developer.
- **Budget Allocation**: $50 for cloud database services and backend tools.
- **Technology**: Python-based Django framework, PostgreSQL.
- **Plan B**: Consider lighter backend frameworks or free database solutions if costs overrun.

#### Navigating Risks
- **Potential Risks**: Technical challenges with database integration.
- **Impact and Severity**: High, as it affects user data management and progress tracking.
- **Risk Detection**: Early testing of database connections and user authentication.
- **Risk Management**: Regular code reviews and mentorship sessions.

#### Mapping the Journey
- **Completion Dates**: Backend setup by Week 6, Database integration by Week 8.
- **Resource Availability**: Backend Developer dedicated to this phase.

#### Terrain Constraints
- **External Dependencies**: Availability of Django and PostgreSQL documentation and community support.
- **Regulations**: Data protection and privacy laws.
- **Limitations**: $50 budget for any backend services or tools.

#### Bonus Information on The Crew
- **The captain and crew**: A proficient Backend Developer experienced in Django and database management.

#### The Quest
- **Our Purpose**: To ensure robust data handling and user management for the platform.
- **Charting Success**: Successful integration of user authentication and progress tracking.
- **Vital Navigational Stars**: Data integrity, security, and scalability of the backend infrastructure.

#### Provisions and Protocols
- **Our Agreement**: Develop a secure and scalable backend system.
- **The Cost of Straying Off Course**: Potential data breaches or loss of user data.
- **Benchmarks**: Efficient data handling, minimal server response times.

#### The Boundaries of Our Map
- **Our Scope**: Backend logic, user authentication, and database management.
- **Outside of Our Scope**: Frontend development and UI/UX design.
"""
SUB_OBJECTIVE_3 = """
### Engaging with Schools for Pilot Testing

#### 1. Resources at Hand
- **Team Members**: Project Manager, QA Engineer, and Educators for outreach.
- **Budget**: Allocated portion of the $200 for outreach materials and potential travel.
- **Equipment and Technology**: Communication tools, presentation materials.
- **Plan B**: Virtual demonstrations and feedback sessions if in-person visits aren't feasible.

#### 2. Navigating Risks
- **Potential Risks**: Difficulty in securing school partnerships; logistical challenges in organizing pilot tests.
- **Impact and Severity**: Moderate, as early feedback is crucial for iterative improvement.
- **Risk Detection**: Early engagement with schools and setting clear expectations.
- **Risk Management**: Flexible scheduling, offering virtual options, and preparing engaging demonstration materials.

#### 3. Mapping the Journey
- **Completion Dates**: Initial school contacts by Week 5, pilot testing scheduled by Week 10.
- **All hands on deck**: Coordination with the development team to ensure the platform is ready for demonstrations.

#### 4. Terrain Constraints
- **External Dependencies**: School schedules and availability.
- **Regulations**: Compliance with school policies and privacy regulations.
- **Limited supplies**: Outreach efforts constrained by budget and resources.

#### 5. Bonus Information on The Crew
- **The captain and crew**: Introduction to the team members leading the outreach and testing efforts.
- **The tale of our quest**: Emphasizing the collaborative nature of the pilot testing phase.

#### 6. The Quest
- **Our purpose**: To establish partnerships with schools for pilot testing and gather valuable feedback.
- **Charting success**: Successful implementation of pilot tests and positive initial feedback from educators and students.
- **Vital navigational stars**: Number of schools engaged, feedback quality, and actionable insights gained.

#### 7. Provisions and Protocols
- **Our agreement**: Clear communication channels with participating schools and adherence to feedback timelines.
- **The cost of straying off course**: Missed opportunities for early improvement and potential delays in full launch.
- **Benchmarks**: Engagement level, feedback implementation rate, and satisfaction scores from pilot participants.

#### 8. The Boundaries of Our Map
- **Our Scope**: Engaging local schools for initial pilot testing and feedback collection.
- **Outside of Our Scope**: Nationwide or international school outreach at this stage.

This section outlines the approach to engaging with schools for pilot testing, a crucial step for validating the platform's educational impact and usability.
"""
SUB_OBJECTIVE_4 = """
### Ensuring Ongoing Improvement and Maintenance

#### 1. Resources at Hand
- **Team Members**: Entire team, with a focus on the Backend Developer and QA Engineer for technical maintenance.
- **Budget**: Remaining funds allocated for ongoing platform support and updates.
- **Equipment and Technology**: Server and database management tools, bug tracking software.
- **Plan B**: Engaging with the open-source community for support and contributions.

#### 2. Navigating Risks
- **Potential Risks**: Technical issues impacting platform stability; evolving educational needs not met.
- **Impact and Severity**: High, as long-term success depends on reliability and relevance.
- **Risk Detection**: Continuous monitoring of platform performance and user feedback.
- **Risk Management**: Regular updates, community engagement for feature requests, and agile response to feedback.

#### 3. Mapping the Journey
- **Completion Dates**: Not applicable, as this is an ongoing effort.
- **All hands on deck**: Establishing a routine for regular check-ins and updates.

#### 4. Terrain Constraints
- **External Dependencies**: Reliance on third-party services for hosting and maintenance tools.
- **Regulations**: Adherence to data protection and privacy laws.
- **Limited supplies**: Continuous effort limited by available team capacity and funding.

#### 5. Bonus Information on The Crew
- **The captain and crew**: Highlighting the dedication of the team to long-term project success.
- **The tale of our quest**: Focusing on the commitment to adapt and grow the platform over time.

#### 6. The Quest
- **Our purpose**: To ensure the platform remains effective, engaging, and technically sound over time.
- **Charting success**: Measured by platform uptime, user satisfaction, and the implementation rate of new features.
- **Vital navigational stars**: User feedback, technical performance metrics, and community engagement levels.

#### 7. Provisions and Protocols
- **Our agreement**: Commitment to regular platform evaluation and updates.
- **The cost of straying off course**: Potential decline in user engagement and educational impact.
- **Benchmarks**: Update frequency, bug resolution times, and new feature release rate.

#### 8. The Boundaries of Our Map
- **Our Scope**: Continuous platform improvement, feature updates, and maintenance.
- **Outside of Our Scope**: Overhauling the platform with new technologies or expanding beyond the initial educational focus without thorough evaluation.

This section emphasizes the importance of ongoing improvement and maintenance to ensure the platform's long-term success and relevance.
"""

SUB_OBJECTIVE_1_CATEGORIES = ['Team', 'Contingencies', 'Risks', 'Schedule', 'Constraints', 'Team', 'Goal', 'Goal',
                              'Scope']
SUB_OBJECTIVE_2_CATEGORIES = ['Team', 'Resources', 'Risks', 'Risks', 'Schedule', 'Constraints', 'Team', 'Goal', 'Risks',
                              'Scope']
SUB_OBJECTIVE_3_CATEGORIES = ['Team', 'Contingencies', 'Risks', 'Schedule', 'Constraints', 'Team', 'Goal', 'Scope',
                              'Scope']
SUB_OBJECTIVE_4_CATEGORIES = ['Team', 'Contingencies', 'Risks', 'Risks', 'Schedule', 'Constraints', 'Team', 'Goal',
                              'Resources', 'Scope']

SUB_OBJECTIVE_1_CONVERSATION = [
    ("AI Assistant",
     "Let's dive into the first sub-objective: Designing and developing the interactive platform. Who's on this task?"),
    ("Project Manager",
     "The Frontend Developer and Designer are leading this. We've allocated $50 from our budget specifically for design tools and React.js resources."),
    ("AI Assistant", "Interesting choice with React.js. What's your Plan B if custom development exceeds the budget?"),
    ("Project Manager",
     "We'll utilize free design templates and open-source React components. It's all about being resourceful."),
    ("AI Assistant", "What potential risks are you foreseeing in this phase?"),
    ("Project Manager",
     "The main risk is the design complexity exceeding our team's skill level. We're planning regular design reviews with our mentor to mitigate this."),
    ("AI Assistant", "How are you mapping the journey for this sub-objective?"),
    ("Project Manager",
     "We aim to complete the design by Week 3 and development by Week 6, with full availability of our Frontend Developer and Designer."),
    ("AI Assistant", "Are there any external dependencies or regulations you're concerned about?"),
    ("Project Manager",
     "We're mainly relying on the React.js community for troubleshooting. Also, we need to ensure compliance with web accessibility standards."),
    ("AI Assistant", "Tell me more about the team working on this."),
    ("Project Manager",
     "We have a skilled Frontend Developer experienced in React.js and a creative Designer focused on user experience."),
    ("AI Assistant", "What defines success for this sub-objective?"),
    ("Project Manager",
     "Success would be a fully functional prototype that's user-friendly and navigable, receiving positive feedback for its interface."),
    ("AI Assistant", "And how will you ensure you stay on course?"),
    ("Project Manager",
     "By delivering a responsive design compatible across devices and adhering to modern web design principles."),
    ("AI Assistant", "Finally, what's outside the scope of this sub-objective?"),
    ("Project Manager",
     "Backend development and content creation for coding lessons are not part of this phase. We're focusing solely on the frontend.")
]
SUB_OBJECTIVE_2_CONVERSATION = [
    ("AI Assistant",
     "Moving on to Sub-Objective 2: Backend Development and Database Management. Who's taking the lead here?"),
    ("Project Manager",
     "Our Backend Developer is in charge. We've allocated $50 from our budget for cloud database services and backend tools."),
    ("AI Assistant", "You're using Django and PostgreSQL. Any Plan B if costs overrun?"),
    ("Project Manager",
     "We might consider lighter backend frameworks or free database solutions to keep within our budget."),
    ("AI Assistant", "What are the potential risks in this phase?"),
    ("Project Manager",
     "The main challenge is integrating the database smoothly. It's crucial for managing user data and tracking progress."),
    ("AI Assistant", "How are you planning to navigate these risks?"),
    ("Project Manager", "By conducting early testing of database connections and implementing regular code reviews."),
    ("AI Assistant", "What's the timeline for completing the backend setup and database integration?"),
    ("Project Manager", "We aim to have the backend setup by Week 6 and complete database integration by Week 8."),
    ("AI Assistant", "Any external dependencies or regulations you're concerned about?"),
    ("Project Manager",
     "We're relying on the Django and PostgreSQL communities for support and must comply with data protection laws."),
    ("AI Assistant", "Can you share more about the team member working on this?"),
    ("Project Manager",
     "Our Backend Developer is highly experienced in Django and database management, ensuring a robust backend system."),
    ("AI Assistant", "What does success look like for this sub-objective?"),
    ("Project Manager",
     "It means having a secure backend where user authentication and progress tracking are seamlessly integrated."),
    ("AI Assistant", "And the provisions and protocols in place?"),
    ("Project Manager",
     "We're committed to developing a scalable backend infrastructure, mindful of data integrity and security."),
    ("AI Assistant", "Finally, what's outside the scope of this sub-objective?"),
    ("Project Manager",
     "This phase won't cover frontend development or UI/UX design. Our focus is solely on the backend.")
]
SUB_OBJECTIVE_3_CONVERSATION = [
    ("AI Assistant",
     "Now, let's discuss engaging with schools for pilot testing. Who are the key players in this phase?"),
    ("Project Manager",
     "The Project Manager, QA Engineer, and some Educators will lead the outreach. We've set aside part of our $200 budget for materials and potential travel."),
    ("AI Assistant", "What's your Plan B if in-person visits aren't feasible?"),
    ("Project Manager",
     "We're prepared to conduct virtual demonstrations and feedback sessions to overcome any logistical challenges."),
    ("AI Assistant", "What risks are you anticipating with this engagement?"),
    ("Project Manager",
     "Securing school partnerships and organizing pilot tests could be challenging. Early engagement and flexible scheduling are our strategies for mitigation."),
    ("AI Assistant", "How are you planning the timeline for these engagements?"),
    ("Project Manager",
     "We aim to make initial school contacts by Week 5 and schedule pilot testing by Week 10, coordinating closely with our development team."),
    ("AI Assistant", "Are there any external dependencies or regulations affecting this phase?"),
    ("Project Manager",
     "Yes, we're mindful of school schedules, availability, and compliance with their policies and privacy regulations."),
    ("AI Assistant", "Could you share more about the team leading these efforts?"),
    ("Project Manager",
     "Certainly. Our Project Manager, QA Engineer, and dedicated Educators are passionate about bringing this platform to schools and gathering feedback."),
    ("AI Assistant", "What defines success for this sub-objective?"),
    ("Project Manager",
     "Success means establishing partnerships with schools, conducting pilot tests, and receiving positive feedback from both educators and students."),
    ("AI Assistant", "What provisions and protocols are in place for this phase?"),
    ("Project Manager",
     "We've established clear communication channels with schools and set benchmarks for engagement levels and feedback implementation."),
    ("AI Assistant", "Finally, what's outside the scope of this engagement?"),
    ("Project Manager",
     "At this stage, we're focusing on local schools. Nationwide or international outreach is beyond our current scope.")
]
SUB_OBJECTIVE_4_CONVERSATION = [
    (
        "AI Assistant",
        "Let's talk about ensuring ongoing improvement and maintenance. Who will be responsible for this?"),
    ("Project Manager",
     "The entire team is involved, but the Backend Developer and QA Engineer will specifically focus on technical maintenance. We've allocated our remaining funds for platform support and updates."),
    ("AI Assistant", "What's your Plan B if you encounter unexpected technical issues?"),
    ("Project Manager",
     "We plan to engage with the open-source community for support and contributions, leveraging collective knowledge and resources."),
    ("AI Assistant", "What are the potential risks in this ongoing process?"),
    ("Project Manager",
     "We're looking at technical issues that could affect platform stability and the challenge of meeting evolving educational needs."),
    ("AI Assistant", "How will you manage these risks?"),
    ("Project Manager",
     "Through continuous monitoring of platform performance, regular updates, and staying agile to feedback from our user community."),
    ("AI Assistant", "Since this is an ongoing effort, how do you plan to organize the work?"),
    ("Project Manager",
     "We're establishing a routine for regular check-ins and updates, ensuring that everyone on the team is aligned and focused."),
    ("AI Assistant", "Are there any external dependencies or regulations you need to consider?"),
    ("Project Manager",
     "Yes, we rely on third-party services for hosting and must adhere to data protection and privacy laws."),
    ("AI Assistant", "Can you share more about the team's dedication to this project?"),
    ("Project Manager",
     "Our team is fully committed to the project's long-term success. We're all dedicated to adapting and growing the platform over time."),
    ("AI Assistant", "What measures will you use to gauge the success of your maintenance efforts?"),
    ("Project Manager",
     "Success will be measured by platform uptime, user satisfaction, and how quickly we can implement new features based on feedback."),
    ("AI Assistant", "What agreements have you made regarding ongoing platform evaluation and updates?"),
    ("Project Manager",
     "We've agreed to a commitment of regular platform evaluation and updates, ensuring we can quickly adapt to user needs."),
    ("AI Assistant", "Finally, what's outside the scope of your ongoing improvement efforts?"),
    ("Project Manager",
     "We won't be overhauling the platform with new technologies or expanding beyond our initial focus without thorough evaluation. Our goal is continuous improvement within our established scope.")
]

TESTING_NAME = "Timmy"
TESTING = True
WELCOME_INSTRUCTIONS1 = "Welcome to SpikyMind! I'm Spiky and I will help you throughout your journey." \
                        "Let's start a new project. What would you like to name it?"
WELCOME_INSTRUCTIONS2 = "Great! Now, for me to understand what your project is about, I need you to fill this form, " \
                        "in order for me organize your project. Here is a little guide to help you fill it out, feel free" \
                        "to let some parts of the form blank: "
PROJECT_FORM_INSTRUCTIONS = """
### Beginners Guide to Sharing Your Project Details

Hello {$name},

As you and I embark on this journey together, it's vital that we're all on the same page. Think of this as less of a rulebook and more of a compass to navigate the complexities of project management together.

#### 1. Resources at Hand
I'm curious, tell me about the toolkit you've got for this adventure:
- **Who's joining you?** Tell us about the team. Is it just you, or are there others?
- **What's your budget?** Insights into financial planning are always valuable.
- **Got the gear?** Equipment, technology, and facilities you'll be using. This can range from software to physical tools.
- **Plan B?** We all know surprises happen; we'd love to hear about your contingencies. If you don't have any, that's okay too.

#### 2. Navigating Risks (This section is more difficult to fill out for beginners, no need to fill it out if you're not sure!)
Every expedition has its uncertainties, and we'd like to understand:
- **What might we encounter?** A brief on potential risks. What might cause this project to fail?
- **Impact and severity:** How critical are these risks? Not all risks are created equal!
- **Can we see it coming?** Your thoughts on the likelihood of detection of those risks.
- **Charting the course:** How do you plan to navigate these risks? Which ones are you prepared to face head-on, and which ones are you hoping to avoid?

#### 3. Mapping the Journey
Timing is everything:
- **When do we celebrate?** Your envisioned completion dates. This is an overview, not a commitment to a specific schedule. Need an example?
- **All hands on deck:** Availability of our crew and resources. Anything time related should be written here!

#### 4. Terrain Constraints
Outside forces that might affect our journey:
- **What's tying our hands?** You depend on unreliable forces, troublesome rules and the likes? Write it here!
- **Navigational charts:** Any approvals or regulations guiding our route.
- **Limited supplies:** Constraints we should be aware of. This might include a budget cap, time constraints, or other limitations.

#### 5. Bonus Information on The Crew
Who's sailing with us, and what's the story behind this voyage?
- **The captain and crew:** I want to learn about you and the team members. write a brief introduction of each member, including yourself!
- **The tale of our quest:** Background of the project and key stakeholders, if any. (Yes, teachers waiting on your project counts as stakeholders!)

#### 6. The Quest
What are we here for? Tell me about your the objective of this project:
- **Our purpose:** What are we expecting out of this project?
- **Charting success:** How we'll know we've found our treasure. What are the key achievements you're looking for?
- **Vital navigational stars:** Critical success factors to guide us. Also known as KPIs(Key Performance Indicators).

#### 7. Provisions and Protocols
Knowing what we need and what's expected is crucial:
- **Our agreement:** What do you expect of me? For what reasons am I needed?
- **The cost of straying off course:** Understanding the penalties. What is the cost of failure? Can we come back from it? How?
- **Benchmarks:** Standards to guide our way. Not necessary to fill now.

#### 8. The Boundaries of Our Map
Knowing where we're not going is as important as knowing where we are going:
- **Our Scope:** What's within the scope of this project. Be specific. Projects are often defined by what they don't include.
- **Outside of Our Scope:** What we've decided not to explore this time. This is where ambiguity needs to be cleared.

#### 9. Charting the Sub-Objectives
Let's break down our main goal into smaller, more manageable steps:
- **Sub-Objectives:** What are the high-level steps that will lead us to our main goal? Think of these as the chapters of our story. For instance, if our project is to create a house, sub-objectives might include designing the house, acquiring the land, and raising the budget.
- **Timeline for Sub-Objectives:** Do we have any preliminary timelines in mind for these sub-objectives? If you already mentionned it in section 3, no need to fill it out again.

This section is **optional** and might not be as straightforward for beginners. But remember :No permanent damage to your project will be done if you do a mistake here and outlining your sub-objectives can provide a clearer roadmap make my job, to help you, more easy.
Usually, having between 3 and 6 sub-objectives is optimal.

Perfect! Should you have any questions or more specific examples to go through the requests above, simply tell me!

**Thank you** for sharing this project with me. Here's to making each project a tale worth telling! Now let's get to it!
"""
FIRST_CONVERSATION_PROMPT = "This is a discussion session. Everything said here will be saved in order to make more " \
                            "informed decisions in the project. Speak freely, it's my job to discern what will be " \
                            "important and what won't be."
PREMADE_CONVERSATION = [
    ("AI Assistant", "Hey there! I heard you're up to something cool with coding for kids. What's the scoop?"),
    ("Project Manager",
     "Hey! Yeah, we're launching a web platform to teach coding to elementary kids. Think of it as coding lessons, but fun, like games."),
    ("AI Assistant", "That's awesome! Why target kids, though?"),
    ("Project Manager",
     "Well, coding's becoming essential, like reading or math. We want to get kids into it early, make it second nature by the time they're older."),
    ("AI Assistant", "Makes sense. How's it going to reach everyone? Sounds like it could be pricey."),
    ("Project Manager",
     "It's totally free. We're running on donations and some help from tech friends. Planning to partner with schools and businesses too."),
    ("AI Assistant", "Free, huh? How will you keep it up and running?"),
    (
        "Project Manager",
        "Donations, mainly. And we're hoping tech pros will chip in, help us make it better over time."),
    ("AI Assistant", "Gotcha. And what tech are you using to build it?"),
    ("Project Manager",
     "For the front, it's the usual web stuff - HTML and CSS. Plus, we're using React for the interactive bits."),
    ("AI Assistant", "Interactive bits? Like games?"),
    ("Project Manager",
     "Exactly! Kids will drag and drop code to solve puzzles, learn loops, if-else stuff. And they get badges to show off."),
    ("AI Assistant", "Badges? Sounds like a good motivator."),
    ("Project Manager", "Yeah, that's the plan. Make it feel more like playing a game than sitting in class."),
    ("AI Assistant", "React and games for coding... sounds like a solid plan. How'd you pick React?"),
    ("Project Manager",
     "React's great for building user interfaces, especially interactive ones. Plus, there's a big community for support."),
    ("AI Assistant", "Community support sounds key for a project like this."),
    ("Project Manager", "Absolutely. We're all about making learning accessible and fun. React helps us do just that."),
    ("AI Assistant", "Cool, the frontend sounds fun! What about the backend? How's that shaping up?"),
    ("Project Manager",
     "We're going with Django, a Python framework. It's solid for the backend stuff like managing users and their progress."),
    ("AI Assistant", "Django, huh? Why choose that for the backend?"),
    ("Project Manager",
     "It's good for building robust web apps. Plus, it makes handling user data and authentication a breeze."),
    ("AI Assistant", "Got it. And where's all this user data going?"),
    ("Project Manager",
     "We're using PostgreSQL for the database. It's going to store progress, badges, all that important stuff."),
    ("AI Assistant",
     "Sounds like you've got user progress tracking covered. What about adding new challenges or content?"),
    ("Project Manager",
     "There's an admin panel for that. Mentors and contributors can jump in to tweak or add new puzzles anytime."),
    ("AI Assistant", "Neat. How are you planning to keep this platform running smoothly?"),
    ("Project Manager",
     "We're using AWS for hosting. Got a small budget, but AWS Educate helps us stretch it. And for updates and testing, GitHub Actions is our go-to."),
    ("AI Assistant", "AWS and GitHub Actions, nice. What's the deal with the budget and team?"),
    ("Project Manager",
     "Budget's tight, just $200. But we've got five high schoolers and a teacher guiding us. Each person has a role, like frontend, backend, testing, and design."),
    ("AI Assistant", "Only $200? How are you managing with that?"),
    ("Project Manager", "It's all about being smart with resources. Plus, AWS Educate gives us some leeway."),
    ("AI Assistant", "What's everyone doing on the team?"),
    ("Project Manager",
     "I'm steering the ship, setting goals. We've got students handling the frontend, backend, QA, and design. Each plays to their strengths."),
    ("AI Assistant", "QA and design too? That's comprehensive."),
    ("Project Manager",
     "Yeah, we want this to be top-notch. Good design draws kids in, and thorough testing keeps everything running smooth."),
    ("AI Assistant", "Makes sense. How will you keep the platform up to date?"),
    ("Project Manager",
     "We'll update it based on what kids and teachers say. Staying current with educational trends is key."),
    ("AI Assistant", "Sounds like a plan. What's driving all this effort?"),
    ("Project Manager",
     "We want to make coding fun and accessible. It's about inspiring kids, showing them coding's not just useful but exciting."),
    ("AI Assistant", "Inspiring kids with coding, I love the sound of that. How important is making learning fun?"),
    ("Project Manager",
     "It's everything. If kids enjoy learning, they'll stick with it. We're using games to teach coding in a way that feels more like play than school."),
    ("AI Assistant", "This project is shaping up nicely! What's the timeline looking like?"),
    ("Project Manager",
     "We're planning it out step by step. First couple of weeks, we're nailing down the features, tech, and who does what. Then we sketch out the site layout by week 3."),
    ("AI Assistant", "Sounds organized. What comes after the planning?"),
    ("Project Manager",
     "Weeks 4 to 6 are all about designing the games and puzzles. We're crafting the challenges to make sure they're fun and educational."),
    ("AI Assistant", "And the actual building of the site?"),
    ("Project Manager",
     "That's the big chunk, weeks 7 to 12. We're coding both the front and back ends at the same time. Got to make sure everything meshes well."),
    ("AI Assistant", "What about testing?"),
    ("Project Manager",
     "Weeks 13 and 14, that's the QA team's time to shine. They'll be squashing bugs and making sure everything runs smoothly."),
    ("AI Assistant", "Then what? Launch time?"),
    ("Project Manager",
     "Almost. Week 15, we're presenting it at the school assembly, see what the kids and teachers think, and tweak anything if we need to."),
    ("AI Assistant", "Sounds like you've got it all mapped out. Any concerns?"),
    ("Project Manager",
     "Biggest worry is the budget and team size. We're running lean, so we've got to be smart with our resources. Open-source help and the community will be big for us."),
    ("AI Assistant", "How are you tackling potential tech issues?"),
    ("Project Manager",
     "Our computer science teacher is a lifesaver. Having someone with experience to guide the students through any technical mazes is key."),
    ("AI Assistant", "And keeping users interested?"),
    ("Project Manager",
     "We're planning to keep things fresh with regular updates based on feedback from the kids and teachers. It's all about evolving with their needs."),
    ("AI Assistant", "It really seems like you're covering all bases. Any final thoughts?"),
    ("Project Manager",
     "Just that we're really excited to see where this goes. It's a big task, but we believe in making coding a fun part of every kid's life. With this team and plan, I think we can really make a difference.")
]  # describes the information inside the mock form in a conversation style


class ProjectHandler:
    def __init__(self, project_name=None):
        self.project = Project()
        self.project_name = project_name
        self.gpt_manager = GPTManager()
        self.drf_manager = DecisionRecordHandler()

    def new_project_init(self, project_name):
        if project_name is None and self.project_name is not None:
            project_name = self.project_name
        if project_name is None:
            print(WELCOME_INSTRUCTIONS1)
            project_name = input()
        self.project.set_project_name(project_name)
        print(WELCOME_INSTRUCTIONS2)
        print(PROJECT_FORM_INSTRUCTIONS.replace("{$name}", TESTING_NAME))
        # self.re_execute_failed_queries()
        #self.project.create_project_form()
        #nodes_precypher = self.form_to_nodes(self.project.initial_form)
        #self.add_nodes_to_graph_db(nodes_precypher)
        self.pair_nodes_without_drf()
        self.handle_general_conversation()
        # all conversations should be saved in the vector db.
        # General information cannot be put in the graph db because it would just float around

        # Initialize and set a ProjectSchedule
        project_schedule = ProjectSchedule()
        self.project.set_project_schedule(project_schedule)

    def sanitize_string(self, s):
        # Remove newlines and trim spaces
        return re.sub(r'\s+', ' ', s.replace('\n', ' ').strip())

    def add_nodes_to_graph_db(self, nodes):
        # Initialize lists to hold node creation and relationship creation queries
        node_queries = []
        relationship_queries = []

        # Determine the path for saving failed queries
        current_script_path = Path(__file__).resolve()
        parent_folder = current_script_path.parent
        failed_queries_folder = parent_folder / "failed_json"
        failed_queries_folder.mkdir(exist_ok=True)
        failed_queries_path = failed_queries_folder / "failed_queries.json"

        # Prepare node creation queries
        for node in nodes:
            # Sanitize name and name_id
            sanitized_name_id = self.sanitize_string(node['name_id'])
            sanitized_name = self.sanitize_string(node['name'])
            sanitized_information = self.sanitize_string(node['information'])

            node_query = f"MERGE (n:{node['label']} {{name_id: $name_id, name: $name, information: $information}})"
            node_params = {
                "name_id": sanitized_name_id,
                "name": sanitized_name,
                "information": sanitized_information
            }
            node_queries.append((node_query, node_params))

        # Prepare relationship creation queries
        for node in nodes:
            sanitized_source_id = self.sanitize_string(node['name_id'])
            for target_id in node['connected_to']:
                sanitized_target_id = self.sanitize_string(target_id)
                target_node = next((n for n in nodes if self.sanitize_string(n['name_id']) == sanitized_target_id), None)
                if target_node:
                    relationships = self.determine_relationships(node, target_node)
                    for relationship in relationships:
                        rel_query = f"MATCH (a:{node['label']} {{name_id: $source_id}}), (b:{target_node['label']} {{name_id: $target_id}}) MERGE (a)-[:{relationship}]->(b)"
                        rel_params = {
                            "source_id": sanitized_source_id,
                            "target_id": sanitized_target_id
                        }
                        relationship_queries.append((rel_query, rel_params))

        def execute_queries(queries):
            failed_queries = []
            for query, params in queries:
                try:
                    self.project.memory_access.neo4j_handler.execute_queries((query, params))
                except Exception as e:
                    failed_queries.append({"query": query, "params": params})
                    print(f"Failed to execute query: {query} with params: {params}\nError: {e}")
            return failed_queries

        # Execute node creation queries first
        failed_node_queries = execute_queries(node_queries)
        # Then execute relationship creation queries
        failed_relationship_queries = execute_queries(relationship_queries)

        # Save failed queries with parameters to a JSON file for retry
        if failed_node_queries or failed_relationship_queries:
            with open(failed_queries_path, 'w') as file:
                json.dump(failed_node_queries + failed_relationship_queries, file, indent=4)
            print(f"Failed queries have been saved to '{failed_queries_path}'. Please review and retry.")

    def re_execute_failed_queries(self, filename="failed_queries.json"):
        # Determine the path for the failed queries file
        current_script_path = Path(__file__).resolve()
        parent_folder = current_script_path.parent
        failed_queries_folder = parent_folder / "failed_json"
        failed_queries_path = failed_queries_folder / filename

        try:
            with open(failed_queries_path, 'r') as file:
                queries_with_params = json.load(file)

            successful_queries = []
            failed_queries = []

            for query_with_params in queries_with_params:
                query = query_with_params["query"]
                params = query_with_params.get("params", {})  # Default to an empty dict if params are not provided
                try:
                    # Assuming execute_queries can handle a tuple of (query, params)
                    self.project.memory_access.neo4j_handler.execute_queries((query, params))
                    print(f"Successfully re-executed query: {query} with params: {params}")
                    successful_queries.append(query_with_params)
                except Exception as e:
                    print(f"Failed to re-execute query: {query} with params: {params}\nError: {e}")
                    failed_queries.append(query_with_params)

            # Update the JSON file with only the failed queries
            with open(failed_queries_path, 'w') as file:
                json.dump(failed_queries, file, indent=4)

            if successful_queries:
                print(f"Removed successful queries from '{failed_queries_path}'. Remaining failed queries need review.")
            else:
                print(f"No queries were successfully executed. All failed queries remain in '{failed_queries_path}'.")

        except FileNotFoundError:
            print(f"File {failed_queries_path} not found.")

    def determine_relationships(self, source_node, target_node):
        relationships = []

        # Direct relationships
        if source_node['label'] == "Project" and target_node['label'] == "Objective":
            relationships.append("HAS_OBJECTIVE")
        elif source_node['label'] in ["Project", "Objective"] and target_node['label'] in ["Resources", "Risks",
                                                                                           "Schedule", "Constraints",
                                                                                           "Goal", "Team",
                                                                                           "Contingencies", "Scope"]:
            relationships.append("HAS_PROPERTY")

        elif source_node['label'] == "Objective" and target_node['label'] == "Objective":
            relationships.append("IS_SUBOBJECTIVE_OF")

        elif source_node['label'] in ["Resources", "Risks", "Schedule", "Constraints", "Goal", "Team", "Contingencies",
                                      "Scope"] and target_node['label'] == "Round":
            relationships.append("HAS_ROUND")

        elif source_node['label'] == "Trajectory" and target_node['label'] == "Round":
            relationships.append("INCLUDES_ROUND")

        if source_node['label'] == "Trajectory" and target_node['label'] in ["Project", "Objective"]:
            relationships.append("GUIDES")

        # Inverse relationships specific adjustment
        if source_node['label'] == "DRF" and target_node['label'] in ["Project", "Objective"]:
            relationships.append("HELPED_DECIDE")

        elif source_node['label'] in ["Project", "Objective"] and target_node['label'] == "Trajectory":
            relationships.append("GUIDED_BY")

        if source_node['label'] in ["Project", "Objective"] and target_node['label'] == "DRF":
            relationships.append("HAS_DRF")

        if source_node['label'] == "Objective" and target_node['label'] == "Project":
            relationships.append("ACHIEVES_GOAL_FOR")

        elif source_node['label'] in ["Resources", "Risks", "Schedule", "Constraints", "Goal", "Team", "Contingencies",
                                      "Scope"] and target_node['label'] in ["Objective", "Project"]:
            relationships.append("CONTRIBUTES_TO")

        if source_node['label'] == "Round" and target_node['label'] in ["Resources", "Risks", "Schedule", "Constraints",
                                                                        "Goal", "Team", "Contingencies", "Scope",
                                                                        "Objective"]:
            relationships.append("DISCUSSES")
        elif target_node['label'] == "Trajectory" and source_node['label'] == "Round":
            relationships.append("PART_OF_TRAJECTORY")

        return relationships

    def create_round_nodes(self, category_rounds, category_node_name_id, is_ai_user_flow, nodes_to_upload):
        # Find the category node once before the loop
        category_node_dict = next((node for node in nodes_to_upload if node['name_id'] == category_node_name_id), None)
        round_node_ids = []
        if not category_node_dict:
            print(f"Error: Category node {category_node_name_id} not found in nodes_to_upload.")
            return

        for round in category_rounds:
            round_node_name = f"Round: {round.user_message.content[:20]}..."
            round_info = f"User: {round.user_message.content}\nAI: {round.ai_message.content}" if not is_ai_user_flow else f"AI: {round.ai_message.content}\nUser: {round.user_message.content}"
            round_node_dict = self.create_node_dict(
                name=round_node_name,
                label="Round",
                information=round_info,
                connected_to=[category_node_name_id],
            )
            nodes_to_upload.append(round_node_dict)
            round_node_ids.append(round_node_dict['name_id'])
        return round_node_ids  # Return the list of created round node IDs

    def create_trajectory_node(self, conversation_session, sub_objective_node_name_id, is_ai_user_flow, nodes_to_upload,
                               all_round_node_ids):
        trajectory_info = "\n\n".join([
            f"AI: {round.ai_message.content}\nUser: {round.user_message.content}" if is_ai_user_flow else f"User: {round.user_message.content}\nAI: {round.ai_message.content}"
            for round in conversation_session.trajectory.rounds
        ])
        trajectory_node_name = f"Trajectory_of_{sub_objective_node_name_id}"
        trajectory_node = self.create_node_dict(
            name=trajectory_node_name,
            label="Trajectory",
            information=trajectory_info,
            connected_to=[sub_objective_node_name_id] + all_round_node_ids
        )
        nodes_to_upload.append(trajectory_node)
        return trajectory_node['name_id']

    def format_node_with_categories(self, conversation_session, sub_objective, categories):
        nodes_to_upload = []
        is_ai_user_flow = bool(conversation_session.trajectory.initial_question)
        sub_objective_node = self.create_node_dict(
            name=sub_objective,
            label="Objective",
            information="",
            connected_to=[]  # This will be updated to include category nodes and the trajectory node
        )
        nodes_to_upload.append(sub_objective_node)
        all_created_round_node_ids = []
        category_node_ids = []  # To collect IDs of category nodes for connecting to the sub-objective

        for category in categories:
            preview, processed_info = self.process_rounds_for_category(conversation_session, category, is_ai_user_flow)
            category_node_name = f"{category}_of_{sub_objective}: {preview}"
            category_node_dict = self.create_node_dict(
                name=category_node_name,
                label=category,
                information=processed_info,
                connected_to=[sub_objective_node['name_id']],  # Connect category to sub-objective
                summary=True
            )
            nodes_to_upload.append(category_node_dict)
            category_node_ids.append(category_node_dict['name_id'])  # Collecting ID for later connection

            category_rounds = [round for round in conversation_session.trajectory.rounds if
                               getattr(round, 'category', None) == category]
            round_node_ids = self.create_round_nodes(category_rounds, category_node_dict['name_id'], is_ai_user_flow,
                                                     nodes_to_upload)
            category_node_dict['connected_to'].extend(round_node_ids)
            all_created_round_node_ids.extend(round_node_ids)

        # Handle remaining rounds
        remaining_round_node_ids = self.create_remaining_round_nodes(conversation_session, is_ai_user_flow,
                                                                     nodes_to_upload)
        all_created_round_node_ids.extend(remaining_round_node_ids)

        # Create the trajectory node and link all rounds to it
        trajectory_node_id = self.create_trajectory_node(conversation_session, sub_objective_node['name_id'],
                                                         is_ai_user_flow, nodes_to_upload, all_created_round_node_ids)

        # Update nodes with connections to the trajectory node
        for node in nodes_to_upload:
            if node['label'] == "Round":
                node['connected_to'].append(trajectory_node_id)
            elif node['label'] == "Objective":
                node['connected_to'].append(trajectory_node_id)
                node['connected_to'].extend(category_node_ids)

        return nodes_to_upload

    def create_remaining_round_nodes(self, conversation_session, is_ai_user_flow, nodes_to_upload):
        remaining_rounds = [round for round in conversation_session.trajectory.rounds if
                            not getattr(round, 'category', None)]
        if not remaining_rounds:  # If there are no remaining rounds, return an empty list immediately
            return []

        # Call to create_round_nodes assumed to always return a list, even if it's empty
        remaining_round_node_ids = self.create_round_nodes(remaining_rounds, None, is_ai_user_flow, nodes_to_upload)

        return remaining_round_node_ids if remaining_round_node_ids is not None else []

    def process_rounds_for_category(self, conversation_session, category, is_ai_user_flow):
        category_rounds = [round for round in conversation_session.trajectory.rounds if
                           getattr(round, 'category', None) == category]
        if not category_rounds:
            return "Empty.", "No relevant information of this type found in the objective."

        # Adjust the format based on the conversation flow
        if is_ai_user_flow:
            rounds_str = "\n".join(
                [f"AI: {round.ai_message.content}\nUser: {round.user_message.content}" for round in category_rounds])
        else:
            rounds_str = "\n".join(
                [f"User: {round.user_message.content}\nAI: {round.ai_message.content}" for round in category_rounds])

        system_prompt = "Extract key information from the following conversation rounds, format it in 1 to 5 words (ex: Timeline is Risky):"
        agent = self.gpt_manager.create_agent(model=ModelType.GPT_3_5_TURBO, system_prompt=system_prompt,
                                              messages=rounds_str, temperature=0.1)
        agent.run_agent()
        preview = agent.get_text()

        return preview, rounds_str

    def create_node_dict(self, label, name, information, connected_to=None, summary: bool = False):
        """
        Helper function to create a dictionary representing a node in the graph database.

        :param label: The label of the node (e.g., "Project", "Resources").
        :param name: The original name of the node. If a UUID is included in the name, it will be removed in the 'name' field but retained in the 'name_id' field for uniqueness.
        :param information: A string or dictionary containing the information to be stored in the node. If it's a dictionary, it will be converted to a JSON string.
        :param connected_to: A list of node names this node is connected to.
        :param summary: A boolean indicating whether to summarize the information. If True, the information will be summarized to 1 to 5 words.
        :return: A dictionary representing the node.
        """
        if connected_to is None:
            connected_to = []

        # Regular expression pattern to match a UUID
        uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
        # Extract the name without UUID for the 'name' field
        name_without_uuid = re.sub(uuid_pattern, '', name).strip("_").strip()
        # Ensure the 'name_id' field contains a UUID for uniqueness
        name_id = name if re.search(uuid_pattern, name, re.IGNORECASE) else name + "_" + str(uuid.uuid4())

        # Convert information to a JSON string if it's a dictionary
        if isinstance(information, dict):
            information = json.dumps(information)

        # Optionally summarize the information
        if summary:
            prompt = "Summarize the following information in order to compress it down to around half of its original size in order to understand the essence of the information." \
                     "As long as the format is easily readable, it is good:"
            summarization_agent = self.gpt_manager.create_agent(model=ModelType.GPT_3_5_TURBO, temperature=0.7,
                                                                messages=information + prompt,
                                                                max_tokens=400)
            if information == "No relevant information of this type found in the objective.":
                pass
            else:
                summarization_agent.run_agent()
                information = summarization_agent.get_text()

        return {
            "label": label,
            "name_id": name_id,  # Use the name with a UUID for uniqueness
            "name": name_without_uuid,  # Original name without UUID
            "information": information,
            "connected_to": connected_to
        }

    def form_to_nodes(self, project_form):
        categories = ["Resources", "Risks", "Schedule", "Constraints", "Goal", "Team", "Contingencies", "Scope"]
        category_mapping = {
            "Resources": "1. Resources at Hand",
            "Risks": "2. Navigating Risks",
            "Schedule": "3. Mapping the Journey",
            "Constraints": "4. Terrain Constraints",
            "Goal": "6. The Quest",
            "Team": "5. Bonus Information on The Crew",
            "Contingencies": "7. Provisions and Protocols",
            "Scope": "8. The Boundaries of Our Map"
        }

        # Create the Project node
        project_node = self.create_node_dict("Project", self.project.name_id, project_form, summary=True)
        nodes_to_upload = [project_node]

        # Create nodes for each category based on the project form
        for category in categories:
            form_key = category_mapping.get(category, "")
            category_info = project_form.get(form_key, {})
            node = self.create_node_dict(category, category, category_info,
                                         summary=False)
            nodes_to_upload.append(node)
            project_node['connected_to'].append(node['name_id'])
            node['connected_to'].append(project_node['name_id'])

        # Handle sub-objectives if present
        if "9. Charting the Sub-Objectives" in project_form:
            sub_objectives_text = project_form["9. Charting the Sub-Objectives"].get("Sub-Objectives", "").strip()
            sub_objectives_list = self.extract_sub_objectives(sub_objectives_text)
            sub_objective_nodes_list = self.handle_sub_objectives_conversation(sub_objectives_list)
            for sub_objective_nodes in sub_objective_nodes_list:
                for sub_objective_node in sub_objective_nodes:
                    if sub_objective_node['label'] == "Objective":
                        project_node['connected_to'].append(sub_objective_node['name_id'])
                        sub_objective_node['connected_to'].append(project_node['name_id'])
                    nodes_to_upload.append(sub_objective_node)

        # Create a Trajectory node for the Project Form without summarization
        project_form_details = json.dumps(project_form, indent=4)
        trajectory_node = self.create_node_dict(
            label="Trajectory",
            name="ProjectFormTrajectory",
            information=project_form_details,
            connected_to=[project_node['name_id']],
            summary=False
        )
        nodes_to_upload.append(trajectory_node)
        for node in nodes_to_upload:
            if node['label'] == "Project":
                node['connected_to'].append(trajectory_node['name_id'])

        return nodes_to_upload

    def pair_nodes_without_drf(self):
        self.drf_manager.pair_nodes_without_drf()  # only pairs Project and Objective nodes

    def handle_sub_objectives_conversation(self, sub_objectives_list):
        # List of premade conversations for testing the four sub-objectives
        premade_conversations = [
            SUB_OBJECTIVE_1_CONVERSATION,
            SUB_OBJECTIVE_2_CONVERSATION,
            SUB_OBJECTIVE_3_CONVERSATION,
            SUB_OBJECTIVE_4_CONVERSATION,
        ]
        premade_categories = [
            SUB_OBJECTIVE_1_CATEGORIES,
            SUB_OBJECTIVE_2_CATEGORIES,
            SUB_OBJECTIVE_3_CATEGORIES,
            SUB_OBJECTIVE_4_CATEGORIES
        ]
        extracted_nodes = []
        for index, sub_objective in enumerate(sub_objectives_list):
            sub_objective = re.sub(r"[^a-zA-Z\s]", "", sub_objective).strip()
            sub_objective_agent = self.gpt_manager.create_agent(model=ModelType.GPT_3_5_TURBO, temperature=0.7,
                                                                messages="",
                                                                system_prompt=f"Discuss the sub-objective ({sub_objective}) with the User. "
                                                                              f"The goal is to obtain information relevant to these instructions: {PROJECT_FORM_INSTRUCTIONS}")
            categories = ["Resources", "Risks", "Schedule", "Constraints", "Goal", "Team", "Contingencies", "Scope"]
            listener = TrajectoryListenerCategorizer(categories)
            sub_objective_conversation = self.new_project_conversation(
                initial_prompt=f"Discuss the sub-objective ({sub_objective}) with the AI.",
                discussion_name=f"Sub-objective: {sub_objective}",
                subject=f"Obtain the 8 elements of an objective: Resources, Risks, Schedule, Constraints, Crew, Goal, Contingencies, and Scope for the sub-objective: {sub_objective}",
                conversation_type=ConversationType.FREESTYLE,
                conversation_memory_type=MemoryType.LAST_X_MESSAGES,
                conversation_agent=sub_objective_agent,
                premade_conversation=premade_conversations[index],
                premade_categories=premade_categories[index],
                listeners=[listener]
            )
            extracted_nodes.append(
                self.format_node_with_categories(sub_objective_conversation, sub_objective, categories))
        return extracted_nodes

    def handle_general_conversation(self):
        system_prompt = f"You are a conversation model. Your goal is to enhance conversations by posing questions " \
                        f"that probe deeper, such as inquiring about the motivations behind someone's project. " \
                        f"Listen empathically while pushing the conversation forward at the pace of the other. " \
                        f"Here is the information that you already know from the user: {self.project.initial_form}"
        general_conversation_agent = self.gpt_manager.create_agent(model=ModelType.GPT_3_5_TURBO,
                                                                   system_prompt=system_prompt, temperature=0.7,
                                                                   messages="")

        general_conversation = self.new_project_conversation(
            initial_prompt="This is a general conversation about the project. Let's get started.",
            discussion_name="General Project Discussion",
            subject="General Project Introduction",
            conversation_type=ConversationType.FREESTYLE,
            conversation_memory_type=MemoryType.LAST_X_MESSAGES,
            # TODO: change to a memory type that has access to the db
            conversation_agent=general_conversation_agent
        )

    def extract_sub_objectives(self, sub_objectives_text) -> List[str]:

        # Check if sub-objectives text is empty or not provided
        if not sub_objectives_text or sub_objectives_text.lower() == "no sub-objectives provided.":
            print("No sub-objectives provided in the project form.")
            return []

        # Update the extraction prompt to include the new instruction
        extraction_prompt = ("You will receive a description of the sub-objectives of a project. "
                             "Please list them in a clear bullet point format(1.\n2.\n,etc). If no sub-objectives are present,"
                             " write '$data' in your answer.")

        # Create and run the GPT agent
        objective_extractor = self.gpt_manager.create_agent(model=ModelType.GPT_3_5_TURBO, messages=sub_objectives_text,
                                                            system_prompt=extraction_prompt,
                                                            temperature=0.1)
        # objective_extractor.run_agent() currently under testing
        extracted_text = objective_extractor.get_text()
        extracted_text = """
- Designing the interactive platform
- Developing curriculum content
- Engaging with schools for pilot testing
- Establishing a feedback loop for continuous improvement
"""

        # Check if the response indicates that no sub-objectives are present
        if extracted_text.strip() == "$data":
            print("GPT agent indicated that no sub-objectives are present.")
            return []

        sub_objectives_list = []
        # Process the response to extract sub-objectives, handling flexible formats
        for line in extracted_text.split('\n'):
            line = line.strip()
            if line and not line.lower().startswith("no sub-objectives"):
                objective_description = line.split(":")[-1].strip().strip("<>").strip() if ":" in line else line
                if objective_description:
                    sub_objectives_list.append(objective_description)

        # Fallback mechanism
        if not sub_objectives_list and extracted_text.strip():
            print(
                "Sub-objectives were not listed in a standard format. Considering the entire response as a single objective.")
            sub_objectives_list.append(extracted_text.strip())

        return sub_objectives_list

    def new_project_conversation(self, initial_prompt="This is a new conversation session.",
                                 # might be better as a class
                                 discussion_name="First Session", subject="Project Introduction",
                                 conversation_type: ConversationType = ConversationType.FREESTYLE,
                                 conversation_memory_type: MemoryType = MemoryType.LAST_X_MESSAGES,
                                 conversation_agent: GPTAgent = None, premade_conversation=None,
                                 premade_categories=None, listeners: list = None):
        print(initial_prompt)
        # Create a DiscussionSession object

        new_conversation = DiscussionSession(discussion_name=discussion_name, subject=subject,
                                             conversation_type=conversation_type, memory_type=conversation_memory_type,
                                             agent=conversation_agent)
        if listeners:
            for listener in listeners:
                new_conversation.register_listener(listener)
        if TESTING and premade_conversation:
            new_conversation.insert_premade_conversation(premade_conversation=premade_conversation,
                                                         premade_categories=premade_categories)
        else:
            new_conversation.start_session(testing=True)

        if self.project:
            self.add_conversation_session_to_project(new_conversation)
        return new_conversation

    def add_conversation_session_to_project(self, session: DiscussionSession):
        self.project.add_conversation_session(session)

    def get_project(self):
        return self.project

    def set_project_schedule(self, schedule: ProjectSchedule):
        self.project.set_project_schedule(schedule)

    def set_memory_access(self, memory_access: MemoryStreamAccess):
        self.project.set_memory_access(memory_access)

    def get_project_name(self):
        return self.project.name_id

    def get_discussion_sessions(self):
        return self.project.discussion_sessions

    def get_project_schedule(self):
        return self.project.project_schedule


if __name__ == "__main__":
    project_handler = ProjectHandler()
    project_handler.new_project_init("SpikyMind")
