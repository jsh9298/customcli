from .base import BaseHandler
from rich.table import Table

class AIHandlers(BaseHandler):
    """[Domain Layer] Handles AI models, personas, and UI themes with Hybrid CLI/UI support."""

    async def model(self, ctx, *args):
        # Direct execution if argument provided
        if args:
            model_name = args[0]
            if model_name in self.cli.available_models:
                self.cli.config['agent']['model'] = model_name
                ctx['should_reinit'] = True
                self.cli.ui.print_success(f"Model set to: {model_name}")
            else:
                self.cli.ui.print_error(f"Unknown model: {model_name}.")
            return

        # Interactive UI
        models = self.cli.available_models
        idx = await self.ask_selection("Select AI Model", models)
        if idx is not None:
            self.cli.config['agent']['model'] = models[int(idx)]
            ctx['should_reinit'] = True
            self.cli.ui.print_success(f"Switched to {self.cli.config['agent']['model']}")

    async def theme(self, ctx, *args):
        themes = ["neon", "hacker", "classic"]
        if args and args[0].lower() in themes:
            self.cli.ui.set_theme(args[0].lower())
            self.cli.ui.print_success(f"Theme: {args[0]}")
            return

        idx = await self.ask_selection("Select UI Theme", themes)
        if idx is not None:
            self.cli.ui.set_theme(themes[int(idx)])
            self.cli.ui.print_success(f"Theme applied: {themes[int(idx)]}")

    async def agents(self, ctx, *args):
        personas = list(self.cli.personas.keys())
        # Direct execution
        if args:
            p_name = args[0].lower()
            if p_name in self.cli.personas:
                self.cli.active_persona = p_name
                self.cli.re_initialize()
                ctx['should_reinit'] = True
                self.cli.ui.print_success(f"Persona: {p_name}")
            else:
                self.cli.ui.print_error(f"Unknown persona: {p_name}")
            return

        # Interactive UI
        idx = await self.ask_selection("Select Agent Persona", personas)
        if idx and idx.isdigit() and int(idx) < len(personas):
            self.cli.active_persona = personas[int(idx)]
            self.cli.re_initialize()
            ctx['should_reinit'] = True
            self.cli.ui.print_success(f"Persona switched to {self.cli.active_persona}")

    async def skills(self, ctx, *args):
        """[Interactive UI] Browse and activate agent skills."""
        available_skills = self.cli.skill_manager.list_skills()
        options = ["List Activated Skills", "Load New Skill", "Save Current Prompt as Skill"]
        
        idx = await self.ask_selection("Agent Skills Manager", options)
        
        if idx == '0':
            self.cli.ui.print_info(f"Available: {available_skills}")
        elif idx == '1':
            s_idx = await self.ask_selection("Select Skill to Load", available_skills)
            if s_idx.isdigit() and int(s_idx) < len(available_skills):
                skill_name = available_skills[int(s_idx)]
                sk = self.cli.skill_manager.load_skill(skill_name)
                if sk:
                    self.cli.prompt = sk.get('instruction', self.cli.prompt)
                    ctx['should_reinit'] = True
                    self.cli.ui.print_success(f"Skill '{skill_name}' activated.")
        elif idx == '2':
            name = await self.cli.session.prompt_async("Skill Name to Save: ")
            if name:
                self.cli.skill_manager.save_skill(name, {"instruction": self.cli.prompt})
                self.cli.ui.print_success(f"Saved skill: {name}")
