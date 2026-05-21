"""
    Caca-Comida (O contra X) - usando Jtme

    Objetivo: pegar as comidas (@) sem ser pego pelo inimigo (X) e sem
    ficar sem energia. A energia cai com o tempo; cada @ da +100 pontos
    e +30 energia. A cada 1000 pontos voce ganha uma vida. A velocidade
    do X aumenta a cada fase. A fase aumenta a cada 500 pontos.

    Apos a fase 10, surgem dois portais (&) — entre num e e teleportado
    pro outro. Os portais somem e reaparecem aleatoriamente.

    Sem paredes laterais: o O passa de um lado para o outro (wrap).

    Controles:
        Setas     - move o O
        Q ou ESC  - sai do jogo
        Enter     - recomecar apos perder vida
"""

from Jtme import *
import random
import time


# ============================================================
# constantes
# ============================================================

# area de jogo (HUD ocupa linha 1; linha 25 e' folga)
X_MIN, X_MAX = 2, 79
Y_MIN, Y_MAX = 2, 24
Y_HUD = 1

# velocidade do tick base (ms)
TICK_MS = 50

set_cursor_off()  # retira o cursor da tela

# Quanto o inimigo X anda em "ticks por movimento".
# Comeca lento (1 movimento a cada 8 ticks = 2.5 mov/s) e desce 1 por fase.
def x_ticks_por_mov(fase):
    return max(2, 9 - fase)

# Energia: cai 1 ponto a cada N ticks. (Em ticks de 50ms, 30 ticks = 1.5s.)
ENERGIA_TICKS = 30
ENERGIA_INICIAL = 100
ENERGIA_MAX = 100

# Comida @
COMIDA_PONTOS = 100
COMIDA_ENERGIA = 30
COMIDA_DURACAO_TICKS_MIN = 60     # 3s
COMIDA_DURACAO_TICKS_MAX = 160    # 8s
COMIDA_CHANCE_SPAWN = 0.02        # 2% por tick quando nao ha comida

# Portais (a partir da fase 11)
PORTAL_CHAR = "&"
PORTAL_FASE_MINIMA = 11
PORTAL_DURACAO_TICKS_MIN = 200    # 10s
PORTAL_DURACAO_TICKS_MAX = 400    # 20s
PORTAL_CHANCE_SPAWN = 0.005       # 0.5% por tick quando nao ha portais

# Vidas
VIDAS_INICIAIS = 3
PONTOS_POR_VIDA_EXTRA = 1000

# Fases
PONTOS_POR_FASE = 500

# Codigos de tecla
VK_LEFT, VK_UP, VK_RIGHT, VK_DOWN = 37, 38, 39, 40
VK_Q, VK_ESC, VK_ENTER = 81, 27, 13
VK_R, VK_T = 82, 84

NOME_MAX = 20


# ============================================================
# estado do jogo (em dict para facil reset)
# ============================================================

def novo_estado(nome):
    return {
        'nome': nome,
        'player_x': 40, 'player_y': 12,
        'inimigo_x': 5, 'inimigo_y': 5,
        'pontos': 0,
        'vidas': VIDAS_INICIAIS,
        'fase': 1,
        'energia': ENERGIA_INICIAL,
        't0': time.time(),         # inicio da sessao (timer cumulativo)
        't_pausa': 0,              # tempo total pausado
        'ticks': 0,
        'comida': None,            # (x, y, ticks_restantes) ou None
        'comida_total_ticks': 0,
        'portais': None,           # ((x1,y1),(x2,y2),ticks_restantes) ou None
        'x_tick_counter': 0,
        'energia_tick_counter': 0,
        'proxima_vida_extra': PONTOS_POR_VIDA_EXTRA,
    }


# ============================================================
# utilidades de tela
# ============================================================

def formatar_tempo(segundos):
    """Formata segundos em '00d00h00m00s000'."""
    ms_total = int(segundos * 1000)
    ms = ms_total % 1000
    s_total = ms_total // 1000
    s = s_total % 60
    m_total = s_total // 60
    m = m_total % 60
    h_total = m_total // 60
    h = h_total % 24
    d = h_total // 24
    return f"{d:02d}d{h:02d}h{m:02d}m{s:02d}s{ms:03d}"


def desenhar_hud(estado):
    """Desenha o HUD na linha 1.
       Formato (78 colunas, comeca em x=2):
         nome (20) v:N F:NN 00d00h00m00s000 E:NNN P:NNNNNN
    """
    tempo = time.time() - estado['t0'] - estado['t_pausa']
    nome = estado['nome'][:NOME_MAX].ljust(NOME_MAX)
    msg = (f" {nome} v:{estado['vidas']:1d} F:{estado['fase']:02d} "
           f"{formatar_tempo(tempo)} "
           f"E:{estado['energia']:03d} P:{estado['pontos']:06d} ")
    # garante 78 chars
    msg = msg[:78].ljust(78)
    goto_xy(2, Y_HUD)
    text(msg)


def desenhar_borda():
    # so a linha de separacao entre HUD e area de jogo
    goto_xy(1, 2)
    text("-" * 80)


def limpar_area_jogo():
    """Apaga area de jogo (sem mexer no HUD)."""
    for y in range(Y_MIN + 1, Y_MAX + 1):  # +1 porque Y_MIN=2 e' a linha separadora
        goto_xy(1, y)
        text(" " * 80)


# ============================================================
# movimento e colisao
# ============================================================

def wrap_x(x):
    if x < X_MIN:
        return X_MAX
    if x > X_MAX:
        return X_MIN
    return x


def wrap_y(y):
    if y < Y_MIN + 1:    # +1 porque Y_MIN=2 e' a borda
        return Y_MAX
    if y > Y_MAX:
        return Y_MIN + 1
    return y


def passo_minimo(de, ate, modulo):
    """Retorna -1/0/+1 indicando para qual lado andar de 'de' a 'ate'
    considerando wraparound de 'modulo' celulas. Escolhe o caminho mais curto."""
    if de == ate:
        return 0
    direto = ate - de
    indireto = direto - modulo if direto > 0 else direto + modulo
    if abs(direto) <= abs(indireto):
        return 1 if direto > 0 else -1
    else:
        return 1 if indireto > 0 else -1


def passo_inimigo_em_direcao_a_player(estado):
    """Calcula (dx, dy) com wraparound."""
    LARG = X_MAX - X_MIN + 1
    ALT = Y_MAX - (Y_MIN + 1) + 1
    dx = passo_minimo(estado['inimigo_x'], estado['player_x'], LARG)
    dy = passo_minimo(estado['inimigo_y'], estado['player_y'], ALT)
    return dx, dy


# ============================================================
# rendering incremental
# ============================================================

def desenhar_em(x, y, c):
    if X_MIN <= x <= X_MAX and (Y_MIN + 1) <= y <= Y_MAX:
        goto_xy(x, y)
        text(c)


def apagar_em(x, y):
    desenhar_em(x, y, " ")


# ============================================================
# tela inicial e menus
# ============================================================

def tela_pedir_nome():
    clr_scr()
    goto_xy(20, 6)
    text("================================================")
    goto_xy(20, 7)
    text("           C A C A   -   C O M I D A             ")
    goto_xy(20, 8)
    text("================================================")
    goto_xy(20, 11)
    text("Voce e o O. Pegue as @ e fuja do X.")
    goto_xy(20, 12)
    text("A cada @ ganha 100 pts e 30 de energia.")
    goto_xy(20, 13)
    text("Energia cai com o tempo. A 1000 pts ganha vida.")
    goto_xy(20, 14)
    text("Apos fase 10, surgem portais (&).")
    goto_xy(20, 15)
    text("Sem paredes: passa de um lado pro outro.")
    goto_xy(20, 17)
    text("Setas movem o O. Q ou ESC sai.")
    goto_xy(20, 20)
    text("Seu nome (max 20 caracteres): ")
    nome = type_text()
    nome = nome.strip()[:NOME_MAX]
    if not nome:
        nome = "Anonimo"
    return nome


def tela_aguarda_enter(estado, motivo):
    """Mensagem que aparece quando perde uma vida. Retorna False se quiser sair."""
    # mostra mensagem no centro
    msg = "(" + motivo + ")"
    box_w = 50
    box_x = (80 - box_w) // 2
    box_y = 11
    # caixa
    goto_xy(box_x, box_y)
    text("+" + "-" * (box_w - 2) + "+")
    for i in range(1, 5):
        goto_xy(box_x, box_y + i)
        text("|" + " " * (box_w - 2) + "|")
    goto_xy(box_x, box_y + 5)
    text("+" + "-" * (box_w - 2) + "+")
    # textos centralizados
    def linha_centro(y, s):
        x = box_x + (box_w - len(s)) // 2
        goto_xy(x, y)
        text(s)
    linha_centro(box_y + 1, "Voce perdeu uma vida!")
    linha_centro(box_y + 2, msg)
    linha_centro(box_y + 3, f"Vidas restantes: {estado['vidas']}")
    linha_centro(box_y + 4, "Pressione ENTER para continuar (Q/ESC sai)")

    # registra tempo de pausa
    pausa_inicio = time.time()
    set_key_released()
    while True:
        if is_key_pressed():
            codigo = get_key_code_pressed()
            set_key_released()
            if codigo == VK_Q or codigo == VK_ESC:
                return False
            if codigo == VK_ENTER:
                break
        delay(20)

    estado['t_pausa'] += time.time() - pausa_inicio
    return True


def tela_game_over_menu(nome, pontuacoes_sessao):
    """Tela final. Retorna 'mesmo', 'trocar' ou 'sair'."""
    clr_scr()
    goto_xy(20, 4)
    text("================================================")
    goto_xy(20, 5)
    text("              G A M E   O V E R                  ")
    goto_xy(20, 6)
    text("================================================")
    goto_xy(20, 8)
    text(f"Jogador: {nome}")
    goto_xy(20, 9)
    text("Suas pontuacoes nesta sessao:")
    for i, p in enumerate(pontuacoes_sessao[-10:]):
        goto_xy(22, 10 + i)
        text(f"  Tentativa {i + 1:2d}: {p:6d} pontos")
    melhor = max(pontuacoes_sessao) if pontuacoes_sessao else 0
    media = sum(pontuacoes_sessao) // len(pontuacoes_sessao) if pontuacoes_sessao else 0
    goto_xy(20, 21)
    text(f"Melhor: {melhor}    Media: {media}")

    goto_xy(20, 23)
    text("[R] Recomecar com mesmo jogador")
    goto_xy(20, 24)
    text("[T] Trocar de jogador     [Q] Sair")

    set_key_released()
    while True:
        if is_key_pressed():
            codigo = get_key_code_pressed()
            set_key_released()
            if codigo == VK_R or codigo == VK_ENTER:
                return 'mesmo'
            if codigo == VK_T:
                return 'trocar'
            if codigo == VK_Q or codigo == VK_ESC:
                return 'sair'
        delay(20)


# ============================================================
# spawn de objetos
# ============================================================

def posicao_aleatoria_livre(estado):
    """Posicao na area de jogo que nao colida com player, inimigo,
    comida, portais."""
    for _ in range(50):
        x = random.randint(X_MIN, X_MAX)
        y = random.randint(Y_MIN + 1, Y_MAX)
        if (x, y) == (estado['player_x'], estado['player_y']):
            continue
        if (x, y) == (estado['inimigo_x'], estado['inimigo_y']):
            continue
        if estado['comida'] is not None:
            cx, cy, _ = estado['comida']
            if (x, y) == (cx, cy):
                continue
        if estado['portais'] is not None:
            (p1, p2, _) = estado['portais']
            if (x, y) == p1 or (x, y) == p2:
                continue
        return x, y
    return None


def spawn_comida(estado):
    pos = posicao_aleatoria_livre(estado)
    if pos is None:
        return
    duracao = random.randint(COMIDA_DURACAO_TICKS_MIN, COMIDA_DURACAO_TICKS_MAX)
    estado['comida'] = (pos[0], pos[1], duracao)
    estado['comida_total_ticks'] = duracao
    desenhar_em(pos[0], pos[1], "@")


def apagar_comida(estado):
    if estado['comida'] is None:
        return
    cx, cy, _ = estado['comida']
    # so apaga se nada estiver em cima
    if (cx, cy) != (estado['player_x'], estado['player_y']) and \
       (cx, cy) != (estado['inimigo_x'], estado['inimigo_y']):
        apagar_em(cx, cy)
    estado['comida'] = None


def spawn_portais(estado):
    if estado['fase'] < PORTAL_FASE_MINIMA:
        return
    p1 = posicao_aleatoria_livre(estado)
    if p1 is None:
        return
    # cria temporario para excluir p1 da segunda escolha
    estado['portais'] = (p1, (-9, -9), 0)
    p2 = posicao_aleatoria_livre(estado)
    if p2 is None:
        estado['portais'] = None
        return
    duracao = random.randint(PORTAL_DURACAO_TICKS_MIN, PORTAL_DURACAO_TICKS_MAX)
    estado['portais'] = (p1, p2, duracao)
    desenhar_em(p1[0], p1[1], PORTAL_CHAR)
    desenhar_em(p2[0], p2[1], PORTAL_CHAR)


def apagar_portais(estado):
    if estado['portais'] is None:
        return
    p1, p2, _ = estado['portais']
    for (px, py) in (p1, p2):
        if (px, py) != (estado['player_x'], estado['player_y']) and \
           (px, py) != (estado['inimigo_x'], estado['inimigo_y']):
            apagar_em(px, py)
    estado['portais'] = None


# ============================================================
# logica de um tick
# ============================================================

def mover_player(estado, dx, dy):
    if dx == 0 and dy == 0:
        return
    novo_x = wrap_x(estado['player_x'] + dx)
    novo_y = wrap_y(estado['player_y'] + dy)

    # apaga posicao antiga
    px, py = estado['player_x'], estado['player_y']
    apagar_em(px, py)
    # se havia algo embaixo do jogador, redesenha:
    #  - inimigo (caso esteja exatamente em cima — ja' indica colisao)
    if (px, py) == (estado['inimigo_x'], estado['inimigo_y']):
        desenhar_em(px, py, "X")
    #  - comida embaixo (jogador estava sobre comida que ainda nao pegou,
    #    ou caso patologico — manter por seguranca)
    if estado['comida'] is not None:
        cx, cy, _ = estado['comida']
        if (cx, cy) == (px, py):
            desenhar_em(cx, cy, "@")
    #  - portal embaixo (caso comum: jogador acabou de sair de um portal)
    if estado['portais'] is not None:
        p1, p2, _ = estado['portais']
        for (qx, qy) in (p1, p2):
            if (qx, qy) == (px, py):
                desenhar_em(qx, qy, PORTAL_CHAR)

    estado['player_x'] = novo_x
    estado['player_y'] = novo_y

    # verificar colisoes apos mover
    verificar_pegou_comida(estado)
    verificar_entrou_portal(estado)

    # redesenha jogador na posicao final (pode ter sido teleportado)
    desenhar_em(estado['player_x'], estado['player_y'], "O")


def mover_inimigo(estado):
    dx, dy = passo_inimigo_em_direcao_a_player(estado)
    if dx == 0 and dy == 0:
        return  # ja em cima do jogador, sera detectado em verificar_colisao
    novo_x = wrap_x(estado['inimigo_x'] + dx)
    novo_y = wrap_y(estado['inimigo_y'] + dy)

    # apaga posicao antiga e redesenha o que estava embaixo
    ix, iy = estado['inimigo_x'], estado['inimigo_y']
    apagar_em(ix, iy)
    # se havia comida na posicao antiga, redesenha
    if estado['comida'] is not None:
        cx, cy, _ = estado['comida']
        if (cx, cy) == (ix, iy):
            desenhar_em(cx, cy, "@")
    # se havia portal
    if estado['portais'] is not None:
        p1, p2, _ = estado['portais']
        for (px, py) in (p1, p2):
            if (px, py) == (ix, iy):
                desenhar_em(px, py, PORTAL_CHAR)

    estado['inimigo_x'] = novo_x
    estado['inimigo_y'] = novo_y
    desenhar_em(novo_x, novo_y, "X")


def verificar_pegou_comida(estado):
    if estado['comida'] is None:
        return
    cx, cy, _ = estado['comida']
    if (estado['player_x'], estado['player_y']) == (cx, cy):
        estado['pontos'] += COMIDA_PONTOS
        estado['energia'] = min(ENERGIA_MAX,
                                estado['energia'] + COMIDA_ENERGIA)
        estado['comida'] = None
        # checar vida extra
        while estado['pontos'] >= estado['proxima_vida_extra']:
            estado['vidas'] += 1
            estado['proxima_vida_extra'] += PONTOS_POR_VIDA_EXTRA
        # checar mudanca de fase
        nova_fase = 1 + estado['pontos'] // PONTOS_POR_FASE
        if nova_fase > estado['fase']:
            estado['fase'] = nova_fase


def verificar_entrou_portal(estado):
    if estado['portais'] is None:
        return
    p1, p2, dur = estado['portais']
    pos = (estado['player_x'], estado['player_y'])
    destino = None
    if pos == p1:
        destino = p2
    elif pos == p2:
        destino = p1
    if destino is None:
        return
    # teleporta. NAO precisamos redesenhar o portal de origem: o proprio
    # mover_player ja' redesenha portal embaixo do jogador no proximo
    # movimento. Mas como o jogador some daqui agora, garantimos que o
    # portal de saida fica visivel:
    desenhar_em(pos[0], pos[1], PORTAL_CHAR)
    estado['player_x'] = destino[0]
    estado['player_y'] = destino[1]
    # o "O" sera desenhado em destino pelo mover_player (caller).


def colidiu_com_inimigo(estado):
    return (estado['player_x'], estado['player_y']) == \
           (estado['inimigo_x'], estado['inimigo_y'])


# ============================================================
# loop principal de uma "vida"
# ============================================================

def jogar_uma_vida(estado):
    """Roda ate o jogador morrer ou pedir para sair.
    Retorna: 'pego', 'sem_energia' ou 'sair'."""

    # inicializa posicoes
    estado['player_x'], estado['player_y'] = 40, 13
    # inimigo comeca longe
    estado['inimigo_x'], estado['inimigo_y'] = 5, 4
    estado['comida'] = None
    estado['portais'] = None
    estado['x_tick_counter'] = 0
    estado['energia_tick_counter'] = 0

    # redesenha cenario
    limpar_area_jogo()
    desenhar_em(estado['player_x'], estado['player_y'], "O")
    desenhar_em(estado['inimigo_x'], estado['inimigo_y'], "X")
    desenhar_hud(estado)

    # contador para nao redesenhar o HUD a cada tick (so a cada 2 ticks
    # para o timer atualizar a ~50ms o que ja' e suficiente)
    hud_counter = 0

    while True:
        estado['ticks'] += 1
        hud_counter += 1

        # ler teclado (nao-bloqueante)
        dx, dy = 0, 0
        if is_key_pressed():
            codigo = get_key_code_pressed()
            if codigo == VK_Q or codigo == VK_ESC:
                return 'sair'
            elif codigo == VK_LEFT:
                dx = -1
            elif codigo == VK_RIGHT:
                dx = 1
            elif codigo == VK_UP:
                dy = -1
            elif codigo == VK_DOWN:
                dy = 1
            # NAO chamamos set_key_released — segurar tecla deve mover continuo

        if dx != 0 or dy != 0:
            mover_player(estado, dx, dy)
            if colidiu_com_inimigo(estado):
                return 'pego'

        # inimigo
        estado['x_tick_counter'] += 1
        if estado['x_tick_counter'] >= x_ticks_por_mov(estado['fase']):
            estado['x_tick_counter'] = 0
            mover_inimigo(estado)
            if colidiu_com_inimigo(estado):
                return 'pego'

        # energia
        estado['energia_tick_counter'] += 1
        if estado['energia_tick_counter'] >= ENERGIA_TICKS:
            estado['energia_tick_counter'] = 0
            estado['energia'] -= 1
            if estado['energia'] <= 0:
                estado['energia'] = 0
                return 'sem_energia'

        # comida: expira ou spawna
        if estado['comida'] is not None:
            cx, cy, restante = estado['comida']
            restante -= 1
            if restante <= 0:
                apagar_comida(estado)
            else:
                estado['comida'] = (cx, cy, restante)
        else:
            if random.random() < COMIDA_CHANCE_SPAWN:
                spawn_comida(estado)

        # portais
        if estado['portais'] is not None:
            p1, p2, restante = estado['portais']
            restante -= 1
            if restante <= 0:
                apagar_portais(estado)
            else:
                estado['portais'] = (p1, p2, restante)
        else:
            if estado['fase'] >= PORTAL_FASE_MINIMA:
                if random.random() < PORTAL_CHANCE_SPAWN:
                    spawn_portais(estado)

        # HUD: redesenha a cada tick para o timer atualizar suave
        if hud_counter >= 1:
            desenhar_hud(estado)
            hud_counter = 0

        delay(TICK_MS)


# ============================================================
# loop de sessao (3 vidas)
# ============================================================

def jogar_sessao(nome):
    """Joga uma sessao completa ate game over. Retorna a lista de
    pontuacoes (cada item = pontos ao final de uma vida)."""
    pontuacoes = []
    estado = novo_estado(nome)

    # prepara tela
    clr_scr()
    desenhar_borda()

    while estado['vidas'] > 0:
        motivo = jogar_uma_vida(estado)
        pontuacoes.append(estado['pontos'])

        if motivo == 'sair':
            return pontuacoes, 'sair'

        estado['vidas'] -= 1
        # reseta energia para a proxima vida
        estado['energia'] = ENERGIA_INICIAL

        if estado['vidas'] > 0:
            motivo_msg = "Pego pelo X!" if motivo == 'pego' else "Sem energia!"
            continuar = tela_aguarda_enter(estado, motivo_msg)
            if not continuar:
                return pontuacoes, 'sair'
            # limpa a caixa antes de continuar
            limpar_area_jogo()
            desenhar_hud(estado)
        # se vidas == 0, sai do while e vai pro menu

    return pontuacoes, 'fim'


# ============================================================
# main
# ============================================================

def main():
    random.seed()
    nome = None
    while True:
        if nome is None:
            nome = tela_pedir_nome()
        pontuacoes, motivo = jogar_sessao(nome)
        if motivo == 'sair':
            break
        escolha = tela_game_over_menu(nome, pontuacoes)
        if escolha == 'sair':
            break
        elif escolha == 'trocar':
            nome = None
        # else 'mesmo': mantem nome, novo loop


main()
