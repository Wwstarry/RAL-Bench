import subprocess

class CliRunner:
    def invoke(self, app, args: List[str]):
        command = ["python", "-c", self._generate_script(app, args)]
        result = subprocess.run(command, capture_output=True, text=True)
        return result

    def _generate_script(self, app, args: List[str]) -> str:
        commands = "\n".join(
            f"@app.command('{name}')\ndef {name}(): pass"
            for name in app._commands.keys()
        )
        script = f"""
import typer
app = typer.Typer()
{commands}
app()
"""
        return script