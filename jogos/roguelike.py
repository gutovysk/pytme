"""
    Roguelike Minimalista - usando PyTME
    
    Controles:
        Setas: move o personagem (atacando monstros se andar em cima deles)
        . (ponto): espera um turno
        > : desce escada (se estiver em uma)
        Q: sai do jogo
    
    Tiles:
        @ = voce      # = parede      . = chao
        M = monstro   $ = ouro        ! = pocao (cura 10 HP)
        > = escada para o proximo andar
    
    Objetivo: descer o maximo de andares e juntar o maximo de ouro.
    Cada andar e mais perigoso que o anterior.
"""

from PyTME import *
import random

set_cursor_off()  # retira o cursor da tela

# --- dimensoes ---
LARGURA = 80
ALTURA = 25
MAPA_X_INI, MAPA_X_FIM = 1, 80
MAPA_Y_INI, MAPA_Y_FIM = 2, 24
MAPA_LARGURA = MAPA_X_FIM - MAPA_X_INI + 1  # 80
MAPA_ALTURA = MAPA_Y_FIM - MAPA_Y_INI + 1   # 23

Y_MENSAGEM = 1
Y_HUD = 25

# --- tiles ---
PAREDE = '#'
CHAO = '.'
ESCADA = '>'
VAZIO = ' '

# --- teclas ---
VK_LEFT, VK_UP, VK_RIGHT, VK_DOWN = 37, 38, 39, 40
VK_Q = 81
# Para '.' e '>' usamos event.char (tecla), nao keycode — mais portavel.

# --- estado global ---
mapa = []            # mapa[y][x] = caracter (PAREDE, CHAO, ESCADA)
monstros = []        # lista de dicts {x, y, hp, atk, vivo}
ouros = []           # lista de (x, y)
pocoes = []          # lista de (x, y)
player = {'x': 0, 'y': 0, 'hp': 20, 'hp_max': 20, 'atk': 5, 'ouro': 0}
andar = 1
mensagens = []       # ultimas mensagens (mostramos a mais recente)


# --- utilitarios de mapa ---
def mapa_get(x, y):
    """x,y em coordenadas absolutas de tela. Retorna o caracter no mapa."""
    mx = x - MAPA_X_INI
    my = y - MAPA_Y_INI
    if mx < 0 or my < 0 or my >= MAPA_ALTURA or mx >= MAPA_LARGURA:
        return PAREDE
    return mapa[my][mx]


def mapa_set(x, y, c):
    mx = x - MAPA_X_INI
    my = y - MAPA_Y_INI
    if 0 <= mx < MAPA_LARGURA and 0 <= my < MAPA_ALTURA:
        mapa[my][mx] = c


def monstro_em(x, y):
    for m in monstros:
        if m['vivo'] and m['x'] == x and m['y'] == y:
            return m
    return None


def ouro_em(x, y):
    for i, (ox, oy) in enumerate(ouros):
        if ox == x and oy == y:
            return i
    return -1


def pocao_em(x, y):
    for i, (px, py) in enumerate(pocoes):
        if px == x and py == y:
            return i
    return -1


# --- geracao de mapa ---
def gerar_mapa():
    """Gera um mapa com salas retangulares conectadas por corredores."""
    global mapa
    mapa = [[PAREDE] * MAPA_LARGURA for _ in range(MAPA_ALTURA)]
    
    salas = []
    tentativas = 0
    while len(salas) < 6 and tentativas < 200:
        tentativas += 1
        w = random.randint(6, 14)
        h = random.randint(4, 7)
        x = random.randint(1, MAPA_LARGURA - w - 2)
        y = random.randint(1, MAPA_ALTURA - h - 2)
        # checa sobreposicao com margem de 1
        sobrepoe = False
        for (sx, sy, sw, sh) in salas:
            if (x < sx + sw + 1 and x + w + 1 > sx
                    and y < sy + sh + 1 and y + h + 1 > sy):
                sobrepoe = True
                break
        if not sobrepoe:
            salas.append((x, y, w, h))
    
    # esculpe salas
    for (x, y, w, h) in salas:
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                mapa[yy][xx] = CHAO
    
    # conecta salas (centro a centro, corredor em L)
    for i in range(1, len(salas)):
        x1 = salas[i-1][0] + salas[i-1][2] // 2
        y1 = salas[i-1][1] + salas[i-1][3] // 2
        x2 = salas[i][0] + salas[i][2] // 2
        y2 = salas[i][1] + salas[i][3] // 2
        # horizontal
        for x in range(min(x1, x2), max(x1, x2) + 1):
            mapa[y1][x] = CHAO
        # vertical
        for y in range(min(y1, y2), max(y1, y2) + 1):
            mapa[y][x2] = CHAO
    
    return salas


def posicao_aleatoria_em(sala):
    x, y, w, h = sala
    # coords absolutas:
    px = MAPA_X_INI + random.randint(x + 1, x + w - 2)
    py = MAPA_Y_INI + random.randint(y + 1, y + h - 2)
    return px, py


def gerar_andar():
    """Cria mapa, posiciona player, escada, monstros, ouros, pocoes."""
    global monstros, ouros, pocoes
    # tenta gerar ate ter pelo menos 2 salas
    salas = []
    for _ in range(10):
        salas = gerar_mapa()
        if len(salas) >= 2:
            break
    if len(salas) < 2:
        # super-fallback: cria duas salas fixas
        salas = [(2, 2, 10, 6), (60, 14, 12, 6)]
        for (x, y, w, h) in salas:
            for yy in range(y, y + h):
                for xx in range(x, x + w):
                    mapa[yy][xx] = CHAO
        for x in range(12, 66):
            mapa[5][x] = CHAO
        for y in range(5, 17):
            mapa[y][65] = CHAO
    
    # player na primeira sala
    player['x'], player['y'] = posicao_aleatoria_em(salas[0])
    
    # escada na ultima sala
    ex, ey = posicao_aleatoria_em(salas[-1])
    mapa_set(ex, ey, ESCADA)
    
    # monstros: 2 + andar, espalhados pelas salas (exceto a primeira)
    monstros = []
    n_monstros = 2 + andar
    for _ in range(n_monstros):
        sala = random.choice(salas[1:])
        mx, my = posicao_aleatoria_em(sala)
        # evita sobrepor escada ou outros monstros
        if mapa_get(mx, my) == ESCADA:
            continue
        if monstro_em(mx, my):
            continue
        hp = 5 + andar * 2 + random.randint(0, 3)
        atk = 2 + andar + random.randint(0, 1)
        monstros.append({'x': mx, 'y': my, 'hp': hp, 'atk': atk, 'vivo': True})
    
    # ouros: 3 + random
    ouros = []
    n_ouros = 3 + random.randint(0, 3)
    for _ in range(n_ouros):
        sala = random.choice(salas)
        ox, oy = posicao_aleatoria_em(sala)
        if (ox, oy) == (player['x'], player['y']):
            continue
        if monstro_em(ox, oy):
            continue
        if mapa_get(ox, oy) == ESCADA:
            continue
        ouros.append((ox, oy))
    
    # pocoes: 0-2
    pocoes = []
    for _ in range(random.randint(0, 2)):
        sala = random.choice(salas)
        px, py = posicao_aleatoria_em(sala)
        if (px, py) == (player['x'], player['y']):
            continue
        if monstro_em(px, py):
            continue
        if ouro_em(px, py) >= 0:
            continue
        if mapa_get(px, py) == ESCADA:
            continue
        pocoes.append((px, py))


# --- desenho ---
def desenhar_mapa():
    for my in range(MAPA_ALTURA):
        goto_xy(MAPA_X_INI, MAPA_Y_INI + my)
        text(''.join(mapa[my]))
    # ouros e pocoes em cima do mapa
    for (ox, oy) in ouros:
        goto_xy(ox, oy)
        text('$')
    for (px, py) in pocoes:
        goto_xy(px, py)
        text('!')
    # monstros
    for m in monstros:
        if m['vivo']:
            goto_xy(m['x'], m['y'])
            text('M')
    # player
    goto_xy(player['x'], player['y'])
    text('@')


def redesenhar_celula(x, y):
    """Redesenha uma celula com o que deve estar nela."""
    # prioridade: player > monstro > ouro/pocao > mapa
    if x == player['x'] and y == player['y']:
        c = '@'
    else:
        m = monstro_em(x, y)
        if m:
            c = 'M'
        elif ouro_em(x, y) >= 0:
            c = '$'
        elif pocao_em(x, y) >= 0:
            c = '!'
        else:
            c = mapa_get(x, y)
    goto_xy(x, y)
    text(c)


def desenhar_hud():
    goto_xy(1, Y_HUD)
    msg_hud = (" HP:" + str(player['hp']) + "/" + str(player['hp_max'])
               + " Ouro:" + str(player['ouro'])
               + " Andar:" + str(andar)
               + "  [setas] move [.] espera [>] desce [Q] sai")
    text(msg_hud[:78].ljust(78))


def msg(texto):
    """Mostra mensagem na linha 1."""
    goto_xy(1, Y_MENSAGEM)
    text(texto[:78].ljust(78))


# --- logica de turno ---
def tentar_mover_player(dx, dy):
    """Tenta mover o player em (dx,dy). Retorna True se houve acao
    valida (custou turno), False caso contrario."""
    nx = player['x'] + dx
    ny = player['y'] + dy
    
    if mapa_get(nx, ny) == PAREDE:
        msg("Voce esbarra na parede.")
        return False
    
    m = monstro_em(nx, ny)
    if m:
        # ataque: jogador bate primeiro
        dano = player['atk'] + random.randint(-1, 1)
        if dano < 1:
            dano = 1
        m['hp'] -= dano
        if m['hp'] <= 0:
            m['vivo'] = False
            msg("Voce matou o monstro! (" + str(dano) + " de dano)")
            redesenhar_celula(nx, ny)
            # nao se move sobre o cadaver — fica parado? Vou deixar mover.
            ant_x, ant_y = player['x'], player['y']
            player['x'], player['y'] = nx, ny
            redesenhar_celula(ant_x, ant_y)
            redesenhar_celula(nx, ny)
            verificar_item_em_pe()
            return True
        else:
            msg("Voce acerta o monstro (-" + str(dano)
                + ", HP dele: " + str(m['hp']) + ")")
            return True
    
    # move
    ant_x, ant_y = player['x'], player['y']
    player['x'], player['y'] = nx, ny
    redesenhar_celula(ant_x, ant_y)
    redesenhar_celula(nx, ny)
    verificar_item_em_pe()
    return True


def verificar_item_em_pe():
    """Pega ouro/pocao se o player parou em cima."""
    x, y = player['x'], player['y']
    i = ouro_em(x, y)
    if i >= 0:
        valor = random.randint(3, 10) + andar
        player['ouro'] += valor
        del ouros[i]
        msg("Voce pegou " + str(valor) + " moedas de ouro.")
        return
    i = pocao_em(x, y)
    if i >= 0:
        cura = 10
        player['hp'] = min(player['hp_max'], player['hp'] + cura)
        del pocoes[i]
        msg("Voce bebe uma pocao. (+" + str(cura) + " HP)")
        return


def turno_monstros():
    """Cada monstro tenta atacar ou se aproximar do jogador."""
    for m in monstros:
        if not m['vivo']:
            continue
        dx = player['x'] - m['x']
        dy = player['y'] - m['y']
        dist = max(abs(dx), abs(dy))
        
        # adjacente: ataca
        if dist == 1:
            dano = m['atk'] + random.randint(-1, 1)
            if dano < 1:
                dano = 1
            player['hp'] -= dano
            msg("Monstro te atacou! (-" + str(dano)
                + ", seu HP: " + str(max(0, player['hp'])) + ")")
            if player['hp'] <= 0:
                return  # morreu, sai
            continue
        
        # so persegue se "viu" o jogador (a uma distancia razoavel)
        if dist > 8:
            continue
        
        # tenta andar em direcao ao jogador (escolhe melhor eixo)
        passo_x = 0 if dx == 0 else (1 if dx > 0 else -1)
        passo_y = 0 if dy == 0 else (1 if dy > 0 else -1)
        # tenta diagonal primeiro? Movimento ortogonal apenas para
        # simplificar: prioriza o eixo com maior distancia
        tentativas = []
        if abs(dx) >= abs(dy):
            tentativas = [(passo_x, 0), (0, passo_y)]
        else:
            tentativas = [(0, passo_y), (passo_x, 0)]
        
        for (px, py) in tentativas:
            if px == 0 and py == 0:
                continue
            nx, ny = m['x'] + px, m['y'] + py
            if mapa_get(nx, ny) == PAREDE:
                continue
            if monstro_em(nx, ny):
                continue
            if nx == player['x'] and ny == player['y']:
                continue
            ant_x, ant_y = m['x'], m['y']
            m['x'], m['y'] = nx, ny
            redesenhar_celula(ant_x, ant_y)
            redesenhar_celula(nx, ny)
            break


# --- telas ---
def tela_inicial():
    clr_scr()
    goto_xy(28, 6)
    text("=================================")
    goto_xy(28, 7)
    text("   R O G U E L I K E   M I N I   ")
    goto_xy(28, 8)
    text("=================================")
    goto_xy(10, 11)
    text("Voce esta numa masmorra. Encontre a escada > e desca o maximo")
    goto_xy(10, 12)
    text("de andares. Cada andar e mais perigoso que o anterior.")
    goto_xy(10, 14)
    text("Tiles:")
    goto_xy(12, 15)
    text("@ voce    # parede   . chao    > escada")
    goto_xy(12, 16)
    text("M monstro $ ouro     ! pocao (cura 10 HP)")
    goto_xy(10, 18)
    text("Setas movem (atacam se for em direcao a um monstro).")
    goto_xy(10, 19)
    text("Tecle '.' para esperar, '>' para descer, 'Q' para sair.")
    goto_xy(20, 22)
    text("Pressione qualquer tecla para comecar...")
    set_key_released()
    read_key()


def tela_morte():
    goto_xy(28, 11)
    text("+--------------------------+")
    goto_xy(28, 12)
    text("|    V O C E   M O R R E U |")
    goto_xy(28, 13)
    text("|                          |")
    goto_xy(28, 14)
    text("|  Andar:  " + str(andar).ljust(16) + "|")
    goto_xy(28, 15)
    text("|  Ouro:   " + str(player['ouro']).ljust(16) + "|")
    goto_xy(28, 16)
    text("+--------------------------+")
    delay(2000)
    goto_xy(20, 19)
    text("Pressione qualquer tecla para sair.")
    set_key_released()
    read_key()


def desceu_escada():
    global andar
    andar += 1
    # recupera um pouco de HP ao descer
    cura = 5
    player['hp'] = min(player['hp_max'], player['hp'] + cura)
    msg("Voce desce a escada para o andar " + str(andar)
        + ". (+" + str(cura) + " HP)")
    delay(800)
    clr_scr()
    gerar_andar()
    desenhar_mapa()
    desenhar_hud()
    msg("Andar " + str(andar) + ".")


def jogar():
    global andar
    andar = 1
    player['hp'] = player['hp_max']
    player['ouro'] = 0
    
    clr_scr()
    gerar_andar()
    desenhar_mapa()
    desenhar_hud()
    msg("Bem-vindo a masmorra. Andar 1.")
    
    while True:
        if player['hp'] <= 0:
            desenhar_hud()
            delay(500)
            tela_morte()
            return
        
        # le tecla (bloqueante, jogo por turnos)
        set_key_released()
        tecla = read_key()
        codigo = get_key_code_pressed()
        
        agiu = False
        
        if codigo == VK_Q:
            return
        elif codigo == VK_LEFT:
            agiu = tentar_mover_player(-1, 0)
        elif codigo == VK_RIGHT:
            agiu = tentar_mover_player(1, 0)
        elif codigo == VK_UP:
            agiu = tentar_mover_player(0, -1)
        elif codigo == VK_DOWN:
            agiu = tentar_mover_player(0, 1)
        elif tecla == '.':
            msg("Voce espera.")
            agiu = True
        elif tecla == '>':
            if mapa_get(player['x'], player['y']) == ESCADA:
                desceu_escada()
                continue  # nao precisa rodar turno dos monstros
            else:
                msg("Nao ha escada aqui.")
        else:
            # tecla nao reconhecida — nao consome turno
            pass
        
        if agiu:
            turno_monstros()
            desenhar_hud()


# --- main ---
random.seed()
tela_inicial()
jogar()
