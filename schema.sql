-- Criação das tabelas
CREATE TABLE IF NOT EXISTS fases_reabilitacao (
    id INTEGER PRIMARY KEY,
    fase TEXT NOT NULL,
    descricao TEXT
);

CREATE TABLE IF NOT EXISTS pacientes (
    id INTEGER PRIMARY KEY,
    nome TEXT NOT NULL,
    data_cirurgia DATE,
    data_cadastro DATE
);

CREATE TABLE IF NOT EXISTS progresso (
    id INTEGER PRIMARY KEY,
    paciente_id INTEGER,
    fase INTEGER,
    data_inicio DATE,
    data_fim DATE,
    status TEXT,
    observacoes TEXT,
    FOREIGN KEY (paciente_id) REFERENCES pacientes(id),
    FOREIGN KEY (fase) REFERENCES fases_reabilitacao(id)
);

-- Inserção das fases de reabilitação
INSERT INTO fases_reabilitacao (id, fase, descricao) VALUES
(1, 'Fase 1 - Proteção', 'Proteção da área lesionada, controle de dor e edema'),
(2, 'Fase 2 - Mobilidade', 'Restauração da amplitude de movimento'),
(3, 'Fase 3 - Força', 'Ganho de força muscular'),
(4, 'Fase 4 - Potência', 'Desenvolvimento de potência e explosão'),
(5, 'Fase 5 - Retorno ao Esporte', 'Preparação para retorno às atividades esportivas'); 