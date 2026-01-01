"""Terminal UI components - Modern & Elegant design."""
from __future__ import annotations

import shutil
from typing import Literal

from colorama import Fore, Style


def get_terminal_width() -> int:
    """Get terminal width, fallback to 80."""
    try:
        return shutil.get_terminal_size().columns
    except Exception:
        return 80


def header(text: str, width: int | None = None) -> str:
    """Create a beautiful header with rounded corners.

    ╭───────────────────────────────────────────────╮
    │  ⚡ TEXT HERE                                 │
    ╰───────────────────────────────────────────────╯
    """
    if width is None:
        width = get_terminal_width()

    inner_width = width - 4
    padded_text = f"  {text}".ljust(inner_width)

    top = f"╭{'─' * (width - 2)}╮"
    mid = f"│{padded_text}│"
    bot = f"╰{'─' * (width - 2)}╯"

    return f"{Fore.CYAN}{Style.BRIGHT}{top}\n{mid}\n{bot}{Style.RESET_ALL}"


def subheader(text: str, icon: str = "▸") -> str:
    """Create a clean subheader with icon.

    ▸ Text Here
    """
    return f"{Fore.BLUE}{Style.BRIGHT}{icon} {text}{Style.RESET_ALL}"


def panel(
    title: str,
    lines: list[str],
    width: int | None = None,
    border_color: str = Fore.CYAN
) -> str:
    """Create an info panel with title.

    ┌─ TITLE ─────────────────────────────────────┐
    │ Line 1                                       │
    │ Line 2                                       │
    └──────────────────────────────────────────────┘
    """
    if width is None:
        width = get_terminal_width()

    inner_width = width - 4

    # Top border with title
    title_part = f"─ {title} "
    remaining = width - len(title_part) - 2
    top = f"┌{title_part}{'─' * remaining}┐"

    # Content lines
    content = []
    for line in lines:
        # Remove any existing color codes for width calculation
        clean_line = line
        padded = line.ljust(inner_width + (len(line) - len(clean_line)))
        content.append(f"│ {padded} │")

    # Bottom border
    bot = f"└{'─' * (width - 2)}┘"

    result = f"{border_color}{top}{Style.RESET_ALL}\n"
    result += "\n".join(content) + "\n"
    result += f"{border_color}{bot}{Style.RESET_ALL}"

    return result


def status_line(
    label: str,
    value: str,
    status: Literal["success", "info", "warning", "error", "neutral"] = "neutral",
    icon: str | None = None
) -> str:
    """Create a status line with optional icon.

    ✓ Label: value
    """
    # Status colors and default icons
    status_map = {
        "success": (Fore.GREEN, "✓"),
        "info": (Fore.CYAN, "●"),
        "warning": (Fore.YELLOW, "⚠"),
        "error": (Fore.RED, "✗"),
        "neutral": (Fore.WHITE, "◦")
    }

    color, default_icon = status_map.get(status, (Fore.WHITE, "◦"))
    icon = icon or default_icon

    return f"{color}{icon}{Style.RESET_ALL} {Fore.WHITE}{label}:{Style.RESET_ALL} {value}"


def divider(char: str = "─", width: int | None = None, color: str = Fore.CYAN) -> str:
    """Create a horizontal divider."""
    if width is None:
        width = get_terminal_width()
    return f"{color}{char * width}{Style.RESET_ALL}"


def banner() -> str:
    """Create app banner with ASCII art."""
    return f"""{Fore.CYAN}{Style.BRIGHT}
╭──────────────────────────────────────────────────────────────────╮
│                                                                  │
│     ███████╗███████╗████████╗██████╗  █████╗ ████████╗          │
│     ██╔════╝██╔════╝╚══██╔══╝██╔══██╗██╔══██╗╚══██╔══╝          │
│     █████╗  ███████╗   ██║   ██████╔╝███████║   ██║             │
│     ██╔══╝  ╚════██║   ██║   ██╔══██╗██╔══██║   ██║             │
│     ███████╗███████║   ██║   ██║  ██║██║  ██║   ██║             │
│     ╚══════╝╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝             │
│                                                                  │
│              D O W N L O A D E R   v 2.0                         │
│                                                                  │
╰──────────────────────────────────────────────────────────────────╯{Style.RESET_ALL}"""


def simple_banner() -> str:
    """Create simple banner for headless mode."""
    return f"""{Fore.CYAN}{Style.BRIGHT}
╔══════════════════════════════════════════════════════════════════╗
║              ⚡ ESTRATÉGIA DOWNLOADER v2.0                       ║
╚══════════════════════════════════════════════════════════════════╝{Style.RESET_ALL}"""


def config_panel(mode: str, workers: int, save_dir: str) -> str:
    """Create configuration info panel."""
    # Truncate save_dir if too long
    max_path_len = 50
    display_dir = save_dir if len(save_dir) <= max_path_len else "..." + save_dir[-max_path_len:]

    lines = [
        status_line("Modo", f"{Fore.YELLOW}{mode}{Style.RESET_ALL}", "info", "⚙"),
        status_line("Workers", f"{Fore.YELLOW}{workers}{Style.RESET_ALL}", "info", "⚡"),
        status_line("Retry", f"{Fore.YELLOW}4x com backoff{Style.RESET_ALL}", "info", "🔄"),
        status_line("Checkpoint", f"{Fore.GREEN}Ativo{Style.RESET_ALL}", "success", "💾"),
        "",
        status_line("Destino", f"{Fore.CYAN}{display_dir}{Style.RESET_ALL}", "neutral", "📁"),
    ]
    return panel("CONFIGURAÇÃO", lines, width=70, border_color=Fore.CYAN)


def course_header(course_num: int, total_courses: int, course_name: str) -> str:
    """Create course header."""
    progress = f"{course_num}/{total_courses}"
    bar_len = 24
    filled = int((course_num / total_courses) * bar_len)
    bar = f"{'█' * filled}{'░' * (bar_len - filled)}"
    percentage = int((course_num / total_courses) * 100)

    # Truncate course name if too long
    max_name_len = 50
    display_name = course_name[:max_name_len].ljust(max_name_len)

    return f"""
{Fore.MAGENTA}{Style.BRIGHT}╭─ CURSO {progress} ─────────────────────────────────────────╮
│ 📚 {display_name} │
│ {bar} {percentage:3d}% │
╰───────────────────────────────────────────────────────────╯{Style.RESET_ALL}"""


def lesson_header(lesson_num: int, total_lessons: int, lesson_name: str) -> str:
    """Create lesson header."""
    return f"\n{Fore.BLUE}{Style.BRIGHT}  ▸ Aula {lesson_num:02d}/{total_lessons:02d}: {lesson_name}{Style.RESET_ALL}"


def download_summary(
    total: int,
    completed: int,
    skipped: int,
    failed: int,
    elapsed_time: str
) -> str:
    """Create download summary panel."""
    lines = [
        status_line("Total", f"{total} arquivos", "info"),
        status_line("Completos", f"{completed}", "success"),
        status_line("Pulados", f"{skipped}", "warning"),
        status_line("Falhas", f"{failed}", "error" if failed > 0 else "success"),
        "",
        status_line("Tempo", elapsed_time, "neutral", "⏱"),
    ]
    return panel("RESUMO DO DOWNLOAD", lines, width=70, border_color=Fore.GREEN if failed == 0 else Fore.YELLOW)


def login_prompt(wait_time: int) -> str:
    """Create login prompt message."""
    return f"""
{Fore.YELLOW}{Style.BRIGHT}╭─ ATENÇÃO: LOGIN NECESSÁRIO ──────────────────────────────────────╮
│                                                                  │
│  ⚠  O navegador será aberto para você fazer login.              │
│                                                                  │
│  ⏱  Você tem {wait_time} segundos para completar o login.              │
│                                                                  │
│  💡 Os cookies serão salvos para próximas execuções.             │
│                                                                  │
╰──────────────────────────────────────────────────────────────────╝{Style.RESET_ALL}"""


def session_restored() -> str:
    """Session restored successfully message."""
    return f"{Fore.GREEN}{Style.BRIGHT}✓ Sessão restaurada com sucesso! Login automático.{Style.RESET_ALL}"


def retry_indicator(attempt: int, max_retries: int, filename: str) -> str:
    """Show retry attempt."""
    dots = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
    dot = dots[attempt % len(dots)]
    return f"{Fore.YELLOW}{dot} Tentativa {attempt}/{max_retries}: {filename}{Style.RESET_ALL}"


def progress_bar_format() -> dict:
    """Get tqdm progress bar format configuration."""
    return {
        "bar_format": "{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]",
        "colour": "cyan",
        "ncols": min(get_terminal_width() - 10, 100),
    }


def file_status(filename: str, size_mb: float, status: Literal["downloaded", "skipped", "failed", "retry"]) -> str:
    """Format file download status."""
    status_map = {
        "downloaded": (Fore.GREEN, "✓", "Baixado"),
        "skipped": (Fore.YELLOW, "○", "Pulado"),
        "failed": (Fore.RED, "✗", "Falhou"),
        "retry": (Fore.YELLOW, "⟳", "Retry"),
    }

    color, icon, label = status_map.get(status, (Fore.WHITE, "?", "Unknown"))
    size_str = f"{size_mb:6.1f} MB" if size_mb > 0 else "  --    "

    # Truncate filename if too long
    max_len = 45
    display_name = filename if len(filename) <= max_len else filename[:max_len-3] + "..."

    return f"{color}{icon}{Style.RESET_ALL} {display_name.ljust(max_len)} {Fore.CYAN}{size_str}{Style.RESET_ALL}"


def goodbye() -> str:
    """Farewell message."""
    return f"""
{Fore.CYAN}{Style.BRIGHT}╭──────────────────────────────────────────────────────────────────╮
│                                                                  │
│                    ✨ Download Concluído! ✨                     │
│                                                                  │
│              Obrigado por usar Estratégia Downloader            │
│                                                                  │
╰──────────────────────────────────────────────────────────────────╝{Style.RESET_ALL}
"""


def course_selection_panel(courses: list[dict[str, str]]) -> str:
    """Create a panel listing all available courses for selection.

    Args:
        courses: List of course dicts with 'title' and 'url' keys.

    Returns:
        Formatted string with numbered course list.
    """
    width = get_terminal_width()
    max_title_len = width - 10  # Leave room for number and padding

    lines = []
    for i, course in enumerate(courses, 1):
        title = str(course.get('title', 'Curso sem título'))
        if len(title) > max_title_len:
            title = title[:max_title_len - 3] + "..."
        lines.append(f"  {Fore.YELLOW}{i:3d}.{Style.RESET_ALL} {title}")

    header_text = f"📚 CURSOS DISPONÍVEIS ({len(courses)} cursos)"

    result = f"\n{Fore.CYAN}{Style.BRIGHT}{header_text}{Style.RESET_ALL}\n"
    result += f"{Fore.CYAN}{'─' * min(width - 2, 60)}{Style.RESET_ALL}\n"
    result += "\n".join(lines)
    result += f"\n{Fore.CYAN}{'─' * min(width - 2, 60)}{Style.RESET_ALL}\n"

    return result


def selection_prompt() -> str:
    """Create the selection prompt with usage instructions.

    Returns:
        Formatted string with selection instructions.
    """
    return f"""
{Fore.GREEN}{Style.BRIGHT}Selecione os cursos para download:{Style.RESET_ALL}
  {Fore.CYAN}•{Style.RESET_ALL} Digite {Fore.YELLOW}'all'{Style.RESET_ALL} para baixar todos
  {Fore.CYAN}•{Style.RESET_ALL} Digite números específicos: {Fore.YELLOW}1,3,5{Style.RESET_ALL}
  {Fore.CYAN}•{Style.RESET_ALL} Digite intervalos: {Fore.YELLOW}1-5{Style.RESET_ALL}
  {Fore.CYAN}•{Style.RESET_ALL} Combine opções: {Fore.YELLOW}1,3,5-7,10{Style.RESET_ALL}

{Fore.GREEN}>{Style.RESET_ALL} """


def selected_courses_summary(courses: list[dict[str, str]]) -> str:
    """Show summary of selected courses.

    Args:
        courses: List of selected course dicts.

    Returns:
        Formatted string showing selected courses.
    """
    result = f"\n{Fore.GREEN}✓ {len(courses)} curso(s) selecionado(s) para download:{Style.RESET_ALL}\n"
    for course in courses:
        title = str(course.get('title', 'Curso sem título'))
        if len(title) > 50:
            title = title[:47] + "..."
        result += f"  {Fore.CYAN}•{Style.RESET_ALL} {title}\n"
    return result

