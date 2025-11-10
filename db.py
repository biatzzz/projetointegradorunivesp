import enum
import hashlib
# Removida a duplicidade de create_engine
from sqlalchemy import ForeignKey, Table, create_engine, Column, Integer, String, Date, DateTime, Enum
from sqlalchemy.orm import declarative_base, relationship, Session, Mapped, mapped_column
from sqlalchemy.sql import func
from datetime import date # Necessário para o default em data_matricula

# Criar conexão com SQLite (arquivo local chamado banco.db)
engine = create_engine("sqlite:///banco.db", echo=True)

# Base para os modelos
Base = declarative_base()

# -----------------------------------------------------
# TABELAS ASSOCIATIVAS N:M (Muitos para Muitos)
# -----------------------------------------------------

# Tabela associativa 1: entre Curso e Turma (M:N)
curso_turma = Table(
    "curso_turma",
    Base.metadata,
    Column("curso_id", Integer, ForeignKey("cursos.id_Curso"), primary_key=True),
    Column("turma_id", Integer, ForeignKey("turmas.id_Turma"), primary_key=True)
)

# Tabela associativa 2: entre Aluno e Curso (NOVA: Alinhamento com o MER)
# Adiciona a data de matrícula conforme o MER para registro do evento
curso_aluno = Table(
    "curso_aluno",
    Base.metadata,
    Column("aluno_id", Integer, ForeignKey("alunos.id_Aluno"), primary_key=True),
    Column("curso_id", Integer, ForeignKey("cursos.id_Curso"), primary_key=True),
    Column("data_matricula", Date, default=date.today) 
)
# -----------------------------------------------------
# FIM TABELAS ASSOCIATIVAS
# -----------------------------------------------------

# Criar tabelas hash
def hash_senha(senha: str) -> str:
    return hashlib.sha256(senha.encode()).hexdigest()

class Usuario(Base):
    __tablename__ = 'usuarios'
    id_Usuario = Column(Integer, primary_key=True, autoincrement=True)
    usuario = Column(String, nullable=False)
    login = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=False, unique=True)
    senha_hash = Column(String, nullable=False)
    criado_em = Column(DateTime, default=func.now())
    
    # Métodos para definir e verificar senha - usando hash
    def set_senha(self, senha: str):
        self.senha_hash = hash_senha(senha)

    def checa_senha(self, senha: str) -> bool:
        return self.senha_hash == hash_senha(senha)

# [ ... SEUS ENUMS (StatusPresenca, StatusArea, StatusTurno) PERMANECEM AQUI ... ]
class StatusPresenca(enum.Enum):
    presente = "presente"
    falta = "falta"
    falta_justificada = "falta_justificada"

class StatusArea(enum.Enum):
    humanas = "humanas"
    exatas = "exatas"
    biologicas = "biologicas"

class StatusTurno(enum.Enum):
    matutino = "matutino"
    vespertino = "vespertino"
    noturno = "noturno"
# [ ... FIM SEUS ENUMS ... ]

# CLASSE AULA (Rastreia quando uma aula foi dada para uma Turma)
class Aula(Base):
    __tablename__ = 'aulas'
    id_Aula = Column(Integer, primary_key=True, autoincrement=True)
    id_Turma = Column(Integer, ForeignKey('turmas.id_Turma'), nullable=False)
    data_aula = Column(Date, nullable=False, default=date.today)
    topico = Column(String) # O que foi ensinado

    # Relacionamento 1:N com Turma
    turma = relationship("Turma", backref="aulas")
    
    # Relação N:M com Alunos, via tabela Frequencia
    alunos_presentes = relationship("Frequencia", back_populates="aula") 


# CLASSE FREQUENCIA (Tabela de Associação N:M entre Aluno e Aula)
# Esta é a tabela que registra a Presença/Falta de cada aluno para cada aula
class Frequencia(Base):
    __tablename__ = 'frequencia'
    
    # Chave Primária Composta pelos IDs
    id_Aluno = Column(Integer, ForeignKey('alunos.id_Aluno'), primary_key=True)
    id_Aula = Column(Integer, ForeignKey('aulas.id_Aula'), primary_key=True)
    
    # Coluna para registrar o status (Presente, Falta, Justificada)
    # Reutiliza o ENUM StatusPresenca que você já definiu
    status = Column(Enum(StatusPresenca), default=StatusPresenca.falta, nullable=False)

    # Relacionamentos
    aluno = relationship("Aluno", back_populates="frequencia_aluno")
    aula = relationship("Aula", back_populates="alunos_presentes")


class Turma(Base):
    __tablename__ = 'turmas'
    id_Turma = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String, nullable=False, unique=True)
    descricao = Column(String)
    turno = Column(Enum(StatusTurno)) 
    cursos = relationship("Curso", secondary=curso_turma, back_populates="turmas") # Relação N:N
    alunos = relationship("Aluno", backref="turma") # Relação 1:N

# [ ... SUAS CLASSES GENERO, PCD, RACA PERMANECEM AQUI ... ]
class Genero(Base):
    __tablename__ = 'generos'
    id_Genero = Column(Integer, primary_key=True, autoincrement=True)
    descricao = Column(String, nullable=False, unique=True)
    alunos = relationship("Aluno", backref="genero") #Relação N:1
    professores = relationship("Professor", backref="genero") #Relação N:1

class Pcd(Base):
    __tablename__ = 'pcds'
    id_Pcd = Column(Integer, primary_key=True, autoincrement=True)
    descricao = Column(String, nullable=False, unique=True)
    alunos = relationship("Aluno", backref="pcd") #Relação N:1
    professores = relationship("Professor", backref="pcd") #Relação N:1

class Raca(Base):
    __tablename__ = 'racas'
    id_Raca = Column(Integer, primary_key=True, autoincrement=True)
    descricao = Column(String, nullable=False, unique=True)
    alunos = relationship("Aluno", backref="raca") #Relação N:1
    professores = relationship("Professor", backref="raca") #Relação N:1
# [ ... FIM SUAS CLASSES GENERO, PCD, RACA ... ]

# CLASSE ALUNO (MODIFICADA COM RELACIONAMENTO N:M)
class Aluno(Base):
    __tablename__ = 'alunos'
    id_Aluno = Column(Integer, primary_key=True, autoincrement=True)
    id_Genero = Column(Integer, ForeignKey('generos.id_Genero'))
    id_Pcd = Column(Integer, ForeignKey('pcds.id_Pcd'))
    id_Raca = Column(Integer, ForeignKey('racas.id_Raca'))
    id_Turma = Column(Integer, ForeignKey('turmas.id_Turma'))
    nome = Column(String, nullable=False)
    dt_nasc = Column(Date)
    # ATENÇÃO: Corrigido o tipo String(11) para String, pois o SQLite não suporta bem o limite, 
    # e a validação do tamanho é melhor feita no Python/HTML. Mantido unique=True.
    cpf = Column(String, unique=True, nullable=False)
    email = Column(String, nullable=False, unique=True)
    telefone = Column(String)
    endereco = Column(String)
    # Modificado default para data.today para consistência
    dt_matricula = Column(Date, default=date.today) 
    dt_conclusao = Column(Date)
    observacoes = Column(String)
    presenca = Column(Enum(StatusPresenca), default=StatusPresenca.falta)
    e_faltoso = Column(Integer, default=0)
    frequencia_aluno = relationship("Frequencia", back_populates="aluno")
    
    # NOVO RELACIONAMENTO N:M (Muitos para Muitos) com Curso, via tabela associativa
    cursos = relationship(
        "Curso", 
        secondary=curso_aluno, 
        back_populates="alunos"
    )

# CLASSE CURSO (MODIFICADA COM RELACIONAMENTO N:M)
class Curso(Base):
    __tablename__ = 'cursos'
    id_Curso = Column(Integer, primary_key=True, autoincrement=True)
    id_Professor = Column(Integer, ForeignKey('professores.id_Professor'))
    nome = Column(String, nullable=False, unique=True)
    area = Column(Enum(StatusArea), nullable=False)
    turno = Column(Enum(StatusTurno))
    professor = relationship("Professor", backref="cursos") # Relação N:1
    turmas = relationship("Turma", secondary=curso_turma, back_populates="cursos") # Relação N:N
    
    # NOVO RELACIONAMENTO N:M (Muitos para Muitos) com Aluno, via tabela associativa
    alunos = relationship(
        "Aluno", 
        secondary=curso_aluno, 
        back_populates="cursos"
    )

class Professor(Base):
    __tablename__ = 'professores'
    id_Professor = Column(Integer, primary_key=True, autoincrement=True)
    id_Genero = Column(Integer, ForeignKey('generos.id_Genero'))
    id_Pcd = Column(Integer, ForeignKey('pcds.id_Pcd'))
    id_Raca = Column(Integer, ForeignKey('racas.id_Raca'))
    nomeProfessor = Column(String, nullable=False)
    cpf = Column(String(11))
    email = Column(String, nullable=False, unique=True)
    telefone = Column(String(11)) #11999999999
    endereco = Column(String)


if __name__ == "__main__":
# [ ... SEUS INSERTS INICIAIS AQUI ... ]
    Base.metadata.create_all(engine)
    print("Tabelas criadas com sucesso!")

    with Session(engine) as session:
        # criando as tabelas de gênero, raça e pcd
        branco = Raca(descricao="branco")
        pardo = Raca(descricao="pardo")
        preto = Raca(descricao="preto")
        amarelo = Raca(descricao="amarelo")
        indigena = Raca(descricao="indigena")
    
        nao_declarado_raca = Raca(descricao="nao declarado")
        homem_cis = Genero(descricao="homem-cis")
        mulher_cis = Genero(descricao="mulher-cis")
        homem_trans = Genero(descricao="homem-trans")
        mulher_trans = Genero(descricao="mulher-trans")
        nao_binario = Genero(descricao="não-binario")
        nao_declarado_genero = Genero(descricao="nao declarado")
        
        deficiencia_fisica = Pcd(descricao="deficiencia fisica")
        deficiencia_auditiva = Pcd(descricao="deficiencia auditiva")
        deficiencia_visual = Pcd(descricao="deficiencia visual")   
        deficiencia_intelectual = Pcd(descricao="deficiencia intelectual")
        neurodivergencia = Pcd(descricao="neurodivergencia")
        nao_declarado_pcd = Pcd(descricao="nao declarado")  

        session.add_all([branco, pardo, preto, amarelo, indigena, nao_declarado_raca,
                        homem_cis, mulher_cis, homem_trans, mulher_trans, nao_binario, nao_declarado_genero,
                        deficiencia_fisica, deficiencia_intelectual, deficiencia_auditiva, deficiencia_visual, nao_declarado_pcd])

        session.commit()
        print("Dados iniciais inseridos com sucesso!")