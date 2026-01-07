"""
Envia relatório semanal automático com métricas das analises.

Este script é executado apos o sucesso do workflow weekly_analysis
e envia um resumo por email com as principais métricas.
"""

import argparse
import json
import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any


def load_latest_results() -> dict[str, Any] | None:
    """Carrega o arquivo de resultados mais recente."""
    results_dir = Path("data/analysis_results")

    if not results_dir.exists():
        print("❌ Diretório de resultados não encontrado")
        return None

    # Buscar arquivo mais recente
    json_files = list(results_dir.glob("analysis_*.json"))

    if not json_files:
        print("❌ Nenhum arquivo de resultado encontrado")
        return None

    latest_file = max(json_files, key=lambda p: p.stat().st_mtime)
    print(f"📁 Carregando: {latest_file.name}")

    with open(latest_file, encoding="utf-8") as f:
        results = json.load(f)

    return {"results": results, "filename": latest_file.name}


def calculate_metrics(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Calcula métricas agregadas dos resultados."""
    if not results:
        return {}

    # Filtrar resultados validos (sem erro)
    valid_results = [r for r in results if "error" not in r]
    total = len(results)
    success_count = len(valid_results)

    if not valid_results:
        return {
            "total_analyzed": total,
            "success_count": 0,
            "error_count": total,
            "success_rate": 0,
        }

    # Métricas de CX
    nps_scores = [
        r.get("cx", {}).get("nps_prediction", 0) for r in valid_results if r.get("cx")
    ]
    humanization_scores = [
        r.get("cx", {}).get("humanization_score", 0)
        for r in valid_results
        if r.get("cx")
    ]
    positive_sentiments = sum(
        1 for r in valid_results if r.get("cx", {}).get("sentiment") == "positivo"
    )

    # Métricas de Vendas
    converted = sum(
        1 for r in valid_results if r.get("sales", {}).get("converted") is True
    )
    objections_handled = sum(
        1 for r in valid_results if r.get("sales", {}).get("objections_handled") is True
    )

    # Performance
    processing_times = [r.get("processing_time_ms", 0) for r in results]
    avg_processing_time = (
        sum(processing_times) / len(processing_times) if processing_times else 0
    )

    return {
        "total_analyzed": total,
        "success_count": success_count,
        "error_count": total - success_count,
        "success_rate": (success_count / total * 100) if total > 0 else 0,
        # CX
        "avg_nps": sum(nps_scores) / len(nps_scores) if nps_scores else 0,
        "avg_humanization": (
            sum(humanization_scores) / len(humanization_scores)
            if humanization_scores
            else 0
        ),
        "positive_rate": (
            (positive_sentiments / success_count * 100) if success_count > 0 else 0
        ),
        # Sales
        "converted": converted,
        "conversion_rate": (
            (converted / success_count * 100) if success_count > 0 else 0
        ),
        "objections_handled_rate": (
            (objections_handled / success_count * 100) if success_count > 0 else 0
        ),
        # Performance
        "avg_processing_time_s": avg_processing_time / 1000,
        "throughput_chats_per_min": (
            (success_count / (avg_processing_time / 1000 / 60))
            if avg_processing_time > 0
            else 0
        ),
    }


def create_html_email(metrics: dict[str, Any], filename: str) -> str:
    """Cria template HTML do email."""
    now = datetime.now()

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                border-radius: 10px 10px 0 0;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 24px;
            }}
            .content {{
                background: #f8f9fa;
                padding: 30px;
                border-radius: 0 0 10px 10px;
            }}
            .metric-card {{
                background: white;
                padding: 20px;
                margin: 15px 0;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .metric-card h3 {{
                margin-top: 0;
                color: #667eea;
                font-size: 16px;
            }}
            .metric {{
                display: flex;
                justify-content: space-between;
                padding: 8px 0;
                border-bottom: 1px solid #eee;
            }}
            .metric:last-child {{
                border-bottom: none;
            }}
            .metric-label {{
                color: #666;
            }}
            .metric-value {{
                font-weight: bold;
                color: #333;
            }}
            .success {{ color: #28a745; }}
            .warning {{ color: #ffc107; }}
            .danger {{ color: #dc3545; }}
            .footer {{
                text-align: center;
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #ddd;
                color: #666;
                font-size: 12px;
            }}
            .cta-button {{
                display: inline-block;
                padding: 12px 24px;
                background: #667eea;
                color: white;
                text-decoration: none;
                border-radius: 6px;
                margin: 20px 0;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>✅ Analise Semanal Concluída</h1>
            <p>{now.strftime("%d/%m/%Y às %H:%M")}</p>
        </div>

        <div class="content">
            <!-- Resumo Geral -->
            <div class="metric-card">
                <h3>📊 Resumo Geral</h3>
                <div class="metric">
                    <span class="metric-label">Chats Analisados:</span>
                    <span class="metric-value">{metrics.get('total_analyzed', 0)}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Taxa de Sucesso:</span>
                    <span class="metric-value success">{metrics.get('success_rate', 0):.1f}%</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Erros:</span>
                    <span class="metric-value {'danger' if metrics.get('error_count', 0) > 0 else ''}">{metrics.get('error_count', 0)}</span>
                </div>
            </div>

            <!-- CX -->
            <div class="metric-card">
                <h3>😊 Experiência do Cliente</h3>
                <div class="metric">
                    <span class="metric-label">NPS Médio:</span>
                    <span class="metric-value {'success' if metrics.get('avg_nps', 0) >= 7 else 'warning'}">{metrics.get('avg_nps', 0):.1f}/10</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Humanização:</span>
                    <span class="metric-value">{metrics.get('avg_humanization', 0):.1f}/5</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Sentimento Positivo:</span>
                    <span class="metric-value success">{metrics.get('positive_rate', 0):.1f}%</span>
                </div>
            </div>

            <!-- Vendas -->
            <div class="metric-card">
                <h3>💼 Performance de Vendas</h3>
                <div class="metric">
                    <span class="metric-label">Conversões:</span>
                    <span class="metric-value">{metrics.get('converted', 0)} chats</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Taxa de Conversão:</span>
                    <span class="metric-value {'success' if metrics.get('conversion_rate', 0) >= 30 else 'warning'}">{metrics.get('conversion_rate', 0):.1f}%</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Objeções Tratadas:</span>
                    <span class="metric-value">{metrics.get('objections_handled_rate', 0):.1f}%</span>
                </div>
            </div>

            <!-- Performance -->
            <div class="metric-card">
                <h3>⚡ Performance Técnica</h3>
                <div class="metric">
                    <span class="metric-label">Tempo Médio/Chat:</span>
                    <span class="metric-value">{metrics.get('avg_processing_time_s', 0):.2f}s</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Throughput:</span>
                    <span class="metric-value">{metrics.get('throughput_chats_per_min', 0):.1f} chats/min</span>
                </div>
            </div>

            <!-- CTA -->
            <center>
                <a href="https://github.com/gabrielpastega-bcmed/projeto_analise_SDR" class="cta-button">
                    Ver Dashboard Completo
                </a>
            </center>

            <!-- Detalhes Técnicos -->
            <div style="margin-top: 30px; padding: 15px; background: #fff; border-radius: 8px; font-size: 12px; color: #666;">
                <strong>Detalhes Técnicos:</strong><br>
                Arquivo: {filename}<br>
                Processamento: Automático via GitHub Actions<br>
                Próxima execução: Segunda-feira 6AM UTC
            </div>
        </div>

        <div class="footer">
            <p>🤖 Relatório gerado automaticamente pelo sistema de analise SDR</p>
            <p>Dúvidas? Entre em contato com a equipe de analise</p>
        </div>
    </body>
    </html>
    """

    return html


def send_email(html_content: str, metrics: dict[str, Any]) -> bool:
    """Envia email com o relatório."""
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender = os.getenv("MAIL_USERNAME")
    password = os.getenv("MAIL_PASSWORD")
    recipient = os.getenv("NOTIFICATION_EMAIL")

    if not all([sender, password, recipient]):
        print("❌ Credenciais de email não configuradas")
        print(f"   MAIL_USERNAME: {'✓' if sender else '✗'}")
        print(f"   MAIL_PASSWORD: {'✓' if password else '✗'}")
        print(f"   NOTIFICATION_EMAIL: {'✓' if recipient else '✗'}")
        return False

    # Criar mensagem
    msg = MIMEMultipart("alternative")
    msg["Subject"] = (
        f"📊 Relatório Semanal - {metrics.get('total_analyzed', 0)} chats analisados"
    )
    msg["From"] = f"SDR Analytics <{sender}>"
    msg["To"] = recipient  # type: ignore[assignment]

    # Anexar HTML
    html_part = MIMEText(html_content, "html")
    msg.attach(html_part)

    # Enviar
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            # Type assertions - we've verified these are not None above
            assert sender is not None and password is not None and recipient is not None
            server.login(sender, password)
            server.sendmail(sender, recipient, msg.as_string())

        print(f"✅ Email enviado para: {recipient}")
        return True

    except Exception as e:
        print(f"❌ Erro ao enviar email: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Envia relatório semanal de analises")
    parser.add_argument(
        "--dry-run", action="store_true", help="Apenas exibe métricas sem enviar email"
    )
    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("📧 RELATÓRIO SEMANAL - ENVIO DE EMAIL")
    print("=" * 60 + "\n")

    # Carregar resultados
    data = load_latest_results()
    if not data:
        print("❌ Não foi possível carregar os resultados")
        return 1

    # Calcular métricas
    print("📊 Calculando métricas...")
    metrics = calculate_metrics(data["results"])

    # Exibir resumo
    print("\n" + "-" * 60)
    print("RESUMO:")
    print(f"  Total: {metrics.get('total_analyzed', 0)} chats")
    print(
        f"  Sucesso: {metrics.get('success_count', 0)} ({metrics.get('success_rate', 0):.1f}%)"
    )
    print(f"  NPS Médio: {metrics.get('avg_nps', 0):.1f}/10")
    print(f"  Conversão: {metrics.get('conversion_rate', 0):.1f}%")
    print("-" * 60 + "\n")

    if args.dry_run:
        print("🔍 DRY RUN - Email não será enviado")
        html = create_html_email(metrics, data["filename"])
        print("\n📄 Preview do HTML:")
        print(html[:500] + "...")
        return 0

    # Criar HTML e enviar
    print("📝 Gerando template HTML...")
    html = create_html_email(metrics, data["filename"])

    print("📧 Enviando email...")
    success = send_email(html, metrics)

    if success:
        print("\n✅ Relatório enviado com sucesso!")
        return 0
    else:
        print("\n❌ Falha ao enviar relatório")
        return 1


if __name__ == "__main__":
    exit(main())
