"""Testes para o sistema de tracking SQLite (DownloadDatabase)."""

import os
import tempfile
import shutil
from pathlib import Path

try:
    from download_database import DownloadDatabase
    DOWNLOAD_DATABASE_AVAILABLE = True
except ImportError:
    DOWNLOAD_DATABASE_AVAILABLE = False
    print("⚠️  download_database.py não encontrado, pulando testes")


def test_download_database_basic():
    """Testa operações básicas do DownloadDatabase."""
    if not DOWNLOAD_DATABASE_AVAILABLE:
        return False

    print("\n🧪 Testando DownloadDatabase (SQLite)...")

    tmpdir = tempfile.mkdtemp()
    try:
        # 1. Criação e inicialização
        db = DownloadDatabase(tmpdir, use_sqlite=True)

        # Verifica se DB foi criado
        db_path = Path(tmpdir) / "download_index.db"
        if not db_path.exists():
            print("  ❌ Arquivo SQLite não foi criado")
            return False
        print("  ✅ Banco SQLite criado")

        # 2. Marca arquivo como baixado
        test_file = os.path.join(tmpdir, "test_video.mp4")
        Path(test_file).touch()  # Cria arquivo vazio

        db.mark_downloaded(
            file_path=test_file,
            url="https://example.com/video.mp4",
            course_name="Curso Teste",
            lesson_name="Aula 01",
            file_type="video",
            size_bytes=1024
        )
        print("  ✅ Arquivo marcado como baixado")

        # 3. Verifica se está marcado
        if not db.is_downloaded(test_file):
            print("  ❌ Arquivo não foi marcado corretamente")
            return False
        print("  ✅ Verificação de download funcionando")

        # 4. Testa estatísticas
        stats = db.get_statistics()
        if stats.get('total_files') != 1:
            print(f"  ❌ Estatísticas incorretas: {stats}")
            return False
        if stats.get('total_videos') != 1:
            print(f"  ❌ Contagem de vídeos incorreta: {stats}")
            return False
        print("  ✅ Estatísticas corretas")

        # 5. Testa query por curso
        downloads = db.get_downloads_by_course("Curso Teste")
        if len(downloads) != 1:
            print(f"  ❌ Query por curso falhou: {len(downloads)} arquivos")
            return False
        if downloads[0]['file_type'] != 'video':
            print(f"  ❌ Tipo de arquivo incorreto: {downloads[0]['file_type']}")
            return False
        print("  ✅ Query por curso funcionando")

        # 6. Testa batch insert
        batch_files = [
            {
                'file_path': os.path.join(tmpdir, 'pdf1.pdf'),
                'url': 'https://example.com/pdf1.pdf',
                'course_name': 'Curso Teste',
                'lesson_name': 'Aula 02',
                'file_type': 'pdf'
            },
            {
                'file_path': os.path.join(tmpdir, 'pdf2.pdf'),
                'url': 'https://example.com/pdf2.pdf',
                'course_name': 'Curso Teste',
                'lesson_name': 'Aula 02',
                'file_type': 'pdf'
            }
        ]

        # Cria arquivos
        for f in batch_files:
            Path(f['file_path']).touch()

        db.mark_downloaded_batch(batch_files)

        stats = db.get_statistics()
        if stats.get('total_files') != 3:
            print(f"  ❌ Batch insert falhou: {stats.get('total_files')} arquivos")
            return False
        if stats.get('total_pdfs') != 2:
            print(f"  ❌ Contagem de PDFs incorreta: {stats.get('total_pdfs')}")
            return False
        print("  ✅ Batch insert funcionando")

        # 7. Testa export para JSON
        export_path = db.export_to_json()
        if not os.path.exists(export_path):
            print(f"  ❌ Export JSON falhou: {export_path}")
            return False
        print(f"  ✅ Export JSON criado: {Path(export_path).name}")

        print("\n✅ DownloadDatabase passou em todos os testes!")
        return True

    except Exception as e:
        print(f"\n❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        shutil.rmtree(tmpdir)


def test_json_to_sqlite_migration():
    """Testa migração automática de JSON para SQLite."""
    if not DOWNLOAD_DATABASE_AVAILABLE:
        return False

    print("\n🧪 Testando migração JSON → SQLite...")

    tmpdir = tempfile.mkdtemp()
    try:
        # 1. Cria um JSON antigo
        import json
        json_path = Path(tmpdir) / "download_index.json"

        test_files = [
            str(Path(tmpdir) / "Curso_Python" / "Aula_01" / "Video_720p.mp4"),
            str(Path(tmpdir) / "Curso_Python" / "Aula_01" / "PDF_Original.pdf"),
        ]

        # Cria arquivos
        for file_path in test_files:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            Path(file_path).touch()

        json_data = {'completed': test_files}

        with open(json_path, 'w') as f:
            json.dump(json_data, f)
        print(f"  ✅ JSON antigo criado com {len(test_files)} arquivos")

        # 2. Inicializa DownloadDatabase (deve migrar automaticamente)
        db = DownloadDatabase(tmpdir, use_sqlite=True)

        # 3. Verifica se arquivos foram migrados
        if not db.is_downloaded(test_files[0]):
            print("  ❌ Arquivo 1 não foi migrado")
            return False
        if not db.is_downloaded(test_files[1]):
            print("  ❌ Arquivo 2 não foi migrado")
            return False
        print("  ✅ Arquivos migrados corretamente")

        # 4. Verifica estatísticas
        stats = db.get_statistics()
        if stats.get('total_files') != 2:
            print(f"  ❌ Total de arquivos incorreto: {stats.get('total_files')}")
            return False
        print(f"  ✅ Estatísticas corretas: {stats.get('total_files')} arquivos")

        # 5. Verifica se JSON foi backupeado
        backup_files = list(Path(tmpdir).glob("download_index.json.backup.*"))
        if not backup_files:
            print("  ❌ JSON antigo não foi backupeado")
            return False
        print(f"  ✅ JSON backupeado: {backup_files[0].name}")

        print("\n✅ Migração JSON → SQLite funcionou perfeitamente!")
        return True

    except Exception as e:
        print(f"\n❌ Erro na migração: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        shutil.rmtree(tmpdir)


def test_hash_verification():
    """Testa verificação de integridade com SHA-256."""
    if not DOWNLOAD_DATABASE_AVAILABLE:
        return False

    print("\n🧪 Testando verificação de integridade (SHA-256)...")

    tmpdir = tempfile.mkdtemp()
    try:
        db = DownloadDatabase(tmpdir, use_sqlite=True)

        # 1. Cria arquivo com conteúdo
        test_file = Path(tmpdir) / "test.txt"
        test_content = b"Hello, World! This is a test file."
        test_file.write_bytes(test_content)

        # 2. Marca como baixado SEM hash
        db.mark_downloaded(
            file_path=str(test_file),
            url="https://example.com/test.txt",
            course_name="Test",
            lesson_name="Test",
            file_type="pdf"
        )
        print("  ✅ Arquivo marcado sem hash")

        # 3. Verifica integridade (deve calcular hash)
        is_valid, message = db.verify_file_integrity(str(test_file))
        if not is_valid:
            print(f"  ❌ Verificação falhou: {message}")
            return False
        print(f"  ✅ Hash calculado: {message}")

        # 4. Verifica novamente (deve usar hash armazenado)
        is_valid, message = db.verify_file_integrity(str(test_file))
        if not is_valid:
            print(f"  ❌ Segunda verificação falhou: {message}")
            return False
        print(f"  ✅ Verificação com hash armazenado: {message}")

        # 5. Corrompe o arquivo
        test_file.write_bytes(b"CORRUPTED DATA")

        is_valid, message = db.verify_file_integrity(str(test_file))
        if is_valid:
            print("  ❌ Deveria detectar corrupção!")
            return False
        print(f"  ✅ Corrupção detectada: {message}")

        print("\n✅ Verificação de integridade funcionando!")
        return True

    except Exception as e:
        print(f"\n❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        shutil.rmtree(tmpdir)


def run_all_tests():
    """Executa todos os testes."""
    print("\n" + "="*60)
    print("  TESTES DO SISTEMA DE TRACKING SQLITE")
    print("="*60)

    if not DOWNLOAD_DATABASE_AVAILABLE:
        print("\n❌ download_database.py não encontrado")
        return False

    results = []

    # Teste 1: Operações básicas
    results.append(("DownloadDatabase básico", test_download_database_basic()))

    # Teste 2: Migração JSON → SQLite
    results.append(("Migração JSON → SQLite", test_json_to_sqlite_migration()))

    # Teste 3: Verificação de hash
    results.append(("Verificação SHA-256", test_hash_verification()))

    # Resumo
    print("\n" + "="*60)
    print("  RESUMO DOS TESTES")
    print("="*60)

    passed = 0
    failed = 0

    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"  {status}: {test_name}")
        if result:
            passed += 1
        else:
            failed += 1

    print("\n" + "="*60)
    print(f"  Total: {passed} passaram, {failed} falharam")
    print("="*60 + "\n")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
