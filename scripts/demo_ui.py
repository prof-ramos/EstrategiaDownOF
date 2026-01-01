"""Demo script to showcase the new UI without requiring login."""
import time
import ui
from colorama import Fore, Style


def demo_ui():
    """Demonstrate the new UI components."""
    # Banner
    print(ui.banner())
    time.sleep(0.5)

    # Config panel
    print("\n" + ui.config_panel("Async", 8, "/Users/user/Downloads/Cursos"))
    print()
    time.sleep(0.5)

    # Session restored
    print(ui.session_restored())
    print()
    time.sleep(0.5)

    # Course header
    print(ui.course_header(1, 5, "Direito Constitucional - Teoria e Questões Comentadas"))
    time.sleep(0.3)

    # Lesson headers
    print(ui.lesson_header(1, 20, "Princípios Fundamentais da Constituição"))
    time.sleep(0.2)

    print(f"\n  {Fore.CYAN}● INFO:{Style.RESET_ALL} Iniciando download de 8 arquivos em paralelo (com retry e resume)...")
    time.sleep(0.3)

    # File statuses
    print("\n  " + ui.file_status("Aula_01_Introducao_PDF_Original.pdf", 2.3, "downloaded"))
    time.sleep(0.1)
    print("  " + ui.file_status("Aula_01_Introducao_PDF_Simplificado.pdf", 1.1, "downloaded"))
    time.sleep(0.1)
    print("  " + ui.file_status("Video_Principios_Fundamentais_720p.mp4", 124.5, "downloaded"))
    time.sleep(0.1)
    print("  " + ui.file_status("Video_Principios_Fundamentais_Resumo.pdf", 0.8, "skipped"))
    time.sleep(0.1)

    print(ui.lesson_header(2, 20, "Direitos e Garantias Fundamentais"))
    time.sleep(0.2)

    print(f"\n  {Fore.CYAN}● INFO:{Style.RESET_ALL} Iniciando download de 6 arquivos em paralelo (com retry e resume)...")
    time.sleep(0.3)

    print("\n  " + ui.file_status("Aula_02_PDF_Original.pdf", 3.2, "downloaded"))
    time.sleep(0.1)
    print("  " + ui.file_status("Video_Direitos_Garantias_720p.mp4", 98.7, "downloaded"))
    time.sleep(0.1)

    # Course 2
    print(ui.course_header(2, 5, "Português - Gramática e Interpretação de Texto"))
    time.sleep(0.3)

    print(ui.lesson_header(1, 15, "Ortografia e Acentuação"))
    time.sleep(0.2)

    print(f"\n  {Fore.GREEN}✓{Style.RESET_ALL} Todos os arquivos já foram baixados.")
    time.sleep(0.3)

    # Divider
    print("\n" + ui.divider())
    time.sleep(0.3)

    # Summary
    print("\n" + ui.download_summary(
        total=50,
        completed=45,
        skipped=3,
        failed=2,
        elapsed_time="00:12:34"
    ))
    print()
    time.sleep(0.5)

    # Goodbye
    print(ui.goodbye())


if __name__ == "__main__":
    demo_ui()
