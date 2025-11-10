# Arquivo: crud/frequencia_crud.py

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from datetime import date

# Importa os modelos e a função de busca
from db import Aluno, Turma, Aula, Frequencia, StatusPresenca
import crud.aluno_crud as aluno_crud

# =================================================================
# 1. GESTÃO DE AULAS (CREATE, READ)
# =================================================================

def criar_aula(session: Session, turma_id: int, topico: str, data: date = date.today()) -> Aula | dict:
    """Cria um novo registro de aula para uma Turma específica."""
    
    nova_aula = Aula(
        id_Turma=turma_id,
        data_aula=data,
        topico=topico
    )
    
    try:
        session.add(nova_aula)
        session.commit()
        session.refresh(nova_aula)
        return nova_aula
    except IntegrityError:
        session.rollback()
        return {"erro": "Erro de integridade ao criar a aula."}

def buscar_aulas_por_turma(session: Session, turma_id: int) -> list[Aula]:
    """Retorna todas as aulas registradas para uma determinada turma."""
    return session.query(Aula).filter(Aula.id_Turma == turma_id).order_by(Aula.data_aula.desc()).all()


# =================================================================
# 2. LANÇAMENTO DE FREQUÊNCIA (CREATE/UPDATE)
# =================================================================

def registrar_presenca(session: Session, aluno_id: int, aula_id: int, status_presenca: str):
    """Registra ou atualiza o status de presença de um aluno em uma aula."""
    
    # Converte a string de status para o ENUM do SQLAlchemy
    try:
        status_enum = StatusPresenca(status_presenca)
    except ValueError:
        return {"erro": "Status de presença inválido."}

    # 1. Verifica se o registro já existe (CREATE or UPDATE)
    registro = session.query(Frequencia).filter(
        Frequencia.id_Aluno == aluno_id,
        Frequencia.id_Aula == aula_id
    ).first()

    if registro:
        # UPDATE: Se o registro existir, apenas atualiza o status
        registro.status = status_enum
    else:
        # CREATE: Cria um novo registro
        novo_registro = Frequencia(
            id_Aluno=aluno_id,
            id_Aula=aula_id,
            status=status_enum
        )
        session.add(novo_registro)
        
    try:
        session.commit()
        return {"sucesso": True}
    except IntegrityError:
        session.rollback()
        return {"erro": "Erro de integridade ao registrar frequência (Aluno/Aula ID inválido)."}


# =================================================================
# 3. RELATÓRIO DE FALTAS (READ / ANÁLISE)
# =================================================================

def calcular_faltas_por_aluno(session: Session, aluno_id: int) -> dict:
    """Calcula o total de aulas, faltas e presenças de um aluno."""

    # Contagem total de aulas que a turma do aluno teve (Opcional: Filtrar apenas as aulas após a data de matrícula)
    total_aulas_result = session.query(
        func.count(Aula.id_Aula)
    ).join(Turma).join(Aluno).filter(Aluno.id_Aluno == aluno_id).scalar()
    
    if total_aulas_result is None:
        total_aulas = 0
    else:
        total_aulas = total_aulas_result

    # Contagem dos status de presença do aluno (Presente, Falta, Justificada)
    contagem_status = session.query(
        Frequencia.status, 
        func.count(Frequencia.status)
    ).filter(
        Frequencia.id_Aluno == aluno_id
    ).group_by(Frequencia.status).all()

    # Formata o resultado para fácil consumo
    relatorio = {
        'total_aulas': total_aulas,
        'presente': 0,
        'falta': 0,
        'falta_justificada': 0
    }
    
    for status, contagem in contagem_status:
        relatorio[status.name] = contagem

    faltas_justificadas = relatorio['falta_justificada']
    presencas = relatorio['presente']
    
    # 1. Recalcula o Total de Aulas Válidas (Base do Percentual)
    # Total Válido = Total Geral - Faltas Justificadas
    total_aulas_validas = total_aulas - faltas_justificadas
    
    # 2. Adiciona o Total de Aulas Válidas ao relatório para uso no HTML
    relatorio['total_aulas_validas'] = total_aulas_validas
        
    return relatorio