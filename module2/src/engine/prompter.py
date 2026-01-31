from jinja2 import Environment, FileSystemLoader
from config import Config

class SystemPrompter:
    def __init__(self):
        # Jinja2 configuration: we specify the folders where the templates are located
        # This allows us to use {% include 'memory/templates/semantic.j2' %}
        self.env = Environment(loader=FileSystemLoader([
            Config.TEMPLATES_DIR, 
            Config.MEMORY_DIR + "/templates"
        ]))
        
    def build_system_prompt(self, core, profile, session, history):
        template = self.env.get_template("main.j2")
        

        return template.render(
            core=core,
            profile=profile,
            session=session,
            history=history
        )    
