# Arquivo: crud/curso_crud.py

from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import IntegrityError
from db import Curso, Professor # Importa os modelos Curso e Professor (para futuras validações)

# C (CREATE) - Cadastrar Curso
def cadastrar_curso(session: Session, dados: dict) -> Curso | dict:
    """Insere um novo curso no banco de dados."""
    
    # Validações de chaves estrangeiras (opcional, mas boa prática)
    if dados.get('id_Professor') is None:
        return {"erro": "O ID do professor é obrigatório para cadastrar um curso."}

    # 1. Cria a instância do objeto Curso com os dados
    novo_curso = Curso(
        nome=dados.get('nome'),
        area=dados.get('area'),
        turno=dados.get('turno'),
        
        # Chave Estrangeira
        id_Professor=dados.get('id_Professor')
    )
    
    try: 
        session.add(novo_curso)
        session.commit()
        session.refresh(novo_curso)
        return novo_curso
    except IntegrityError:
        session.rollback()
        # Retorna erro se o nome do curso for duplicado (unique=True)
        return {"erro": "Erro de integridade: Já existe um curso com esse nome ou ID de Professor inválido."}


# R (READ) - Buscar Cursos
def buscar_cursos(session: Session) -> list[Curso]:
    """Retorna todos os cursos cadastrados, carregando o Professor responsável."""
    
    # Carrega (Eagerly Load) o relacionamento N:1 com Professor para evitar DetachedInstanceError
    return session.query(Curso).options(
        selectinload(Curso.professor)
    ).all()

def buscar_curso_por_id(session: Session, curso_id: int) -> Curso | None:
    """Busca um curso específico pelo ID."""
    
    # Usaremos o get, mas também carregaremos o professor para consistência
    return session.query(Curso).options(
        selectinload(Curso.professor)
    ).filter(Curso.id_Curso == curso_id).first()


# U (UPDATE) - Atualizar Curso
def atualizar_curso(session: Session, curso_id: int, dados_atualizados: dict) -> Curso | dict | None:
    """Atualiza os dados de um curso existente."""
    curso = buscar_curso_por_id(session, curso_id)
    
    if not curso:
        return None

    # Itera sobre os dados e atualiza os atributos do objeto
    for chave, valor in dados_atualizados.items():
        if valor is not None:
            try:
                setattr(curso, chave, valor)
            except AttributeError:
                continue
            
    try:
        session.commit()
        session.refresh(curso)
        return curso
    except IntegrityError:
        session.rollback()
        return {"erro": "Erro de integridade: Tentativa de duplicar nome de curso ou ID inválido."}


# D (DELETE) - Deletar Curso
def deletar_curso(session: Session, curso_id: int) -> bool:
    """Exclui um curso do banco de dados."""
    curso = buscar_curso_por_id(session, curso_id)
    
    if not curso:
        return False
        
    try:
        session.delete(curso)
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        # Captura erros como tentar deletar um curso associado a turmas ou alunos (N:M)
        print(f"Erro ao deletar curso {curso_id}: {e}")
        return False