from pathlib import Path
from scripts import utils

class Task:
    category:str
    description:str
    is_done:bool
    effort:int|None

class Nutri:
    description:str
    is_done:bool
    is_meta:bool

class Note:
    date:str
    labels:dict[str, str]
    tasks:list[Task]
    nutri:list[Nutri]
    introspection:str


def _parse_checklist(line:str, section_name:str) -> tuple[str, bool]:
    if '- [x]' in line:
        return line.lstrip('- [x]').strip(), True
    elif '- []' in line:
        return line.lstrip('- []').strip(), False

    print(line)
    raise Exception(f"Element in section '{section_name}' is not a proper checklist.")


def parse(filepath:Path) -> Note:
    note = Note()

    note.tasks = []
    note.nutri = []
    note.labels = dict()

    note.date = filepath.name.split('.')[0]

    content = filepath.read_text().lower()
    content = utils.remove_accents(content)

    sections = content.split('## ')

    for section in sections:
        lines = section.split('\n')
        lines = [line for line in lines if len(line.strip()) > 0]

        if len(lines) == 0:
            continue

        subtitle = lines[0].replace('#', '').strip()

        if subtitle == 'tarefas':
            for line in lines:
                task = Task()

                row, task.is_done = _parse_checklist(line, 'tarefas')
                key, value = row.split(':', 1)
                value_alt, effort = value.rsplit(' ', 1)

                task.category = key.strip()
                task.description = value

                if effort in ('+', '++', '+++'):
                    task.description = value_alt
                    task.effort = len(effort)

                note.tasks.append(task)
        if subtitle == 'nutricao':
            for line in lines:
                nutri = Nutri()

                row, nutri.is_done = _parse_checklist(line, 'nutricao')
                nutri.description = row
                nutri.is_meta = row.startswith('[')

                note.nutri.append(nutri)
        elif subtitle == 'reflexao':
            note.introspection = "\n".join(lines)
        else:
            for line in lines:
                key, value = line.split(':', 1)
                note.labels[key.strip()] = value.strip()

    return note
