"""
Sistema de rastreamento de downloads com SQLite.

Substitui o sistema JSON simples com um banco de dados SQLite que oferece:
- Performance 10-100x melhor com muitos arquivos
- Metadados ricos (data, tamanho, hash, curso, aula)
- Queries SQL complexas
- Verificação de integridade com SHA-256
- Estatísticas detalhadas
- Migration automática do JSON antigo
- Thread-safe com locks
"""

import sqlite3
import hashlib
import json
import os
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Tuple, Any

# Importa orjson se disponível (10x mais rápido que json padrão)
try:
    from orjson import loads as json_loads, dumps as json_dumps
    JSON_WRITE_MODE = 'wb'

    def write_json(data: Any) -> bytes:
        """Wrapper para orjson.dumps com formatação."""
        return json_dumps(data, option=1)  # OPT_INDENT_2
except ImportError:
    json_loads = json.loads
    json_dumps = json.dumps
    JSON_WRITE_MODE = 'w'

    def write_json(data: Any) -> str:
        """Wrapper para json.dumps com formatação."""
        return json.dumps(data, indent=2)


# Constantes
DB_FILE = "download_index.db"
JSON_FILE = "download_index.json"
CHUNK_SIZE = 65536  # 64KB para leitura de hash


class DownloadDatabase:
    """
    Sistema de rastreamento de downloads com SQLite + JSON backup.

    Features:
    - SQLite para performance e queries complexas
    - Thread-safe com locks
    - Migration automática de JSON antigo
    - Verificação de integridade com SHA-256
    - Estatísticas detalhadas
    - Export/Import JSON para backup
    """

    def __init__(self, base_dir: str, use_sqlite: bool = True):
        """
        Inicializa o sistema de tracking.

        Args:
            base_dir: Diretório base onde salvar o database.
            use_sqlite: Se True usa SQLite, se False usa JSON (fallback).
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.use_sqlite = use_sqlite
        self._lock = threading.Lock()

        if use_sqlite:
            self.db_path = self.base_dir / DB_FILE
            self._init_sqlite()
            self._migrate_from_json_if_needed()
        else:
            self.json_path = self.base_dir / JSON_FILE
            self.completed: set[str] = set()
            self._load_json()

    def _init_sqlite(self) -> None:
        """Inicializa o banco SQLite com schema completo."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()

        # Tabela principal de downloads
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS downloads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT UNIQUE NOT NULL,
                file_name TEXT NOT NULL,
                url TEXT NOT NULL,
                course_name TEXT NOT NULL,
                lesson_name TEXT NOT NULL,
                file_type TEXT NOT NULL,
                size_bytes INTEGER,
                sha256 TEXT,
                downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                verified BOOLEAN DEFAULT FALSE,
                last_verified_at TIMESTAMP,
                status TEXT DEFAULT 'completed',
                error_message TEXT,
                retry_count INTEGER DEFAULT 0
            )
        """)

        # Índices para queries rápidas
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_course ON downloads(course_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_lesson ON downloads(lesson_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_type ON downloads(file_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_status ON downloads(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_path ON downloads(file_path)")

        # Tabela de estatísticas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS statistics (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                total_files INTEGER DEFAULT 0,
                total_bytes INTEGER DEFAULT 0,
                total_videos INTEGER DEFAULT 0,
                total_pdfs INTEGER DEFAULT 0,
                total_materials INTEGER DEFAULT 0,
                last_download_at TIMESTAMP,
                last_sync_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Inicializa estatísticas se não existirem
        cursor.execute("INSERT OR IGNORE INTO statistics (id) VALUES (1)")

        conn.commit()
        conn.close()

    def _migrate_from_json_if_needed(self) -> None:
        """Migra dados do JSON antigo para SQLite automaticamente."""
        json_path = self.base_dir / JSON_FILE

        if not json_path.exists():
            return

        # Verifica se já temos dados no SQLite
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM downloads")
        count = cursor.fetchone()[0]
        conn.close()

        if count > 0:
            # Já temos dados no SQLite, não migra
            return

        print("🔄 Detectado download_index.json antigo. Migrando para SQLite...")

        try:
            with open(json_path, 'rb' if JSON_WRITE_MODE == 'wb' else 'r') as f:
                data = json_loads(f.read() if JSON_WRITE_MODE == 'wb' else f.read())

            completed_files = data.get('completed', [])

            if not completed_files:
                return

            # Migra cada arquivo
            migrated = 0
            for file_path in completed_files:
                # Extrai informações do caminho
                path_obj = Path(file_path)
                file_name = path_obj.name

                # Tenta extrair curso e aula do caminho
                parts = path_obj.parts
                course_name = "Migrado"
                lesson_name = "Migrado"

                if len(parts) >= 3:
                    lesson_name = parts[-2]  # Pasta da aula
                if len(parts) >= 4:
                    course_name = parts[-3]  # Pasta do curso

                # Detecta tipo de arquivo
                file_type = "unknown"
                if file_name.endswith('.mp4') or file_name.endswith('.mkv'):
                    file_type = "video"
                elif file_name.endswith('.pdf'):
                    file_type = "pdf"
                elif any(x in file_name for x in ['Resumo', 'Slides', 'Mapa']):
                    file_type = "material"

                # Tenta obter tamanho do arquivo
                size_bytes = None
                if os.path.exists(file_path):
                    try:
                        size_bytes = os.path.getsize(file_path)
                    except OSError:
                        pass

                # Marca como baixado
                self.mark_downloaded(
                    file_path=file_path,
                    url="migrated://unknown",
                    course_name=course_name,
                    lesson_name=lesson_name,
                    file_type=file_type,
                    size_bytes=size_bytes
                )
                migrated += 1

            print(f"✅ Migração completa: {migrated} arquivos migrados para SQLite")

            # Backup do JSON antigo
            backup_path = self.base_dir / f"download_index.json.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            json_path.rename(backup_path)
            print(f"📦 JSON antigo salvo em: {backup_path.name}")

        except Exception as e:
            print(f"⚠️  Erro na migração: {e}")
            print("   O sistema continuará usando SQLite vazio.")

    def _load_json(self) -> None:
        """Carrega index do JSON (modo fallback)."""
        if self.json_path.exists():
            try:
                with open(self.json_path, 'rb' if JSON_WRITE_MODE == 'wb' else 'r') as f:
                    data = json_loads(f.read() if JSON_WRITE_MODE == 'wb' else f.read())
                    self.completed = set(data.get('completed', []))
            except (ValueError, OSError):
                self.completed = set()

    def _save_json(self) -> None:
        """Salva index para JSON (modo fallback)."""
        with self._lock:
            completed_snapshot = list(self.completed)

        with open(self.json_path, JSON_WRITE_MODE) as f:
            f.write(write_json({'completed': completed_snapshot}))

    def is_downloaded(self, file_path: str) -> bool:
        """
        Verifica se um arquivo já foi baixado.

        Args:
            file_path: Caminho completo do arquivo.

        Returns:
            True se o arquivo já foi baixado.
        """
        if not self.use_sqlite:
            with self._lock:
                return file_path in self.completed

        with self._lock:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM downloads WHERE file_path = ? AND status = 'completed'",
                (file_path,)
            )
            count = cursor.fetchone()[0]
            conn.close()
            return count > 0

    def mark_downloaded(
        self,
        file_path: str,
        url: str,
        course_name: str,
        lesson_name: str,
        file_type: str,
        size_bytes: Optional[int] = None,
        calculate_hash: bool = False
    ) -> None:
        """
        Marca um arquivo como baixado.

        Args:
            file_path: Caminho completo do arquivo.
            url: URL de download original.
            course_name: Nome do curso.
            lesson_name: Nome da aula.
            file_type: Tipo do arquivo (video, pdf, material).
            size_bytes: Tamanho do arquivo em bytes (opcional).
            calculate_hash: Se True, calcula SHA-256 do arquivo.
        """
        if not self.use_sqlite:
            with self._lock:
                self.completed.add(file_path)
            self._save_json()
            return

        # Calcula hash se solicitado
        sha256 = None
        if calculate_hash and os.path.exists(file_path):
            sha256 = self._calculate_sha256(file_path)

        # Obtém tamanho se não fornecido
        if size_bytes is None and os.path.exists(file_path):
            try:
                size_bytes = os.path.getsize(file_path)
            except OSError:
                pass

        file_name = Path(file_path).name

        with self._lock:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = conn.cursor()

            # Check if file already exists to avoid duplicating statistics
            cursor.execute("SELECT COUNT(*) FROM downloads WHERE file_path = ?", (file_path,))
            already_exists = cursor.fetchone()[0] > 0

            # Insert or replace
            cursor.execute("""
                INSERT OR REPLACE INTO downloads
                (file_path, file_name, url, course_name, lesson_name, file_type,
                 size_bytes, sha256, downloaded_at, verified, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?, 'completed')
            """, (
                file_path, file_name, url, course_name, lesson_name, file_type,
                size_bytes, sha256, sha256 is not None
            ))

            # Only update statistics if this is a new file
            if not already_exists:
                self._update_statistics(cursor, file_type, size_bytes)

            conn.commit()
            conn.close()

    def mark_downloaded_batch(self, downloads: List[Dict[str, Any]]) -> None:
        """
        Marca múltiplos arquivos como baixados em uma transação (mais eficiente).

        Args:
            downloads: Lista de dicts com keys: file_path, url, course_name,
                      lesson_name, file_type, size_bytes (opcional).
        """
        if not self.use_sqlite:
            with self._lock:
                self.completed.update([d['file_path'] for d in downloads])
            self._save_json()
            return

        with self._lock:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = conn.cursor()

            for d in downloads:
                file_path = d['file_path']
                file_name = Path(file_path).name
                size_bytes = d.get('size_bytes')

                if size_bytes is None and os.path.exists(file_path):
                    try:
                        size_bytes = os.path.getsize(file_path)
                    except OSError:
                        pass

                # Check if file already exists to avoid duplicating statistics
                cursor.execute("SELECT COUNT(*) FROM downloads WHERE file_path = ?", (file_path,))
                already_exists = cursor.fetchone()[0] > 0

                cursor.execute("""
                    INSERT OR REPLACE INTO downloads
                    (file_path, file_name, url, course_name, lesson_name, file_type,
                     size_bytes, downloaded_at, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, 'completed')
                """, (
                    file_path, file_name, d['url'], d['course_name'],
                    d['lesson_name'], d['file_type'], size_bytes
                ))

                # Only update statistics if this is a new file
                if not already_exists:
                    self._update_statistics(cursor, d['file_type'], size_bytes)

            conn.commit()
            conn.close()

    def _update_statistics(self, cursor: sqlite3.Cursor, file_type: str, size_bytes: Optional[int]) -> None:
        """Atualiza estatísticas após um download."""
        cursor.execute("UPDATE statistics SET total_files = total_files + 1 WHERE id = 1")

        if size_bytes:
            cursor.execute("UPDATE statistics SET total_bytes = total_bytes + ? WHERE id = 1", (size_bytes,))

        if file_type == 'video':
            cursor.execute("UPDATE statistics SET total_videos = total_videos + 1 WHERE id = 1")
        elif file_type == 'pdf':
            cursor.execute("UPDATE statistics SET total_pdfs = total_pdfs + 1 WHERE id = 1")
        elif file_type == 'material':
            cursor.execute("UPDATE statistics SET total_materials = total_materials + 1 WHERE id = 1")

        cursor.execute("UPDATE statistics SET last_download_at = CURRENT_TIMESTAMP WHERE id = 1")

    def _calculate_sha256(self, file_path: str) -> str:
        """
        Calcula SHA-256 hash de um arquivo.

        Args:
            file_path: Caminho do arquivo.

        Returns:
            Hash SHA-256 em hexadecimal.
        """
        sha256_hash = hashlib.sha256()

        try:
            with open(file_path, 'rb') as f:
                while chunk := f.read(CHUNK_SIZE):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except (OSError, IOError):
            return ""

    def verify_file_integrity(self, file_path: str, recalculate: bool = False) -> Tuple[bool, str]:
        """
        Verifica integridade de um arquivo baixado.

        Args:
            file_path: Caminho do arquivo.
            recalculate: Se True, recalcula o hash mesmo se já existir.

        Returns:
            Tupla (is_valid, message).
        """
        if not self.use_sqlite:
            return (False, "Verificação de integridade requer SQLite")

        # Verifica se arquivo existe
        if not os.path.exists(file_path):
            return (False, "Arquivo não existe no disco")

        with self._lock:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = conn.cursor()

            cursor.execute(
                "SELECT sha256, size_bytes FROM downloads WHERE file_path = ?",
                (file_path,)
            )
            result = cursor.fetchone()

            if not result:
                conn.close()
                return (False, "Arquivo não está no banco de dados")

            stored_hash, stored_size = result

            # Verifica tamanho
            try:
                actual_size = os.path.getsize(file_path)
                if stored_size and actual_size != stored_size:
                    conn.close()
                    return (False, f"Tamanho diferente: esperado {stored_size}, atual {actual_size}")
            except OSError:
                conn.close()
                return (False, "Erro ao ler tamanho do arquivo")

            # Verifica hash
            if not stored_hash or recalculate:
                actual_hash = self._calculate_sha256(file_path)

                # Verifica se hash foi calculado com sucesso
                if not actual_hash:
                    conn.close()
                    return (False, "Erro ao calcular hash do arquivo")

                if not stored_hash:
                    # Primeira verificação, salva o hash
                    cursor.execute(
                        "UPDATE downloads SET sha256 = ?, verified = TRUE, last_verified_at = CURRENT_TIMESTAMP WHERE file_path = ?",
                        (actual_hash, file_path)
                    )
                    conn.commit()
                    conn.close()
                    return (True, "Hash calculado e salvo")
                else:
                    # Verifica se hash bate
                    if actual_hash == stored_hash:
                        cursor.execute(
                            "UPDATE downloads SET verified = TRUE, last_verified_at = CURRENT_TIMESTAMP WHERE file_path = ?",
                            (file_path,)
                        )
                        conn.commit()
                        conn.close()
                        return (True, "Arquivo íntegro")
                    else:
                        conn.close()
                        return (False, f"Hash diferente: esperado {stored_hash[:16]}..., atual {actual_hash[:16]}...")
            else:
                # Já tem hash, verifica
                actual_hash = self._calculate_sha256(file_path)

                # Verifica se hash foi calculado com sucesso
                if not actual_hash:
                    conn.close()
                    return (False, "Erro ao calcular hash do arquivo")

                if actual_hash == stored_hash:
                    cursor.execute(
                        "UPDATE downloads SET verified = TRUE, last_verified_at = CURRENT_TIMESTAMP WHERE file_path = ?",
                        (file_path,)
                    )
                    conn.commit()
                    conn.close()
                    return (True, "Arquivo íntegro")
                else:
                    conn.close()
                    return (False, f"Hash diferente: esperado {stored_hash[:16]}..., atual {actual_hash[:16]}...")

    def get_statistics(self) -> Dict[str, Any]:
        """
        Retorna estatísticas de downloads.

        Returns:
            Dict com estatísticas.
        """
        if not self.use_sqlite:
            return {
                'total_files': len(self.completed),
                'mode': 'json'
            }

        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM statistics WHERE id = 1")
        row = cursor.fetchone()

        if not row:
            conn.close()
            return {}

        stats = {
            'total_files': row[1],
            'total_bytes': row[2],
            'total_videos': row[3],
            'total_pdfs': row[4],
            'total_materials': row[5],
            'last_download_at': row[6],
            'last_sync_at': row[7],
            'mode': 'sqlite'
        }

        # Adiciona estatísticas por curso
        cursor.execute("""
            SELECT course_name, COUNT(*), SUM(size_bytes)
            FROM downloads
            GROUP BY course_name
            ORDER BY COUNT(*) DESC
        """)
        stats['by_course'] = [
            {'course': row[0], 'files': row[1], 'bytes': row[2] or 0}
            for row in cursor.fetchall()
        ]

        conn.close()
        return stats

    def get_downloads_by_course(self, course_name: str) -> List[Dict[str, Any]]:
        """
        Retorna todos os downloads de um curso.

        Args:
            course_name: Nome do curso.

        Returns:
            Lista de downloads.
        """
        if not self.use_sqlite:
            return []

        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT file_path, file_name, lesson_name, file_type, size_bytes,
                   downloaded_at, verified
            FROM downloads
            WHERE course_name = ?
            ORDER BY lesson_name, file_name
        """, (course_name,))

        downloads = []
        for row in cursor.fetchall():
            downloads.append({
                'file_path': row[0],
                'file_name': row[1],
                'lesson_name': row[2],
                'file_type': row[3],
                'size_bytes': row[4],
                'downloaded_at': row[5],
                'verified': bool(row[6])
            })

        conn.close()
        return downloads

    def get_unverified_files(self) -> List[str]:
        """
        Retorna lista de arquivos que ainda não foram verificados.

        Returns:
            Lista de caminhos de arquivos.
        """
        if not self.use_sqlite:
            return []

        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT file_path
            FROM downloads
            WHERE verified = FALSE OR sha256 IS NULL
        """)

        files = [row[0] for row in cursor.fetchall()]
        conn.close()
        return files

    def export_to_json(self, output_path: Optional[str] = None) -> str:
        """
        Exporta dados do SQLite para JSON (backup/debug).

        Args:
            output_path: Caminho do arquivo JSON (opcional).

        Returns:
            Caminho do arquivo exportado.
        """
        if not self.use_sqlite:
            return str(self.json_path)

        if output_path is None:
            output_path = str(self.base_dir / f"download_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")

        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM downloads")
        columns = [desc[0] for desc in cursor.description]
        downloads = [dict(zip(columns, row)) for row in cursor.fetchall()]

        cursor.execute("SELECT * FROM statistics WHERE id = 1")
        stats_row = cursor.fetchone()
        stats_columns = [desc[0] for desc in cursor.description]
        statistics = dict(zip(stats_columns, stats_row)) if stats_row else {}

        conn.close()

        export_data = {
            'version': '2.0',
            'exported_at': datetime.now().isoformat(),
            'downloads': downloads,
            'statistics': statistics
        }

        with open(output_path, JSON_WRITE_MODE) as f:
            f.write(write_json(export_data))

        return output_path

    def __enter__(self):
        """Context manager support."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup."""
        if self.use_sqlite:
            # Sync final statistics
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute("UPDATE statistics SET last_sync_at = CURRENT_TIMESTAMP WHERE id = 1")
            conn.commit()
            conn.close()
