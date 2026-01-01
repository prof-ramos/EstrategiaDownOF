"""Test script to verify thread-safety of DownloadIndex."""
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from async_downloader import DownloadIndex


def test_concurrent_mark_completed():
    """Test that multiple threads can mark files as completed without race conditions."""
    print("🧪 Testando thread-safety do DownloadIndex...")

    with tempfile.TemporaryDirectory() as tmpdir:
        index = DownloadIndex(tmpdir)

        # Número de threads e arquivos para testar
        num_threads = 10
        files_per_thread = 100

        def mark_files(thread_id):
            """Marca arquivos como completos em uma thread."""
            for i in range(files_per_thread):
                file_path = f"/tmp/thread_{thread_id}_file_{i}.mp4"
                index.mark_completed(file_path)

        # Executa em paralelo
        start = time.time()
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(mark_files, i) for i in range(num_threads)]
            for future in futures:
                future.result()  # Aguarda completar

        elapsed = time.time() - start

        # Verifica resultados
        expected_count = num_threads * files_per_thread
        actual_count = len(index.completed)

        print(f"  ⏱  Tempo: {elapsed:.2f}s")
        print(f"  📊 Arquivos esperados: {expected_count}")
        print(f"  📊 Arquivos no índice: {actual_count}")

        if actual_count == expected_count:
            print(f"  ✅ PASSOU: Todos os {expected_count} arquivos foram marcados corretamente")
        else:
            print(f"  ❌ FALHOU: Esperado {expected_count}, obtido {actual_count}")
            return False

        # Testa persistência
        index2 = DownloadIndex(tmpdir)
        if len(index2.completed) == expected_count:
            print(f"  ✅ PASSOU: Persistência funcionando ({len(index2.completed)} arquivos)")
        else:
            print(f"  ❌ FALHOU: Persistência quebrada. Esperado {expected_count}, lido {len(index2.completed)}")
            return False

        # Testa is_completed concorrente
        def check_files(thread_id):
            """Verifica se arquivos estão marcados como completos."""
            for i in range(files_per_thread):
                file_path = f"/tmp/thread_{thread_id}_file_{i}.mp4"
                if not index.is_completed(file_path):
                    raise RuntimeError(f"Arquivo {file_path} deveria estar completo!")

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(check_files, i) for i in range(num_threads)]
            for future in futures:
                future.result()

        print(f"  ✅ PASSOU: is_completed() thread-safe")

        return True


def test_concurrent_save():
    """Test that save() doesn't crash with 'Set changed size during iteration'."""
    print("\n🧪 Testando save() sob stress...")

    with tempfile.TemporaryDirectory() as tmpdir:
        index = DownloadIndex(tmpdir)

        def add_and_save(thread_id):
            """Adiciona arquivos e força save múltiplas vezes."""
            for i in range(50):
                file_path = f"/tmp/stress_thread_{thread_id}_file_{i}.mp4"
                index.mark_completed(file_path)  # Isso chama save() internamente

        try:
            with ThreadPoolExecutor(max_workers=20) as executor:
                futures = [executor.submit(add_and_save, i) for i in range(20)]
                for future in futures:
                    future.result()

            print(f"  ✅ PASSOU: Nenhum RuntimeError durante save() concorrente")
            print(f"  📊 Total de arquivos: {len(index.completed)}")
            return True

        except RuntimeError as e:
            print(f"  ❌ FALHOU: {e}")
            return False


if __name__ == "__main__":
    print("=" * 60)
    print("🔒 TESTES DE THREAD-SAFETY DO DOWNLOADINDEX")
    print("=" * 60)

    results = []
    results.append(("Concurrent mark_completed", test_concurrent_mark_completed()))
    results.append(("Concurrent save", test_concurrent_save()))

    print("\n" + "=" * 60)
    print("📊 RESULTADO DOS TESTES")
    print("=" * 60)

    for name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"  {name:.<40} {status}")

    all_passed = all(result for _, result in results)

    print("=" * 60)
    if all_passed:
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("\n✅ DownloadIndex é thread-safe:")
        print("   • mark_completed() protegido com lock")
        print("   • is_completed() protegido com lock")
        print("   • save() cria snapshot antes de iterar")
        print("   • Sem race conditions em alta concorrência")
        exit(0)
    else:
        print("⚠️  ALGUNS TESTES FALHARAM")
        exit(1)
