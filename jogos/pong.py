"""
    Pong - 2 jogadores - usando PyTME

    Dois jogadores controlam raquetes verticais e tentam fazer a bola
    passar pela raquete do oponente. Primeiro a 7 pontos vence.

    Controles:
        Jogador 1 (esquerda):  W (sobe)   S (desce)
        Jogador 2 (direita):   I (sobe)   K (desce)
        Espaco: lanca a bola
        P: pausa
        Q: sai
"""

from PyTME import *
from PyTME import Pytme  # acesso direto para multi-tecla simultanea
import random


# --- constantes ---
LARGURA = 80
ALTURA = 25

X_RAQUETE_E = 3       # coluna da raquete esquerda
X_RAQUETE_D = 78      # coluna da raquete direita
Y_AREA_MIN = 3        # linha superior da area de jogo (depois do placar)
Y_AREA_MAX = 23       # linha inferior da area de jogo

RAQUETE_TAMANHO = 5   # raquete tem 5 chars de altura
RAQUETE_CHAR = "|"

TICK_MS = 40          # ~25 FPS
PONTOS_PARA_VENCER = 7

# velocidade da bola em "ticks por movimento"
# (menor = mais rapida). Aumenta ligeiramente quando bate na raquete.
BOLA_TICKS_INICIAL = 3
BOLA_TICKS_MIN = 1

# raquete: movimento por "ticks por movimento" enquanto tecla esta pressionada
RAQUETE_TICKS_POR_MOV = 1

# codigos de tecla
VK_W, VK_S = 87, 83
VK_I, VK_K = 73, 75
VK_SPACE, VK_P, VK_Q, VK_ESC = 32, 80, 81, 27


# --- estado ---
estado = {}


def reset_estado_jogo():
    estado.clear()
    estado.update({
        'y_raq_e': (Y_AREA_MIN + Y_AREA_MAX) // 2 - RAQUETE_TAMANHO // 2,
        'y_raq_d': (Y_AREA_MIN + Y_AREA_MAX) // 2 - RAQUETE_TAMANHO // 2,
        'bola_x': 40, 'bola_y': 13,
        'bola_dx': 0, 'bola_dy': 0,
        'bola_presa': True,
        'bola_lado_servico': random.choice(['e', 'd']),  # quem saca
        'pontos_e': 0, 'pontos_d': 0,
        'bola_tick_counter': 0,
        'bola_ticks_por_mov': BOLA_TICKS_INICIAL,
    })


def desenhar_borda_e_meio():
    # topo
    goto_xy(1, 1)
    text("+" + "-" * (LARGURA - 2) + "+")
    # placar (linha 2)
    desenhar_placar()
    # linha entre placar e area de jogo
    goto_xy(1, Y_AREA_MIN - 1)
    text("+" + "-" * (LARGURA - 2) + "+")
    # laterais
    for y in range(Y_AREA_MIN, Y_AREA_MAX + 1):
        goto_xy(1, y); text("|")
        goto_xy(LARGURA, y); text("|")
    # fundo
    goto_xy(1, Y_AREA_MAX + 1)
    text("+" + "-" * (LARGURA - 2) + "+")
    # linha central tracejada
    meio = LARGURA // 2
    for y in range(Y_AREA_MIN, Y_AREA_MAX + 1):
        if y % 2 == 0:
            goto_xy(meio, y); text(":")


def desenhar_placar():
    goto_xy(1, 2)
    text(" " * (LARGURA - 2))  # limpa
    msg = (f" Jogador 1 (W/S): {estado['pontos_e']}   "
           f"vs   Jogador 2 (I/K): {estado['pontos_d']}   "
           f"[Espaco] lanca  [P] pausa  [Q] sai")
    x_ini = max(2, (LARGURA - len(msg)) // 2)
    goto_xy(x_ini, 2)
    text(msg)


def desenhar_raquete(x, y):
    for i in range(RAQUETE_TAMANHO):
        goto_xy(x, y + i)
        text(RAQUETE_CHAR)


def apagar_raquete(x, y):
    for i in range(RAQUETE_TAMANHO):
        goto_xy(x, y + i)
        text(" ")


def desenhar_bola(x, y):
    goto_xy(x, y)
    text("O")


def apagar_bola(x, y):
    goto_xy(x, y)
    text(" ")
    # se a apagada caiu sobre a linha central, redesenha a marca
    if x == LARGURA // 2 and y % 2 == 0:
        goto_xy(x, y); text(":")


def mover_raquete(lado, direcao):
    """direcao: -1 sobe, +1 desce"""
    key = 'y_raq_e' if lado == 'e' else 'y_raq_d'
    x = X_RAQUETE_E if lado == 'e' else X_RAQUETE_D
    novo = estado[key] + direcao
    if novo < Y_AREA_MIN or (novo + RAQUETE_TAMANHO - 1) > Y_AREA_MAX:
        return
    apagar_raquete(x, estado[key])
    estado[key] = novo
    desenhar_raquete(x, estado[key])
    # se a bola estava grudada nessa raquete e ainda esta presa,
    # leva a bola junto
    if estado['bola_presa'] and estado['bola_lado_servico'] == lado:
        apagar_bola(estado['bola_x'], estado['bola_y'])
        ajustar_bola_na_raquete()
        desenhar_bola(estado['bola_x'], estado['bola_y'])


def ajustar_bola_na_raquete():
    """Posiciona a bola colada na raquete que vai sacar."""
    lado = estado['bola_lado_servico']
    if lado == 'e':
        estado['bola_x'] = X_RAQUETE_E + 1
        estado['bola_y'] = estado['y_raq_e'] + RAQUETE_TAMANHO // 2
        estado['bola_dx'] = 1
    else:
        estado['bola_x'] = X_RAQUETE_D - 1
        estado['bola_y'] = estado['y_raq_d'] + RAQUETE_TAMANHO // 2
        estado['bola_dx'] = -1
    estado['bola_dy'] = random.choice([-1, 0, 1])
    estado['bola_presa'] = True
    estado['bola_ticks_por_mov'] = BOLA_TICKS_INICIAL


def colide_com_raquete(x, y, lado):
    """Checa se (x,y) bate na raquete do lado dado."""
    yr = estado['y_raq_e'] if lado == 'e' else estado['y_raq_d']
    xr = X_RAQUETE_E if lado == 'e' else X_RAQUETE_D
    return x == xr and yr <= y < yr + RAQUETE_TAMANHO


def rebater_em_raquete(lado):
    """Inverte dx, ajusta dy conforme o ponto de impacto."""
    estado['bola_dx'] = -estado['bola_dx']
    yr = estado['y_raq_e'] if lado == 'e' else estado['y_raq_d']
    impacto = estado['bola_y'] - yr  # 0..RAQUETE_TAMANHO-1
    # extremidades viram pra' cima/baixo, meio horizontal
    if impacto <= 0:
        estado['bola_dy'] = -1
    elif impacto >= RAQUETE_TAMANHO - 1:
        estado['bola_dy'] = 1
    elif impacto == RAQUETE_TAMANHO // 2:
        estado['bola_dy'] = 0
    # acelera um pouquinho
    if estado['bola_ticks_por_mov'] > BOLA_TICKS_MIN:
        estado['bola_ticks_por_mov'] -= 0 if random.random() > 0.5 else 0
        # acelera so a cada algumas rebatidas (probabilistico)
        if random.random() < 0.3:
            estado['bola_ticks_por_mov'] = max(
                BOLA_TICKS_MIN, estado['bola_ticks_por_mov'] - 1)


def mover_bola():
    """Move 1 passo. Retorna 'ok' / 'ponto_e' / 'ponto_d'."""
    novo_x = estado['bola_x'] + estado['bola_dx']
    novo_y = estado['bola_y'] + estado['bola_dy']

    # rebate no topo/baixo
    if novo_y < Y_AREA_MIN:
        novo_y = Y_AREA_MIN
        estado['bola_dy'] = -estado['bola_dy']
    elif novo_y > Y_AREA_MAX:
        novo_y = Y_AREA_MAX
        estado['bola_dy'] = -estado['bola_dy']

    # colisao com raquete esquerda
    if colide_com_raquete(novo_x, novo_y, 'e'):
        rebater_em_raquete('e')
        novo_x = X_RAQUETE_E + 1
    # colisao com raquete direita
    elif colide_com_raquete(novo_x, novo_y, 'd'):
        rebater_em_raquete('d')
        novo_x = X_RAQUETE_D - 1

    # passou pela raquete? ponto pro adversario
    if novo_x <= 1:
        return 'ponto_d'   # passou pela raquete esquerda
    if novo_x >= LARGURA:
        return 'ponto_e'   # passou pela raquete direita

    # move
    apagar_bola(estado['bola_x'], estado['bola_y'])
    estado['bola_x'] = novo_x
    estado['bola_y'] = novo_y
    desenhar_bola(novo_x, novo_y)
    return 'ok'


def tela_pausa():
    msg = " *** PAUSA - tecla para continuar *** "
    x = (LARGURA - len(msg)) // 2
    goto_xy(x, 13)
    text(msg)
    set_key_released()
    read_key()
    goto_xy(x, 13)
    text(" " * len(msg))
    set_key_released()


def tela_inicial():
    clr_scr()
    goto_xy(28, 6); text("==========================")
    goto_xy(28, 7); text("         P O N G          ")
    goto_xy(28, 8); text("==========================")
    goto_xy(20, 11); text("Dois jogadores. Primeiro a "
                          + str(PONTOS_PARA_VENCER) + " pontos vence.")
    goto_xy(20, 13); text("Jogador 1 (esquerda): W sobe, S desce")
    goto_xy(20, 14); text("Jogador 2 (direita):  I sobe, K desce")
    goto_xy(20, 16); text("[Espaco] lanca a bola   [P] pausa   [Q] sai")
    goto_xy(20, 19); text("Pressione qualquer tecla para comecar...")
    set_key_released()
    read_key()


def tela_vitoria(vencedor):
    msg = f"     J O G A D O R   {vencedor}   V E N C E U !     "
    x = (LARGURA - len(msg)) // 2
    goto_xy(x, 12)
    text("+" + "-" * (len(msg) - 2) + "+")
    goto_xy(x, 13)
    text("|" + " " * (len(msg) - 2) + "|")
    goto_xy(x + 1, 13)
    text(msg[1:-1])
    goto_xy(x, 14)
    text("|" + " " * (len(msg) - 2) + "|")
    goto_xy(x, 15)
    text("+" + "-" * (len(msg) - 2) + "+")
    delay(1500)
    goto_xy(20, 18)
    text("Pressione qualquer tecla para sair.")
    set_key_released()
    read_key()


def jogar():
    clr_scr()
    set_cursor_off()
    reset_estado_jogo()
    desenhar_borda_e_meio()
    desenhar_raquete(X_RAQUETE_E, estado['y_raq_e'])
    desenhar_raquete(X_RAQUETE_D, estado['y_raq_d'])
    ajustar_bola_na_raquete()
    desenhar_bola(estado['bola_x'], estado['bola_y'])

    raquete_tick_counter = 0

    while True:
        # Pong precisa de leitura SIMULTANEA das duas raquetes.
        # Como get_key_code_pressed() retorna apenas a tecla mais
        # recente, consultamos diretamente o conjunto _keys_down (que
        # contem TODAS as teclas atualmente pressionadas) para mover
        # ambas as raquetes ao mesmo tempo.
        # Antes precisamos forcar o Tk a processar eventos pendentes,
        # o que e' feito por is_key_pressed():
        is_key_pressed()  # apenas para drenar eventos pendentes
        teclas_atuais = set(Pytme._keys_down)  # snapshot

        if VK_Q in teclas_atuais or VK_ESC in teclas_atuais:
            return
        if VK_P in teclas_atuais:
            tela_pausa()
            continue
        if VK_SPACE in teclas_atuais and estado['bola_presa']:
            estado['bola_presa'] = False

        if raquete_tick_counter >= RAQUETE_TICKS_POR_MOV:
            # Jogador 1 (esquerda)
            if VK_W in teclas_atuais:
                mover_raquete('e', -1)
            elif VK_S in teclas_atuais:
                mover_raquete('e', 1)
            # Jogador 2 (direita) — checado independentemente,
            # so na mesma iteracao do tick. Os dois podem mover juntos.
            if VK_I in teclas_atuais:
                mover_raquete('d', -1)
            elif VK_K in teclas_atuais:
                mover_raquete('d', 1)
            raquete_tick_counter = 0

        raquete_tick_counter += 1

        # bola
        if not estado['bola_presa']:
            estado['bola_tick_counter'] += 1
            if estado['bola_tick_counter'] >= estado['bola_ticks_por_mov']:
                estado['bola_tick_counter'] = 0
                resultado = mover_bola()
                if resultado == 'ponto_e':
                    estado['pontos_e'] += 1
                    estado['bola_lado_servico'] = 'd'
                    apagar_bola(estado['bola_x'], estado['bola_y'])
                    ajustar_bola_na_raquete()
                    desenhar_bola(estado['bola_x'], estado['bola_y'])
                    desenhar_placar()
                    if estado['pontos_e'] >= PONTOS_PARA_VENCER:
                        tela_vitoria(1)
                        return
                elif resultado == 'ponto_d':
                    estado['pontos_d'] += 1
                    estado['bola_lado_servico'] = 'e'
                    apagar_bola(estado['bola_x'], estado['bola_y'])
                    ajustar_bola_na_raquete()
                    desenhar_bola(estado['bola_x'], estado['bola_y'])
                    desenhar_placar()
                    if estado['pontos_d'] >= PONTOS_PARA_VENCER:
                        tela_vitoria(2)
                        return

        delay(TICK_MS)


# --- main ---
random.seed()
tela_inicial()
jogar()
