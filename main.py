"""AutoDownload Estratégia Concursos - Downloader otimizado para macOS."""
from __future__ import annotations

import argparse
import os

# Use orjson for 10x faster JSON if available, fallback to stdlib
try:
    import orjson
    def json_loads(data: str | bytes) -> dict:
        return orjson.loads(data)
    def json_dumps(obj: dict, indent: bool = False) -> bytes:
        opts = orjson.OPT_INDENT_2 if indent else 0
        return orjson.dumps(obj, option=opts)
    JSON_WRITE_MODE = 'wb'
except ImportError:
    import json
    def json_loads(data: str | bytes) -> dict:
        return json.loads(data)
    def json_dumps(obj: dict, indent: bool = False) -> str:
        return json.dumps(obj, indent=2 if indent else None)
    JSON_WRITE_MODE = 'w'
import ssl
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import TYPE_CHECKING
from urllib.parse import urljoin

import requests
import urllib3
from colorama import Fore, Style, init
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from tqdm import tqdm

from async_downloader import run_async_downloads, DownloadIndex
import ui

if TYPE_CHECKING:
    from selenium.webdriver.remote.webdriver import WebDriver


# --- Configurações Iniciais ---
init(autoreset=True)  # Inicializa o Colorama

# Ajuste para certificados SSL no macOS (caso o Python não encontre os certificados do sistema)
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

BASE_URL = "https://www.estrategiaconcursos.com.br"
MY_COURSES_URL = urljoin(BASE_URL, "/app/dashboard/cursos")
MAX_WORKERS = 4  # Número de downloads simultâneos
COOKIES_FILE = "cookies.json"
SESSION = requests.Session()  # Sessão global para reaproveitar conexões
SESSION.verify = False  # Desabilita verificação SSL apenas para esta sessão

# Suprimir avisos de SSL (opcional, mas evita poluir o terminal)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- Funções de Log Coloridas ---
def log_info(msg: str) -> None:
    """Log informational message."""
    tqdm.write(f"{Fore.CYAN}● INFO:{Style.RESET_ALL} {msg}")


def log_success(msg: str) -> None:
    """Log success message."""
    tqdm.write(f"{Fore.GREEN}✓ OK:{Style.RESET_ALL} {msg}")


def log_warn(msg: str) -> None:
    """Log warning message."""
    tqdm.write(f"{Fore.YELLOW}⚠ AVISO:{Style.RESET_ALL} {msg}")


def log_error(msg: str) -> None:
    """Log error message."""
    tqdm.write(f"{Fore.RED}✗ ERRO:{Style.RESET_ALL} {msg}")

# --- Funções Auxiliares ---

# Translation table for filename sanitization (computed once at module load)
_SANITIZE_TRANS = str.maketrans({
    '<': None, '>': None, ':': None, '"': None, '/': None,
    '\\': None, '|': None, '?': None, '*': None, '.': None, ',': None,
    ' ': '_', '-': '_'
})

def sanitize_filename(original_filename: str) -> str:
    """Remove caracteres inválidos do nome do arquivo (optimized single-pass)."""
    sanitized = original_filename.translate(_SANITIZE_TRANS)
    # Collapse multiple consecutive underscores
    while '__' in sanitized:
        sanitized = sanitized.replace('__', '_')
    return sanitized.strip('_')

def retry_with_backoff(func, max_retries: int = 3, initial_delay: float = 2.0):
    """Executa função com retry e backoff exponencial.

    Args:
        func: Função a executar (deve retornar tuple (success: bool, result))
        max_retries: Número máximo de tentativas
        initial_delay: Delay inicial em segundos

    Returns:
        Resultado da função ou None se todas tentativas falharem
    """
    delay = initial_delay
    for attempt in range(max_retries):
        try:
            success, result = func()
            if success:
                return result
            # Se não teve sucesso mas não lançou exceção, tenta novamente
            if attempt < max_retries - 1:
                time.sleep(delay)
                delay *= 2  # Backoff exponencial
        except Exception:
            if attempt < max_retries - 1:
                time.sleep(delay)
                delay *= 2
            else:
                raise  # Re-lança exceção na última tentativa
    return None

def save_cookies(driver: WebDriver, path: str) -> bool:
    """Salva cookies do navegador em arquivo JSON (orjson optimized)."""
    try:
        with open(path, JSON_WRITE_MODE) as f:
            f.write(json_dumps(driver.get_cookies(), indent=True))
        log_info("Cookies salvos.")
        return True
    except (OSError, IOError) as e:
        log_warn(f"Erro ao salvar cookies: {e}")
        return False


def load_cookies(driver: WebDriver, path: str) -> bool:
    """Carrega cookies de arquivo JSON para o navegador (orjson optimized)."""
    if not os.path.exists(path):
        return False
    try:
        with open(path, 'rb') as f:
            cookies = json_loads(f.read())
        for cookie in cookies:
            # Alguns cookies podem ter campos incompatíveis
            cookie.pop('sameSite', None)  # Remove campo problemático
            try:
                driver.add_cookie(cookie)
            except Exception:
                pass  # Ignora cookies inválidos
        log_info("Cookies carregados.")
        return True
    except (ValueError, OSError, IOError) as e:
        log_warn(f"Erro ao carregar cookies: {e}")
        return False

def download_file_task(task: dict[str, str], index: DownloadIndex = None) -> str:
    """Função individual de download executada em thread com retry e resume.

    Args:
        task: Dicionário com url, path, filename, referer.
        index: DownloadIndex para checkpoint (opcional).

    Returns:
        Mensagem de status do download.
    """
    url = task['url']
    path = task['path']
    filename = task['filename']
    referer = task.get('referer')

    # Verifica checkpoint primeiro
    if index and index.is_completed(path):
        return f"{Fore.YELLOW}Já indexado (pulado): {filename}"

    # Verifica se arquivo final já existe
    if os.path.exists(path):
        if index:
            index.mark_completed(path)
        return f"{Fore.YELLOW}Já existe (pulado): {filename}"

    temp_path = path + ".part"

    def attempt_download():
        """Tenta fazer o download uma vez. Retorna (success, message)."""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*'
        }
        if referer:
            headers['Referer'] = referer

        # Verifica se há download parcial para retomar
        existing_size = 0
        if os.path.exists(temp_path):
            existing_size = os.path.getsize(temp_path)
            headers['Range'] = f'bytes={existing_size}-'

        try:
            response = SESSION.get(url, stream=True, timeout=120, headers=headers)

            # Status 416 = Range not satisfiable (arquivo já completo)
            if response.status_code == 416:
                if os.path.exists(temp_path):
                    os.rename(temp_path, path)
                if index:
                    index.mark_completed(path)
                return (True, f"{Fore.GREEN}Resumido (completo): {filename}")

            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))

            # Se server retornou 206 Partial Content, abre em modo append
            mode = 'ab' if response.status_code == 206 else 'wb'
            if mode == 'wb' and os.path.exists(temp_path):
                os.remove(temp_path)  # Remove parcial anterior se não for continuar

            # Cria o diretório pai se não existir
            os.makedirs(os.path.dirname(path), exist_ok=True)

            with open(temp_path, mode) as f:
                # Barra de progresso individual
                initial = existing_size if mode == 'ab' else 0
                with tqdm(total=total_size + initial, initial=initial, unit='B', unit_scale=True,
                         desc=filename[:20], leave=False, colour='green') as pbar:
                    for chunk in response.iter_content(chunk_size=131072):
                        if chunk:
                            f.write(chunk)
                            pbar.update(len(chunk))

            # Download completo, renomeia .part para nome final
            os.rename(temp_path, path)
            if index:
                index.mark_completed(path)
            return (True, f"{Fore.GREEN}Baixado: {filename}")

        except requests.exceptions.RequestException as e:
            # Erros de rede são recuperáveis, mantém .part para retry
            return (False, f"Erro de rede: {e}")
        except Exception:
            # Outros erros, remove arquivo parcial
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
            raise

    # Executa com retry
    try:
        result = retry_with_backoff(attempt_download, max_retries=4, initial_delay=2.0)
        if result:
            return result
        else:
            return f"{Fore.RED}Falha após 4 tentativas: {filename}"
    except Exception as e:
        # Limpa arquivo parcial em caso de erro fatal
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass
        return f"{Fore.RED}Falha ao baixar {filename}: {e}"

def process_download_queue(queue: list[dict[str, str]], base_dir: str) -> None:
    """Gerencia a fila de downloads usando ThreadPoolExecutor com checkpoint.

    Args:
        queue: Lista de tarefas de download.
        base_dir: Diretório base para salvar o index.
    """
    if not queue:
        return

    # Inicializa o sistema de checkpoint
    index = DownloadIndex(base_dir)

    # Filtra arquivos já completos
    pending = [t for t in queue if not index.is_completed(t['path']) and not os.path.exists(t['path'])]

    if not pending:
        log_info("Todos os arquivos já foram baixados.")
        return

    log_info(f"Iniciando download de {len(pending)} arquivos em paralelo (com retry e resume)...")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_task = {executor.submit(download_file_task, task, index): task for task in pending}

        # Barra de progresso geral (quantidade de arquivos)
        pbar_config = {
            "desc": "  📦 Baixando",
            "unit": " arq",
            "colour": "cyan",
            "bar_format": "{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]"
        }
        for future in tqdm(as_completed(future_to_task), total=len(pending), **pbar_config):
            future.result()
            # Opcional: descomentar para ver resultado de cada arquivo
            # tqdm.write(result_msg)

# --- Selenium e Scraping ---

def get_driver(headless: bool = False) -> WebDriver:
    """Configura o driver Chrome/Edge com otimizações de performance."""
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # Bloqueia carregamento de imagens e outros assets para ganhar velocidade
    prefs = {
        "profile.managed_default_content_settings.images": 2,
        "profile.default_content_settings.banners": 2,
        "profile.default_content_settings.notifications": 2
    }
    options.add_experimental_option("prefs", prefs)

    try:
        log_info(f"Iniciando Google Chrome{' (Headless)' if headless else ''}...")
        return webdriver.Chrome(options=options)
    except Exception as e:
        log_warn(f"Chrome não encontrado ou erro: {e}. Tentando Microsoft Edge...")
        try:
            edge_options = webdriver.EdgeOptions()
            if headless:
                edge_options.add_argument("--headless")
            edge_options.add_argument("--start-maximized")
            return webdriver.Edge(options=edge_options)
        except Exception as ex:
            log_error(f"Nenhum navegador suportado encontrado: {ex}")
            sys.exit(1)

def handle_popups(driver: WebDriver) -> None:
    try:
        getsitecontrol_widget = WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.ID, "getsitecontrol-44266"))
        )
        driver.execute_script("arguments[0].style.display = 'none';", getsitecontrol_widget)
    except Exception:
        pass

def scrape_lesson_data(
    driver: WebDriver,
    lesson_info: dict[str, str],
    course_title: str,
    base_dir: str,
) -> list[dict[str, str]]:
    """Navega na aula e coleta todos os links (PDFs e Vídeos).

    Returns:
        Lista de tarefas para download.
    """
    download_queue = []

    lesson_title = lesson_info['title']
    lesson_url = lesson_info['url']

    # Prepara caminhos
    sanitized_course = sanitize_filename(course_title)
    sanitized_lesson = sanitize_filename(lesson_title)
    lesson_path = os.path.join(base_dir, sanitized_course, sanitized_lesson)
    os.makedirs(lesson_path, exist_ok=True)

    # Salva txt de assuntos
    if lesson_info['subtitle']:
        with open(os.path.join(lesson_path, "Assuntos.txt"), 'w', encoding='utf-8') as f:
            f.write(lesson_info['subtitle'])

    driver.get(lesson_url)
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.Lesson-contentTop, div.LessonVideos"))
        )
    except Exception:
        log_error(f"Erro ao carregar aula: {lesson_title}")
        return []

    handle_popups(driver)
    current_referer = driver.current_url

    # 1. Coletar PDFs da Aula
    try:
        pdf_links = driver.find_elements(By.XPATH, "//a[contains(@class, 'LessonButton') and .//i[contains(@class, 'icon-file')]]")
        for link in pdf_links:
            url = link.get_attribute('href')
            if not url or "api.estrategiaconcursos" not in url:
                continue

            try:
                text = link.find_element(By.CSS_SELECTOR, "span.LessonButton-text > span").text.strip()
            except Exception:
                text = "Material"

            fname = f"{sanitized_lesson}_{sanitize_filename(text)}.pdf"
            download_queue.append({
                "url": url,
                "path": os.path.join(lesson_path, fname),
                "filename": fname,
                "referer": current_referer
            })
    except Exception as e:
        log_warn(f"Erro ao ler PDFs: {e}")

    # 2. Coletar Vídeos
    try:
        # Pega a lista de vídeos para iterar
        try:
            playlist = WebDriverWait(driver, 5).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.ListVideos-items-video a.VideoItem"))
            )
        except TimeoutException:
            playlist = []

        # Extrai infos básicas para não perder referência ao navegar
        videos_info = []
        for item in playlist:
            videos_info.append({
                "url": item.get_attribute('href'),
                "title": item.find_element(By.CSS_SELECTOR, "span.VideoItem-info-title").text
            })

        if videos_info:
            log_info(f"Mapeando {len(videos_info)} vídeos (isso pode levar um momento)...")

        for idx, vid in enumerate(videos_info):
            # Navega para cada vídeo para pegar o link direto e materiais
            driver.get(vid['url'])
            # Tenta esperar por um elemento chave do vídeo em vez de sleep fixo
            try:
                WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.LessonVideos")))
            except Exception:
                pass

            sanitized_vid_title = sanitize_filename(vid['title'])

            # a) Materiais do Vídeo
            extras = [
                ("Baixar Resumo", f"_Resumo_{idx}.pdf"),
                ("Baixar Slides", f"_Slides_{idx}.pdf"),
                ("Baixar Mapa Mental", f"_Mapa_{idx}.pdf")
            ]
            for btn_text, suffix in extras:
                try:
                    elem = driver.find_element(By.XPATH, f"//a[contains(@class, 'LessonButton') and .//span[contains(text(), '{btn_text}')]]")
                    url = elem.get_attribute('href')
                    fname = f"{sanitized_lesson}_{sanitized_vid_title}{suffix}"
                    download_queue.append({
                        "url": url,
                        "path": os.path.join(lesson_path, fname),
                        "filename": fname,
                        "referer": driver.current_url
                    })
                except Exception:
                    pass

            # b) O Arquivo de Vídeo
            try:
                # Clica em 'Opções de download' se necessário
                try:
                    dl_header = driver.find_element(By.XPATH, "//div[contains(@class, 'Collapse-header')]//strong[text()='Opções de download']")
                    driver.execute_script("arguments[0].click();", dl_header)
                    time.sleep(0.5)
                except Exception:
                    pass

                found = False
                for quality in ["720p", "480p", "360p"]:
                    try:
                        link_elem = driver.find_element(By.XPATH, f"//div[contains(@class, 'Collapse-body')]//a[contains(text(), '{quality}')]")
                        video_url = link_elem.get_attribute('href')
                        fname = f"{sanitized_vid_title}_{quality}.mp4"

                        download_queue.append({
                            "url": video_url,
                            "path": os.path.join(lesson_path, fname),
                            "filename": fname,
                            "referer": driver.current_url
                        })
                        found = True
                        break # Pega apenas a melhor qualidade
                    except Exception:
                        continue

                if not found:
                    tqdm.write(f"{Fore.YELLOW}Vídeo sem link detectado: {vid['title']}")

            except Exception as e:
                tqdm.write(f"{Fore.RED}Erro ao extrair vídeo: {e}")

    except Exception as e:
        log_warn(f"Erro ao processar playlist: {e}")

    return download_queue

def get_courses_list(driver: WebDriver) -> list[dict[str, str]]:
    """Obtém lista de cursos disponíveis."""
    log_info("Carregando lista de cursos...")
    driver.get(MY_COURSES_URL)
    try:
        # Espera até que pelo menos um card de curso esteja presente
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, "section[id^='card']")))
        elements = driver.find_elements(By.CSS_SELECTOR, "section[id^='card']")
        courses = []
        for el in elements:
            try:
                title = el.find_element(By.CSS_SELECTOR, "h1.sc-ksYbfQ").text
                url = el.find_element(By.CSS_SELECTOR, "a.sc-cHGsZl").get_attribute("href")
                courses.append({"title": title, "url": url})
            except Exception:
                pass
        return courses
    except Exception:
        return []

def get_lessons_list(driver: WebDriver, course_url: str) -> list[dict[str, str]]:
    """Obtém lista de aulas de um curso."""
    driver.get(course_url)
    try:
        # Espera até que pelo menos um item da aula apareça
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.LessonList-item")))
        elements = driver.find_elements(By.CSS_SELECTOR, "div.LessonList-item")
        lessons = []
        for el in elements:
            try:
                if "isDisabled" in el.get_attribute("class"):
                    continue
                title = el.find_element(By.CSS_SELECTOR, "h2.SectionTitle").text
                url = el.find_element(By.CSS_SELECTOR, "a.Collapse-header").get_attribute("href")
                subtitle = ""
                try:
                    subtitle = el.find_element(By.CSS_SELECTOR, "p.sc-gZMcBi").text
                except Exception:
                    pass
                lessons.append({"title": title, "url": url, "subtitle": subtitle})
            except Exception:
                pass
        return lessons
    except Exception:
        return []

# --- Main ---

def main() -> None:
    """Função principal do downloader."""
    global MAX_WORKERS
    # Caminho específico solicitado
    default_path = "/Users/gabrielramos/Library/Mobile Documents/com~apple~CloudDocs/Estudo/Estrategia/Meus Cursos - Estratégia Concursos"

    parser = argparse.ArgumentParser(
        description="Downloader Estratégia Concursos (Otimizado com retry e checkpoint)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Recursos:
  • Retry automático com backoff exponencial (4 tentativas)
  • Resume de downloads interrompidos (.part files)
  • Checkpoint/index para não re-baixar arquivos completos
  • Modo async (padrão) com melhor performance
  • Login persistente via cookies
        """
    )
    parser.add_argument('-d', '--dir', type=str, default=default_path, help="Diretório de download")
    parser.add_argument('-w', '--wait-time', type=int, default=60, help="Tempo para login manual (segundos)")
    parser.add_argument('--headless', action='store_true', help="Executa o navegador em modo oculto")
    parser.add_argument('--workers', type=int, default=MAX_WORKERS, help="Número de downloads paralelos (padrão: 4)")
    parser.add_argument('--sync', action='store_true', help="Usa modo síncrono em vez de async (mais lento)")
    args = parser.parse_args()

    # Async é o padrão agora
    args.use_async = not args.sync

    MAX_WORKERS = args.workers

    # Expande o '~' se o usuário passar um caminho relativo, mas usa o absoluto se for o default
    save_dir = os.path.expanduser(args.dir)

    # Banner e configurações
    mode_label = "Async" if args.use_async else "Síncrono"

    if args.headless:
        print(ui.simple_banner())
    else:
        print(ui.banner())

    print("\n" + ui.config_panel(mode_label, MAX_WORKERS, save_dir))
    print()

    driver = get_driver(headless=args.headless)

    try:
        # Tenta carregar sessão
        driver.get(BASE_URL)
        session_loaded = load_cookies(driver, COOKIES_FILE)

        if session_loaded:
            driver.get(MY_COURSES_URL)
            # Verifica se realmente está logado
            try:
                WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, "section[id^='card']")))
                print(ui.session_restored())
            except Exception:
                log_warn("Sessão expirada. Necessário login manual.")
                session_loaded = False

        if not session_loaded:
            print(ui.login_prompt(args.wait_time))
            driver.get("https://perfil.estrategia.com/login")
            for _ in tqdm(range(args.wait_time), desc="⏳ Aguardando Login", bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt}s", colour='yellow'):
                time.sleep(1)
            # Salva cookies após login
            save_cookies(driver, COOKIES_FILE)
            print(f"\n{Fore.GREEN}✓ Cookies salvos com sucesso!{Style.RESET_ALL}\n")

        courses = get_courses_list(driver)
        if not courses:
            log_error("Nenhum curso encontrado. Verifique se logou corretamente.")
            return

        for i, course in enumerate(courses, 1):
            print(ui.course_header(i, len(courses), course['title']))

            lessons = get_lessons_list(driver, course['url'])
            for j, lesson in enumerate(lessons, 1):
                print(ui.lesson_header(j, len(lessons), lesson['title']))

                # 1. Coleta Links (Serial)
                queue = scrape_lesson_data(driver, lesson, course['title'], save_dir)

                # 2. Baixa (Paralelo ou Async)
                if queue:
                    if args.use_async:
                        run_async_downloads(queue, save_dir, MAX_WORKERS)
                    else:
                        process_download_queue(queue, save_dir)
                else:
                    log_warn("  Nenhum arquivo encontrado nesta aula.")

    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}⚠  Interrompido pelo usuário.{Style.RESET_ALL}")
        print(f"{Fore.CYAN}💾 Progresso salvo! Execute novamente para continuar.{Style.RESET_ALL}\n")
    except Exception as e:
        log_error(f"Erro fatal: {e}")
    finally:
        driver.quit()
        print(f"\n{Fore.CYAN}🌐 Navegador fechado.{Style.RESET_ALL}")
        print(ui.goodbye())

if __name__ == "__main__":
    main()
