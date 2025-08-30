import pandas as pd
import json
import re

def inferir_tribunal(numero_processo: str) -> str:
    """
    Infer the tribunal abbreviation from a CNJ process number based on
    the Judicial Branch and Tribunal codes (J.TR part).

    Examples:
    - 8.15 -> TJPB (State Justice, Tribunal 15)
    - 4.05 -> TRF5 (Federal Justice, Tribunal 05 - 5th Region)
    - 5.13 -> TRT13 (Labor Justice, Tribunal 13 - 13th Region)
    """
    if not isinstance(numero_processo, str):
        return "NULO/INVALIDO" # Handle non-string inputs

    # Regex to capture the J.TR part: NNNNNNN-DD.YYYY.J.TR.OOOO.C
    # We are interested in the J (group 2) and TR (group 3)
    match = re.search(r'\d{7}-\d{2}\.\d{4}\.((\d{1,2})\.(\d{1,2}))\.', numero_processo)
    
    if match:
        judicial_branch_code = match.group(2) # J (e.g., '8', '4', '5')
        tribunal_code = match.group(3)        # TR (e.g., '15', '05', '13')

        # Mapping based on common CNJ codes for Paraíba and surrounding regions
        if judicial_branch_code == '8': # Justiça Estadual
            if tribunal_code == '15':
                return "TJPB"
            # Adicione outros tribunais estaduais se necessário
            # elif tribunal_code == 'XX': return "TJXX"
        elif judicial_branch_code == '4': # Justiça Federal
            if tribunal_code == '05':
                return "TRF5"
        elif judicial_branch_code == '5': # Justiça do Trabalho
            if tribunal_code == '13':
                return "TRT13"
        # Adicione outros ramos da justiça ou tribunais específicos se necessário
        elif judicial_branch_code == '7': # Justiça Eleitoral
            if tribunal_code == 'XX': return "TREXX"
        elif judicial_branch_code == '6': # Justiça Militar
            if tribunal_code == 'XX': return "TJMXX"

    return "DESCONHECIDO" # If the pattern doesn't match or code is not mapped

# --- Configurações do Script ---
# Nome do arquivo Excel de entrada. Certifique-se de que este arquivo esteja na mesma pasta
# do script ou forneça o caminho completo.
EXCEL_FILE_PATH = r'C:\IFPB\bd\projeto\processos_unificados.xlsx'

# Nome do arquivo JSON de saída.
OUTPUT_JSON_PATH = r'C:\IFPB\bd\projeto\carga_processos.json'

# Nome da coluna no seu arquivo Excel que contém os números dos processos.
# Se o Excel não tiver cabeçalho e os processos estiverem na primeira coluna,
# você pode precisar ler sem cabeçalho e usar df.iloc[:, 0]
PROCESS_COLUMN_NAME = 'PROCESSOS' 

# --- Script Principal ---
print(f"Iniciando a leitura do arquivo Excel: '{EXCEL_FILE_PATH}'")
try:
    # Lê o arquivo Excel para um DataFrame do pandas
    df = pd.read_excel(EXCEL_FILE_PATH)

    # Verifica se a coluna de processos existe no DataFrame
    if PROCESS_COLUMN_NAME not in df.columns:
        raise ValueError(f"A coluna '{PROCESS_COLUMN_NAME}' não foi encontrada no arquivo Excel. "
                         f"Colunas disponíveis: {df.columns.tolist()}")

    # Converte a coluna de processos para string, para garantir que inferir_tribunal funcione corretamente
    df[PROCESS_COLUMN_NAME] = df[PROCESS_COLUMN_NAME].astype(str)

    # Prepara a lista de dicionários no formato JSON desejado
    processos_para_json = []
    
    for index, row in df.iterrows():
        numero_processo = str(row[PROCESS_COLUMN_NAME]).strip() # Garante que é string e remove espaços
        
        # Verifica se o número do processo não está vazio
        if numero_processo and numero_processo.lower() != 'nan': # pd.read_excel pode ler células vazias como NaN
            tribunal_inferido = inferir_tribunal(numero_processo)
            processos_para_json.append({
                "numeroProcesso": numero_processo,
                "tribunal": tribunal_inferido
            })
        else:
            print(f"Aviso: Linha {index + 1} contém um número de processo vazio ou inválido e será ignorada.")

    # Escreve a lista de dicionários para um arquivo JSON
    with open(OUTPUT_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(processos_para_json, f, ensure_ascii=False, indent=2)

    print(f"\nArquivo JSON '{OUTPUT_JSON_PATH}' gerado com sucesso!")
    print(f"Total de {len(processos_para_json)} processos processados.")

except FileNotFoundError:
    print(f"ERRO: O arquivo Excel não foi encontrado no caminho especificado: '{EXCEL_FILE_PATH}'.")
    print("Por favor, verifique o nome do arquivo e se ele está na mesma pasta do script.")
except ValueError as ve:
    print(f"ERRO: {ve}")
except Exception as e:
    print(f"Ocorreu um erro inesperado: {e}")
