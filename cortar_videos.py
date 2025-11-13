import pandas as pd
# Importa as funções específicas que precisamos
from moviepy.editor import VideoFileClip, concatenate_videoclips
import os
import sys
# Importa a biblioteca 'random' para baralhar a ordem
import random 

# -------------------------------------------------------------------
# --- CONFIGURAÇÃO ---
# -------------------------------------------------------------------

# 1. O nome exato do seu arquivo CSV 
NOME_ARQUIVO_CSV = "v4.csv"

# 2. O nome da pasta onde estão seus vídeos MPG originais.
PASTA_DOS_VIDEOS = "videos_originais" 

# 3. O nome que você quer para o vídeo final compilado.
NOME_ARQUIVO_SAIDA = "video_final_COMPILADO_ALEATORIO.mp4"

# 4. A extensão dos seus vídeos de origem 
EXTENSAO_VIDEO = ".mpg"

# -------------------------------------------------------------------
# --- FIM DA CONFIGURAÇÃO ---
# -------------------------------------------------------------------


def processar_videos():
    """
    Função principal que lê o CSV, processa os cortes
    e junta tudo em um único vídeo.
    """
    print("Iniciando processo de corte e junção...")
    
    # --- 1. Validar Caminhos ---
    if not os.path.exists(NOME_ARQUIVO_CSV):
        print(f"Erro Crítico: Arquivo CSV não encontrado no caminho:")
        print(f"'{os.path.abspath(NOME_ARQUIVO_CSV)}'")
        print("Por favor, verifique a variável 'NOME_ARQUIVO_CSV'.")
        sys.exit() 

    if not os.path.exists(PASTA_DOS_VIDEOS):
        print(f"Erro Crítico: Pasta de vídeos não encontrada no caminho:")
        print(f"'{os.path.abspath(PASTA_DOS_VIDEOS)}'")
        print("Por favor, verifique a variável 'PASTA_DOS_VIDEOS'.")
        sys.exit() 
    
    print(f"Lendo CSV: {NOME_ARQUIVO_CSV}")
    
    # --- 2. Ler e Preparar o CSV ---
    try:
        df = pd.read_csv(NOME_ARQUIVO_CSV)
        # Renomeia a primeira coluna para 'Arquivo_Grupo'
        df = df.rename(columns={df.columns[0]: 'Arquivo_Grupo'})
        start_col = "COMEÇO DO CORTE"
        end_col = "FINAL DO CORTE"
        
        start_sec = pd.to_datetime(df[start_col], format='%H:%M:%S', errors='coerce')
        end_sec = pd.to_datetime(df[end_col], format='%H:%M:%S', errors='coerce')
        df['duration_sec'] = (end_sec - start_sec).dt.total_seconds()
        
        df_valid = df.dropna(subset=['Arquivo_Grupo', 'duration_sec'])
        df_valid = df_valid[df_valid['duration_sec'] > 0]
        
        print(f"Encontrados {len(df_valid)} cortes válidos para processar.")
        
    except Exception as e:
        print(f"Erro ao ler ou processar o CSV: {e}")
        print("Verifique se o CSV não está corrompido.")
        sys.exit()

    # --- 3. Processar os Vídeos ---
    
    lista_de_cortes_final = []
    videos_carregados = {}
    
    try:
        todos_os_videos_na_pasta = os.listdir(PASTA_DOS_VIDEOS)
    except Exception as e:
        print(f"Erro ao ler a pasta de vídeos '{PASTA_DOS_VIDEOS}': {e}")
        sys.exit()

    try:
        grupos_de_arquivo = df_valid.groupby('Arquivo_Grupo')
        
        for nome_arquivo_base, grupo_de_cortes in grupos_de_arquivo:
            nome_arquivo_base = nome_arquivo_base.strip() 
            print(f"\n--- Processando Grupo: {nome_arquivo_base} ---")
            
            caminho_video_mpg_encontrado = None
            for nome_de_arquivo_real in todos_os_videos_na_pasta:
                # Lógica para encontrar o vídeo que COMEÇA COM "ARQUIVO 01" e termina com ".mpg"
                if nome_de_arquivo_real.startswith(nome_arquivo_base) and nome_de_arquivo_real.endswith(EXTENSAO_VIDEO):
                    caminho_video_mpg_encontrado = os.path.join(PASTA_DOS_VIDEOS, nome_de_arquivo_real)
                    break 
            
            if not caminho_video_mpg_encontrado:
                print(f"  AVISO: Nenhum vídeo encontrado na pasta '{PASTA_DOS_VIDEOS}' que COMECE COM '{nome_arquivo_base}' e termine com '{EXTENSAO_VIDEO}'.")
                print(f"  Pulando {len(grupo_de_cortes)} cortes deste grupo.")
                continue
            
            print(f"  Arquivo encontrado: {caminho_video_mpg_encontrado}")
            print(f"  Carregando vídeo...")
            
            # 'VideoFileClip' está agora definido por causa do 'import' corrigido
            video_clip = VideoFileClip(caminho_video_mpg_encontrado)
            videos_carregados[nome_arquivo_base] = video_clip
            
            for index, row in grupo_de_cortes.iterrows():
                start_time_str = row[start_col] # "HH:MM:SS"
                end_time_str = row[end_col]     # "HH:MM:SS"
                linha_num = index + 2 
                
                print(f"    [Linha {linha_num}] Extraindo corte: {start_time_str} -> {end_time_str}")
                
                try:
                    sub_clip = video_clip.subclip(start_time_str, end_time_str)
                    lista_de_cortes_final.append(sub_clip)
                    
                except Exception as e:
                    print(f"      ERRO ao cortar {nome_arquivo_base} (Linha {linha_num}): {e}")
                    print(f"      Pulando este corte específico.")
        
        if not lista_de_cortes_final:
            print("\nNenhum corte foi extraído com sucesso. O vídeo final não será gerado.")
            return

        # --- 4. Baralhar e Salvar ---
        print("\n--- Junção Final ---")
        
        print(f"Baralhando a ordem de {len(lista_de_cortes_final)} cortes...")
        random.shuffle(lista_de_cortes_final) # Baralha a lista
        
        print(f"Juntando os cortes em um único vídeo...")
        
        # 'concatenate_videoclips' está agora definido
        video_final = concatenate_videoclips(lista_de_cortes_final)
        
        print(f"Salvando vídeo final em '{NOME_ARQUIVO_SAIDA}'...")
        
        video_final.write_videofile(
            NOME_ARQUIVO_SAIDA,
            codec="libx264",
            audio_codec="aac",
            temp_audiofile='temp-audio.m4a',
            remove_temp=True
        )
        
        print("\n--- PROCESSO CONCLUÍDO COM SUCESSO! ---")

    except Exception as e:
        print(f"Ocorreu um erro inesperado durante o processamento dos vídeos: {e}")
    
    finally:
        # --- 5. Limpeza (Muito Importante) ---
        print("\nLimpando e fechando arquivos...")
        if 'video_final' in locals(): 
            video_final.close()
            
        for clip in videos_carregados.values():
            clip.close()
            
        print("Limpeza concluída.")

# --- Ponto de Entrada Principal ---
if __name__ == "__main__":
    processar_videos()