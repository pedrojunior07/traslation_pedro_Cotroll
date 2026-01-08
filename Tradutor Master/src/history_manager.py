# -*- coding: utf-8 -*-
"""
Gerenciador de Histórico de Traduções
Salva traduções concluídas e em andamento para recuperação posterior
"""
import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict


@dataclass
class TranslationHistory:
    """Registro de histórico de tradução"""
    id: str  # UUID único
    timestamp: str  # Data/hora de criação
    status: str  # "in_progress", "completed", "failed"
    source_lang: str
    target_lang: str
    total_files: int
    total_tokens: int
    translated_tokens: int
    files: List[Dict]  # Lista de arquivos e seus estados
    progress_data: Optional[Dict] = None  # Dados de progresso detalhados
    output_dir: Optional[str] = None
    error_message: Optional[str] = None


class HistoryManager:
    """Gerencia histórico de traduções"""

    def __init__(self, history_file: str = "translation_history.json"):
        """
        Args:
            history_file: Arquivo JSON para armazenar histórico
        """
        self.history_file = history_file
        self._ensure_history_file()

    def _ensure_history_file(self):
        """Garante que arquivo de histórico existe"""
        if not os.path.exists(self.history_file):
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump({"translations": []}, f, ensure_ascii=False, indent=2)

    def _load_history(self) -> List[Dict]:
        """Carrega histórico do arquivo"""
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("translations", [])
        except Exception as e:
            print(f"⚠ Erro ao carregar histórico: {e}")
            return []

    def _save_history(self, history: List[Dict]):
        """Salva histórico no arquivo"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump({"translations": history}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠ Erro ao salvar histórico: {e}")

    def create_translation(
        self,
        source_lang: str,
        target_lang: str,
        files: List[str],
        total_tokens: int,
        output_dir: str
    ) -> str:
        """
        Cria nova entrada de tradução no histórico

        Args:
            source_lang: Idioma de origem
            target_lang: Idioma de destino
            files: Lista de caminhos de arquivos
            total_tokens: Total de tokens a traduzir
            output_dir: Diretório de saída

        Returns:
            ID único da tradução
        """
        import uuid

        translation_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()

        # Criar lista de arquivos com estado
        files_data = [
            {
                "path": file_path,
                "name": os.path.basename(file_path),
                "status": "pending",
                "tokens": 0,
                "translated": 0
            }
            for file_path in files
        ]

        translation = TranslationHistory(
            id=translation_id,
            timestamp=timestamp,
            status="in_progress",
            source_lang=source_lang,
            target_lang=target_lang,
            total_files=len(files),
            total_tokens=total_tokens,
            translated_tokens=0,
            files=files_data,
            output_dir=output_dir
        )

        # Adicionar ao histórico
        history = self._load_history()
        history.insert(0, asdict(translation))  # Mais recente primeiro
        self._save_history(history)

        print(f"📝 Nova tradução criada no histórico: {translation_id}")
        return translation_id

    def update_translation(
        self,
        translation_id: str,
        status: Optional[str] = None,
        translated_tokens: Optional[int] = None,
        current_file_idx: Optional[int] = None,
        files_data: Optional[List[Dict]] = None,
        progress_data: Optional[Dict] = None,
        error_message: Optional[str] = None
    ):
        """
        Atualiza entrada de tradução existente

        Args:
            translation_id: ID da tradução
            status: Novo status
            translated_tokens: Quantidade de tokens traduzidos
            current_file_idx: Índice do arquivo atual
            files_data: Dados atualizados dos arquivos
            progress_data: Dados de progresso detalhados
            error_message: Mensagem de erro (se houver)
        """
        history = self._load_history()

        for entry in history:
            if entry.get("id") == translation_id:
                if status:
                    entry["status"] = status
                if translated_tokens is not None:
                    entry["translated_tokens"] = translated_tokens
                if files_data:
                    entry["files"] = files_data
                if progress_data:
                    entry["progress_data"] = progress_data
                if error_message:
                    entry["error_message"] = error_message

                # Atualizar timestamp de última modificação
                entry["last_updated"] = datetime.now().isoformat()

                self._save_history(history)
                print(f"📝 Tradução atualizada: {translation_id} - Status: {status or 'N/A'}")
                return

        print(f"⚠ Tradução não encontrada: {translation_id}")

    def complete_translation(self, translation_id: str):
        """Marca tradução como completa"""
        self.update_translation(
            translation_id,
            status="completed",
            progress_data=None  # Limpar progresso detalhado
        )

    def fail_translation(self, translation_id: str, error_message: str):
        """Marca tradução como falha"""
        self.update_translation(
            translation_id,
            status="failed",
            error_message=error_message
        )

    def get_translation(self, translation_id: str) -> Optional[Dict]:
        """Obtém tradução específica pelo ID"""
        history = self._load_history()
        for entry in history:
            if entry.get("id") == translation_id:
                return entry
        return None

    def get_all_translations(self) -> List[Dict]:
        """Retorna todas as traduções do histórico"""
        return self._load_history()

    def get_in_progress_translations(self) -> List[Dict]:
        """Retorna traduções em andamento"""
        history = self._load_history()
        return [t for t in history if t.get("status") == "in_progress"]

    def get_failed_translations(self) -> List[Dict]:
        """Retorna traduções que falharam"""
        history = self._load_history()
        return [t for t in history if t.get("status") == "failed"]

    def get_completed_translations(self) -> List[Dict]:
        """Retorna traduções concluídas"""
        history = self._load_history()
        return [t for t in history if t.get("status") == "completed"]

    def resume_translation(self, translation_id: str) -> Optional[Dict]:
        """
        Retoma uma tradução falha ou em progresso de onde parou

        Returns:
            Dicionário com informações para retomar a tradução:
            - files: Lista de arquivos
            - current_file_idx: Índice do arquivo onde parou
            - translated_tokens: Tokens já traduzidos
            - output_dir: Diretório de saída
            - source_lang: Idioma de origem
            - target_lang: Idioma de destino
        """
        translation = self.get_translation(translation_id)
        if not translation:
            return None

        # Determinar onde parou
        files_data = translation.get("files", [])
        current_file_idx = 0

        # Encontrar primeiro arquivo não completado
        for idx, file_data in enumerate(files_data):
            if file_data.get("status") != "completed":
                current_file_idx = idx
                break

        # Marcar como "in_progress" novamente
        self.update_translation(
            translation_id,
            status="in_progress",
            error_message=None  # Limpar erro anterior
        )

        print(f"\n🔄 RETOMANDO TRADUÇÃO:")
        print(f"   ID: {translation_id}")
        print(f"   Arquivo atual: {files_data[current_file_idx].get('name', 'N/A')}")
        print(f"   Progresso: {current_file_idx + 1}/{len(files_data)} arquivos")
        print(f"   Tokens traduzidos: {translation.get('translated_tokens', 0)}/{translation.get('total_tokens', 0)}")

        return {
            "files": [f.get("path") for f in files_data],
            "current_file_idx": current_file_idx,
            "translated_tokens": translation.get("translated_tokens", 0),
            "output_dir": translation.get("output_dir"),
            "source_lang": translation.get("source_lang"),
            "target_lang": translation.get("target_lang"),
            "files_data": files_data
        }

    def delete_translation(self, translation_id: str) -> bool:
        """
        Remove tradução do histórico

        Returns:
            True se removido com sucesso, False caso contrário
        """
        history = self._load_history()
        original_len = len(history)
        history = [t for t in history if t.get("id") != translation_id]

        if len(history) < original_len:
            self._save_history(history)
            print(f"🗑 Tradução removida: {translation_id}")
            return True
        return False

    def clear_completed_translations(self):
        """Remove todas as traduções concluídas do histórico"""
        history = self._load_history()
        history = [t for t in history if t.get("status") != "completed"]
        self._save_history(history)
        print("🗑 Traduções concluídas removidas do histórico")

    def get_statistics(self) -> Dict:
        """Retorna estatísticas do histórico"""
        history = self._load_history()

        total = len(history)
        in_progress = len([t for t in history if t.get("status") == "in_progress"])
        completed = len([t for t in history if t.get("status") == "completed"])
        failed = len([t for t in history if t.get("status") == "failed"])

        total_files_completed = sum(
            t.get("total_files", 0)
            for t in history
            if t.get("status") == "completed"
        )

        total_tokens_translated = sum(
            t.get("translated_tokens", 0)
            for t in history
            if t.get("status") == "completed"
        )

        return {
            "total": total,
            "in_progress": in_progress,
            "completed": completed,
            "failed": failed,
            "total_files_completed": total_files_completed,
            "total_tokens_translated": total_tokens_translated
        }

    def export_completed_files(self, translation_id: str) -> List[str]:
        """
        Retorna lista de arquivos traduzidos de uma tradução completa

        Returns:
            Lista de caminhos de arquivos de saída
        """
        translation = self.get_translation(translation_id)
        if not translation or translation.get("status") != "completed":
            return []

        output_dir = translation.get("output_dir")
        if not output_dir:
            return []

        # Coletar arquivos de saída
        output_files = []
        for file_data in translation.get("files", []):
            if file_data.get("status") == "completed":
                # Construir caminho de saída
                source_path = file_data.get("path")
                if source_path:
                    # Assumir que saída é no output_dir com mesmo nome + _traduzido
                    base_name = os.path.basename(source_path)
                    name, ext = os.path.splitext(base_name)
                    output_path = os.path.join(output_dir, f"{name}_traduzido.docx")

                    if os.path.exists(output_path):
                        output_files.append(output_path)

        return output_files


if __name__ == "__main__":
    # Teste
    manager = HistoryManager("test_history.json")

    # Criar nova tradução
    files = ["test1.docx", "test2.docx", "test3.docx"]
    translation_id = manager.create_translation(
        source_lang="en",
        target_lang="pt",
        files=files,
        total_tokens=1000,
        output_dir="./output"
    )

    print(f"\nCriada tradução: {translation_id}")

    # Atualizar progresso
    manager.update_translation(
        translation_id,
        translated_tokens=300
    )

    # Completar
    manager.complete_translation(translation_id)

    # Estatísticas
    stats = manager.get_statistics()
    print(f"\nEstatísticas: {stats}")

    # Limpar arquivo de teste
    if os.path.exists("test_history.json"):
        os.remove("test_history.json")
