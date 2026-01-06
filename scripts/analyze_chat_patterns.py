"""
Script de Analise Exploratoria de Chats SDR
Objetivo: Identificar padroes e dados extraiveis para melhorar Insights
"""

import sys
from pathlib import Path

# Adicionar diretorio raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from collections import Counter

from src.ingestion import load_chats_from_bigquery, load_chats_from_json


def load_data(days: int = 30, limit: int = 500, local_path: str = "data/raw/bigquery_sample.json"):
    """
    Carrega dados. Tenta BigQuery primeiro, fallback para local se falhar ou se credenciais nao existirem.
    """
    print("\n[INFO] Carregando dados...")

    # Tentar carregar localmente se o arquivo existir
    file_path = Path(local_path)
    if file_path.exists():
        print(f"   [INFO] Encontrado arquivo local: {local_path}")
        print(f"   [INFO] Carregando de {local_path} (Modo Offline/Dev)...")
        try:
            chats = load_chats_from_json(str(file_path))
            print(f"   [OK] Sucesso! {len(chats)} chats carregados do arquivo local.")
            return chats
        except Exception as e:
            print(f"   [WARN] Erro ao carregar arquivo local: {e}")
            print("   [WARN] Tentando BigQuery...")

    # Se não existir local ou falhar, tenta BigQuery
    try:
        print(f"   [INFO] Tentando conectar ao BigQuery (ultimos {days} dias)...")
        return load_chats_from_bigquery(days=days, limit=limit, lightweight=False)
    except Exception as e:
        print("\n[ERROR] ERRO FATAL: Falha ao carregar dados.")
        print(f"   Erro: {e}")
        print(f"   Dica: Verifique credenciais do BigQuery ou coloque um arquivo em {local_path}")
        sys.exit(1)


def analyze_origins(chats):
    """Analisa origens dos leads."""
    origins = []
    for chat in chats:
        if chat.contact and chat.contact.customFields:
            origin = chat.contact.customFields.get("origem_do_negocio", "Não informado")
            origins.append(origin)
    return Counter(origins)


def analyze_tags(chats):
    """Analisa tags de qualificação."""
    all_tags = []
    for chat in chats:
        if chat.tags:
            for tag in chat.tags:
                all_tags.append(tag.get("name", ""))
    return Counter(all_tags)


def analyze_keywords(chats, tech_patterns=None, intent_patterns=None):
    """Analisa palavras-chave em mensagens."""
    if tech_patterns is None:
        tech_patterns = [
            "equipamento_a",
            "equipamento_b",
            "equipamento_c",
            "ultrassom",
            "IPL",
            "equipamento_d",
            "peeling",
            "LED",
            "cavitação",
            "hifu",
            "carboxiterapia",
            "depilação",
            "rejuvenescimento",
            "lipo",
        ]

    if intent_patterns is None:
        intent_patterns = [
            "comprar",
            "valor",
            "preço",
            "orçamento",
            "financiamento",
            "parcela",
            "condição",
            "dúvida",
            "informação",
            "quanto custa",
            "cotação",
            "pagamento",
            "entrada",
        ]

    keywords_tech = []
    keywords_intent = []

    for chat in chats:
        for msg in chat.messages:
            if not msg.body:
                continue
            body_lower = msg.body.lower()
            for tech in tech_patterns:
                if tech.lower() in body_lower:
                    keywords_tech.append(tech)
            for intent in intent_patterns:
                if intent.lower() in body_lower:
                    keywords_intent.append(intent)

    return Counter(keywords_tech), Counter(keywords_intent)


def print_analysis(chats):
    """Função principal para rodar analise no terminal."""
    print("=" * 60)
    print("ANALISE EXPLORATORIA DE CHATS SDR")
    print("=" * 60)

    # 1. Origens
    origin_counts = analyze_origins(chats)
    print("\n[1] ORIGENS DOS LEADS")
    for origin, count in origin_counts.most_common(10):
        print(f"   {origin}: {count}")

    # 2. Tags
    tag_counts = analyze_tags(chats)
    print("\n[2] TAGS DE QUALIFICACAO")
    for tag, count in tag_counts.most_common(15):
        print(f"   {tag}: {count}")

    # 3. Keywords
    tech_counts, intent_counts = analyze_keywords(chats)
    print("\n[3] PALAVRAS-CHAVE FREQUENTES")
    print("   Tecnologias:")
    for tech, count in tech_counts.most_common(10):
        print(f"      {tech}: {count}")
    print("\n   Intencoes:")
    for intent, count in intent_counts.most_common(10):
        print(f"      {intent}: {count}")


if __name__ == "__main__":
    chats = load_data()
    print_analysis(chats)
