from pathlib import Path
from scripts import utils


class Task:
    category: str
    description: str
    is_done: bool
    effort: int | None


class Nutri:
    description: str
    is_done: bool
    is_meta: bool


class Note:
    date: str
    labels: dict[str, str]
    tasks: list[Task]
    nutri: list[Nutri]
    introspection: str


def _parse_checklist(line: str, section_name: str) -> tuple[str, bool]:
    if "- [x]" in line:
        return line.removeprefix("- [x]").strip(), True

    elif "- [ ]" in line:
        return line.removeprefix("- [ ]").strip(), False

    raise Exception(
        f"Element in section '{section_name}' is not a proper checklist. ({line})"
    )


def parse(filepath: Path) -> Note:
    note = Note()

    note.tasks = []
    note.nutri = []
    note.labels = dict()
    note.date = filepath.name.split(".")[0]

    content = filepath.read_text().lower()
    content = utils.remove_accents(content)
    sections = content.split("## ")

    for section in sections:
        lines = section.split("\n")
        lines = [line for line in lines if len(line.strip()) > 0]

        if len(lines) == 0:
            continue

        subtitle = lines[0].replace("#", "").strip()

        if subtitle == "tarefas":
            for line in lines[1:]:
                task = Task()
                row, task.is_done = _parse_checklist(line, subtitle)
                key, value = (row + " ").split(":", 1)
                value_alt, effort = value.rsplit(" ", 1)
                task.category = key.strip()

                if effort in ("+", "++", "+++"):
                    task.description = value_alt.strip()
                    task.effort = len(effort)
                else:
                    task.description = value.strip()
                    task.effort = None

                note.tasks.append(task)

        elif subtitle == "nutricao":
            for line in lines[1:]:
                nutri = Nutri()
                row, nutri.is_done = _parse_checklist(line, subtitle)
                nutri.description = row
                nutri.is_meta = row.startswith("[")
                note.nutri.append(nutri)

        elif subtitle == "reflexao":
            note.introspection = "\n".join(lines[1:])

        else:
            for line in lines[1:]:
                if ":" in line:
                    key, value = (line + " ").split(":", 1)
                    note.labels[key.strip()] = value.strip()

    return note
