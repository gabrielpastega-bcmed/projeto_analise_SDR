"""
Testes para o módulo reporting.py.
"""

from src.reporting import generate_report


class TestGenerateReport:
    """Testes para a função generate_report."""

    def test_empty_input(self):
        """Testa com lista vazia."""
        result = generate_report([])
        assert result == {
            "agent_ranking": [],
            "product_cloud": [],
            "sales_funnel": {},
            "loss_reasons": {},
        }

    def test_single_chat(self):
        """Testa com um único chat."""
        chats_data = [
            {
                "chat_id": "123",
                "agent_name": "Maria",
                "ops_metrics": {"tme_seconds": 60, "tma_seconds": 120},
                "llm_results": {
                    "cx": {"humanization_score": 4},
                    "product": {"products_mentioned": ["equipamento_a", "ultrassom"]},
                    "sales": {"outcome": "convertido", "rejection_reason": None},
                },
            }
        ]
        result = generate_report(chats_data)

        assert len(result["agent_ranking"]) == 1
        assert result["agent_ranking"][0]["agent"] == "Maria"
        assert result["agent_ranking"][0]["chats"] == 1
        assert result["agent_ranking"][0]["avg_tme"] == 60
        assert result["agent_ranking"][0]["avg_humanization"] == 4
        assert result["product_cloud"] == [("equipamento_a", 1), ("ultrassom", 1)]
        assert result["sales_funnel"] == {"convertido": 1}
        assert result["loss_reasons"] == {}

    def test_multiple_chats_same_agent(self):
        """Testa múltiplos chats do mesmo agente."""
        chats_data = [
            {
                "chat_id": "1",
                "agent_name": "João",
                "ops_metrics": {"tme_seconds": 30, "tma_seconds": 60},
                "llm_results": {
                    "cx": {"humanization_score": 5},
                    "product": {"products_mentioned": ["equipamento_a"]},
                    "sales": {"outcome": "convertido", "rejection_reason": None},
                },
            },
            {
                "chat_id": "2",
                "agent_name": "João",
                "ops_metrics": {"tme_seconds": 90, "tma_seconds": 180},
                "llm_results": {
                    "cx": {"humanization_score": 3},
                    "product": {"products_mentioned": ["equipamento_a", "equipamento_b"]},
                    "sales": {"outcome": "em_andamento", "rejection_reason": None},
                },
            },
        ]
        result = generate_report(chats_data)

        assert len(result["agent_ranking"]) == 1
        agent = result["agent_ranking"][0]
        assert agent["chats"] == 2
        assert agent["avg_tme"] == 60  # (30 + 90) / 2
        assert agent["avg_humanization"] == 4  # (5 + 3) / 2
        assert result["sales_funnel"] == {"convertido": 1, "em_andamento": 1}

    def test_multiple_agents(self):
        """Testa ranking com múltiplos agentes."""
        chats_data = [
            {
                "chat_id": "1",
                "agent_name": "Ana",
                "ops_metrics": {"tme_seconds": 120, "tma_seconds": 60},
                "llm_results": {
                    "cx": {"humanization_score": 3},
                    "product": {"products_mentioned": []},
                    "sales": {"outcome": "perdido", "rejection_reason": None},
                },
            },
            {
                "chat_id": "2",
                "agent_name": "Bruno",
                "ops_metrics": {"tme_seconds": 30, "tma_seconds": 60},
                "llm_results": {
                    "cx": {"humanization_score": 5},
                    "product": {"products_mentioned": []},
                    "sales": {"outcome": "convertido", "rejection_reason": None},
                },
            },
        ]
        result = generate_report(chats_data)

        # Ranking ordenado por menor TME
        assert len(result["agent_ranking"]) == 2
        assert result["agent_ranking"][0]["agent"] == "Bruno"  # TME 30
        assert result["agent_ranking"][1]["agent"] == "Ana"  # TME 120

    def test_loss_reasons(self):
        """Testa contagem de motivos de perda."""
        chats_data = [
            {
                "chat_id": "1",
                "agent_name": "Maria",
                "ops_metrics": {"tme_seconds": 60, "tma_seconds": 60},
                "llm_results": {
                    "cx": {"humanization_score": 2},
                    "product": {"products_mentioned": []},
                    "sales": {"outcome": "lost", "rejection_reason": "Preço alto"},
                },
            },
            {
                "chat_id": "2",
                "agent_name": "Maria",
                "ops_metrics": {"tme_seconds": 60, "tma_seconds": 60},
                "llm_results": {
                    "cx": {"humanization_score": 2},
                    "product": {"products_mentioned": []},
                    "sales": {"outcome": "lost", "rejection_reason": "Preço alto"},
                },
            },
            {
                "chat_id": "3",
                "agent_name": "Maria",
                "ops_metrics": {"tme_seconds": 60, "tma_seconds": 60},
                "llm_results": {
                    "cx": {"humanization_score": 3},
                    "product": {"products_mentioned": []},
                    "sales": {"outcome": "lost", "rejection_reason": "Sem interesse"},
                },
            },
        ]
        result = generate_report(chats_data)

        assert result["loss_reasons"] == {"Preço alto": 2, "Sem interesse": 1}

    def test_null_agent_ignored(self):
        """Testa que agentes nulos são ignorados."""
        chats_data = [
            {
                "chat_id": "1",
                "agent_name": None,
                "ops_metrics": {"tme_seconds": 60, "tma_seconds": 60},
                "llm_results": {
                    "cx": {"humanization_score": 3},
                    "product": {"products_mentioned": []},
                    "sales": {"outcome": "convertido", "rejection_reason": None},
                },
            },
        ]
        result = generate_report(chats_data)

        assert result["agent_ranking"] == []
