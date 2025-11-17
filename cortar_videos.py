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
NOME_ARQUIVO_CSV = "v4-especiais.csv"

# 2. O nome da pasta onde estão seus vídeos MPG originais.
PASTA_DOS_VIDEOS = "videos_originais" 

# 3. O nome do vídeo final (se for juntar tudo)
NOME_ARQUIVO_SAIDA_COMPILADO = "video_final_compilado.mp4"

# 4. O nome da pasta para salvar os cortes (se for salvar separado)
PASTA_SAIDA_CORTES_INDIVIDUAIS = "cortes_individuais"

# 5. A extensão dos seus vídeos de ORIGEM 
EXTENSAO_VIDEO_ORIGEM = ".mpg"

# 6. A extensão dos seus vídeos de SAÍDA (para cortes individuais)
EXTENSAO_SAIDA_INDIVIDUAL = ".mp4"

# -------------------------------------------------------------------
# --- FIM DA CONFIGURAÇÃO ---
# -------------------------------------------------------------------

def obter_modo_operacao():
    """Pergunta ao usuário como ele deseja processar os vídeos."""
    while True:
        print("\nO que você deseja fazer?")
        print(" [1] Juntar todos os cortes em um ÚNICO vídeo.")
        print(" [2] Salvar cada corte como um ARQUIVO SEPARADO.")
        modo_operacao = input("Escolha (1 ou 2): ").strip()

        if modo_operacao in ['1', '2']:
            break
        print("Opção inválida. Por favor, digite 1 ou 2.")
    
    modo_ordem = '1' # Padrão (Cronológico)
    if modo_operacao == '1':
        while True:
            print("\nQual deve ser a ordem do vídeo final?")
            print(" [1] Cronológica (mesma ordem do arquivo CSV).")
            print(" [2] Aleatória (baralhar todos os cortes).")
            modo_ordem = input("Escolha (1 ou 2): ").strip()
            
            if modo_ordem in ['1', '2']:
                break
            print("Opção inválida. Por favor, digite 1 ou 2.")
            
    return modo_operacao, modo_ordem

def processar_videos():
    """
    Função principal que lê o CSV, processa os cortes
    e junta tudo ou salva separadamente.
    """
    
    # --- 0. Obter Modo de Operação ---
    modo_operacao, modo_ordem = obter_modo_operacao()

    print("\nIniciando processo...")
    
    # --- 1. Validar Caminhos ---
    if not os.path.exists(NOME_ARQUIVO_CSV):
        print(f"Erro Crítico: Arquivo CSV não encontrado: '{NOME_ARQUIVO_CSV}'")
        sys.exit() 

    if not os.path.exists(PASTA_DOS_VIDEOS):
        print(f"Erro Crítico: Pasta de vídeos não encontrada: '{PASTA_DOS_VIDEOS}'")
        sys.exit() 
    
    # --- 2. Ler e Preparar o CSV ---
    print(f"Lendo CSV: {NOME_ARQUIVO_CSV}")
    try:
        df = pd.read_csv(NOME_ARQUIVO_CSV)
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
        sys.exit()

    # --- 3. Preparar Saída ---
    lista_de_cortes_final = []
    videos_carregados = {}
    contador_cortes = 1

    if modo_operacao == '2':
        # Cria a pasta para os cortes individuais, se não existir
        os.makedirs(PASTA_SAIDA_CORTES_INDIVIDUAIS, exist_ok=True)
        print(f"Salvando cortes individuais em: '{PASTA_SAIDA_CORTES_INDIVIDUAIS}/'")

    try:
        todos_os_videos_na_pasta = os.listdir(PASTA_DOS_VIDEOS)
    except Exception as e:
        print(f"Erro ao ler a pasta de vídeos '{PASTA_DOS_VIDEOS}': {e}")
        sys.exit()

    # --- 4. Processar os Vídeos ---
    try:
        # Loop principal (agrupado por ficheiro de vídeo)
        grupos_de_arquivo = df_valid.groupby('Arquivo_Grupo')
        
        for nome_arquivo_base, grupo_de_cortes in grupos_de_arquivo:
            nome_arquivo_base = nome_arquivo_base.strip() 
            print(f"\n--- Processando Grupo: {nome_arquivo_base} ---")
            
            # Encontra o ficheiro de vídeo .mpg correspondente
            caminho_video_mpg_encontrado = None
            for nome_de_arquivo_real in todos_os_videos_na_pasta:
                if nome_de_arquivo_real.startswith(nome_arquivo_base) and nome_de_arquivo_real.endswith(EXTENSAO_VIDEO_ORIGEM):
                    caminho_video_mpg_encontrado = os.path.join(PASTA_DOS_VIDEOS, nome_de_arquivo_real)
                    break 
            
            if not caminho_video_mpg_encontrado:
                print(f"  AVISO: Vídeo não encontrado. Pulando {len(grupo_de_cortes)} cortes.")
                continue
            
            print(f"  Arquivo encontrado: {caminho_video_mpg_encontrado}")
            print(f"  Carregando vídeo...")
            
            video_clip = VideoFileClip(caminho_video_mpg_encontrado)
            videos_carregados[nome_arquivo_base] = video_clip
            
            # Loop secundário (processa cada corte da planilha)
            for index, row in grupo_de_cortes.iterrows():
                start_time_str = row[start_col]
                end_time_str = row[end_col]
                linha_num = index + 2 
                
                print(f"    [Linha {linha_num}] Extraindo corte: {start_time_str} -> {end_time_str}")
                
                try:
                    # Extrai o subclip
                    sub_clip = video_clip.subclip(start_time_str, end_time_str)
                    
                    if modo_operacao == '1':
                        # MODO 1: Adiciona à lista para juntar no final
                        lista_de_cortes_final.append(sub_clip)
                    
                    else:
                        # MODO 2: Salva o corte individualmente
                        
                        # --- MUDANÇA AQUI ---
                        # 1. O nome do ficheiro usa a nova extensão de SAÍDA (.mp4)
                        # 2. O contador é incrementado AQUI, antes do 'try',
                        #    para garantir que o próximo corte tenha um nome diferente.
                        nome_saida_corte = f"corte{contador_cortes:04d}{EXTENSAO_SAIDA_INDIVIDUAL}"
                        caminho_saida_corte = os.path.join(PASTA_SAIDA_CORTES_INDIVIDUAIS, nome_saida_corte)
                        contador_cortes += 1
                        
                        print(f"      -> Salvando como: {caminho_saida_corte}")
                        
                        # Os codecs padrão (libx264/aac) agora são compatíveis
                        # com a extensão .mp4
                        sub_clip.write_videofile(caminho_saida_corte, codec="libx264", audio_codec="aac")
                        
                        # Fechamos o subclip imediatamente para libertar memória
                        sub_clip.close()
                        
                        # --- MUDANÇA AQUI ---
                        # O contador foi movido para cima
                        # contador_cortes += 1 (LINHA ANTIGA APAGADA)
                        
                except Exception as e:
                    print(f"      ERRO ao cortar {nome_arquivo_base} (Linha {linha_num}): {e}")
        
        # --- 5. Finalização ---
        
        if modo_operacao == '1':
            # MODO 1: Juntar e Salvar o vídeo compilado
            if not lista_de_cortes_final:
                print("\nNenhum corte foi extraído. Vídeo final não gerado.")
                return
                
            print("\n--- Junção Final ---")
            
            if modo_ordem == '2':
                # Opção de ordem Aleatória
                print(f"Baralhando a ordem de {len(lista_de_cortes_final)} cortes...")
                random.shuffle(lista_de_cortes_final)
            else:
                # Opção de ordem Cronológica
                print(f"Mantendo a ordem cronológica (total: {len(lista_de_cortes_final)} cortes)...")
            
            print(f"Juntando os cortes em um único vídeo...")
            video_final = concatenate_videoclips(lista_de_cortes_final)
            
            print(f"Salvando vídeo final em '{NOME_ARQUIVO_SAIDA_COMPILADO}'...")
            video_final.write_videofile(
                NOME_ARQUIVO_SAIDA_COMPILADO,
                codec="libx264",
                audio_codec="aac",
                temp_audiofile='temp-audio.m4a',
                remove_temp=True
            )
            print("\n--- PROCESSO CONCLUÍDO COM SUCESSO! ---")
        
        else:
            # MODO 2: Finalização do salvamento individual
            print(f"\n--- PROCESSO CONCLUÍDO COM SUCESSO! ---")
            print(f"Foram salvos {contador_cortes - 1} cortes individuais na pasta '{PASTA_SAIDA_CORTES_INDIVIDUAIS}'.")

    except Exception as e:
        print(f"Ocorreu um erro inesperado durante o processamento: {e}")
    
    finally:
        # --- 6. Limpeza (Muito Importante) ---
        print("\nLimpando e fechando arquivos...")
        if 'video_final' in locals(): 
            video_final.close()
            
        # Fecha todos os subclips que foram para a lista (Modo 1)
        for clip in lista_de_cortes_final:
            clip.close()
            
        # Fecha todos os vídeos-fonte (MPGs)
        for clip in videos_carregados.values():
            clip.close()
            
        print("Limpeza concluída.")

# --- Ponto de Entrada Principal ---
if __name__ == "__main__":
    processar_videos()