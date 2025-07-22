// Conecte ao seu banco de dados: use meuBancoDeDados
db.createCollection("empresas", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      title: "Validação do Documento de Empresa",
      required: ["cnpj", "nome", "endereco", "createdAt"],
      properties: {
        cnpj: {
          bsonType: "string",
          description: "CNPJ deve ser uma string de 14 dígitos.",
          pattern: "^[0-9]{14}$"
        },
        nome: {
          bsonType: "string",
          description: "Nome da empresa é obrigatório."
        },
        endereco: {
          bsonType: "object",
          required: ["logradouro", "cidade", "estado", "cep"],
          properties: {
            logradouro: { bsonType: "string" },
            numero: { bsonType: "string" },
            complemento: { bsonType: "string" },
            bairro: { bsonType: "string" },
            cidade: { bsonType: "string" },
            estado: { bsonType: "string" },
            cep: { bsonType: "string", pattern: "^[0-9]{8}$" }
          }
        },
        createdAt: {
          bsonType: "date",
          description: "Data de criação do registro."
        }
      }
    }
  }
});

// Índice único para garantir que não haja CNPJs duplicados
db.empresas.createIndex({ "cnpj": 1 }, { unique: true });

db.createCollection("processosMonitorados", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      title: "Validação do Documento de Processo Monitorado",
      required: ["empresaId", "numeroProcesso", "situacao", "dataCadastro", "orgaoJulgador"],
      properties: {
        empresaId: { 
          bsonType: "objectId", 
          description: "ID da empresa que monitora o processo." 
        },
        numeroProcesso: {
          bsonType: "string",
          description: "Número do processo no padrão CNJ (20 caracteres).",
          // Ex: 0712345-67.2025.8.07.0001
          pattern: "^[0-9]{7}-[0-9]{2}\\.[0-9]{4}\\.[0-9]{1}\\.[0-9]{2}\\.[0-9]{4}$"
        },
        situacao: { 
          bsonType: "string",
          description: "Situação atual do monitoramento (ex: ATIVO, ARQUIVADO)."
        },
        dataCadastro: { bsonType: "date" },
        orgaoJulgador: {
          bsonType: "object",
          required: ["nome", "codigo"],
          properties: {
            nome: { bsonType: "string" },
            codigo: { bsonType: "int" },
            municipioIBGE: { bsonType: "int" }
          }
        },
        dadosAPI: {
            bsonType: "object",
            description: "Objeto contendo os dados brutos da API do tribunal."
        }
      }
    }
  }
});

// Índices para otimizar as buscas mais comuns
db.processosMonitorados.createIndex({ "numeroProcesso": 1 }, { unique: true });
db.processosMonitorados.createIndex({ "empresaId": 1 });
db.processosMonitorados.createIndex({ "situacao": 1 });


db.createCollection("notificacoes", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            title: "Validação do Documento de Notificação",
            required: ["processoMonitoradoId", "empresaId", "tipo", "descricao", "dataNotificacao", "status"],
            properties: {
                processoMonitoradoId: { bsonType: "objectId" },
                empresaId: { bsonType: "objectId" },
                tipo: { bsonType: "string" },
                descricao: { bsonType: "string" },
                dataMovimentacao: { bsonType: "date" },
                dataNotificacao: { bsonType: "date" },
                status: {
                    bsonType: "string",
                    enum: ["PENDENTE", "ENVIADA", "LIDA", "ERRO"],
                    description: "Status da notificação."
                }
            }
        }
    }
});

// Índices para buscar notificações por processo, por empresa e por status
db.notificacoes.createIndex({ "processoMonitoradoId": 1 });
db.notificacoes.createIndex({ "empresaId": 1, "status": 1 });
db.notificacoes.createIndex({ "status": 1, "dataNotificacao": -1 });
